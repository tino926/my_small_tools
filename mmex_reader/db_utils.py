"""Database utility functions for the MMEX Kivy application.

This module provides functions for interacting with the MMEX SQLite database,
including loading the database path, retrieving accounts and transactions,
and calculating account balances. Implements connection pooling for better performance.

Classes:
    ConnectionPool: Singleton connection pool for SQLite database connections.

Functions:
    load_db_path: Load database path from environment and initialize connection pool.
    get_all_accounts: Retrieve all active accounts from the database.
    get_account_by_id: Retrieve specific account details by ID.
    get_transactions: Retrieve transactions with optional filtering.
    calculate_balance_for_account: Calculate account balance up to a specific date.

Constants:
    Various MMEX database schema constants for table and field names.
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

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
# Primary env var name for DB path (prefer consistent with README and .env)
DB_PATH_PRIMARY_ENV: str = "DB_FILE_PATH"
# Legacy/secondary env var maintained for backward compatibility
DB_PATH_SECONDARY_ENV: str = "MMEX_DB_PATH"
DEFAULT_LOG_LEVEL: str = "INFO"

# Connection pool configuration
MAX_CONNECTIONS: int = 5
CONNECTION_TIMEOUT: int = 30  # seconds

# MMEX database schema constants - Table names
CATEGORY_TABLE: str = "CATEGORY_V1"
SUBCATEGORY_TABLE: str = "SUBCATEGORY_V1"
ACCOUNT_TABLE: str = "ACCOUNTLIST_V1"
TRANSACTION_TABLE: str = "CHECKINGACCOUNT_V1"
PAYEE_TABLE: str = "PAYEE_V1"
TAG_TABLE: str = "TAG_V1"
TAGLINK_TABLE: str = "TAGLINK_V1"

# MMEX database schema constants - Account table columns
ACCOUNT_COLS: Dict[str, str] = {
    "id": "ACCOUNTID",
    "name": "ACCOUNTNAME",
    "type": "ACCOUNTTYPE",
    "initial_balance": "INITIALBAL",
    "is_favorite": "FAVORITEACCT",
    "currency_id": "CURRENCYID",
    "status": "STATUS",
    "notes": "NOTES",
    "held_at": "HELDAT",
    "website": "WEBSITE",
    "contact_info": "CONTACTINFO",
    "access_info": "ACCESSINFO",
    "statement_locked": "STATEMENTLOCKED",
    "statement_date": "STATEMENTDATE",
    "min_balance": "MINIMUMBALANCE",
    "credit_limit": "CREDITLIMIT",
    "interest_rate": "INTERESTRATE",
    "payment_due_date": "PAYMENTDUEDATE",
    "min_payment": "MINIMUMPAYMENT"
}

# Application configuration
class DatabaseConfig:
    """Configuration class for database-related settings.
    
    This class centralizes all database configuration options and provides
    methods to load configuration from environment variables or files.
    
    Attributes:
        db_path: Path to the MMEX database file.
        max_connections: Maximum number of connections in the pool.
        connection_timeout: Timeout for database connections in seconds.
        query_timeout: Timeout for database queries in seconds.
        max_retry_attempts: Maximum number of retry attempts for failed operations.
        log_level: Logging level for database operations.
    """
    
    def __init__(self):
        """Initialize database configuration with default values."""
        self.db_path: Optional[str] = None
        self.max_connections: int = MAX_CONNECTIONS
        self.connection_timeout: int = CONNECTION_TIMEOUT
        self.query_timeout: int = DEFAULT_QUERY_TIMEOUT
        self.max_retry_attempts: int = MAX_RETRY_ATTEMPTS
        self.log_level: str = DEFAULT_LOG_LEVEL
    
    def load_from_env(self) -> None:
        """Load configuration from environment variables.
        Prefer `DB_FILE_PATH`, fallback to `MMEX_DB_PATH` for compatibility.
        """
        self.db_path = os.getenv(DB_PATH_PRIMARY_ENV) or os.getenv(DB_PATH_SECONDARY_ENV)
        self.max_connections = int(os.getenv("MMEX_MAX_CONNECTIONS", MAX_CONNECTIONS))
        self.connection_timeout = int(os.getenv("MMEX_CONNECTION_TIMEOUT", CONNECTION_TIMEOUT))
        self.query_timeout = int(os.getenv("MMEX_QUERY_TIMEOUT", DEFAULT_QUERY_TIMEOUT))
        self.max_retry_attempts = int(os.getenv("MMEX_MAX_RETRY_ATTEMPTS", MAX_RETRY_ATTEMPTS))
        self.log_level = os.getenv("MMEX_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    
    def validate(self) -> bool:
        """Validate the current configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
        """
        if not self.db_path:
            logger.error("Database path is not configured")
            return False
        
        if not os.path.exists(self.db_path):
            logger.error(f"Database file not found: {self.db_path}")
            return False
        
        if self.max_connections <= 0:
            logger.error("Max connections must be greater than 0")
            return False
        
        if self.connection_timeout <= 0:
            logger.error("Connection timeout must be greater than 0")
            return False
        
        return True

# Global configuration instance
_db_config = DatabaseConfig()


class ConnectionPool:
    """A thread-safe SQLite connection pool implementation using the Singleton pattern.
    
    This class manages a pool of SQLite connections to improve performance
    by reusing connections instead of creating new ones for each operation.
    
    Attributes:
        _instance: Singleton instance of the connection pool.
        _lock: Thread lock for thread-safe operations.
        _db_path: Path to the SQLite database file.
        _pool: Dictionary mapping connection IDs to connection objects.
        _in_use: Dictionary tracking which connections are currently in use.
        _initialized: Flag to prevent re-initialization.
    
    Methods:
        initialize: Initialize the pool with a database path.
        get_connection: Retrieve an available connection from the pool.
        release_connection: Return a connection to the pool.
        close_all: Close all connections and clear the pool.
    """
    
    _instance: Optional['ConnectionPool'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'ConnectionPool':
        """Create or return the singleton instance of ConnectionPool.
        
        Returns:
            The singleton ConnectionPool instance.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConnectionPool, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self) -> None:
        """Initialize the ConnectionPool instance (only once due to singleton pattern)."""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._db_path: Optional[str] = None
        self._pool: Dict[int, sqlite3.Connection] = {}
        self._in_use: Dict[int, bool] = {}
        self._pool_lock: threading.Lock = threading.Lock()
        self._initialized: bool = True
    
    def initialize(self, db_path: str) -> None:
        """Initialize the connection pool with the database path.
        
        Args:
            db_path: Path to the SQLite database file.
            
        Raises:
            FileNotFoundError: If the database file doesn't exist.
            ValueError: If the database path is invalid.
        """
        if not db_path or not isinstance(db_path, str):
            raise ValueError("Database path must be a non-empty string")
            
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
            
        with self._pool_lock:
            self._db_path = db_path
            # Close any existing connections before reinitializing
            self._close_all_connections()
            logger.info(f"Connection pool initialized with database: {db_path}")
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """Get a connection from the pool or create a new one if needed.
        
        Returns:
            A SQLite connection object or None if unable to provide a connection.
            
        Raises:
            ValueError: If the connection pool hasn't been initialized.
        """
        if not self._db_path:
            raise ValueError("Connection pool not initialized with a database path")
            
        with self._pool_lock:
            # First, try to find an existing connection that's not in use
            for conn_id, in_use in self._in_use.items():
                if not in_use and conn_id in self._pool:
                    try:
                        # Test the connection to ensure it's still valid
                        conn = self._pool[conn_id]
                        conn.execute("SELECT 1")  # Simple test query
                        self._in_use[conn_id] = True
                        logger.debug(f"Reusing existing connection {conn_id}")
                        return conn
                    except sqlite3.Error as e:
                        logger.warning(f"Connection {conn_id} is invalid, removing: {e}")
                        self._remove_connection(conn_id)
            
            # If all connections are in use but we haven't reached the max, create a new one
            if len(self._pool) < MAX_CONNECTIONS:
                try:
                    conn = sqlite3.connect(
                        self._db_path,
                        timeout=CONNECTION_TIMEOUT,
                        check_same_thread=False
                    )
                    # Enable foreign key constraints
                    conn.execute("PRAGMA foreign_keys = ON")
                    
                    conn_id = id(conn)
                    self._pool[conn_id] = conn
                    self._in_use[conn_id] = True
                    logger.debug(f"Created new connection {conn_id}")
                    return conn
                except sqlite3.Error as e:
                    logger.error(f"Error creating new connection: {e}")
                    return None
            
            # If we've reached the max connections, return None
            logger.warning("Connection pool exhausted, no available connections")
            return None
    
    def release_connection(self, conn: Optional[sqlite3.Connection]) -> None:
        """Release a connection back to the pool.
        
        Args:
            conn: The connection to release.
        """
        if not conn:
            return
            
        conn_id = id(conn)
        with self._pool_lock:
            if conn_id in self._pool and conn_id in self._in_use:
                self._in_use[conn_id] = False
                logger.debug(f"Released connection {conn_id}")
            else:
                logger.warning(f"Attempted to release unknown connection {conn_id}")
    
    def close_all(self) -> None:
        """Close all connections in the pool and clear the pool."""
        with self._pool_lock:
            self._close_all_connections()
            logger.info("All connections closed and pool cleared")
    
    def _close_all_connections(self) -> None:
        """Internal method to close all connections without acquiring the lock."""
        for conn_id, conn in self._pool.items():
            try:
                conn.close()
                logger.debug(f"Closed connection {conn_id}")
            except sqlite3.Error as e:
                logger.warning(f"Error closing connection {conn_id}: {e}")
        self._pool.clear()
        self._in_use.clear()
    
    def _remove_connection(self, conn_id: int) -> None:
        """Remove a specific connection from the pool.
        
        Args:
            conn_id: The ID of the connection to remove.
        """
        if conn_id in self._pool:
            try:
                self._pool[conn_id].close()
            except sqlite3.Error as e:
                logger.warning(f"Error closing connection {conn_id}: {e}")
            del self._pool[conn_id]
            
        if conn_id in self._in_use:
            del self._in_use[conn_id]
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get the current status of the connection pool.
        
        Returns:
            Dictionary containing pool statistics.
        """
        with self._pool_lock:
            total_connections = len(self._pool)
            active_connections = sum(1 for in_use in self._in_use.values() if in_use)
            return {
                'total_connections': total_connections,
                'active_connections': active_connections,
                'available_connections': total_connections - active_connections,
                'max_connections': MAX_CONNECTIONS,
                'database_path': self._db_path
            }


# Global connection pool instance
_connection_pool = ConnectionPool()

def _resolve_db_path(preferred_path: Optional[str] = None) -> Optional[str]:
    """Resolve the best available database path with clear priority.

    Priority:
    1) `preferred_path` argument if provided
    2) `config_manager.AppConfig.db_file_path` (if available)
    3) Environment `DB_FILE_PATH`
    4) Environment `MMEX_DB_PATH` (legacy)
    5) `.env` file located next to this module

    Returns:
        Optional[str]: Resolved path string if found, else None
    """
    try:
        # 1) explicit preferred path
        if preferred_path:
            return preferred_path

        # 2) config_manager (optional dependency)
        try:
            from config_manager import config_manager  # local import to avoid hard dependency at import time
            cfg = config_manager.get_config()
            if getattr(cfg, 'db_file_path', None):
                return cfg.db_file_path
        except Exception:
            # Swallow import/config errors; continue to env fallbacks
            pass

        # 3) primary env var
        db_path = os.getenv(DB_PATH_PRIMARY_ENV)
        if db_path:
            return db_path

        # 4) secondary/legacy env var
        db_path = os.getenv(DB_PATH_SECONDARY_ENV)
        if db_path:
            return db_path

        # 5) .env file next to this module
        env_file_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file_path):
            load_dotenv(env_file_path)
            db_path = os.getenv(DB_PATH_PRIMARY_ENV) or os.getenv(DB_PATH_SECONDARY_ENV)
            if db_path:
                return db_path

        return None
    except Exception as e:
        logger.error(f"Error resolving database path: {e}")
        return None


def _ensure_pool_for_path(db_path: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Ensure the connection pool is initialized for the provided database path.

    Resolves the effective DB path using existing resolution logic, validates the
    path, and initializes the pool if it's not yet initialized or points to a
    different database.

    Args:
        db_path: Preferred database path or None to resolve via config/env.

    Returns:
        Tuple of (error_message, resolved_path). If error_message is not None,
        the operation failed.
    """
    try:
        resolved_path = _resolve_db_path(db_path)
        if not resolved_path:
            return "Database path not found in config/env/.env", None
        if not os.path.exists(resolved_path):
            return f"Database file not found: {resolved_path}", None

        status = _connection_pool.get_pool_status()
        current_path = status.get('database_path')
        if current_path != resolved_path:
            try:
                _connection_pool.initialize(resolved_path)
            except Exception as e:
                logger.error(f"Failed to initialize connection pool: {e}")
                return f"Failed to initialize connection pool: {e}", None
        return None, resolved_path
    except Exception as e:
        logger.error(f"Error ensuring connection pool for path: {e}")
        return f"Error ensuring connection pool for path: {e}", None


def load_db_path(db_path: Optional[str] = None, initialize_pool: bool = True) -> Optional[str]:
    """Load and optionally initialize the database path for the connection pool.

    This function is backward-compatible with prior usage where it returned the
    path only. It now also supports passing a `db_path` argument and can
    initialize the connection pool with the resolved path.

    Args:
        db_path: Optional preferred database path to use.
        initialize_pool: Whether to initialize the connection pool with the path.

    Returns:
        Optional[str]: The resolved database path if found and valid, else None.
    """
    try:
        resolved_path = _resolve_db_path(db_path)

        if not resolved_path:
            logger.warning(
                "Database path not found in config, environment ('%s'/'%s'), or .env file",
                DB_PATH_PRIMARY_ENV,
                DB_PATH_SECONDARY_ENV,
            )
            return None

        # Validate existence
        if not os.path.exists(resolved_path):
            logger.error(f"Database file not found: {resolved_path}")
            return None

        if initialize_pool:
            try:
                _connection_pool.initialize(resolved_path)
            except Exception as init_err:
                logger.error(f"Failed to initialize connection pool: {init_err}")
                return None

        logger.info(f"Database path resolved: {resolved_path}")
        return resolved_path
    except Exception as e:
        logger.error(f"Error loading database path: {e}")
        return None


def get_all_accounts(db_path: str) -> Tuple[Optional[str], pd.DataFrame]:
    """Get all accounts from the MMEX database using the connection pool.

    Args:
        db_path: Path to the MMEX database file.

    Returns:
        Tuple containing:
            - error_message (str or None): Error message if any, None if successful
            - accounts_dataframe (DataFrame): DataFrame containing account information
            
    Raises:
        ValueError: If the database path is invalid.
    """
    if not db_path or not isinstance(db_path, str):
        logger.error("Invalid database path provided")
        return "Invalid database path", pd.DataFrame()
        
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return "Database file not found", pd.DataFrame()

    conn = None
    try:
        # Get a connection from the pool
        conn = _connection_pool.get_connection()
        if not conn:
            logger.error("Could not get a database connection from the pool")
            return "Could not get a database connection from the pool", pd.DataFrame()
        
        # Dynamically build the list of columns to select
        columns_to_select = ", ".join(ACCOUNT_COLS.values())
        
        query = f"""
        SELECT {columns_to_select}
        FROM {ACCOUNT_TABLE}
        WHERE {ACCOUNT_COLS['status']} = 'Open'
        ORDER BY {ACCOUNT_COLS['name']}
        """
        
        error, accounts_df = handle_database_query(conn, query)
        if error:
            logger.error(f"Error retrieving accounts: {error}")
        else:
            logger.info(f"Retrieved {len(accounts_df)} accounts from database")
            
        return error, accounts_df

    except Exception as e:
        logger.error(f"Unexpected error retrieving accounts: {e}")
        return f"Unexpected error: {e}", pd.DataFrame()
    finally:
        # Release the connection back to the pool
        if conn:
            _connection_pool.release_connection(conn)


def get_account_by_id(db_path: str, account_id: int) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Get account details by ID using the connection pool.

    Args:
        db_path: Path to the MMEX database file.
        account_id: Account ID to retrieve.

    Returns:
        Tuple containing:
            - error_message (str or None): Error message if any, None if successful
            - account_data (dict or None): Dictionary containing account information
            
    Raises:
        ValueError: If the database path or account_id is invalid.
    """
    if not db_path or not isinstance(db_path, str):
        logger.error("Invalid database path provided")
        return "Invalid database path", None
        
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return "Database file not found", None
        
    if not isinstance(account_id, int) or account_id <= 0:
        logger.error(f"Invalid account_id: {account_id}")
        return f"Invalid account_id: {account_id}", None

    conn = None
    try:
        # Get a connection from the pool
        conn = _connection_pool.get_connection()
        if not conn:
            logger.error("Could not get a database connection from the pool")
            return "Could not get a database connection from the pool", None

        query = f"""
        SELECT 
            ACCOUNTID, 
            ACCOUNTNAME, 
            ACCOUNTTYPE, 
            INITIALBAL, 
            STATUS,
            NOTES,
            HELDAT,
            WEBSITE,
            CONTACTINFO,
            ACCESSINFO,
            FAVORITEACCT,
            CURRENCYID,
            STATEMENTLOCKED,
            STATEMENTDATE,
            MINIMUMBALANCE,
            CREDITLIMIT,
            INTERESTRATE,
            PAYMENTDUEDATE,
            MINIMUMPAYMENT
        FROM {ACCOUNT_TABLE}
        WHERE ACCOUNTID = ?
        """

        # Use centralized query handler for consistent error handling and resource safety
        error, df = handle_database_query(conn, query, [account_id])
        if error:
            logger.error(f"Error retrieving account {account_id}: {error}")
            return error, None

        if df.empty:
            logger.warning(f"Account with ID {account_id} not found")
            return f"Account with ID {account_id} not found", None

        row = df.iloc[0]
        account_data = {
            "id": int(row["ACCOUNTID"]),
            "name": row["ACCOUNTNAME"],
            "type": row["ACCOUNTTYPE"],
            "initial_balance": float(row["INITIALBAL"]) if pd.notna(row["INITIALBAL"]) else 0.0,
            "status": row["STATUS"],
            "notes": row["NOTES"],
            "held_at": row["HELDAT"],
            "website": row["WEBSITE"],
            "contact_info": row["CONTACTINFO"],
            "access_info": row["ACCESSINFO"],
            "favorite_account": int(row["FAVORITEACCT"]) if pd.notna(row["FAVORITEACCT"]) else 0,
            "currency_id": int(row["CURRENCYID"]) if pd.notna(row["CURRENCYID"]) else 0,
            "statement_locked": int(row["STATEMENTLOCKED"]) if pd.notna(row["STATEMENTLOCKED"]) else 0,
            "statement_date": row["STATEMENTDATE"],
            "minimum_balance": float(row["MINIMUMBALANCE"]) if pd.notna(row["MINIMUMBALANCE"]) else 0.0,
            "credit_limit": float(row["CREDITLIMIT"]) if pd.notna(row["CREDITLIMIT"]) else 0.0,
            "interest_rate": float(row["INTERESTRATE"]) if pd.notna(row["INTERESTRATE"]) else 0.0,
            "payment_due_date": row["PAYMENTDUEDATE"],
            "minimum_payment": float(row["MINIMUMPAYMENT"]) if pd.notna(row["MINIMUMPAYMENT"]) else 0.0,
        }

        logger.info(f"Retrieved account details for ID {account_id}: {account_data['name']}")
        return None, account_data

    except sqlite3.Error as e:
        logger.error(f"Database error retrieving account {account_id}: {e}")
        return f"Database error: {e}", None
    except Exception as e:
        logger.error(f"Unexpected error retrieving account {account_id}: {e}")
        return f"Unexpected error: {e}", None
    finally:
        # Release the connection back to the pool
        if conn:
            _connection_pool.release_connection(conn)


def _build_transactions_query(start_date: Optional[datetime], end_date: Optional[datetime], account_id: Optional[int], page_size: Optional[int], page_number: Optional[int]) -> Tuple[str, list]:
    query = f"""
        SELECT 
            t.TRANSID, 
            t.ACCOUNTID, 
            t.TRANSCODE, 
            t.TRANSAMOUNT, 
            t.TRANSACTIONNUMBER, 
            t.NOTES, 
            t.TRANSDATE, 
            t.FOLLOWUPID, 
            t.TOTRANSAMOUNT, 
            t.TOSPLITCATEGORY, 
            t.CATEGID, 
            t.SUBCATEGID, 
            t.TRANSACTIONDATE, 
            t.DELETEDTIME, 
            t.PAYEEID,
            t.STATUS,
            a.ACCOUNTNAME, 
            c.CATEGNAME, 
            s.SUBCATEGNAME, 
            p.PAYEENAME
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
    """Optimized function to get tags for transaction IDs in batches.

    This function has been optimized to improve performance by fetching
    all tags in a single query rather than multiple batched queries.
    """
    if not transaction_ids:
        return {}

    # Create a single query with all transaction IDs to minimize database round trips
    placeholders = ','.join(['?' for _ in transaction_ids])
    tag_query = f"""
                SELECT tl.REFID as TRANSID, t.TAGNAME
                FROM {TAG_TABLE} t
                JOIN {TAGLINK_TABLE} tl ON t.TAGID = tl.TAGID
                WHERE tl.REFID IN ({placeholders}) AND tl.REFTYPE = 'Transaction'
                ORDER BY tl.REFID, t.TAGNAME
                """

    tag_error, tags_df = handle_database_query(conn, tag_query, transaction_ids)
    if tag_error:
        logger.warning(f"Error retrieving tags: {tag_error}")
        return {}

    if tags_df.empty:
        # Return empty dict with all transaction IDs mapped to empty strings for consistency
        return {tid: '' for tid in transaction_ids}

    # Group tags by transaction ID efficiently
    tags_dict: Dict[int, list] = {}
    for _, tag_row in tags_df.iterrows():
        trans_id = tag_row['TRANSID']
        tag_name = tag_row['TAGNAME']
        if trans_id not in tags_dict:
            tags_dict[trans_id] = []
        tags_dict[trans_id].append(tag_name)

    # Join tags for each transaction ID and ensure all original IDs are represented
    result = {tid: ', '.join(tags_dict.get(tid, [])) for tid in transaction_ids}
    return result

def get_transactions(db_path: str, start_date_str: Optional[str] = None, 
                    end_date_str: Optional[str] = None, account_id: Optional[int] = None,
                    page_size: Optional[int] = None, page_number: Optional[int] = None) -> Tuple[Optional[str], pd.DataFrame]:
    """Get transactions from the MMEX database using the connection pool.

    Args:
        db_path: Path to the MMEX database file.
        start_date_str: Start date string in YYYY-MM-DD format (optional).
        end_date_str: End date string in YYYY-MM-DD format (optional).
        account_id: Account ID to filter transactions (optional).
        page_size: Number of transactions per page (optional, defaults to all).
        page_number: Page number to retrieve (1-based, optional).

    Returns:
        Tuple containing:
            - error_message (str or None): Error message if any, None if successful
            - transactions_dataframe (DataFrame): DataFrame containing transaction information
            
    Raises:
        ValueError: If the database path is invalid or date formats are incorrect.
    """
    # Ensure connection pool is initialized for the requested path
    err, resolved_path = _ensure_pool_for_path(db_path)
    if err:
        logger.error(err)
        return err, pd.DataFrame()

    # Validate date strings
    start_date = None
    end_date = None

    if start_date_str:
        error, start_date = validate_date_format(start_date_str, "start_date_str")
        if error:
            logger.error(f"Invalid start date format: {start_date_str}")
            return error, pd.DataFrame()

    if end_date_str:
        error, end_date = validate_date_format(end_date_str, "end_date_str")
        if error:
            logger.error(f"Invalid end date format: {end_date_str}")
            return error, pd.DataFrame()

    if start_date and end_date:
        error = validate_date_range(start_date_str, end_date_str)
        if error:
            logger.error(f"Invalid date range: {start_date_str} to {end_date_str}")
            return error, pd.DataFrame()
            
    # Validate account_id if provided
    if account_id is not None and (not isinstance(account_id, int) or account_id <= 0):
        logger.error(f"Invalid account_id: {account_id}")
        return f"Invalid account_id: {account_id}", pd.DataFrame()

    # Validate pagination parameters
    if page_size is not None and (not isinstance(page_size, int) or page_size <= 0):
        logger.error(f"Invalid page_size: {page_size}")
        return f"Invalid page_size: {page_size}", pd.DataFrame()
        
    if page_number is not None and (not isinstance(page_number, int) or page_number <= 0):
        logger.error(f"Invalid page_number: {page_number}")
        return f"Invalid page_number: {page_number}", pd.DataFrame()
        
    # If page_number is provided, page_size must also be provided
    if page_number is not None and page_size is None:
        logger.error("page_size must be provided when page_number is specified")
        return "page_size must be provided when page_number is specified", pd.DataFrame()

    conn = None
    try:
        # Get a connection from the pool
        conn = _connection_pool.get_connection()
        if not conn:
            logger.error("Could not get a database connection from the pool")
            return "Could not get a database connection from the pool", pd.DataFrame()
            
        query, params = _build_transactions_query(start_date, end_date, account_id, page_size, page_number)

        # Execute query with proper error handling
        error, transactions_df = handle_database_query(conn, query, params)
        if error:
            logger.error(f"Error retrieving transactions: {error}")
            return error, pd.DataFrame()

        if not transactions_df.empty:
            ids = transactions_df['TRANSID'].tolist()
            tags_map = _get_tags_for(conn, ids)
            transactions_df['TAGS'] = transactions_df['TRANSID'].apply(lambda tid: tags_map.get(tid, ''))
        else:
            transactions_df['TAGS'] = ''

        logger.info(f"Retrieved {len(transactions_df)} transactions from database")
        return None, transactions_df

    except Exception as e:
        logger.error(f"Unexpected error retrieving transactions: {e}")
        return f"Unexpected error: {e}", pd.DataFrame()
    finally:
        # Release the connection back to the pool
        if conn:
            _connection_pool.release_connection(conn)


def calculate_balance_for_account(db_path: str, account_id: int) -> Tuple[Optional[str], float]:
    """Calculate the balance for a specific account using SQL aggregation.

    Args:
        db_path: Path to the MMEX database file.
        account_id: The account ID to calculate balance for.

    Returns:
        Tuple containing:
            - error_message (str or None): Error message if any, None if successful
            - balance (float): The calculated balance for the account
            
    Raises:
        ValueError: If the database path is invalid or account_id is invalid.
    """
    if not db_path or not isinstance(db_path, str):
        logger.error("Invalid database path provided")
        return "Invalid database path", 0.0
        
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return "Database file not found", 0.0
        
    if not isinstance(account_id, int) or account_id <= 0:
        logger.error(f"Invalid account_id: {account_id}")
        return f"Invalid account_id: {account_id}", 0.0

    conn = None
    try:
        # Get a connection from the pool
        conn = _connection_pool.get_connection()
        if not conn:
            logger.error("Could not get a database connection from the pool")
            return "Could not get a database connection from the pool", 0.0

        # Use SQL aggregation for better performance
        query = f"""
        SELECT 
            COALESCE(SUM(
                CASE 
                    WHEN TRANSCODE = 'Deposit' THEN TRANSAMOUNT
                    WHEN TRANSCODE = 'Withdrawal' THEN -TRANSAMOUNT
                    WHEN TRANSCODE = 'Transfer' AND t.ACCOUNTID = ? THEN -t.TRANSAMOUNT
                    ELSE 0
                END
            ), 0.0) + 
            COALESCE((
                SELECT SUM(t2.TRANSAMOUNT) 
                FROM {TRANSACTION_TABLE} t2 
                WHERE t2.TOACCOUNTID = ? AND t2.TRANSCODE = 'Transfer' AND t2.DELETEDTIME = ''
            ), 0.0) as BALANCE
        FROM {TRANSACTION_TABLE} t
        WHERE t.ACCOUNTID = ? AND t.DELETEDTIME = ''
        """

        # Execute query with proper parameter binding
        params = [account_id, account_id, account_id]
        error, result_df = handle_database_query(conn, query, params)
        
        if error:
            logger.error(f"Error calculating balance for account {account_id}: {error}")
            return error, 0.0

        if result_df.empty:
            logger.warning(f"No transactions found for account {account_id}")
            return None, 0.0

        balance = float(result_df.iloc[0]['BALANCE'])
        logger.info(f"Calculated balance for account {account_id}: {balance}")
        return None, balance

    except Exception as e:
        logger.error(f"Unexpected error calculating balance for account {account_id}: {e}")
        return f"Unexpected error: {e}", 0.0
    finally:
        # Release the connection back to the pool
        if conn:
            _connection_pool.release_connection(conn)
