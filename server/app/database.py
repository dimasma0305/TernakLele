"""
Module with SQLite helpers, see http://flask.pocoo.org/docs/0.12/patterns/sqlite3/
"""

import logging
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from constants import SCHEMA_PATH, SQLITE_DB_PATH

logger = logging.getLogger(__name__)


class DBPool:
    _lock = threading.RLock()
    _value = None

    @staticmethod
    def create():
        # Ensure the directory exists
        db_path = Path(SQLITE_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create connection to SQLite database
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        
        logger.info("Initializing db schema")
        try:
            with conn:
                conn.executescript(SCHEMA_PATH.read_text())
        finally:
            conn.close()
        
        return SQLITE_DB_PATH

    @classmethod
    def get(cls):
        with cls._lock:
            if cls._value is None:
                cls._value = cls.create()
        return cls._value


@contextmanager
def db_cursor(dict_cursor: bool = True):
    # Ensure database is initialized first
    DBPool.get()
    
    # SQLite doesn't need a connection pool like PostgreSQL
    # We'll create a new connection for each operation
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    
    if dict_cursor:
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    else:
        conn.row_factory = None  # Return tuples
    
    curs = conn.cursor()
    try:
        yield conn, curs
    finally:
        curs.close()
        conn.close()