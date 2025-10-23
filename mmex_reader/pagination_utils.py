"""Pagination utilities for the MMEX Kivy application.

This module provides functions for handling pagination of transaction data,
including counting total records and managing pagination state.
"""

import logging
from typing import Optional, Tuple
import pandas as pd

from error_handling import handle_database_query, validate_date_format, validate_date_range
from db_utils import (
    TRANSACTION_TABLE, ACCOUNT_TABLE, CATEGORY_TABLE, 
    SUBCATEGORY_TABLE, PAYEE_TABLE, _connection_pool
)

logger = logging.getLogger(__name__)


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

    # Validate date formats and range before executing query
    try:
        if start_date_str:
            if not validate_date_format(start_date_str, "start_date"):
                logger.error(f"Invalid start_date format: {start_date_str}")
                return f"Invalid start_date format: {start_date_str}. Expected format: YYYY-MM-DD", 0

        if end_date_str:
            if not validate_date_format(end_date_str, "end_date"):
                logger.error(f"Invalid end_date format: {end_date_str}")
                return f"Invalid end_date format: {end_date_str}. Expected format: YYYY-MM-DD", 0

        if start_date_str and end_date_str:
            if not validate_date_range(start_date_str, end_date_str):
                logger.error(f"Invalid date range: {start_date_str} to {end_date_str}")
                return f"Invalid date range: start date {start_date_str} must be before or equal to end date {end_date_str}", 0
    except Exception as e:
        logger.error(f"Unexpected error validating dates: {e}")
        return f"Unexpected error validating dates: {e}", 0

    conn = None
    try:
        # Get a connection from the pool
        conn = _connection_pool.get_connection()
        if not conn:
            logger.error("Could not get a database connection from the pool")
            return "Could not get a database connection from the pool", 0
            
        # Build count query with same filters as main query
        query = f"""
        SELECT COUNT(*) as total_count
        FROM {TRANSACTION_TABLE} t
        LEFT JOIN {ACCOUNT_TABLE} a ON t.ACCOUNTID = a.ACCOUNTID
        LEFT JOIN {CATEGORY_TABLE} c ON t.CATEGID = c.CATEGID
        LEFT JOIN {SUBCATEGORY_TABLE} s ON t.SUBCATEGID = s.SUBCATEGID
        LEFT JOIN {PAYEE_TABLE} p ON t.PAYEEID = p.PAYEEID
        WHERE t.DELETEDTIME = ''
        """

        # Add filters with proper parameter binding
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

        # Execute count query using standardized query handler
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
        if self.total_count == 0:
            return 0
        return (self.current_page - 1) * self.page_size + 1
    
    @property
    def end_index(self) -> int:
        """Get the ending index for current page (1-based)."""
        if self.total_count == 0:
            return 0
        end = self.current_page * self.page_size
        return min(end, self.total_count)
    
    def get_page_info_text(self) -> str:
        """Get formatted pagination info text."""
        if self.total_count == 0:
            return "No records found"
        return f"Showing {self.start_index}-{self.end_index} of {self.total_count} transactions (Page {self.current_page} of {self.total_pages})"