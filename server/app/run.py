#!/usr/bin/env python3
"""
Looping solver runner + submitter for TernakLele (threaded, immediate-run-on-new-script).

Behavior:
 - Watch ./solvers for new/updated .py files (polling).
 - When a new/updated solver appears, run it immediately (concurrently) against all teams.
 - Collected flags are stored as pending queued flags and retried on the periodic submit cycle.
 - Periodic submit cycle runs every RUN_INTERVAL seconds to submit queued flags (applies fair-share).
"""
from __future__ import annotations

import os
import sys
import re
import time
import signal
import subprocess
import traceback
import threading
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, Future

# repo imports (adapt if your repo layout differs)
from config import CONFIG
from models import Flag, FlagStatus, SubmitResult
from protocols.ailurus import submit_flags as ailurus_submit_flags
from utils import get_fair_share

# Configurable intervals
RUN_INTERVAL = int(CONFIG.get('RUN_INTERVAL', 30))      # submit cycle
WATCH_POLL = int(CONFIG.get('WATCH_POLL', 2))           # watcher poll interval (seconds)

def find_flags_in_output(output: str, flag_format: re.Pattern) -> List[str]:
    return flag_format.findall(output)

def run_solver_process(solver_path: Path, target_ip: str, timeout: int = 30) -> Tuple[str, bool]:
    try:
        cmd = [sys.executable, str(solver_path), target_ip]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = (proc.stdout or '') + (proc.stderr or '')
        success = proc.returncode == 0
        return output, success
    except subprocess.TimeoutExpired:
        return f"Solver timed out after {timeout} seconds", False
    except Exception as e:
        return f"Error running solver: {e}", False

def create_flag_objects(flags: List[str], solver_name: str, team_name: str) -> List[Flag]:
    objs: List[Flag] = []
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
        results = list(ailurus_submit_flags(flag_objs, CONFIG))
        return results
    except Exception:
        print("❌ Exception when submitting flags:")
        traceback.print_exc()
        return []

def summarize_results(results: List[SubmitResult]):
    accepted = sum(1 for r in results if getattr(r, 'status', None) == FlagStatus.ACCEPTED)
    rejected = sum(1 for r in results if getattr(r, 'status', None) == FlagStatus.REJECTED)
    queued = sum(1 for r in results if getattr(r, 'status', None) == FlagStatus.QUEUED)
    print(f"📊 Submission Summary: ✅ {accepted}  ❌ {rejected}  ⏳ {queued}")

class SolverMonitor:
    """Monitors the solvers directory for file changes (new/modified)."""
    def __init__(self, solvers_dir: Path):
        self.solvers_dir = solvers_dir
        self._mtimes: Dict[Path, float] = {}

    def scan(self) -> List[Path]:
        found = []
        if not self.solvers_dir.exists():
            return found
        current_files = {p for p in self.solvers_dir.glob("*.py") if p.is_file()}
        # removed
        removed = set(self._mtimes.keys()) - current_files
        for r in removed:
            del self._mtimes[r]
        for p in current_files:
            try:
                m = p.stat().st_mtime
            except Exception:
                m = 0
            prev = self._mtimes.get(p)
            if prev is None:
                found.append(p)
                self._mtimes[p] = m
            else:
                if m != prev:
                    found.append(p)
                    self._mtimes[p] = m
        return sorted(found)

def worker_run_solver_and_collect(solver_path: Path, team_name: str, team_ip: str, flag_regex: re.Pattern, timeout: int) -> List[Flag]:
    solver_name = solver_path.stem
    out, ok = run_solver_process(solver_path, team_ip, timeout=timeout)
    found_flag_objs: List[Flag] = []
    if ok:
        found_flags = find_flags_in_output(out, flag_regex)
        if found_flags:
            with print_lock:
                print(f"   ✅ [{solver_name} -> {team_name}] Found {len(found_flags)} flag(s)")
                for ff in found_flags:
                    print(f"      🏁 {ff}")
            found_flag_objs = create_flag_objects(found_flags, solver_name, team_name)
        else:
            with print_lock:
                if out.strip():
                    print(f"   ⚠ [{solver_name} -> {team_name}] No flags. Sample output: {out.strip()[:160]}...")
                else:
                    print(f"   ⚠ [{solver_name} -> {team_name}] No flags and no output.")
    else:
        with print_lock:
            print(f"   ❌ [{solver_name} -> {team_name}] Solver failed/timed out. Output: {out.strip()[:400]}")
    return found_flag_objs

def handle_worker_result(fut: Future, pending_flags: List[Flag], pending_lock: threading.Lock):
    """Callback for worker future: add found flags to pending list safely."""
    try:
        flags_from_task = fut.result()
        if flags_from_task:
            with pending_lock:
                pending_flags.extend(flags_from_task)
    except Exception:
        with print_lock:
            print("❌ Exception in worker future callback:")
            traceback.print_exc()

print_lock = threading.Lock()  # serialize print outputs

def graceful_exit(signum, frame):
    print("\n🛑 Received interrupt/termination signal, exiting gracefully...")
    raise KeyboardInterrupt()

def main_loop():
    with print_lock:
        print("🚀 TernakLele Loop Runner (watcher + threaded solvers) — press Ctrl-C to stop")
        print("=" * 80)

    config = CONFIG
    flag_regex = re.compile(config['FLAG_FORMAT'])
    solvers_dir = Path(__file__).parent / "solvers"

    if not solvers_dir.exists():
        with print_lock:
            print(f"❌ Solvers directory not found at {solvers_dir}. Create it and put solver .py files there.")
        return

    teams = config.get('TEAMS', {})
    if not teams:
        with print_lock:
            print("❌ No TEAMS configured in CONFIG['TEAMS']. Exiting.")
        return

    monitor = SolverMonitor(solvers_dir)

    # pending flags + lock
    pending_flags: List[Flag] = []
    pending_lock = threading.Lock()

    # thread pool for solver tasks (shared between watcher and initial run)
    solver_threads = int(config.get('SOLVER_THREADS', max(4, len(list(solvers_dir.glob('*.py'))) * max(1, len(teams)))))
    executor = ThreadPoolExecutor(max_workers=solver_threads)

    # watcher state
    stop_event = threading.Event()
    first_run_done = threading.Event()

    signal.signal(signal.SIGINT, graceful_exit)

    def watcher_thread_func():
        """Continuously poll solvers dir and schedule immediate runs for new/updated files."""
        # On start, schedule all solvers (first-run behavior)
        try:
            initial = sorted([p for p in (solvers_dir.glob("*.py") if solvers_dir.exists() else [])])
            if initial:
                with print_lock:
                    print(f"🔎 Watcher startup: scheduling initial {len(initial)} solver(s) for execution.")
                for solver_path in initial:
                    # update monitor mtimes so scan won't mark them new again
                    try:
                        monitor._mtimes[solver_path] = solver_path.stat().st_mtime
                    except Exception:
                        pass
                    # schedule immediately
                    for team_name, team_ip in teams.items():
                        fut = executor.submit(worker_run_solver_and_collect, solver_path, team_name, team_ip, flag_regex, config.get('SOLVER_TIMEOUT', 30))
                        fut.add_done_callback(lambda f: handle_worker_result(f, pending_flags, pending_lock))
            first_run_done.set()

            # main watcher loop
            while not stop_event.is_set():
                changed = monitor.scan()
                if changed:
                    with print_lock:
                        print(f"\n⚡ Watcher detected {len(changed)} new/updated solver(s):")
                        for s in changed:
                            print(f"   - {s.name}")
                    for solver_path in changed:
                        # schedule to run immediately against all teams
                        for team_name, team_ip in teams.items():
                            fut = executor.submit(worker_run_solver_and_collect, solver_path, team_name, team_ip, flag_regex, config.get('SOLVER_TIMEOUT', 30))
                            fut.add_done_callback(lambda f: handle_worker_result(f, pending_flags, pending_lock))
                # small sleep
                stop_event.wait(WATCH_POLL)
        except KeyboardInterrupt:
            pass
        except Exception:
            with print_lock:
                print("❌ Exception in watcher thread:")
                traceback.print_exc()

    # start watcher
    watcher = threading.Thread(target=watcher_thread_func, daemon=True)
    watcher.start()

    # wait until watcher did initial scheduling
    first_run_done.wait(timeout=5)

    try:
        # main submit loop: every RUN_INTERVAL seconds, try to submit queued flags
        while True:
            loop_start = time.time()
            with print_lock:
                print("\n" + "=" * 80)
                print(time.strftime("🕒 Starting submit cycle at %Y-%m-%d %H:%M:%S", time.localtime(loop_start)))

            try:
                # collect queued flags snapshot
                with pending_lock:
                    queued_flags = [f for f in pending_flags if getattr(f, 'status', None) == FlagStatus.QUEUED]

                if queued_flags:
                    with print_lock:
                        print(f"\n📤 Attempting to submit {len(queued_flags)} queued flag(s)...")
                    # group and apply fair share
                    grouped = {}
                    for f in queued_flags:
                        key = (f.sploit, f.team)
                        grouped.setdefault(key, []).append(f)

                    limit = config.get('SUBMIT_FLAG_LIMIT', len(queued_flags))
                    to_submit = get_fair_share(list(grouped.values()), limit)
                    with print_lock:
                        print(f"   -> Selected {len(to_submit)} flag(s) for submission after fair-share")

                    results = submit_flags_to_system(to_submit)

                    # update pending list according to results
                    with pending_lock:
                        for res in results:
                            flag_str = getattr(res, 'flag', None)
                            matching = [f for f in pending_flags if f.flag == flag_str]
                            for m in matching:
                                m.checksystem_response = getattr(res, 'checksystem_response', '') or ''
                                m.status = getattr(res, 'status', m.status)
                                with print_lock:
                                    print(f"   {res.flag}: {m.status.name}  ({m.checksystem_response})")
                        # keep only queued
                        pending_flags = [f for f in pending_flags if f.status == FlagStatus.QUEUED]

                    summarize_results(results)
                else:
                    with print_lock:
                        print("\nℹ️ No queued flags to submit this cycle.")

                # show pending summary
                with pending_lock:
                    if pending_flags:
                        with print_lock:
                            print(f"\n⏳ Pending QUEUED flags to retry next cycles: {len(pending_flags)}")
                            for p in pending_flags:
                                print(f"   - {p.flag} [{p.sploit} -> {p.team}]")
                    else:
                        with print_lock:
                            print("\n✅ No pending queued flags.")

            except Exception:
                with print_lock:
                    print("❌ Exception during submit cycle:")
                    traceback.print_exc()

            # sleep until next iteration, but watch for KeyboardInterrupt
            loop_duration = time.time() - loop_start
            sleep_for = max(0, RUN_INTERVAL - loop_duration)
            with print_lock:
                print(time.strftime("⏱ Submit cycle finished at %Y-%m-%d %H:%M:%S", time.localtime()))
            if sleep_for > 0:
                try:
                    time.sleep(sleep_for)
                except KeyboardInterrupt:
                    break

    except KeyboardInterrupt:
        with print_lock:
            print("\n👋 KeyboardInterrupt received: shutting down watcher and executor...")

    # shutdown
    stop_event.set()
    watcher.join(timeout=5)
    executor.shutdown(wait=True)
    with print_lock:
        print("🛑 Shutdown complete. Goodbye.")

if __name__ == "__main__":
    main_loop()
