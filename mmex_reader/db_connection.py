"""Database connection management and pooling for the MMEX application."""

import logging
import os
import sqlite3
import threading
from typing import Dict, Optional, Tuple, Any
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
DB_PATH_PRIMARY_ENV: str = "DB_FILE_PATH"
DB_PATH_SECONDARY_ENV: str = "MMEX_DB_PATH"
DEFAULT_LOG_LEVEL: str = "INFO"

# Connection pool configuration
MAX_CONNECTIONS: int = 5
CONNECTION_TIMEOUT: int = 30  # seconds

# Default timeouts and retry attempts (previously missing in db_utils.py)
DEFAULT_QUERY_TIMEOUT: int = 30
MAX_RETRY_ATTEMPTS: int = 3

class DatabaseConfig:
    """Configuration class for database-related settings."""
    
    def __init__(self):
        """Initialize database configuration with default values."""
        self.db_path: Optional[str] = None
        self.max_connections: int = MAX_CONNECTIONS
        self.connection_timeout: int = CONNECTION_TIMEOUT
        self.query_timeout: int = DEFAULT_QUERY_TIMEOUT
        self.max_retry_attempts: int = MAX_RETRY_ATTEMPTS
        self.log_level: str = DEFAULT_LOG_LEVEL
    
    def load_from_env(self) -> None:
        """Load configuration from environment variables."""
        self.db_path = os.getenv(DB_PATH_PRIMARY_ENV) or os.getenv(DB_PATH_SECONDARY_ENV)
        self.max_connections = int(os.getenv("MMEX_MAX_CONNECTIONS", MAX_CONNECTIONS))
        self.connection_timeout = int(os.getenv("MMEX_CONNECTION_TIMEOUT", CONNECTION_TIMEOUT))
        self.query_timeout = int(os.getenv("MMEX_QUERY_TIMEOUT", DEFAULT_QUERY_TIMEOUT))
        self.max_retry_attempts = int(os.getenv("MMEX_MAX_RETRY_ATTEMPTS", MAX_RETRY_ATTEMPTS))
        self.log_level = os.getenv("MMEX_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    
    def validate(self) -> bool:
        """Validate the current configuration."""
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
    """A thread-safe SQLite connection pool implementation using the Singleton pattern."""
    
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
        if not db_path or not isinstance(db_path, str):
            raise ValueError("Database path must be a non-empty string")
            
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
            
        with self._pool_lock:
            self._db_path = db_path
            self._close_all_connections()
            logger.info(f"Connection pool initialized with database: {db_path}")
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        if not self._db_path:
            raise ValueError("Connection pool not initialized with a database path")
            
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
                    conn = sqlite3.connect(
                        self._db_path,
                        timeout=CONNECTION_TIMEOUT,
                        check_same_thread=False
                    )
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn_id = id(conn)
                    self._pool[conn_id] = conn
                    self._in_use[conn_id] = True
                    return conn
                except sqlite3.Error as e:
                    logger.error(f"Error creating new connection: {e}")
                    return None
            return None
    
    def release_connection(self, conn: Optional[sqlite3.Connection]) -> None:
        if not conn:
            return
            
        conn_id = id(conn)
        with self._pool_lock:
            if conn_id in self._pool and conn_id in self._in_use:
                self._in_use[conn_id] = False
    
    def close_all(self) -> None:
        with self._pool_lock:
            self._close_all_connections()
    
    def _close_all_connections(self) -> None:
        for conn_id, conn in self._pool.items():
            try:
                conn.close()
            except sqlite3.Error:
                pass
        self._pool.clear()
        self._in_use.clear()
    
    def _remove_connection(self, conn_id: int) -> None:
        if conn_id in self._pool:
            try:
                self._pool[conn_id].close()
            except sqlite3.Error:
                pass
            del self._pool[conn_id]
        if conn_id in self._in_use:
            del self._in_use[conn_id]
    
    def get_pool_status(self) -> Dict[str, Any]:
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

_connection_pool = ConnectionPool()

def _resolve_db_path(preferred_path: Optional[str] = None) -> Optional[str]:
    try:
        if preferred_path:
            return preferred_path
        try:
            from mmex_reader.config_manager import config_manager
            cfg = config_manager.get_config()
            if getattr(cfg, 'db_file_path', None):
                return cfg.db_file_path
        except Exception:
            pass
        db_path = os.getenv(DB_PATH_PRIMARY_ENV)
        if db_path:
            return db_path
        db_path = os.getenv(DB_PATH_SECONDARY_ENV)
        if db_path:
            return db_path
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
    try:
        resolved_path = _resolve_db_path(db_path)
        if not resolved_path:
            return "Database path not found", None
        if not os.path.exists(resolved_path):
            return f"Database file not found: {resolved_path}", None
        status = _connection_pool.get_pool_status()
        current_path = status.get('database_path')
        if current_path != resolved_path:
            _connection_pool.initialize(resolved_path)
        return None, resolved_path
    except Exception as e:
        return str(e), None

def load_db_path(db_path: Optional[str] = None, initialize_pool: bool = True) -> Optional[str]:
    try:
        resolved_path = _resolve_db_path(db_path)
        if not resolved_path or not os.path.exists(resolved_path):
            return None
        if initialize_pool:
            _connection_pool.initialize(resolved_path)
        return resolved_path
    except Exception:
        return None
