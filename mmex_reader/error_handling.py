"""Common error handling utilities for the MMEX application.

This module provides centralized error handling functions to reduce code duplication
across the application.
"""

import sqlite3
import pandas as pd
from typing import Tuple, Any, Optional


def handle_database_operation(operation_func, *args, **kwargs) -> Tuple[Optional[str], Any]:
    """Generic database operation handler with consistent error handling.
    
    Args:
        operation_func: The database operation function to execute
        *args: Arguments to pass to the operation function
        **kwargs: Keyword arguments to pass to the operation function
        
    Returns:
        tuple: (error_message, result)
            - error_message (str or None): Error message if any, None if successful
            - result (Any): Result of the operation, or default value on error
    """
    try:
        return None, operation_func(*args, **kwargs)
    except sqlite3.Error as e:
        return f"Database error: {e}", None
    except pd.io.sql.DatabaseError as e:
        return f"Database error: {e}", None
    except Exception as e:
        return f"Unexpected error: {e}", None


def handle_database_query(conn, query: str, params: list = None, return_dataframe: bool = True) -> Tuple[Optional[str], Any]:
    """Execute a database query with consistent error handling.
    
    Args:
        conn: Database connection
        query: SQL query string
        params: Query parameters (optional)
        return_dataframe: Whether to return a DataFrame (True) or raw result (False)
        
    Returns:
        tuple: (error_message, result)
            - error_message (str or None): Error message if any, None if successful
            - result (DataFrame or list): Query result
    """
    try:
        if return_dataframe:
            result = pd.read_sql_query(query, conn, params=params or [])
        else:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            result = cursor.fetchall()
        return None, result
    except sqlite3.Error as e:
        return f"Database error: {e}", pd.DataFrame() if return_dataframe else []
    except pd.io.sql.DatabaseError as e:
        return f"Database error: {e}", pd.DataFrame() if return_dataframe else []
    except Exception as e:
        return f"Unexpected error: {e}", pd.DataFrame() if return_dataframe else []


def validate_date_format(date_str: str, date_name: str = "date") -> Tuple[Optional[str], Optional[str]]:
    """Validate date string format.
    
    Args:
        date_str: Date string to validate
        date_name: Name of the date field for error messages
        
    Returns:
        tuple: (error_message, validated_date_str)
            - error_message (str or None): Error message if invalid, None if valid
            - validated_date_str (str or None): Validated date string
    """
    if not date_str:
        return None, None
        
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return None, date_str
    except ValueError:
        return f"Invalid {date_name} format: {date_str}. Expected YYYY-MM-DD", None


def validate_date_range(start_date_str: str, end_date_str: str) -> Optional[str]:
    """Validate date range.
    
    Args:
        start_date_str: Start date string
        end_date_str: End date string
        
    Returns:
        str or None: Error message if invalid, None if valid
    """
    if not start_date_str or not end_date_str:
        return None
        
    try:
        from datetime import datetime
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        if start_date > end_date:
            return "Start date cannot be after end date"
        return None
    except ValueError as e:
        return f"Date validation error: {e}"