"""Database utility functions for the MMEX Kivy application - Final Refactor (Bridge).

This module is now a bridge that imports all functionality from modular files.
"""

from mmex_reader.db_schema import (
    CATEGORY_TABLE, SUBCATEGORY_TABLE, ACCOUNT_TABLE, 
    TRANSACTION_TABLE, PAYEE_TABLE, TAG_TABLE, TAGLINK_TABLE,
    ACCOUNT_COLS
)
from mmex_reader.db_connection import (
    _connection_pool, _ensure_pool_for_path, load_db_path,
    DatabaseConfig, _db_config, ConnectionPool
)
from mmex_reader.db_queries import (
    get_all_accounts, get_account_by_id, get_transactions,
    calculate_balance_for_account
)

__all__ = [
    'CATEGORY_TABLE', 'SUBCATEGORY_TABLE', 'ACCOUNT_TABLE', 
    'TRANSACTION_TABLE', 'PAYEE_TABLE', 'TAG_TABLE', 'TAGLINK_TABLE',
    'ACCOUNT_COLS', '_connection_pool', '_ensure_pool_for_path', 'load_db_path',
    'DatabaseConfig', '_db_config', 'ConnectionPool',
    'get_all_accounts', 'get_account_by_id', 'get_transactions',
    'calculate_balance_for_account'
]
