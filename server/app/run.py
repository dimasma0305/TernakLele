#!/usr/bin/env python3
"""
Enhanced TernakLele Loop Runner (simplified, improved logging + colors)
- Runs ALL solvers every RUN_INTERVAL seconds against all teams
- Starts a dedicated thread per solver script (this is ALWAYS used, independent of USE_THREADING)
- USE_THREADING toggles whether each solver will attack its teams concurrently (per-solver executor)
- Watches ./solvers for new/updated solver .py and runs them immediately
- Deduplicates flags using SQLite database for persistence and unique constraints
- Uses repo's configured protocol module (CONFIG['SYSTEM_PROTOCOL']) to submit flags

Configuration keys (in CONFIG) that are used/added:
 - RUN_INTERVAL (seconds, default 30)
 - WATCH_POLL (seconds, default 2)
 - SOLVER_TIMEOUT (seconds, default 60)
 - SUBMIT_FLAG_LIMIT (int) - forwarded to get_fair_share
 - USE_THREADING (bool) - when True each solver will run attacks against teams concurrently; when False each solver will run teams sequentially
 - SOLVER_RETRIES (int, default 1) - retries for failed solver runs
 - SOLVER_THREADS_PER_SOLVER (int) - max workers per solver executor
 - MAX_CONCURRENT_ATTACKS (int, default 50) - global limit on concurrent attacks
"""
from __future__ import annotations

import os
import sys
import re
import time
import signal
import subprocess
import threading
import logging
import queue
from pathlib import Path
from typing import Dict, List, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, Future
import importlib
import random
import sqlite3
import argparse
from colorama import Fore, Style, init as colorama_init
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

try:
    import psutil
except ImportError:
    psutil = None

# Initialize colorama
colorama_init()

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
SOLVER_TIMEOUT = int(CONFIG.get('SOLVER_TIMEOUT', 60))
SOLVER_RETRIES = int(CONFIG.get('SOLVER_RETRIES', 1))
MAX_CONCURRENT_ATTACKS = int(CONFIG.get('MAX_CONCURRENT_ATTACKS', 50))

def colorize(text: str, color: str) -> str:
    color_map = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'blue': Fore.BLUE,
        'magenta': Fore.MAGENTA,
        'cyan': Fore.CYAN,
        'bold': Style.BRIGHT,
    }
    code = color_map.get(color, '')
    return f"{code}{text}{Style.RESET_ALL}" if code else text

# Setup logging (console + file) with time-only timestamps
class ColoredFormatter(logging.Formatter):
    LEVEL_COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red'
    }

    def __init__(self, fmt=None, datefmt=None, use_color=True):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_color = use_color

    def format(self, record):
        # color levelname if using color
        lvl = record.levelname
        if self.use_color:
            col = self.LEVEL_COLORS.get(lvl, None)
            if col:
                record.levelname = colorize(lvl, col)
        # format message normally
        msg = super().format(record)
        return msg

logger = logging.getLogger('->')
logger.setLevel(logging.DEBUG)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
fmt = '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
ch.setFormatter(ColoredFormatter(fmt=fmt, datefmt='%H:%M:%S', use_color=True))
logger.addHandler(ch)

# Create tmp dir
tmp_dir = Path('./tmp')
tmp_dir.mkdir(exist_ok=True)

# File handler (rotating) in ./tmp/
from logging.handlers import RotatingFileHandler
fh = RotatingFileHandler(tmp_dir / 'runner.log', maxBytes=10*1024*1024, backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(ColoredFormatter(fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s', use_color=False))
logger.addHandler(fh)

# Internal runtime state
print_lock = threading.Lock()  # serialize prints

def is_solver_file(path: Path) -> bool:
    """Check if a file has a shebang (starts with #!)."""
    if not path.is_file():
        return False
    try:
        with open(path, 'r') as f:
            first_line = f.readline().strip()
            return first_line.startswith('#!')
    except Exception:
        return False

class SolverEventHandler(FileSystemEventHandler):
    def __init__(self, solvers_dir: Path, ensure_solver_worker_func, print_lock):
        self.solvers_dir = solvers_dir
        self.ensure_solver_worker = ensure_solver_worker_func
        self.print_lock = print_lock

    def on_created(self, event):
        if not event.is_directory:
            p = Path(event.src_path)
            if is_solver_file(p):
                self._handle_change(p)

    def on_modified(self, event):
        if not event.is_directory:
            p = Path(event.src_path)
            if is_solver_file(p):
                self._handle_change(p)

    def _handle_change(self, solver_path: Path):
        q = self.ensure_solver_worker(solver_path)
        try:
            q.put_nowait('run_all')
            with self.print_lock:
                logger.info(f"{colorize(EMOJI['scheduled'], 'blue')} {colorize('Scheduled immediate run:', 'blue')} {solver_path.name}")
        except Exception:
            logger.exception('Failed to enqueue immediate run for %s', solver_path.name)

# SQLite database in ./tmp/
DB_FILE = tmp_dir / 'flags.db'

class FlagManager:
    """Manages pending and accepted flags using SQLite for persistence and deduplication."""
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            cur = self.conn.cursor()
            # Pending flags table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS pending_flags (
                    flag TEXT PRIMARY KEY,
                    sploit TEXT,
                    team TEXT,
                    time INTEGER,
                    status TEXT,
                    checksystem_response TEXT
                )
            ''')
            # Accepted flags table (unique on flag)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS accepted_flags (
                    flag TEXT PRIMARY KEY
                )
            ''')
            self.conn.commit()
        logger.info('Initialized SQLite DB for flags')

    def close(self):
        self.conn.close()

    def add_flags(self, new_flags: List[Flag]):
        if not new_flags:
            return
        added_count = 0
        added_list = []
        with self.lock:
            cur = self.conn.cursor()
            for f in new_flags:
                # Check if exists in pending or accepted
                cur.execute('SELECT 1 FROM pending_flags WHERE flag = ?', (f.flag,))
                if cur.fetchone():
                    logger.debug('Skipping duplicate pending flag: %s', f.flag)
                    continue
                cur.execute('SELECT 1 FROM accepted_flags WHERE flag = ?', (f.flag,))
                if cur.fetchone():
                    logger.debug('Skipping already accepted flag: %s', f.flag)
                    continue
                # Insert to pending
                cur.execute('''
                    INSERT INTO pending_flags (flag, sploit, team, time, status, checksystem_response)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (f.flag, f.sploit, f.team, f.time, f.status.name, f.checksystem_response))
                added_count += 1
                added_list.append(f.flag)
            self.conn.commit()
        if added_count > 0:
            with print_lock:
                logger.info(f"{colorize(EMOJI['added'], 'blue')} {colorize('Added', 'blue')} {added_count} pending flag(s): {format_flags_list(added_list)}")

    def get_queued_candidates(self) -> List[Flag]:
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('SELECT flag, sploit, team, time, status, checksystem_response FROM pending_flags WHERE status = ?', (FlagStatus.QUEUED.name,))
            rows = cur.fetchall()
            return [Flag(flag=r[0], sploit=r[1], team=r[2], time=r[3], status=FlagStatus[r[4]], checksystem_response=r[5]) for r in rows]

    def update_after_submission(self, results: List[SubmitResult]):
        with self.lock:
            cur = self.conn.cursor()
            for res in results:
                flag_str = getattr(res, 'flag', None)
                status = getattr(res, 'status', None)
                response = getattr(res, 'checksystem_response', '') or ''
                if status == FlagStatus.ACCEPTED:
                    # Move to accepted
                    cur.execute('INSERT OR IGNORE INTO accepted_flags (flag) VALUES (?)', (flag_str,))
                    # Remove from pending
                    cur.execute('DELETE FROM pending_flags WHERE flag = ?', (flag_str,))
                else:
                    # Update pending
                    cur.execute('UPDATE pending_flags SET status = ?, checksystem_response = ? WHERE flag = ?', (status.name if status else FlagStatus.QUEUED.name, response, flag_str))
            # Clean up non-QUEUED from pending
            cur.execute('DELETE FROM pending_flags WHERE status != ?', (FlagStatus.QUEUED.name,))
            self.conn.commit()

# Runner helpers

def find_flags_in_output(output: str, flag_format: re.Pattern) -> List[str]:
    return flag_format.findall(output)

def get_solver_interpreter(solver_path: Path) -> List[str]:
    """Parse shebang from solver file to determine interpreter."""
    try:
        with open(solver_path, 'r') as f:
            first_line = f.readline().strip()
            if first_line.startswith('#!'):
                # Extract interpreter, handle /usr/bin/env python3
                shebang = first_line[2:].strip().split()
                return shebang
    except Exception:
        pass
    # Default to current Python
    return [sys.executable]

def run_solver_process(solver_path: Path, target_ip: str, timeout: int = SOLVER_TIMEOUT) -> Tuple[str, bool]:
    interpreter = get_solver_interpreter(solver_path)
    cmd = interpreter + [str(solver_path), target_ip]
    for attempt in range(1, SOLVER_RETRIES + 1):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            out = (proc.stdout or '') + (proc.stderr or '')
            if proc.returncode == 0:
                return out, True
            else:
                logger.warning('Solver attempt %d/%d failed with code %d', attempt, SOLVER_RETRIES, proc.returncode)
                if attempt == SOLVER_RETRIES:
                    return out, False
        except subprocess.TimeoutExpired:
            logger.warning('Solver attempt %d/%d timed out', attempt, SOLVER_RETRIES)
            if attempt == SOLVER_RETRIES:
                return f"Solver timed out after {timeout} seconds", False
        except Exception as e:
            logger.warning('Solver attempt %d/%d error: %s', attempt, SOLVER_RETRIES, e)
            if attempt == SOLVER_RETRIES:
                return f"Error running solver: {e}", False
        time.sleep(1)  # Short delay between retries
    return '', False

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
    except Exception as e:
        logger.warning(f"Submission failed: {e}")
        return [SubmitResult(flag=f.flag, status=FlagStatus.QUEUED) for f in flag_objs]

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

def parse_args():
    parser = argparse.ArgumentParser(description="Enhanced TernakLele Loop Runner")
    parser.add_argument('--fresh', action='store_true', help="Run fresh: clear previous logs and database before starting")
    args = parser.parse_args()
    return args

def clear_data():
    # Clear logs
    log_files = list(tmp_dir.glob('runner.log*'))
    for log_file in log_files:
        try:
            log_file.unlink()
            logger.info(f"Cleared log file: {log_file}")
        except Exception as e:
            logger.warning(f"Failed to clear log file {log_file}: {e}")
    
    # Clear database
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
            logger.info(f"Cleared database: {DB_FILE}")
        except Exception as e:
            logger.warning(f"Failed to clear database {DB_FILE}: {e}")

# Main loop

def main_loop():
    # Validate config
    required_keys = ['TEAMS', 'FLAG_FORMAT']
    for key in required_keys:
        if key not in CONFIG:
            raise ValueError(f"Missing required config key: {key}")

    config = CONFIG
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

    flag_manager = FlagManager()

    # in-progress trackers to avoid scheduling duplicate (solver_path, team)
    in_progress: Set[Tuple[str,str]] = set()
    in_progress_lock = threading.Lock()

    # Global semaphore for concurrent attacks
    global_semaphore = threading.Semaphore(MAX_CONCURRENT_ATTACKS)

    stop_event = threading.Event()

    def graceful(signum, frame):
        logger.info('Received signal %s, shutting down...', signum)
        stop_event.set()

    signal.signal(signal.SIGINT, graceful)
    signal.signal(signal.SIGTERM, graceful)

    # Reused worker that runs a single solver against a single team and returns Flag objects
    def worker_run_solver_and_collect(solver_path: Path, team_name: str, team_ip: str, flag_regex: re.Pattern) -> List[Flag]:
        global_semaphore.acquire()
        try:
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
        finally:
            global_semaphore.release()

    def handle_found_flags_from_task(flags_from_task: List[Flag]):
        if not flags_from_task:
            return
        flag_manager.add_flags(flags_from_task)

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
                        random.shuffle(teams_items)  # Randomize order
                        if not teams_items:
                            continue

                        if use_threading:
                            # create/reuse a small executor for this solver
                            if local_executor is None:
                                max_workers = int(config.get('SOLVER_THREADS_PER_SOLVER', max(2, len(teams_items))))
                                if psutil:
                                    max_workers = min(max_workers, psutil.cpu_count(logical=False) // 2)
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
        observer = Observer()
        event_handler = SolverEventHandler(solvers_dir, ensure_solver_worker, print_lock)
        observer.schedule(event_handler, str(solvers_dir), recursive=False)
        observer.start()

        # Initial scan and schedule
        initial_solvers = sorted([p for p in solvers_dir.glob('*') if is_solver_file(p)])
        for s in initial_solvers:
            q = ensure_solver_worker(s)
            try:
                q.put_nowait('run_all')
            except queue.Full:
                logger.debug('Solver queue full for %s', s.name)
        logger.info('Watcher started, initial solvers=%d', len(initial_solvers))

        try:
            while not stop_event.is_set():
                stop_event.wait(1)
        except Exception:
            logger.exception('Watcher thread exception')
        finally:
            observer.stop()
            observer.join()

    watcher = threading.Thread(target=watcher_thread, daemon=True)
    watcher.start()

    # Cycle stats
    cycle_stats = {'flags_found': 0, 'flags_submitted': 0, 'accepted': 0}

    try:
        while not stop_event.is_set():
            cycle_start = time.time()
            logger.info('Starting full-run cycle: signaling all solver threads to run')

            # ensure worker thread exists for each solver and tell it to run
            all_solvers = sorted([p for p in (solvers_dir.glob('*') if solvers_dir.exists() else []) if is_solver_file(p)])
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

            # Get all queued flags (no grace period, dedup handled by DB)
            queued_candidates = flag_manager.get_queued_candidates()

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
                cycle_stats['flags_submitted'] += len(to_submit)

                # pretty-print selected flags
                with print_lock:
                    logger.info(f"{colorize(EMOJI['submit'], 'yellow')} {colorize('Selected to submit', 'yellow')} ({len(to_submit)}): {format_flags_list([f.flag for f in to_submit])}")

                logger.info('Submitting %d flags', len(to_submit))
                results = submit_flags_to_system(to_submit)

                # process results: update DB
                flag_manager.update_after_submission(results)
                cycle_stats['accepted'] += sum(1 for r in results if getattr(r, 'status', None) == FlagStatus.ACCEPTED)

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

                summarize_results(results)
            else:
                logger.debug('No queued flags to submit this cycle')

            # Log cycle stats
            total_submitted = cycle_stats['flags_submitted']
            success_rate = (cycle_stats['accepted'] / total_submitted * 100) if total_submitted else 0
            logger.info('Cycle stats: flags_found=%d, flags_submitted=%d, accepted=%d, success_rate=%.2f%%',
                        cycle_stats['flags_found'], total_submitted, cycle_stats['accepted'], success_rate)

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
        flag_manager.close()
        logger.info('Shutdown complete')

if __name__ == '__main__':
    args = parse_args()
    if args.fresh:
        clear_data()
    main_loop()