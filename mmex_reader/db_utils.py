"""Database utility functions for the MMEX Kivy application - Step 1 Refactor.

This module now imports schema constants from db_schema.py.
"""

import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Dict, Optional, Tuple, Any, Union

import pandas as pd
from dotenv import load_dotenv

from mmex_reader.error_handling import handle_database_query, validate_date_format, validate_date_range
from mmex_reader.db_schema import (
    CATEGORY_TABLE, SUBCATEGORY_TABLE, ACCOUNT_TABLE, 
    TRANSACTION_TABLE, PAYEE_TABLE, TAG_TABLE, TAGLINK_TABLE,
    ACCOUNT_COLS
)

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
DB_PATH_PRIMARY_ENV: str = "DB_FILE_PATH"
DB_PATH_SECONDARY_ENV: str = "MMEX_DB_PATH"
DEFAULT_LOG_LEVEL: str = "INFO"

# Connection pool configuration
MAX_CONNECTIONS: int = 5
CONNECTION_TIMEOUT: int = 30  # seconds

# Missing constants in original db_utils.py (fixed here)
DEFAULT_QUERY_TIMEOUT: int = 30
MAX_RETRY_ATTEMPTS: int = 3

# Application configuration
class DatabaseConfig:
    def __init__(self):
        self.db_path: Optional[str] = None
        self.max_connections: int = MAX_CONNECTIONS
        self.connection_timeout: int = CONNECTION_TIMEOUT
        self.query_timeout: int = DEFAULT_QUERY_TIMEOUT
        self.max_retry_attempts: int = MAX_RETRY_ATTEMPTS
        self.log_level: str = DEFAULT_LOG_LEVEL
    
    def load_from_env(self) -> None:
        self.db_path = os.getenv(DB_PATH_PRIMARY_ENV) or os.getenv(DB_PATH_SECONDARY_ENV)
        self.max_connections = int(os.getenv("MMEX_MAX_CONNECTIONS", MAX_CONNECTIONS))
        self.connection_timeout = int(os.getenv("MMEX_CONNECTION_TIMEOUT", CONNECTION_TIMEOUT))
        self.query_timeout = int(os.getenv("MMEX_QUERY_TIMEOUT", DEFAULT_QUERY_TIMEOUT))
        self.max_retry_attempts = int(os.getenv("MMEX_MAX_RETRY_ATTEMPTS", MAX_RETRY_ATTEMPTS))
        self.log_level = os.getenv("MMEX_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    
    def validate(self) -> bool:
        if not self.db_path or not os.path.exists(self.db_path):
            return False
        return True

_db_config = DatabaseConfig()

class ConnectionPool:
    _instance: Optional['ConnectionPool'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'ConnectionPool':
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConnectionPool, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self) -> None:
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._db_path: Optional[str] = None
        self._pool: Dict[int, sqlite3.Connection] = {}
        self._in_use: Dict[int, bool] = {}
        self._pool_lock: threading.Lock = threading.Lock()
        self._initialized: bool = True
    
    def initialize(self, db_path: str) -> None:
        if not db_path or not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
        with self._pool_lock:
            self._db_path = db_path
            self._close_all_connections()
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        if not self._db_path:
            return None
        with self._pool_lock:
            for conn_id, in_use in self._in_use.items():
                if not in_use and conn_id in self._pool:
                    try:
                        conn = self._pool[conn_id]
                        conn.execute("SELECT 1")
                        self._in_use[conn_id] = True
                        return conn
                    except sqlite3.Error:
                        self._remove_connection(conn_id)
            if len(self._pool) < MAX_CONNECTIONS:
                try:
                    conn = sqlite3.connect(self._db_path, timeout=CONNECTION_TIMEOUT, check_same_thread=False)
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn_id = id(conn)
                    self._pool[conn_id] = conn
                    self._in_use[conn_id] = True
                    return conn
                except sqlite3.Error:
                    return None
            return None
    
    def release_connection(self, conn: Optional[sqlite3.Connection]) -> None:
        if not conn: return
        conn_id = id(conn)
        with self._pool_lock:
            if conn_id in self._pool:
                self._in_use[conn_id] = False
    
    def close_all(self) -> None:
        with self._pool_lock:
            self._close_all_connections()
    
    def _close_all_connections(self) -> None:
        for conn_id, conn in self._pool.items():
            try: conn.close()
            except sqlite3.Error: pass
        self._pool.clear()
        self._in_use.clear()
    
    def _remove_connection(self, conn_id: int) -> None:
        if conn_id in self._pool:
            try: self._pool[conn_id].close()
            except sqlite3.Error: pass
            del self._pool[conn_id]
        if conn_id in self._in_use:
            del self._in_use[conn_id]
    
    def get_pool_status(self) -> Dict[str, Any]:
        with self._pool_lock:
            total = len(self._pool)
            active = sum(1 for v in self._in_use.values() if v)
            return {'total_connections': total, 'active_connections': active, 'database_path': self._db_path}

_connection_pool = ConnectionPool()

def _resolve_db_path(preferred_path: Optional[str] = None) -> Optional[str]:
    if preferred_path: return preferred_path
    try:
        from mmex_reader.config_manager import config_manager
        cfg = config_manager.get_config()
        if getattr(cfg, 'db_file_path', None): return cfg.db_file_path
    except Exception: pass
    db_path = os.getenv(DB_PATH_PRIMARY_ENV) or os.getenv(DB_PATH_SECONDARY_ENV)
    if db_path: return db_path
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        return os.getenv(DB_PATH_PRIMARY_ENV) or os.getenv(DB_PATH_SECONDARY_ENV)
    return None

def _ensure_pool_for_path(db_path: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    resolved = _resolve_db_path(db_path)
    if not resolved or not os.path.exists(resolved):
        return "Database path not found", None
    status = _connection_pool.get_pool_status()
    if status.get('database_path') != resolved:
        _connection_pool.initialize(resolved)
    return None, resolved

def load_db_path(db_path: Optional[str] = None, initialize_pool: bool = True) -> Optional[str]:
    resolved = _resolve_db_path(db_path)
    if not resolved or not os.path.exists(resolved): return None
    if initialize_pool: _connection_pool.initialize(resolved)
    return resolved

def get_all_accounts(db_path: str) -> Tuple[Optional[str], pd.DataFrame]:
    if not db_path or not os.path.exists(db_path): return "Invalid path", pd.DataFrame()
    conn = _connection_pool.get_connection()
    if not conn: return "No connection", pd.DataFrame()
    try:
        cols = ", ".join(ACCOUNT_COLS.values())
        query = f"SELECT {cols} FROM {ACCOUNT_TABLE} WHERE {ACCOUNT_COLS['status']} = 'Open' ORDER BY {ACCOUNT_COLS['name']}"
        return handle_database_query(conn, query)
    finally: _connection_pool.release_connection(conn)

def get_account_by_id(db_path: str, account_id: int) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    if not db_path or account_id <= 0: return "Invalid params", None
    conn = _connection_pool.get_connection()
    if not conn: return "No connection", None
    try:
        query = f"SELECT * FROM {ACCOUNT_TABLE} WHERE ACCOUNTID = ?"
        err, df = handle_database_query(conn, query, [account_id])
        if err or df.empty: return err or "Not found", None
        row = df.iloc[0]
        return None, {k: row.get(v) for k, v in ACCOUNT_COLS.items()}
    finally: _connection_pool.release_connection(conn)

def _build_transactions_query(start_date, end_date, account_id, page_size, page_number):
    query = f"SELECT t.*, a.ACCOUNTNAME, c.CATEGNAME, s.SUBCATEGNAME, p.PAYEENAME FROM {TRANSACTION_TABLE} t LEFT JOIN {ACCOUNT_TABLE} a ON t.ACCOUNTID = a.ACCOUNTID LEFT JOIN {CATEGORY_TABLE} c ON t.CATEGID = c.CATEGID LEFT JOIN {SUBCATEGORY_TABLE} s ON t.SUBCATEGID = s.SUBCATEGID LEFT JOIN {PAYEE_TABLE} p ON t.PAYEEID = p.PAYEEID WHERE t.DELETEDTIME = ''"
    params = []
    if account_id: query += " AND t.ACCOUNTID = ?"; params.append(account_id)
    if start_date: query += " AND t.TRANSDATE >= ?"; params.append(start_date.strftime("%Y-%m-%d"))
    if end_date: query += " AND t.TRANSDATE <= ?"; params.append(end_date.strftime("%Y-%m-%d"))
    query += " ORDER BY t.TRANSDATE DESC, t.TRANSID DESC"
    if page_size:
        if page_number: query += " LIMIT ? OFFSET ?"; params.extend([page_size, (page_number-1)*page_size])
        else: query += " LIMIT ?"; params.append(page_size)
    return query, params

def _get_tags_for(conn, transaction_ids):
    if not transaction_ids: return {}
    placeholders = ','.join('?' for _ in transaction_ids)
    query = f"SELECT tl.REFID as TRANSID, t.TAGNAME FROM {TAG_TABLE} t JOIN {TAGLINK_TABLE} tl ON t.TAGID = tl.TAGID WHERE tl.REFID IN ({placeholders}) AND tl.REFTYPE = 'Transaction'"
    err, df = handle_database_query(conn, query, transaction_ids)
    if err or df.empty: return {tid: '' for tid in transaction_ids}
    res = {}
    for _, row in df.iterrows(): res.setdefault(row['TRANSID'], []).append(row['TAGNAME'])
    return {tid: ', '.join(res.get(tid, [])) for tid in transaction_ids}

def get_transactions(db_path, start_date_str=None, end_date_str=None, account_id=None, page_size=None, page_number=None):
    err, resolved = _ensure_pool_for_path(db_path)
    if err: return err, pd.DataFrame()
    start = end = None
    if start_date_str: _, start = validate_date_format(start_date_str)
    if end_date_str: _, end = validate_date_format(end_date_str)
    conn = _connection_pool.get_connection()
    if not conn: return "No connection", pd.DataFrame()
    try:
        query, params = _build_transactions_query(start, end, account_id, page_size, page_number)
        err, df = handle_database_query(conn, query, params)
        if not err and not df.empty:
            tags = _get_tags_for(conn, df['TRANSID'].tolist())
            df['TAGS'] = df['TRANSID'].map(tags).fillna('')
        return err, df
    finally: _connection_pool.release_connection(conn)

def calculate_balance_for_account(db_path, account_id):
    if not db_path or account_id <= 0: return "Invalid", 0.0
    conn = _connection_pool.get_connection()
    if not conn: return "No connection", 0.0
    try:
        query = f"SELECT SUM(CASE WHEN TRANSCODE='Deposit' THEN TRANSAMOUNT WHEN TRANSCODE='Withdrawal' THEN -TRANSAMOUNT ELSE 0 END) as BALANCE FROM {TRANSACTION_TABLE} WHERE ACCOUNTID = ? AND DELETEDTIME = ''"
        err, df = handle_database_query(conn, query, [account_id])
        return err, float(df.iloc[0]['BALANCE']) if not err and not df.empty else 0.0
    finally: _connection_pool.release_connection(conn)
