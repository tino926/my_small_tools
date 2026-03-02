"""Database query functions for the MMEX application."""

import logging
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, Tuple, Any, List

from mmex_reader.error_handling import handle_database_query, validate_date_format, validate_date_range
from mmex_reader.db_schema import (
    CATEGORY_TABLE, SUBCATEGORY_TABLE, ACCOUNT_TABLE, 
    TRANSACTION_TABLE, PAYEE_TABLE, TAG_TABLE, TAGLINK_TABLE,
    ACCOUNT_COLS
)
from mmex_reader.db_connection import _connection_pool, _ensure_pool_for_path

logger = logging.getLogger(__name__)

def get_all_accounts(db_path: str) -> Tuple[Optional[str], pd.DataFrame]:
    if not db_path:
        return "Invalid database path", pd.DataFrame()
    
    conn = None
    try:
        conn = _connection_pool.get_connection()
        if not conn:
            return "Could not get a database connection", pd.DataFrame()
        
        columns_to_select = ", ".join(ACCOUNT_COLS.values())
        query = f"""
        SELECT {columns_to_select}
        FROM {ACCOUNT_TABLE}
        WHERE {ACCOUNT_COLS['status']} = 'Open'
        ORDER BY {ACCOUNT_COLS['name']}
        """
        return handle_database_query(conn, query)
    except Exception as e:
        return str(e), pd.DataFrame()
    finally:
        if conn:
            _connection_pool.release_connection(conn)

def get_account_by_id(db_path: str, account_id: int) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    if not db_path or not isinstance(account_id, int) or account_id <= 0:
        return "Invalid parameters", None

    conn = None
    try:
        conn = _connection_pool.get_connection()
        if not conn:
            return "Could not get a database connection", None

        query = f"SELECT * FROM {ACCOUNT_TABLE} WHERE ACCOUNTID = ?"
        error, df = handle_database_query(conn, query, [account_id])
        
        if error or df.empty:
            return error or "Account not found", None

        row = df.iloc[0]
        # Simplification for refactoring purposes, assuming same keys as before
        account_data = {
            "id": int(row["ACCOUNTID"]),
            "name": row["ACCOUNTNAME"],
            "type": row["ACCOUNTTYPE"],
            "initial_balance": float(row["INITIALBAL"]) if pd.notna(row["INITIALBAL"]) else 0.0,
            "status": row["STATUS"],
            "notes": row.get("NOTES", ""),
            "held_at": row.get("HELDAT", ""),
            "website": row.get("WEBSITE", ""),
            "contact_info": row.get("CONTACTINFO", ""),
            "access_info": row.get("ACCESSINFO", ""),
            "favorite_account": int(row.get("FAVORITEACCT", 0)),
            "currency_id": int(row.get("CURRENCYID", 0)),
            "statement_locked": int(row.get("STATEMENTLOCKED", 0)),
            "statement_date": row.get("STATEMENTDATE", ""),
            "minimum_balance": float(row.get("MINIMUMBALANCE", 0.0)),
            "credit_limit": float(row.get("CREDITLIMIT", 0.0)),
            "interest_rate": float(row.get("INTERESTRATE", 0.0)),
            "payment_due_date": row.get("PAYMENTDUEDATE", ""),
            "minimum_payment": float(row.get("MINIMUMPAYMENT", 0.0)),
        }
        return None, account_data
    except Exception as e:
        return str(e), None
    finally:
        if conn:
            _connection_pool.release_connection(conn)

def _build_transactions_query(start_date: Optional[datetime], end_date: Optional[datetime], 
                             account_id: Optional[int], page_size: Optional[int], 
                             page_number: Optional[int]) -> Tuple[str, list]:
    query = f"""
        SELECT 
            t.TRANSID, t.ACCOUNTID, t.TRANSCODE, t.TRANSAMOUNT, t.TRANSACTIONNUMBER, 
            t.NOTES, t.TRANSDATE, t.FOLLOWUPID, t.TOTRANSAMOUNT, t.TOSPLITCATEGORY, 
            t.CATEGID, t.SUBCATEGID, t.TRANSACTIONDATE, t.DELETEDTIME, t.PAYEEID,
            t.STATUS, a.ACCOUNTNAME, c.CATEGNAME, s.SUBCATEGNAME, p.PAYEENAME
        FROM {TRANSACTION_TABLE} t
        LEFT JOIN {ACCOUNT_TABLE} a ON t.ACCOUNTID = a.ACCOUNTID
        LEFT JOIN {CATEGORY_TABLE} c ON t.CATEGID = c.CATEGID
        LEFT JOIN {SUBCATEGORY_TABLE} s ON t.SUBCATEGID = s.SUBCATEGID
        LEFT JOIN {PAYEE_TABLE} p ON t.PAYEEID = p.PAYEEID
        WHERE t.DELETEDTIME = ''
    """
    params: list = []
    if account_id is not None:
        query += " AND t.ACCOUNTID = ?"
        params.append(account_id)
    if start_date:
        query += " AND t.TRANSDATE >= ?"
        params.append(start_date.strftime("%Y-%m-%d"))
    if end_date:
        query += " AND t.TRANSDATE <= ?"
        params.append(end_date.strftime("%Y-%m-%d"))
    
    query += " ORDER BY t.TRANSDATE DESC, t.TRANSID DESC"
    
    if page_size is not None:
        if page_number is not None:
            offset = (page_number - 1) * page_size
            query += " LIMIT ? OFFSET ?"
            params.extend([page_size, offset])
        else:
            query += " LIMIT ?"
            params.append(page_size)
    return query, params

def _get_tags_for(conn: sqlite3.Connection, transaction_ids: list) -> Dict[int, str]:
    if not transaction_ids:
        return {}
    placeholders = ','.join(['?' for _ in transaction_ids])
    tag_query = f"""
                SELECT tl.REFID as TRANSID, t.TAGNAME
                FROM {TAG_TABLE} t
                JOIN {TAGLINK_TABLE} tl ON t.TAGID = tl.TAGID
                WHERE tl.REFID IN ({placeholders}) AND tl.REFTYPE = 'Transaction'
                ORDER BY tl.REFID, t.TAGNAME
                """
    tag_error, tags_df = handle_database_query(conn, tag_query, transaction_ids)
    if tag_error or tags_df.empty:
        return {tid: '' for tid in transaction_ids}
    
    tags_dict: Dict[int, list] = {}
    for _, tag_row in tags_df.iterrows():
        tid, name = tag_row['TRANSID'], tag_row['TAGNAME']
        tags_dict.setdefault(tid, []).append(name)
    return {tid: ', '.join(tags_dict.get(tid, [])) for tid in transaction_ids}

def get_transactions(db_path: str, start_date_str: Optional[str] = None, 
                    end_date_str: Optional[str] = None, account_id: Optional[int] = None,
                    page_size: Optional[int] = None, page_number: Optional[int] = None) -> Tuple[Optional[str], pd.DataFrame]:
    err, resolved_path = _ensure_pool_for_path(db_path)
    if err:
        return err, pd.DataFrame()

    start_date = end_date = None
    if start_date_str:
        _, start_date = validate_date_format(start_date_str)
    if end_date_str:
        _, end_date = validate_date_format(end_date_str)

    conn = None
    try:
        conn = _connection_pool.get_connection()
        if not conn:
            return "Could not get a database connection", pd.DataFrame()
            
        query, params = _build_transactions_query(start_date, end_date, account_id, page_size, page_number)
        error, df = handle_database_query(conn, query, params)
        if not error and not df.empty:
            tags_map = _get_tags_for(conn, df['TRANSID'].tolist())
            df['TAGS'] = df['TRANSID'].map(tags_map).fillna('')
        return error, df
    except Exception as e:
        return str(e), pd.DataFrame()
    finally:
        if conn:
            _connection_pool.release_connection(conn)

def calculate_balance_for_account(db_path: str, account_id: int) -> Tuple[Optional[str], float]:
    if not db_path or account_id <= 0:
        return "Invalid parameters", 0.0

    conn = None
    try:
        conn = _connection_pool.get_connection()
        if not conn:
            return "Could not get a database connection", 0.0

        query = f"""
        SELECT 
            COALESCE(SUM(CASE WHEN TRANSCODE = 'Deposit' THEN TRANSAMOUNT WHEN TRANSCODE = 'Withdrawal' THEN -TRANSAMOUNT WHEN TRANSCODE = 'Transfer' AND ACCOUNTID = ? THEN -TRANSAMOUNT ELSE 0 END), 0.0) + 
            COALESCE((SELECT SUM(TRANSAMOUNT) FROM {TRANSACTION_TABLE} WHERE TOACCOUNTID = ? AND TRANSCODE = 'Transfer' AND DELETEDTIME = ''), 0.0) as BALANCE
        FROM {TRANSACTION_TABLE} WHERE ACCOUNTID = ? AND DELETEDTIME = ''
        """
        error, df = handle_database_query(conn, query, [account_id, account_id, account_id])
        return error, float(df.iloc[0]['BALANCE']) if not error and not df.empty else 0.0
    except Exception as e:
        return str(e), 0.0
    finally:
        if conn:
            _connection_pool.release_connection(conn)
