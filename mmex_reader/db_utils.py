"""Database utility functions for the MMEX Kivy application - Step 2 Refactor.

This module now imports schema and connection logic from separate modules.
"""

import logging
import pandas as pd
from typing import Dict, Optional, Tuple, Any, Union

from mmex_reader.error_handling import handle_database_query, validate_date_format
from mmex_reader.db_schema import (
    CATEGORY_TABLE, SUBCATEGORY_TABLE, ACCOUNT_TABLE, 
    TRANSACTION_TABLE, PAYEE_TABLE, TAG_TABLE, TAGLINK_TABLE,
    ACCOUNT_COLS
)
from mmex_reader.db_connection import (
    _connection_pool, _ensure_pool_for_path, load_db_path,
    DatabaseConfig, _db_config, ConnectionPool
)

# Configure logging
logger = logging.getLogger(__name__)

def get_all_accounts(db_path: str) -> Tuple[Optional[str], pd.DataFrame]:
    if not db_path: return "Invalid path", pd.DataFrame()
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
        return err, float(df.iloc[0]['BALANCE']) if not error and not df.empty else 0.0
    finally: _connection_pool.release_connection(conn)
