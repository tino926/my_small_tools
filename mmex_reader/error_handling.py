"""Common error handling utilities for the MMEX application.

This module provides centralized error handling functions to reduce code duplication
across the application. It includes utilities for database operations, query execution,
and data validation.

Classes:
    None

Functions:
    handle_database_operation: Generic database operation handler with consistent error handling
    handle_database_query: Execute database queries with error handling and result formatting
    validate_date_format: Validate date string format against YYYY-MM-DD pattern
    validate_date_range: Validate that start date is not after end date

Constants:
    DATE_FORMAT: Standard date format pattern used throughout the application
    DEFAULT_ERROR_MESSAGES: Common error message templates
"""

# Standard library imports
import logging
import sqlite3
from datetime import datetime
from typing import Any, Callable, List, Optional, Tuple, Union

# Third-party imports
import pandas as pd

# Module exports
__all__ = [
    'handle_database_operation',
    'handle_database_query', 
    'validate_date_format',
    'validate_date_range',
    'is_valid_date_format',
    'is_valid_date_range',
    'validate_amount',
    'is_valid_amount',
    'DATE_FORMAT',
    'DEFAULT_ERROR_MESSAGES'
]

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# MODULE CONSTANTS
# =============================================================================

# Date format constants
DATE_FORMAT: str = "%Y-%m-%d"

# Debug message constants
DEBUG_MSG_OPERATION_SUCCESS = "Database operation completed successfully"
DEBUG_MSG_QUERY_SUCCESS_DF = "Query executed successfully, returned {count} rows as DataFrame"
DEBUG_MSG_QUERY_SUCCESS_LIST = "Query executed successfully, returned {count} rows as list"
DEBUG_MSG_DATE_VALIDATED = "Successfully validated {name}: {date}"
DEBUG_MSG_DATE_RANGE_VALID = "Valid date range: {start} to {end}"
DEBUG_MSG_EMPTY_DATE = "Empty date string provided for {name}"
DEBUG_MSG_SKIP_RANGE_VALIDATION = "One or both dates are empty, skipping range validation"

# Error message constants
ERROR_MSG_UNEXPECTED_RANGE_VALIDATION = "Unexpected error during date range validation"

# Error message templates
DEFAULT_ERROR_MESSAGES = {
    # Database operation errors
    'database_error': "Database error: {error}",
    'connection_error': "Database connection error: {error}",
    'execution_error': "Query execution error: {error}",
    
    # Validation errors
    'invalid_date_format': "Invalid {field} format: '{value}'. Expected YYYY-MM-DD",
    'invalid_date_string': "Invalid date string: '{date_str}'. Must be a non-empty string",
    'invalid_date_range': "Start date '{start}' must be before or equal to end date '{end}'",
    'validation_error': "Validation error: {error}",
    'invalid_amount_format': "Invalid {field} format: '{value}'",
    
    # Input validation errors
    'invalid_connection': "Invalid database connection provided",
    'invalid_query': "Invalid query provided: {query}",
    'invalid_parameters': "Invalid parameters provided: {params}",
    'invalid_operation': "Invalid operation: {operation}",
    
    # Generic errors
    'unexpected_error': "Unexpected error: {error}",
}

# =============================================================================
# ERROR HANDLING FUNCTIONS
# =============================================================================


def handle_database_operation(operation_func: Callable[..., Any], *args: Any, **kwargs: Any) -> Tuple[Optional[str], Any]:
    """Generic database operation handler with consistent error handling.
    
    This function provides a centralized way to handle database operations with
    consistent error handling and logging. It catches common database exceptions
    and returns standardized error messages.
    
    Args:
        operation_func (Callable[..., Any]): The database operation function to execute.
        *args (Any): Positional arguments to pass to the operation function.
        **kwargs (Any): Keyword arguments to pass to the operation function.
        
    Returns:
        Tuple containing:
            - error_message (str or None): Error message if any, None if successful
            - result (Any): Result of the operation, or None on error
            
    Raises:
        None: All exceptions are caught and returned as error messages.
        
    Example:
        >>> def query_func(conn, query):
        ...     return conn.execute(query).fetchall()
        >>> error, result = handle_database_operation(query_func, conn, "SELECT * FROM table")
    """
    if not callable(operation_func):
        error_msg = DEFAULT_ERROR_MESSAGES['invalid_operation'].format(operation="function is not callable")
        logger.error(error_msg)
        return error_msg, None
        
    try:
        result = operation_func(*args, **kwargs)
        logger.debug(DEBUG_MSG_OPERATION_SUCCESS)
        return None, result
    except sqlite3.Error as e:
        error_msg = DEFAULT_ERROR_MESSAGES['database_error'].format(error=e)
        logger.error(f"SQLite error in database operation: {e}")
        return error_msg, None
    except pd.io.sql.DatabaseError as e:
        error_msg = DEFAULT_ERROR_MESSAGES['database_error'].format(error=e)
        logger.error(f"Pandas database error in operation: {e}")
        return error_msg, None
    except Exception as e:
        error_msg = DEFAULT_ERROR_MESSAGES['unexpected_error'].format(error=e)
        logger.error(f"Unexpected error in database operation: {e}")
        return error_msg, None


def handle_database_query(conn: sqlite3.Connection, query: str, params: Optional[List[Any]] = None,
                         return_dataframe: bool = True) -> Tuple[Optional[str], Union[pd.DataFrame, List[Any]]]:
    """Execute a database query with consistent error handling and result formatting.

    This function provides a standardized way to execute SQL queries with proper
    error handling, parameter binding, and result formatting. It supports both
    DataFrame and raw result returns.

    Args:
        conn (sqlite3.Connection): Database connection object.
        query (str): SQL query string to execute.
        params (Optional[List[Any]]): List of query parameters for parameter binding.
        return_dataframe (bool): Whether to return a pandas DataFrame (True) or raw result (False).

    Returns:
        Tuple containing:
            - error_message (str or None): Error message if any, None if successful
            - result (DataFrame or List): Query result as DataFrame or list based on return_dataframe

    Raises:
        None: All exceptions are caught and returned as error messages.

    Example:
        >>> error, df = handle_database_query(conn, "SELECT * FROM accounts WHERE id = ?", [1])
        >>> error, rows = handle_database_query(conn, "SELECT COUNT(*) FROM accounts",
        ...                                    return_dataframe=False)
    """
    # Input validation
    if not conn:
        error_msg = DEFAULT_ERROR_MESSAGES['invalid_connection']
        logger.error(error_msg)
        return error_msg, pd.DataFrame() if return_dataframe else []

    if not query or not isinstance(query, str):
        error_msg = DEFAULT_ERROR_MESSAGES['invalid_query'].format(query=query)
        logger.error(error_msg)
        return error_msg, pd.DataFrame() if return_dataframe else []

    if params is not None and not isinstance(params, (list, tuple)):
        error_msg = DEFAULT_ERROR_MESSAGES['invalid_parameters'].format(params=type(params).__name__)
        logger.error(error_msg)
        return error_msg, pd.DataFrame() if return_dataframe else []

    # Track query execution time for performance monitoring
    import time
    start_time = time.time()

    try:
        if return_dataframe:
            result = pd.read_sql_query(query, conn, params=params or [])
            execution_time = time.time() - start_time
            logger.debug(DEBUG_MSG_QUERY_SUCCESS_DF.format(count=len(result)))
            if execution_time > 1.0:  # Log slow queries (taking more than 1 second)
                logger.warning(f"Slow query detected (execution time: {execution_time:.2f}s): {query[:100]}...")
            return None, result
        else:
            cursor = None
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or [])
                result = cursor.fetchall()
                execution_time = time.time() - start_time
                logger.debug(DEBUG_MSG_QUERY_SUCCESS_LIST.format(count=len(result)))
                if execution_time > 1.0:  # Log slow queries (taking more than 1 second)
                    logger.warning(f"Slow query detected (execution time: {execution_time:.2f}s): {query[:100]}...")
                return None, result
            finally:
                # Ensure cursor is closed to avoid resource leaks
                try:
                    if cursor is not None:
                        cursor.close()
                except Exception as close_err:
                    # Non-critical: log at debug level and continue
                    logger.debug(f"Non-critical error closing cursor: {close_err}")
    except sqlite3.Error as e:
        execution_time = time.time() - start_time
        error_msg = DEFAULT_ERROR_MESSAGES['database_error'].format(error=e)
        logger.error(f"SQLite error executing query (execution time: {execution_time:.2f}s): {e}")
        return error_msg, pd.DataFrame() if return_dataframe else []
    except pd.io.sql.DatabaseError as e:
        execution_time = time.time() - start_time
        error_msg = DEFAULT_ERROR_MESSAGES['database_error'].format(error=e)
        logger.error(f"Pandas database error executing query (execution time: {execution_time:.2f}s): {e}")
        return error_msg, pd.DataFrame() if return_dataframe else []
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = DEFAULT_ERROR_MESSAGES['unexpected_error'].format(error=e)
        logger.error(f"Unexpected error executing query (execution_time: {execution_time:.2f}s): {e}")
        return error_msg, pd.DataFrame() if return_dataframe else []


def validate_date_format(date_str: str, date_name: str = "date") -> Tuple[Optional[str], Optional[datetime]]:
    """Validate date string format against the standard YYYY-MM-DD pattern.
    
    This function validates that a date string conforms to the expected format
    and can be parsed as a valid date. It provides detailed error messages
    for debugging purposes.
    
    Args:
        date_str (str): Date string to validate (expected format: YYYY-MM-DD).
        date_name (str): Name of the date field for error messages (default: "date").
        
    Returns:
        Tuple containing:
            - error_message (str or None): Error message if invalid, None if valid
            - validated_date (datetime or None): Parsed datetime object if valid, None otherwise
            
    Raises:
        None: All exceptions are caught and returned as error messages.
        
    Example:
        >>> error, date_obj = validate_date_format("2023-12-25", "start_date")
        >>> if not error:
        ...     print(f"Valid date: {date_obj}")
    """
    # Input validation
    if not date_str:
        logger.debug(DEBUG_MSG_EMPTY_DATE.format(name=date_name))
        return None, None
        
    if not isinstance(date_str, str):
        error_msg = DEFAULT_ERROR_MESSAGES['invalid_date_string'].format(date_str=date_str)
        logger.error(error_msg)
        return error_msg, None
        
    if not isinstance(date_name, str):
        error_msg = DEFAULT_ERROR_MESSAGES['invalid_parameters'].format(params='date_name')
        logger.error(error_msg)
        return error_msg, None
        
    try:
        parsed_date = datetime.strptime(date_str, DATE_FORMAT)
        logger.debug(DEBUG_MSG_DATE_VALIDATED.format(name=date_name, date=date_str))
        return None, parsed_date
    except ValueError as e:
        error_msg = DEFAULT_ERROR_MESSAGES['invalid_date_format'].format(
            field=date_name, value=date_str
        )
        logger.error(f"Date format validation failed for {date_name} '{date_str}': {e}")
        return error_msg, None
    except Exception as e:
        error_msg = DEFAULT_ERROR_MESSAGES['unexpected_error'].format(error=e)
        logger.error(f"Unexpected error validating date format: {e}")
        return error_msg, None


def validate_date_range(start_date_str: str, end_date_str: str) -> Optional[str]:
    """Validate that start_date is before or equal to end_date.
    
    This function validates a date range by ensuring the start date comes
    before or is equal to the end date. Both dates must be in valid format
    before range validation is performed.
    
    Args:
        start_date_str (str): Start date string in YYYY-MM-DD format.
        end_date_str (str): End date string in YYYY-MM-DD format.
        
    Returns:
        Optional[str]: Error message if validation fails, None if valid.
        
    Raises:
        None: All exceptions are caught and returned as error messages.
        
    Example:
        >>> error = validate_date_range("2023-01-01", "2023-12-31")
        >>> if not error:
        ...     print("Valid date range")
    """
    # Input validation
    if not start_date_str or not end_date_str:
        logger.debug(DEBUG_MSG_SKIP_RANGE_VALIDATION)
        return None
        
    # Validate individual date formats first
    start_error, start_datetime = validate_date_format(start_date_str, "start_date")
    if start_error:
        return start_error
        
    end_error, end_datetime = validate_date_format(end_date_str, "end_date")
    if end_error:
        return end_error
        
    # Compare dates
    if start_datetime and end_datetime:
        if start_datetime > end_datetime:
            error_msg = DEFAULT_ERROR_MESSAGES['invalid_date_range'].format(
                start=start_date_str, end=end_date_str
            )
            logger.error(f"Date range validation failed: {error_msg}")
            return error_msg
            
        logger.debug(DEBUG_MSG_DATE_RANGE_VALID.format(start=start_date_str, end=end_date_str))
        return None
        
    # This should not happen if validate_date_format works correctly
    error_msg = ERROR_MSG_UNEXPECTED_RANGE_VALIDATION
    logger.error(error_msg)
    return error_msg


def is_valid_date_format(date_str: str, date_name: str = "date") -> bool:
    """Return True/False for date format validity (YYYY-MM-DD).

    Convenience wrapper around validate_date_format for callers expecting
    boolean semantics. Logs internally and never raises.

    Args:
        date_str: Date string to validate.
        date_name: Field name for logging context.

    Returns:
        bool: True if date_str is valid or empty (treated as valid), False otherwise.
    """
    try:
        error, _ = validate_date_format(date_str, date_name)
        return error is None
    except Exception as e:
        logger.error(DEFAULT_ERROR_MESSAGES['unexpected_error'].format(error=e))
        return False


def is_valid_date_range(start_date_str: str, end_date_str: str) -> bool:
    """Return True/False for date range validity (start <= end).

    Convenience wrapper around validate_date_range for callers expecting
    boolean semantics. Logs internally and never raises.

    Args:
        start_date_str: Start date string.
        end_date_str: End date string.

    Returns:
        bool: True if range is valid or one/both dates empty (treated as valid), False otherwise.
    """
    try:
        error = validate_date_range(start_date_str, end_date_str)
        return error is None
    except Exception as e:
        logger.error(DEFAULT_ERROR_MESSAGES['unexpected_error'].format(error=e))
        return False


def validate_amount(amount: Any, field_name: str = "amount") -> Tuple[Optional[str], Optional[float]]:
    """Validate and parse amount value into float.

    Accepts numeric types and strings with optional currency symbols or separators,
    e.g., "$1,234.56" or "-987.00". Returns a standardized error message on failure.

    Args:
        amount: Input amount value (str or number)
        field_name: Field name for error message context

    Returns:
        Tuple[Optional[str], Optional[float]]: (error_message, parsed_float)
    """
    try:
        if amount is None:
            return DEFAULT_ERROR_MESSAGES['invalid_amount_format'].format(field=field_name, value=amount), None

        if isinstance(amount, (int, float)):
            return None, float(amount)

        if isinstance(amount, str):
            s = amount.strip()
            if not s:
                return DEFAULT_ERROR_MESSAGES['invalid_amount_format'].format(field=field_name, value=amount), None
            s = s.replace('$', '').replace(',', '')
            # Allow leading plus/minus and decimal
            try:
                return None, float(s)
            except ValueError:
                return DEFAULT_ERROR_MESSAGES['invalid_amount_format'].format(field=field_name, value=amount), None

        return DEFAULT_ERROR_MESSAGES['invalid_amount_format'].format(field=field_name, value=amount), None
    except Exception as e:
        err = DEFAULT_ERROR_MESSAGES['unexpected_error'].format(error=e)
        logger.error(err)
        return err, None


def is_valid_amount(amount: Any) -> bool:
    """Boolean wrapper for amount validation."""
    try:
        error, parsed = validate_amount(amount)
        return error is None and parsed is not None
    except Exception as e:
        logger.error(DEFAULT_ERROR_MESSAGES['unexpected_error'].format(error=e))
        return False
