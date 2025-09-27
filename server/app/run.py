#!/usr/bin/env python3
"""
Enhanced TernakLele Loop Runner (simplified, improved logging + colors)
- Runs ALL solvers every RUN_INTERVAL seconds against all teams
- Starts a dedicated thread per solver script (this is ALWAYS used, independent of USE_THREADING)
- USE_THREADING toggles whether each solver will attack its teams concurrently (per-solver executor)
- Watches ./solvers for new/updated solver .py and runs them immediately
- Deduplicates flags, keeps pending queue in-memory
- Applies grace window before submitting freshly-discovered flags
- Uses repo's configured protocol module (CONFIG['SYSTEM_PROTOCOL']) to submit flags

Place this file under your `app/` package (e.g. server/app/cli_runner_enhanced.py) and run
from the repository root (so `app` package is importable):

  python -m app.run

Configuration keys (in CONFIG) that are used/added:
 - RUN_INTERVAL (seconds, default 30)
 - WATCH_POLL (seconds, default 2)
 - SOLVER_TIMEOUT (seconds, default 60)
 - SUBMIT_FLAG_LIMIT (int) - forwarded to get_fair_share
 - SUBMIT_GRACE_SECONDS (sec, default 5)
 - USE_THREADING (bool) - when True each solver will run attacks against teams concurrently; when False each solver will run teams sequentially
"""
from __future__ import annotations

import os
import sys
import re
import time
import signal
import subprocess
import threading
import functools
import logging
import queue
from pathlib import Path
from typing import Dict, List, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, Future
import importlib

# Ensure app package importable when placed under server/app/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# repo imports
from config import CONFIG
from models import Flag, FlagStatus, SubmitResult
from utils import get_fair_share

# Load protocol submit implementation via CONFIG
SYSTEM_PROTOCOL = CONFIG.get('SYSTEM_PROTOCOL', 'ailurus')
try:
    protocol_module = importlib.import_module(f'protocols.{SYSTEM_PROTOCOL}')
    submit_flags_impl = getattr(protocol_module, 'submit_flags')
except Exception:
    raise RuntimeError(f"Failed to import protocol module protocols.{SYSTEM_PROTOCOL} or it lacks submit_flags")

# Config defaults
RUN_INTERVAL = int(CONFIG.get('RUN_INTERVAL', 30))
WATCH_POLL = int(CONFIG.get('WATCH_POLL', 2))
SOLVER_TIMEOUT = int(CONFIG.get('SOLVER_TIMEOUT', 60))
SUBMIT_GRACE_SECONDS = int(CONFIG.get('SUBMIT_GRACE_SECONDS', 5))

# ANSI color codes
COLORS = {
    'reset': '\u001b[0m',
    'red': '\u001b[31m',
    'green': '\u001b[32m',
    'yellow': '\u001b[33m',
    'blue': '\u001b[34m',
    'magenta': '\u001b[35m',
    'cyan': '\u001b[36m',
    'bold': '\u001b[1m'
}

def colorize(text: str, color: str) -> str:
    code = COLORS.get(color, '')
    reset = COLORS['reset']
    return f"{code}{text}{reset}" if code else text

# Setup logging (console only) with time-only timestamps
class ColoredFormatter(logging.Formatter):
    LEVEL_COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red'
    }

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record):
        # color levelname
        lvl = record.levelname
        col = self.LEVEL_COLORS.get(lvl, None)
        if col:
            record.levelname = colorize(lvl, col)
        # format message normally
        msg = super().format(record)
        return msg

logger = logging.getLogger('->')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# time only: HH:MM:SS
fmt = '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
ch.setFormatter(ColoredFormatter(fmt=fmt, datefmt='%H:%M:%S'))
logger.addHandler(ch)

# Internal runtime state
print_lock = threading.Lock()  # serialize prints

class SolverMonitor:
    def __init__(self, solvers_dir: Path):
        self.solvers_dir = solvers_dir
        self._mtimes: Dict[str, float] = {}

    def scan(self) -> List[Path]:
        found = []
        if not self.solvers_dir.exists():
            return found
        current_files = [p for p in self.solvers_dir.glob('*.py') if p.is_file()]
        current_map = {str(p.resolve()): p for p in current_files}

        # removed
        removed = set(self._mtimes.keys()) - set(current_map.keys())
        for r in removed:
            del self._mtimes[r]

        for p_str, p in current_map.items():
            try:
                m = p.stat().st_mtime
            except Exception:
                m = 0
            prev = self._mtimes.get(p_str)
            if prev is None:
                found.append(p)
                self._mtimes[p_str] = m
            else:
                if m != prev:
                    found.append(p)
                    self._mtimes[p_str] = m
        return sorted(found)

# Runner helpers

def find_flags_in_output(output: str, flag_format: re.Pattern) -> List[str]:
    return flag_format.findall(output)


def run_solver_process(solver_path: Path, target_ip: str, timeout: int = SOLVER_TIMEOUT) -> Tuple[str, bool]:
    try:
        cmd = [sys.executable, str(solver_path), target_ip]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (proc.stdout or '') + (proc.stderr or '')
        return out, proc.returncode == 0
    except subprocess.TimeoutExpired:
        return f"Solver timed out after {timeout} seconds", False
    except Exception as e:
        return f"Error running solver: {e}", False


def create_flag_objects(flags: List[str], solver_name: str, team_name: str) -> List[Flag]:
    objs = []
    now = int(time.time())
    for f in flags:
        flag_obj = Flag(
            flag=f,
            sploit=solver_name,
            team=team_name,
            time=now,
            status=FlagStatus.QUEUED,
            checksystem_response=""
        )
        objs.append(flag_obj)
    return objs


def submit_flags_to_system(flag_objs: List[Flag]) -> List[SubmitResult]:
    if not flag_objs:
        return []
    try:
        return list(submit_flags_impl(flag_objs, CONFIG))
    except Exception:
        logger.exception('Exception when submitting flags')
        return []


def summarize_results(results: List[SubmitResult]):
    accepted = sum(1 for r in results if getattr(r, 'status', None) == FlagStatus.ACCEPTED)
    rejected = sum(1 for r in results if getattr(r, 'status', None) == FlagStatus.REJECTED)
    queued = sum(1 for r in results if getattr(r, 'status', None) == FlagStatus.QUEUED)
    logger.info('Submission Summary: accepted=%d rejected=%d queued=%d', accepted, rejected, queued)

# Emoji helpers
EMOJI = {
    'found': '🏁',
    'submit': '📤',
    'added': '➕',
    'scheduled': '▶️',
    'accepted': '✅',
    'rejected': '❌',
    'queued': '⏳',
    'skipped': '⏭️',
    'error': '⚠️'
}

# Short helper to format a list of flags nicely (limit and join), colored
def format_flags_list(flags: List[str], limit: int = 10) -> str:
    if not flags:
        return ''
    display = flags if len(flags) <= limit else flags[:limit]
    s = ', '.join(display)
    if len(flags) > limit:
        s += f', ...(+{len(flags)-limit} more)'
    return colorize(s, 'cyan')

# Main loop

def main_loop():
    config = CONFIG
    # NOTE: USE_THREADING now controls per-solver concurrency (i.e. whether a solver attacks multiple teams concurrently).
    use_threading = bool(config.get('USE_THREADING', True))

    logger.info('Starting enhanced runner: per-solver threads ALWAYS on. Per-solver concurrent attacks=%s', use_threading)

    flag_regex = re.compile(config['FLAG_FORMAT'])
    solvers_dir = Path(__file__).parent / 'solvers'

    if not solvers_dir.exists():
        logger.error('Solvers dir not found: %s', solvers_dir)
        return

    teams = config.get('TEAMS', {})
    if not teams:
        logger.error('No TEAMS configured in CONFIG')
        return

    monitor = SolverMonitor(solvers_dir)

    # In-memory pending state
    pending_flags: List[Flag] = []
    pending_lock = threading.Lock()

    # accepted_set memory-only to avoid re-adding accepted flags
    accepted_set: Set[str] = set()

    # in-progress trackers to avoid scheduling duplicate (solver_path, team)
    in_progress: Set[Tuple[str,str]] = set()
    in_progress_lock = threading.Lock()

    stop_event = threading.Event()

    def graceful(signum, frame):
        logger.info('Received signal %s, shutting down...', signum)
        stop_event.set()

    signal.signal(signal.SIGINT, graceful)
    signal.signal(signal.SIGTERM, graceful)

    # Reused worker that runs a single solver against a single team and returns Flag objects
    def worker_run_solver_and_collect(solver_path: Path, team_name: str, team_ip: str, flag_regex: re.Pattern) -> List[Flag]:
        solver_name = solver_path.stem
        out, ok = run_solver_process(solver_path, team_ip)
        found_objs: List[Flag] = []
        if ok:
            found = find_flags_in_output(out, flag_regex)
            if found:
                # log found flags with icon and list (colored)
                with print_lock:
                    logger.info(f"{colorize(EMOJI['found'], 'magenta')} {colorize(f'[{solver_name} -> {team_name}]', 'bold')} Found {len(found)} flag(s): {format_flags_list(found)}")
                found_objs = create_flag_objects(found, solver_name, team_name)
            else:
                if out.strip():
                    logger.debug('[%s -> %s] No flags. Sample output: %s', solver_name, team_name, out.strip()[:200])
                else:
                    logger.debug('[%s -> %s] No output', solver_name, team_name)
        else:
            logger.warning('%s %s [%s -> %s] Solver failed/timed out. Output: %s', colorize(EMOJI['error'], 'yellow'), colorize('ERROR', 'red'), solver_name, team_name, out.strip()[:400])
        return found_objs

    def handle_found_flags_from_task(flags_from_task: List[Flag]):
        # dedupe vs pending and accepted
        if not flags_from_task:
            return
        with pending_lock:
            existing = {f.flag for f in pending_flags}
            to_add = []
            for f in flags_from_task:
                if f.flag in existing or f.flag in accepted_set:
                    logger.debug('Skipping duplicate/newly-accepted flag: %s', f.flag)
                    continue
                to_add.append(f)
            if to_add:
                pending_flags.extend(to_add)
                # pretty-print added flags
                with print_lock:
                    logger.info(f"{colorize(EMOJI['added'], 'blue')} {colorize('Added', 'blue')} {len(to_add)} pending flag(s): {format_flags_list([x.flag for x in to_add])}")

    # Per-solver thread management
    solver_threads: Dict[str, Dict] = {}
    solver_threads_lock = threading.Lock()

    def ensure_solver_worker(solver_path: Path):
        key = str(solver_path.resolve())
        with solver_threads_lock:
            if key in solver_threads:
                return solver_threads[key]['queue']

            q = queue.Queue()

            def solver_thread_loop():
                # Each solver thread can optionally create its own ThreadPoolExecutor when use_threading==True
                logger.info('Solver thread started for %s', solver_path.name)
                local_executor = None
                while not stop_event.is_set():
                    try:
                        # wait for a 'run' command or timeout to allow shutdown check
                        cmd = q.get(timeout=1)
                    except queue.Empty:
                        continue
                    if cmd == 'run_all':
                        # Run this solver against all teams. If use_threading True then run per-team concurrently.
                        teams_items = list(teams.items())
                        if not teams_items:
                            continue

                        if use_threading:
                            # create/reuse a small executor for this solver
                            if local_executor is None:
                                max_workers = int(config.get('SOLVER_THREADS_PER_SOLVER', max(2, len(teams_items))))
                                local_executor = ThreadPoolExecutor(max_workers=max_workers)

                            futures: List[Future] = []

                            for tn, tip in teams_items:
                                key_inp = (key, tn)
                                with in_progress_lock:
                                    if key_inp in in_progress:
                                        logger.debug('Skipping already in-progress %s -> %s', solver_path.name, tn)
                                        continue
                                    in_progress.add(key_inp)

                                fut = local_executor.submit(worker_run_solver_and_collect, solver_path, tn, tip, flag_regex)

                                # attach a callback to process flags and clear in_progress
                                def _cb(fut, solver_key=key, team_name=tn):
                                    try:
                                        res = fut.result()
                                        handle_found_flags_from_task(res)
                                    except Exception:
                                        logger.exception('Exception in per-solver future')
                                    finally:
                                        with in_progress_lock:
                                            k = (solver_key, team_name)
                                            if k in in_progress:
                                                in_progress.remove(k)

                                fut.add_done_callback(_cb)
                                futures.append(fut)

                            # optionally wait a small amount or continue; we don't block the solver thread here

                        else:
                            # sequential execution in this solver thread
                            for tn, tip in teams_items:
                                key_inp = (key, tn)
                                with in_progress_lock:
                                    if key_inp in in_progress:
                                        logger.debug('Skipping already in-progress %s -> %s', solver_path.name, tn)
                                        continue
                                    in_progress.add(key_inp)
                                try:
                                    res = worker_run_solver_and_collect(solver_path, tn, tip, flag_regex)
                                    handle_found_flags_from_task(res)
                                except Exception:
                                    logger.exception('Exception while running solver sequentially')
                                finally:
                                    with in_progress_lock:
                                        if key_inp in in_progress:
                                            in_progress.remove(key_inp)

                    elif cmd == 'shutdown':
                        break

                if local_executor:
                    local_executor.shutdown(wait=True)
                logger.info('Solver thread exiting for %s', solver_path.name)

            t = threading.Thread(target=solver_thread_loop, daemon=True)
            solver_threads[key] = {'thread': t, 'queue': q, 'path': solver_path}
            t.start()
            return q

    # watcher thread (always present) to detect file changes and enqueue immediate runs
    def watcher_thread():
        # mark initial mtimes so they don't all appear changed (main loop will schedule full runs)
        try:
            initial = sorted([p for p in (solvers_dir.glob('*.py') if solvers_dir.exists() else [])])
            for p in initial:
                try:
                    monitor._mtimes[str(p.resolve())] = p.stat().st_mtime
                except Exception:
                    pass
            logger.info('Watcher started, initial solvers=%d', len(initial))

            while not stop_event.is_set():
                changed = monitor.scan()
                if changed:
                    logger.info('Watcher detected %d changed/new solver(s)', len(changed))
                    for s in changed:
                        q = ensure_solver_worker(s)
                        # Schedule immediate run for this solver
                        try:
                            q.put_nowait('run_all')
                            with print_lock:
                                logger.info(f"{colorize(EMOJI['scheduled'], 'blue')} {colorize('Scheduled immediate run:', 'blue')} {s.name}")
                        except Exception:
                            logger.exception('Failed to enqueue immediate run for %s', s)
                stop_event.wait(WATCH_POLL)
        except Exception:
            logger.exception('Watcher thread exception')

    watcher = threading.Thread(target=watcher_thread, daemon=True)
    watcher.start()

    try:
        while not stop_event.is_set():
            cycle_start = time.time()
            logger.info('Starting full-run cycle: signaling all solver threads to run')

            # ensure worker thread exists for each solver and tell it to run
            all_solvers = sorted([p for p in (solvers_dir.glob('*.py') if solvers_dir.exists() else [])])
            scheduled = 0
            for s in all_solvers:
                q = ensure_solver_worker(s)
                try:
                    q.put_nowait('run_all')
                    scheduled += 1
                except queue.Full:
                    logger.debug('Solver queue full for %s', s.name)

            logger.info('Signaled %d solver threads this cycle', scheduled)

            # small grace to let some tasks finish and populate pending flags
            time.sleep(0.5)

            # prepare queued flags that are old enough (grace)
            now = time.time()
            with pending_lock:
                queued_candidates = [f for f in pending_flags if getattr(f, 'status', None) == FlagStatus.QUEUED and (now - getattr(f, 'time', now)) >= SUBMIT_GRACE_SECONDS]

            if queued_candidates:
                # show flags that are candidates
                with print_lock:
                    logger.info(f"{colorize(EMOJI['submit'], 'yellow')} {colorize('Candidates for submission', 'yellow')} ({len(queued_candidates)}): {format_flags_list([f.flag for f in queued_candidates])}")

                # group and fair-share
                grouped = {}
                for f in queued_candidates:
                    key = (f.sploit, f.team)
                    grouped.setdefault(key, []).append(f)
                limit = config.get('SUBMIT_FLAG_LIMIT', len(queued_candidates))
                to_submit = get_fair_share(list(grouped.values()), limit)

                # pretty-print selected flags
                with print_lock:
                    logger.info(f"{colorize(EMOJI['submit'], 'yellow')} {colorize('Selected to submit', 'yellow')} ({len(to_submit)}): {format_flags_list([f.flag for f in to_submit])}")

                logger.info('Submitting %d flags', len(to_submit))
                results = submit_flags_to_system(to_submit)

                # process results: update pending_flags and accepted_set
                with pending_lock:
                    for res in results:
                        flag_str = getattr(res, 'flag', None)
                        status = getattr(res, 'status', None)
                        # pick icon + color for status
                        if status == FlagStatus.ACCEPTED:
                            icon = colorize(EMOJI['accepted'], 'green')
                        elif status == FlagStatus.REJECTED:
                            icon = colorize(EMOJI['rejected'], 'red')
                        elif status == FlagStatus.QUEUED:
                            icon = colorize(EMOJI['queued'], 'yellow')
                        else:
                            icon = colorize(EMOJI.get('skipped','⏭️'), 'blue')

                        with print_lock:
                            logger.info(f"{icon} {flag_str}: {getattr(status, 'name', status)} {getattr(res, 'checksystem_response', '') or ''}")

                        # update matching pending flags
                        for f in list(pending_flags):
                            if f.flag == flag_str:
                                f.checksystem_response = getattr(res, 'checksystem_response', '') or ''
                                f.status = status or f.status
                                if status == FlagStatus.ACCEPTED:
                                    accepted_set.add(flag_str)

                    # cleanup pending_flags in-place: keep only QUEUED
                    pending_flags[:] = [f for f in pending_flags if f.status == FlagStatus.QUEUED]

                summarize_results(results)
            else:
                logger.debug('No queued flags to submit this cycle')

            # Sleep until next full cycle
            elapsed = time.time() - cycle_start
            wait = max(0, RUN_INTERVAL - elapsed)
            logger.info('Cycle finished; sleeping %ds', wait)
            stop_event.wait(wait)

    except Exception:
        logger.exception('Main loop exception')
    finally:
        logger.info('Shutting down: stopping watcher and solver threads')
        stop_event.set()
        # ask solver threads to shutdown
        with solver_threads_lock:
            for k, v in solver_threads.items():
                try:
                    v['queue'].put_nowait('shutdown')
                except Exception:
                    pass
            for k, v in solver_threads.items():
                t = v.get('thread')
                if t and t.is_alive():
                    t.join(timeout=5)

        if watcher:
            watcher.join(timeout=5)
        logger.info('Shutdown complete')

if __name__ == '__main__':
    main_loop()
