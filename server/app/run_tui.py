#!/usr/bin/env python3
"""
Enhanced TernakLele Loop Runner with TUI (Terminal User Interface)
Preserves all existing functionality while adding a rich interactive interface
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
from typing import Dict, List, Tuple, Set, Optional
from concurrent.futures import ThreadPoolExecutor, Future
import importlib
import random
import sqlite3
import argparse
from datetime import datetime
from collections import deque, defaultdict

# TUI imports
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Label, Button, TabbedContent, TabPane, RichLog, Sparkline
from textual.containers import Horizontal, Vertical, ScrollableContainer, Container
from textual.reactive import reactive
from textual.timer import Timer
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich import box

try:
    import psutil
except ImportError:
    psutil = None

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

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

# Setup logging (using in-memory handler for TUI)
class TUILogHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put_nowait({
                'time': datetime.now(),
                'level': record.levelname,
                'message': msg,
                'record': record
            })
        except:
            pass

# Keep original logger setup but add TUI handler
logger = logging.getLogger('->')
logger.setLevel(logging.DEBUG)

# Create tmp dir
tmp_dir = Path('./tmp')
tmp_dir.mkdir(exist_ok=True)

# File handler (rotating) in ./tmp/ - keep original
from logging.handlers import RotatingFileHandler
fh = RotatingFileHandler(tmp_dir / 'runner.log', maxBytes=10*1024*1024, backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
logger.addHandler(fh)

# Keep all original functions unchanged
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
                logger.info(f"📅 Scheduled immediate run: {solver_path.name}")
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
            cur.execute('''
                CREATE TABLE IF NOT EXISTS accepted_flags (
                    flag TEXT PRIMARY KEY
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS rejected_flags (
                    flag TEXT PRIMARY KEY,
                    sploit TEXT,
                    team TEXT,
                    time INTEGER,
                    checksystem_response TEXT
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
                cur.execute('SELECT 1 FROM pending_flags WHERE flag = ?', (f.flag,))
                if cur.fetchone():
                    logger.debug('Skipping duplicate pending flag: %s', f.flag)
                    continue
                cur.execute('SELECT 1 FROM accepted_flags WHERE flag = ?', (f.flag,))
                if cur.fetchone():
                    logger.debug('Skipping already accepted flag: %s', f.flag)
                    continue
                cur.execute('''
                    INSERT INTO pending_flags (flag, sploit, team, time, status, checksystem_response)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (f.flag, f.sploit, f.team, f.time, f.status.name, f.checksystem_response))
                added_count += 1
                added_list.append(f.flag)
            self.conn.commit()
        if added_count > 0:
            logger.info(f"➕ Added {added_count} pending flag(s): {', '.join(added_list[:10])}")

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
                
                # Get original flag data for rejected flags
                cur.execute('SELECT sploit, team, time FROM pending_flags WHERE flag = ?', (flag_str,))
                flag_data = cur.fetchone()
                
                if status == FlagStatus.ACCEPTED:
                    cur.execute('INSERT OR IGNORE INTO accepted_flags (flag) VALUES (?)', (flag_str,))
                    cur.execute('DELETE FROM pending_flags WHERE flag = ?', (flag_str,))
                elif status == FlagStatus.REJECTED:
                    # Move to rejected_flags table
                    if flag_data:
                        cur.execute('''
                            INSERT OR IGNORE INTO rejected_flags (flag, sploit, team, time, checksystem_response)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (flag_str, flag_data[0], flag_data[1], flag_data[2], response))
                    cur.execute('DELETE FROM pending_flags WHERE flag = ?', (flag_str,))
                else:
                    cur.execute('UPDATE pending_flags SET status = ?, checksystem_response = ? WHERE flag = ?', (status.name if status else FlagStatus.QUEUED.name, response, flag_str))
            cur.execute('DELETE FROM pending_flags WHERE status != ?', (FlagStatus.QUEUED.name,))
            self.conn.commit()

    def get_stats(self) -> Dict:
        """Get comprehensive statistics for TUI display"""
        with self.lock:
            cur = self.conn.cursor()
            
            # Get counts from each table
            cur.execute('SELECT COUNT(*) FROM pending_flags')
            pending = cur.fetchone()[0]
            
            cur.execute('SELECT COUNT(*) FROM accepted_flags')
            accepted = cur.fetchone()[0]
            
            cur.execute('SELECT COUNT(*) FROM rejected_flags')
            rejected = cur.fetchone()[0]
            
            # Get total flags found (all flags that have been processed)
            total_found = pending + accepted + rejected
            
            # Get solver-specific stats
            cur.execute('''
                SELECT sploit, COUNT(*) as found_count
                FROM (
                    SELECT sploit FROM pending_flags
                    UNION ALL
                    SELECT sploit FROM accepted_flags af
                    JOIN pending_flags pf ON af.flag = pf.flag
                    UNION ALL  
                    SELECT sploit FROM rejected_flags
                ) GROUP BY sploit
            ''')
            solver_stats = dict(cur.fetchall())
            
            return {
                'pending': pending,
                'accepted': accepted, 
                'rejected': rejected,
                'total_found': total_found,
                'solver_stats': solver_stats
            }

# Keep all runner helper functions unchanged
def find_flags_in_output(output: str, flag_format: re.Pattern) -> List[str]:
    return flag_format.findall(output)

def get_solver_interpreter(solver_path: Path) -> List[str]:
    try:
        with open(solver_path, 'r') as f:
            first_line = f.readline().strip()
            if first_line.startswith('#!'):
                shebang = first_line[2:].strip().split()
                return shebang
    except Exception:
        pass
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
        time.sleep(1)
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

def parse_args():
    parser = argparse.ArgumentParser(description="Enhanced TernakLele Loop Runner")
    parser.add_argument('--fresh', action='store_true', help="Run fresh: clear previous logs and database before starting")
    parser.add_argument('--no-tui', action='store_true', help="Run without TUI (original CLI mode)")
    args = parser.parse_args()
    return args

def clear_data():
    log_files = list(tmp_dir.glob('runner.log*'))
    for log_file in log_files:
        try:
            log_file.unlink()
            logger.info(f"Cleared log file: {log_file}")
        except Exception as e:
            logger.warning(f"Failed to clear log file {log_file}: {e}")
    
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
            logger.info(f"Cleared database: {DB_FILE}")
        except Exception as e:
            logger.warning(f"Failed to clear database {DB_FILE}: {e}")

# TUI Application
class TernakLeleTUI(App):
    """TUI for TernakLele Runner"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #stats-container {
        height: 4;
        margin: 0;
        padding: 0;
    }
    
    #solver-table {
        height: 100%;
        border: solid $primary;
    }
    
    RichLog {
        border: solid $primary;
        padding: 1;
    }
    
    .stat-box {
        width: 1fr;
        height: 5;
        padding: 1;
        margin: 0 1;
        text-align: center;
    }
    
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("c", "clear_logs", "Clear Logs"),
        ("s", "start_runner", "Start Runner"),
        ("p", "pause_runner", "Pause Runner"),
        ("f", "force_run", "Force Run"),
    ]
    
    def __init__(self, runner_thread_func, **kwargs):
        super().__init__(**kwargs)
        self.runner_thread_func = runner_thread_func
        self.log_queue = queue.Queue()
        self.stats_queue = queue.Queue()
        self.runner_thread = None
        self.stop_event = threading.Event()
        
        # Stats tracking - now using database
        self.active_solvers = 0
        self.cycle_count = 0
        self.solver_stats = defaultdict(lambda: {'found': 0, 'accepted': 0, 'last_run': 'Never'})
        self.flag_manager = None  # Will be set by the runner thread
        
        # Setup TUI log handler
        tui_handler = TUILogHandler(self.log_queue)
        tui_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(tui_handler)
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        
        with TabbedContent():
            with TabPane("Dashboard", id="dashboard"):
                with Vertical():
                    # Stats Panel
                    with Horizontal(id="stats-container"):
                        yield Static("[bold cyan]🏁 Flags Found:[/bold cyan]", classes="stat-box", id="stat-found")
                        yield Static("[bold green]✅ Accepted:[/bold green]", classes="stat-box", id="stat-accepted")
                        yield Static("[bold red]❌ Rejected:[/bold red]", classes="stat-box", id="stat-rejected")
                        yield Static("[bold yellow]🔄 Cycles:[/bold yellow]", classes="stat-box", id="stat-cycles")
                        yield Static("[bold magenta]⚡ Active:[/bold magenta]", classes="stat-box", id="stat-active")
                    
                    # Solver Status Table
                    yield DataTable(id="solver-table")
            
            with TabPane("Logs", id="logs"):
                yield RichLog(highlight=True, markup=True, id="log-viewer")
            
            with TabPane("Flags", id="flags"):
                yield DataTable(id="flag-table")
    
    def on_mount(self) -> None:
        # Setup solver table
        solver_table = self.query_one("#solver-table", DataTable)
        solver_table.add_columns("Solver", "Status", "Teams", "Flags Found", "Success Rate", "Last Run")
        solver_table.show_cursor = False
        
        # Setup flag table
        flag_table = self.query_one("#flag-table", DataTable)
        flag_table.add_columns("Time", "Flag", "Solver", "Team", "Status")
        flag_table.show_cursor = False
        
        # Start update timer
        self.set_interval(0.5, self.update_display)
        
        # Start runner thread
        self.start_runner()
    
    def start_runner(self):
        """Start the runner thread"""
        if not self.runner_thread or not self.runner_thread.is_alive():
            self.runner_thread = threading.Thread(
                target=self.runner_thread_func, 
                args=(self.log_queue, self.stats_queue, self.stop_event),
                daemon=True
            )
            self.runner_thread.start()
    
    def update_display(self):
        """Update the TUI display with latest data"""
        # Process log queue
        log_viewer = self.query_one("#log-viewer", RichLog)
        processed_logs = 0
        while not self.log_queue.empty() and processed_logs < 50:  # Limit to prevent UI freeze
            try:
                log_entry = self.log_queue.get_nowait()
                level = log_entry['level']
                msg = log_entry['message']
                
                # Color based on level
                if level == 'ERROR':
                    log_viewer.write(f"[red]{msg}[/red]")
                elif level == 'WARNING':
                    log_viewer.write(f"[yellow]{msg}[/yellow]")
                elif level == 'INFO':
                    if '🏁' in msg or 'Found' in msg:
                        log_viewer.write(f"[magenta]{msg}[/magenta]")
                    elif '✅' in msg or 'ACCEPTED' in msg:
                        log_viewer.write(f"[green]{msg}[/green]")
                    elif '❌' in msg or 'REJECTED' in msg:
                        log_viewer.write(f"[red]{msg}[/red]")
                    else:
                        log_viewer.write(f"[cyan]{msg}[/cyan]")
                else:
                    log_viewer.write(msg)
                processed_logs += 1
            except queue.Empty:
                break
        
        # Process stats queue
        processed_stats = 0
        while not self.stats_queue.empty() and processed_stats < 50:  # Limit to prevent UI freeze
            try:
                stats = self.stats_queue.get_nowait()
                if stats['type'] == 'cycle':
                    self.cycle_count += 1
                elif stats['type'] == 'active_solvers':
                    self.active_solvers = stats.get('count', 0)
                elif stats['type'] == 'solver_update':
                    solver_name = stats['solver']
                    self.solver_stats[solver_name].update(stats.get('data', {}))
                    self.update_solver_table()
                elif stats['type'] == 'flag_entry':
                    # Add to flag table
                    flag_table = self.query_one("#flag-table", DataTable)
                    flag_table.add_row(
                        stats.get('time', ''),
                        stats.get('flag', '')[:20] + '...' if len(stats.get('flag', '')) > 20 else stats.get('flag', ''),
                        stats.get('solver', 'unknown'),
                        stats.get('team', 'unknown'),
                        stats.get('status', 'UNKNOWN')
                    )
                elif stats['type'] == 'flag_manager':
                    # Set flag manager reference
                    self.flag_manager = stats.get('flag_manager')
                processed_stats += 1
            except queue.Empty:
                break
        
        # Update stat displays from database
        if self.flag_manager:
            db_stats = self.flag_manager.get_stats()
            self.query_one("#stat-found").update(f"[bold cyan]🏁 Flags Found:[/bold cyan] {db_stats.get('total_found', 0)}")
            self.query_one("#stat-accepted").update(f"[bold green]✅ Accepted:[/bold green] {db_stats.get('accepted', 0)}")
            self.query_one("#stat-rejected").update(f"[bold red]❌ Rejected:[/bold red] {db_stats.get('rejected', 0)}")
            self.query_one("#stat-cycles").update(f"[bold yellow]🔄 Cycles:[/bold yellow] {self.cycle_count}")
            self.query_one("#stat-active").update(f"[bold magenta]⚡ Active:[/bold magenta] {self.active_solvers}")
        else:
            # Fallback to zeros if flag_manager not available yet
            self.query_one("#stat-found").update(f"[bold cyan]🏁 Flags Found:[/bold cyan] 0")
            self.query_one("#stat-accepted").update(f"[bold green]✅ Accepted:[/bold green] 0")
            self.query_one("#stat-rejected").update(f"[bold red]❌ Rejected:[/bold red] 0")
            self.query_one("#stat-cycles").update(f"[bold yellow]🔄 Cycles:[/bold yellow] {self.cycle_count}")
            self.query_one("#stat-active").update(f"[bold magenta]⚡ Active:[/bold magenta] {self.active_solvers}")
    
    def update_solver_table(self):
        """Update solver status table"""
        solver_table = self.query_one("#solver-table", DataTable)
        solver_table.clear()
        
        for solver_name, stats in self.solver_stats.items():
            total_found = stats.get('found', 0)
            total_accepted = stats.get('accepted', 0)
            success_rate = f"{(total_accepted/total_found*100):.1f}%" if total_found > 0 else "0%"
            solver_table.add_row(
                solver_name,
                stats.get('status', 'Idle'),
                str(stats.get('teams', 0)),
                str(total_found),
                success_rate,
                stats.get('last_run', 'Never')
            )
    
    def action_pause_runner(self):
        self.stop_event.set()
    
    def action_start_runner(self):
        self.stop_event.clear()
        self.start_runner()
    
    def action_force_run(self):
        # Signal force run through stats queue
        self.stats_queue.put({'type': 'force_run'})
    
    def action_clear_logs(self):
        self.query_one("#log-viewer", RichLog).clear()
    
    def action_refresh(self):
        self.update_display()

# Modified main_loop to work with TUI
def main_loop_tui(log_queue: queue.Queue, stats_queue: queue.Queue, stop_event: threading.Event):
    """Modified main loop that works with TUI"""
    
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
    
    # Send flag manager reference to TUI
    stats_queue.put({'type': 'flag_manager', 'flag_manager': flag_manager})
    
    # Print lock for thread safety
    print_lock = threading.Lock()

    # in-progress trackers
    in_progress: Set[Tuple[str,str]] = set()
    in_progress_lock = threading.Lock()

    # Global semaphore for concurrent attacks
    global_semaphore = threading.Semaphore(MAX_CONCURRENT_ATTACKS)

    # Worker function (unchanged from original)
    def worker_run_solver_and_collect(solver_path: Path, team_name: str, team_ip: str, flag_regex: re.Pattern) -> List[Flag]:
        global_semaphore.acquire()
        try:
            solver_name = solver_path.stem
            
            # Update solver status
            stats_queue.put({
                'type': 'solver_update',
                'solver': solver_name,
                'data': {'status': 'Running', 'teams': len(teams)}
            })
            
            out, ok = run_solver_process(solver_path, team_ip)
            found_objs: List[Flag] = []
            if ok:
                found = find_flags_in_output(out, flag_regex)
                if found:
                    with print_lock:
                        logger.info(f"🏁 [{solver_name} -> {team_name}] Found {len(found)} flag(s)")
                        
                        # Track per-solver stats
                        stats_queue.put({
                            'type': 'solver_update',
                            'solver': solver_name,
                            'data': {
                                'found': len(found),
                                'last_run': datetime.now().strftime('%H:%M:%S'),
                                'status': 'Success'
                            }
                        })
                    found_objs = create_flag_objects(found, solver_name, team_name)
                    
                    # Send individual flag entries for tracking
                    for flag_obj in found_objs:
                        stats_queue.put({
                            'type': 'flag_entry',
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'flag': flag_obj.flag,
                            'solver': solver_name,
                            'team': team_name,
                            'status': 'FOUND'
                        })
                else:
                    if out.strip():
                        logger.debug('[%s -> %s] No flags. Sample output: %s', solver_name, team_name, out.strip()[:200])
                    else:
                        logger.debug('[%s -> %s] No output', solver_name, team_name)
                    
                    stats_queue.put({
                        'type': 'solver_update',
                        'solver': solver_name,
                        'data': {
                            'last_run': datetime.now().strftime('%H:%M:%S'),
                            'status': 'No flags'
                        }
                    })
            else:
                logger.warning('⚠️ ERROR [%s -> %s] Solver failed/timed out', solver_name, team_name)
                stats_queue.put({
                    'type': 'solver_update',
                    'solver': solver_name,
                    'data': {
                        'last_run': datetime.now().strftime('%H:%M:%S'),
                        'status': 'Failed'
                    }
                })
            
            return found_objs
        finally:
            global_semaphore.release()

    def handle_found_flags_from_task(flags_from_task: List[Flag]):
        if not flags_from_task:
            return
        flag_manager.add_flags(flags_from_task)

    # Per-solver thread management (unchanged)
    solver_threads: Dict[str, Dict] = {}
    solver_threads_lock = threading.Lock()

    def ensure_solver_worker(solver_path: Path):
        key = str(solver_path.resolve())
        with solver_threads_lock:
            if key in solver_threads:
                return solver_threads[key]['queue']

            q = queue.Queue()

            def solver_thread_loop():
                logger.info('Solver thread started for %s', solver_path.name)
                local_executor = None
                while not stop_event.is_set():
                    try:
                        cmd = q.get(timeout=1)
                    except queue.Empty:
                        continue
                    if cmd == 'run_all':
                        teams_items = list(teams.items())
                        random.shuffle(teams_items)
                        if not teams_items:
                            continue

                        if use_threading:
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

                        else:
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

    # Watcher thread (unchanged)
    def watcher_thread():
        observer = Observer()
        event_handler = SolverEventHandler(solvers_dir, ensure_solver_worker, print_lock)
        observer.schedule(event_handler, str(solvers_dir), recursive=False)
        observer.start()

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
                # Check for force run commands from TUI
                try:
                    if not stats_queue.empty():
                        stat = stats_queue.get_nowait()
                        if stat.get('type') == 'force_run':
                            for s in initial_solvers:
                                q = ensure_solver_worker(s)
                                try:
                                    q.put_nowait('run_all')
                                except queue.Full:
                                    pass
                            logger.info('Force run triggered from TUI')
                except:
                    pass
        except Exception:
            logger.exception('Watcher thread exception')
        finally:
            observer.stop()
            observer.join()

    watcher = threading.Thread(target=watcher_thread, daemon=True)
    watcher.start()

    # Main loop
    try:
        while not stop_event.is_set():
            cycle_start = time.time()
            logger.info('Starting full-run cycle: signaling all solver threads to run')
            stats_queue.put({'type': 'cycle'})

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
            stats_queue.put({'type': 'active_solvers', 'count': scheduled})

            # small grace to let some tasks finish and populate pending flags
            time.sleep(0.5)

            # Get all queued flags
            queued_candidates = flag_manager.get_queued_candidates()

            if queued_candidates:
                logger.info(f"📤 Candidates for submission ({len(queued_candidates)})")

                # group and fair-share
                grouped = {}
                for f in queued_candidates:
                    key = (f.sploit, f.team)
                    grouped.setdefault(key, []).append(f)
                limit = config.get('SUBMIT_FLAG_LIMIT', len(queued_candidates))
                to_submit = get_fair_share(list(grouped.values()), limit)

                logger.info(f"📤 Selected to submit ({len(to_submit)})")
                
                results = submit_flags_to_system(to_submit)

                # process results: update DB
                flag_manager.update_after_submission(results)

                for res in results:
                    flag_str = getattr(res, 'flag', None)
                    status = getattr(res, 'status', None)
                    
                    # Extract solver and team from flag object if available
                    solver_name = 'unknown'
                    team_name = 'unknown'
                    for f in to_submit:
                        if f.flag == flag_str:
                            solver_name = f.sploit
                            team_name = f.team
                            break
                    
                    # Send to TUI with proper details
                    stats_queue.put({
                        'type': 'flag_entry',
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'flag': flag_str,
                        'solver': solver_name,
                        'team': team_name,
                        'status': getattr(status, 'name', 'UNKNOWN')
                    })
                    
                    # Update stats
                    if status == FlagStatus.ACCEPTED:
                        icon = '✅'
                        # Update solver accepted count
                        stats_queue.put({
                            'type': 'solver_update',
                            'solver': solver_name,
                            'data': {'accepted': 1}
                        })
                    elif status == FlagStatus.REJECTED:
                        icon = '❌'
                    elif status == FlagStatus.QUEUED:
                        icon = '⏳'
                    else:
                        icon = '⏭️'

                    logger.info(f"{icon} {flag_str}: {getattr(status, 'name', status)} {getattr(res, 'checksystem_response', '') or ''}")

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
        flag_manager.close()
        logger.info('Shutdown complete')

# Original main_loop for CLI mode (keep unchanged)
def main_loop():
    """Original main loop for CLI mode"""
    
    # Internal runtime state
    print_lock = threading.Lock()
    
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
    
    def format_flags_list(flags: List[str], limit: int = 10) -> str:
        if not flags:
            return ''
        display = flags if len(flags) <= limit else flags[:limit]
        s = ', '.join(display)
        if len(flags) > limit:
            s += f', ...(+{len(flags)-limit} more)'
        return s
    
    # Validate config
    required_keys = ['TEAMS', 'FLAG_FORMAT']
    for key in required_keys:
        if key not in CONFIG:
            raise ValueError(f"Missing required config key: {key}")

    config = CONFIG
    use_threading = bool(config.get('USE_THREADING', True))

    # Add console handler for CLI mode
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(ch)
    
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

    # in-progress trackers
    in_progress: Set[Tuple[str,str]] = set()
    in_progress_lock = threading.Lock()

    # Global semaphore
    global_semaphore = threading.Semaphore(MAX_CONCURRENT_ATTACKS)

    stop_event = threading.Event()

    def graceful(signum, frame):
        logger.info('Received signal %s, shutting down...', signum)
        stop_event.set()

    signal.signal(signal.SIGINT, graceful)
    signal.signal(signal.SIGTERM, graceful)

    # Worker function
    def worker_run_solver_and_collect(solver_path: Path, team_name: str, team_ip: str, flag_regex: re.Pattern) -> List[Flag]:
        global_semaphore.acquire()
        try:
            solver_name = solver_path.stem
            out, ok = run_solver_process(solver_path, team_ip)
            found_objs: List[Flag] = []
            if ok:
                found = find_flags_in_output(out, flag_regex)
                if found:
                    with print_lock:
                        logger.info(f"{EMOJI['found']} [{solver_name} -> {team_name}] Found {len(found)} flag(s): {format_flags_list(found)}")
                    found_objs = create_flag_objects(found, solver_name, team_name)
                else:
                    if out.strip():
                        logger.debug('[%s -> %s] No flags. Sample output: %s', solver_name, team_name, out.strip()[:200])
                    else:
                        logger.debug('[%s -> %s] No output', solver_name, team_name)
            else:
                logger.warning('%s ERROR [%s -> %s] Solver failed/timed out. Output: %s', EMOJI['error'], solver_name, team_name, out.strip()[:400])
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
                logger.info('Solver thread started for %s', solver_path.name)
                local_executor = None
                while not stop_event.is_set():
                    try:
                        cmd = q.get(timeout=1)
                    except queue.Empty:
                        continue
                    if cmd == 'run_all':
                        teams_items = list(teams.items())
                        random.shuffle(teams_items)
                        if not teams_items:
                            continue

                        if use_threading:
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

                        else:
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

    # Watcher thread
    def watcher_thread():
        observer = Observer()
        event_handler = SolverEventHandler(solvers_dir, ensure_solver_worker, print_lock)
        observer.schedule(event_handler, str(solvers_dir), recursive=False)
        observer.start()

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

            time.sleep(0.5)

            queued_candidates = flag_manager.get_queued_candidates()

            if queued_candidates:
                with print_lock:
                    logger.info(f"{EMOJI['submit']} Candidates for submission ({len(queued_candidates)}): {format_flags_list([f.flag for f in queued_candidates])}")

                grouped = {}
                for f in queued_candidates:
                    key = (f.sploit, f.team)
                    grouped.setdefault(key, []).append(f)
                limit = config.get('SUBMIT_FLAG_LIMIT', len(queued_candidates))
                to_submit = get_fair_share(list(grouped.values()), limit)
                cycle_stats['flags_submitted'] += len(to_submit)

                with print_lock:
                    logger.info(f"{EMOJI['submit']} Selected to submit ({len(to_submit)}): {format_flags_list([f.flag for f in to_submit])}")

                logger.info('Submitting %d flags', len(to_submit))
                results = submit_flags_to_system(to_submit)

                flag_manager.update_after_submission(results)
                cycle_stats['accepted'] += sum(1 for r in results if getattr(r, 'status', None) == FlagStatus.ACCEPTED)

                for res in results:
                    flag_str = getattr(res, 'flag', None)
                    status = getattr(res, 'status', None)
                    if status == FlagStatus.ACCEPTED:
                        icon = EMOJI['accepted']
                    elif status == FlagStatus.REJECTED:
                        icon = EMOJI['rejected']
                    elif status == FlagStatus.QUEUED:
                        icon = EMOJI['queued']
                    else:
                        icon = EMOJI.get('skipped','⏭️')

                    with print_lock:
                        logger.info(f"{icon} {flag_str}: {getattr(status, 'name', status)} {getattr(res, 'checksystem_response', '') or ''}")

                summarize_results(results)
            else:
                logger.debug('No queued flags to submit this cycle')

            total_submitted = cycle_stats['flags_submitted']
            success_rate = (cycle_stats['accepted'] / total_submitted * 100) if total_submitted else 0
            logger.info('Cycle stats: flags_found=%d, flags_submitted=%d, accepted=%d, success_rate=%.2f%%',
                        cycle_stats['flags_found'], total_submitted, cycle_stats['accepted'], success_rate)

            elapsed = time.time() - cycle_start
            wait = max(0, RUN_INTERVAL - elapsed)
            logger.info('Cycle finished; sleeping %ds', wait)
            stop_event.wait(wait)

    except Exception:
        logger.exception('Main loop exception')
    finally:
        logger.info('Shutting down: stopping watcher and solver threads')
        stop_event.set()
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

# Main entry point
if __name__ == '__main__':
    args = parse_args()
    if args.fresh:
        clear_data()
    
    if args.no_tui:
        # Run in original CLI mode
        main_loop()
    else:
        # Run with TUI
        app = TernakLeleTUI(main_loop_tui)
        app.run()