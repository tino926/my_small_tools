"""Pagination utilities for the MMEX Kivy application.

This module provides functions for handling pagination of transaction data,
including counting total records and managing pagination state.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def get_offset_limit(page: int, page_size: int) -> Tuple[int, int]:
    """Calculate offset and limit for pagination."""
    if page_size is None or page_size <= 0:
        return 0, 0
    page = 1 if page is None or page <= 0 else page
    return (page - 1) * page_size, page_size

def get_transaction_count(db_path: str, start_date_str: Optional[str] = None, 
                         end_date_str: Optional[str] = None, 
                         account_id: Optional[int] = None) -> Tuple[Optional[str], int]:
    """Get the total count of transactions matching the given criteria.

    Args:
        db_path: Path to the MMEX database file.
        start_date_str: Start date string in YYYY-MM-DD format (optional).
        end_date_str: End date string in YYYY-MM-DD format (optional).
        account_id: Account ID to filter transactions (optional).

    Returns:
        Tuple containing:
            - error_message (str or None): Error message if any, None if successful
            - total_count (int): Total number of transactions matching criteria
    """
    if not db_path:
        logger.error("Invalid database path provided")
        return "Invalid database path", 0

    try:
        from mmex_reader.error_handling import handle_database_query, is_valid_date_format, validate_date_range
        from mmex_reader.db_utils import (
            TRANSACTION_TABLE,
            _connection_pool,
            _ensure_pool_for_path,
        )
    except Exception:
        from error_handling import handle_database_query, is_valid_date_format, validate_date_range
        from db_utils import (
            TRANSACTION_TABLE,
            _connection_pool,
            _ensure_pool_for_path,
        )

    # Ensure connection pool is initialized for the provided path
    init_error = None
    try:
        init_error, _ = _ensure_pool_for_path(db_path)
    except Exception as e:
        logger.error(f"Unexpected error ensuring pool for path: {e}")
        return f"Unexpected error ensuring pool for path: {e}", 0

    if init_error:
        logger.error(f"Database initialization error: {init_error}")
        return init_error, 0

    # Validate date formats and range before executing query
    try:
        if start_date_str:
            if not is_valid_date_format(start_date_str, "start_date"):
                logger.error(f"Invalid start_date format: {start_date_str}")
                return f"Invalid start_date format: {start_date_str}. Expected format: YYYY-MM-DD", 0

        if end_date_str:
            if not is_valid_date_format(end_date_str, "end_date"):
                logger.error(f"Invalid end_date format: {end_date_str}")
                return f"Invalid end_date format: {end_date_str}. Expected format: YYYY-MM-DD", 0

        if start_date_str and end_date_str:
            range_error = validate_date_range(start_date_str, end_date_str)
            if range_error:
                logger.error(f"Invalid date range: {start_date_str} to {end_date_str}")
                return f"Invalid date range: start date {start_date_str} must be before or equal to end date {end_date_str}", 0
    except Exception as e:
        logger.error(f"Unexpected error validating dates: {e}")
        return f"Unexpected error validating dates: {e}", 0

    conn = None
    try:
        conn = _connection_pool.get_connection()
        if not conn:
            logger.error("Could not get a database connection from the pool")
            return "Could not get a database connection from the pool", 0

        query = f"""
        SELECT COUNT(*) as total_count
        FROM {TRANSACTION_TABLE} t
        WHERE t.DELETEDTIME = ''
        """

        params = []
        if account_id is not None:
            query += " AND t.ACCOUNTID = ?"
            params.append(account_id)
        if start_date_str:
            query += " AND t.TRANSDATE >= ?"
            params.append(start_date_str)
        if end_date_str:
            query += " AND t.TRANSDATE <= ?"
            params.append(end_date_str)

        error, rows = handle_database_query(conn, query, params, return_dataframe=False)
        total_count = rows[0][0] if rows else 0
        if error:
            logger.error(f"Error getting transaction count: {error}")
            return error, 0

        logger.info(f"Total transaction count: {total_count}")
        return None, total_count

    except Exception as e:
        logger.error(f"Unexpected error getting transaction count: {e}")
        return f"Unexpected error: {e}", 0
    finally:
        # Release the connection back to the pool
        if conn:
            _connection_pool.release_connection(conn)


class PaginationInfo:
    """Class to hold pagination information and calculations."""
    
    def __init__(self, total_count: int, page_size: int, current_page: int = 1):
        """Initialize pagination info.
        
        Args:
            total_count: Total number of items
            page_size: Number of items per page
            current_page: Current page number (1-based)
        """
        self.total_count = total_count
        self.page_size = page_size
        self.current_page = max(1, current_page)
        
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.page_size <= 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.current_page > 1
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.current_page < self.total_pages
    
    @property
    def start_index(self) -> int:
        """Get the starting index for current page (1-based)."""
        # No records or invalid page size yields no range
        if self.total_count == 0 or self.page_size <= 0:
            return 0
        # Clamp current page within valid bounds to avoid invalid ranges
        page = min(max(1, self.current_page), self.total_pages)
        return (page - 1) * self.page_size + 1
    
    @property
    def end_index(self) -> int:
        """Get the ending index for current page (1-based)."""
        # No records or invalid page size yields no range
        if self.total_count == 0 or self.page_size <= 0:
            return 0
        # Clamp current page within valid bounds
        page = min(max(1, self.current_page), self.total_pages)
        end = page * self.page_size
        return min(end, self.total_count)
    
    def get_page_info_text(self) -> str:
        """Get formatted pagination info text."""
        if self.total_count == 0:
            return "No records found"
        return f"Showing {self.start_index}-{self.end_index} of {self.total_count} transactions (Page {self.current_page} of {self.total_pages})"
