"""Asynchronous utilities for the MMEX Kivy application.

This module provides threading utilities for performing database operations
asynchronously to prevent UI freezing during long-running queries.
"""

import threading
import logging
from typing import Callable, Any, Optional
from functools import wraps
from kivy.clock import Clock

logger = logging.getLogger(__name__)


class AsyncDatabaseOperation:
    """Handles asynchronous database operations with UI callbacks.

    Usage:
        - Direct: `AsyncDatabaseOperation().execute_async(func, on_success=..., ...)`
        - Builder: `AsyncDatabaseOperation(target_func=..., args=(...), success_callback=..., error_callback=...).start()`

    Attributes:
        is_running: Whether an operation is currently running
        current_thread: Background thread executing the operation
        _completed: Whether the current operation finished (success or error)
        _timeout: Optional timeout in seconds for the operation
        _timeout_timer: Internal timer used to implement timeout
    """

    def __init__(
        self,
        target_func: Optional[Callable] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        success_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        start_callback: Optional[Callable] = None,
        complete_callback: Optional[Callable] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.is_running = False
        self.current_thread = None
        self._completed = False
        self._timeout = timeout
        self._timeout_timer = None
        # Stored configuration for builder-style usage
        self._target_func = target_func
        self._args = args or ()
        self._kwargs = kwargs or {}
        self._success_cb = success_callback
        self._error_cb = error_callback
        self._start_cb = start_callback
        self._complete_cb = complete_callback

    def _schedule_cb(self, cb: Optional[Callable], *cb_args, **cb_kwargs) -> None:
        if not cb:
            return

        def _wrapper(dt):
            try:
                cb(*cb_args, **cb_kwargs)
            except Exception as e:
                logger.exception(f"Error in scheduled callback {getattr(cb, '__name__', cb)}: {e}")

        Clock.schedule_once(_wrapper, 0)

    def execute_async(
        self,
        operation: Callable,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_start: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        *args,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> "AsyncDatabaseOperation":
        """Execute a database operation asynchronously.

        Args:
            operation: The database operation function to execute
            on_success: Callback for successful operation (called with result)
            on_error: Callback for error handling (called with error message)
            on_start: Callback called when operation starts
            on_complete: Callback called when operation completes (success or error)
            timeout: Seconds before operation is considered timed out (best-effort)
            *args, **kwargs: Arguments to pass to the operation function
        """
        if self.is_running:
            op_name = getattr(self.current_thread, "name", "Unknown Operation")
            logger.warning(f"Another async operation '{op_name}' is already running")
            return self

        self.is_running = True
        self._completed = False

        # Call start callback on main thread
        self._schedule_cb(on_start)

        def _on_timeout():
            if self.is_running and not self._completed:
                logger.warning("Async operation timed out")
                self.is_running = False
                # Notify error and completion on main thread
                self._schedule_cb(on_error, "Operation timed out")
                self._schedule_cb(on_complete)

        # Setup timeout timer if provided
        op_timeout = timeout if timeout is not None else self._timeout
        if op_timeout and op_timeout > 0:
            try:
                self._timeout_timer = threading.Timer(op_timeout, _on_timeout)
                self._timeout_timer.daemon = True
                self._timeout_timer.start()
            except Exception as e:
                logger.exception(f"Failed to start timeout timer: {e}")

        def worker() -> None:
            """Worker function that runs in background thread."""
            try:
                op_name = getattr(operation, "__name__", str(operation))
                logger.debug(f"Starting async operation: {op_name}")
                result = operation(*args, **kwargs)

                # Schedule success callback on main thread only if still running
                if self.is_running and not self._completed:
                    self._schedule_cb(on_success, result)

            except Exception as e:
                error_msg = str(e)
                logger.exception(f"Async operation failed: {error_msg}")

                # Schedule error callback on main thread
                self._schedule_cb(on_error, error_msg)

            finally:
                # Mark operation as complete
                self.is_running = False
                self._completed = True

                # Cancel timeout timer if any
                try:
                    if self._timeout_timer:
                        self._timeout_timer.cancel()
                        self._timeout_timer = None
                except Exception as e:
                    logger.debug(f"Failed to cancel timeout timer: {e}")

                # Schedule complete callback on main thread
                self._schedule_cb(on_complete)

        # Start the worker thread
        op_name_for_thread = getattr(operation, "__name__", "AsyncOperation")
        self.current_thread = threading.Thread(target=worker, daemon=True, name=op_name_for_thread)
        self.current_thread.start()
        return self

    def start(self) -> Optional["AsyncDatabaseOperation"]:
        """Start the operation using stored builder-style configuration."""
        if not callable(self._target_func):
            logger.error("No target_func provided to AsyncDatabaseOperation.start()")
            return
        return self.execute_async(
            self._target_func,
            on_success=self._success_cb,
            on_error=self._error_cb,
            on_start=self._start_cb,
            on_complete=self._complete_cb,
            *self._args,
            timeout=self._timeout,
            **self._kwargs,
        )

    def cancel(self) -> None:
        """Cancel the current operation if possible."""
        if self.is_running and self.current_thread:
            logger.info("Attempting to cancel async operation")
            # Note: Python threads cannot be forcefully cancelled
            # This just marks the operation as not running
            self.is_running = False
            try:
                if self._timeout_timer:
                    self._timeout_timer.cancel()
                    self._timeout_timer = None
            except Exception as e:
                logger.debug(f"Failed to cancel timeout timer during cancel(): {e}")


def async_database_operation(on_success=None, on_error=None, on_start=None, on_complete=None):
    """Decorator for making database operations asynchronous.
    
    Args:
        on_success: Default success callback
        on_error: Default error callback
        on_start: Default start callback
        on_complete: Default complete callback
    
    Returns:
        Decorated function that executes asynchronously
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract callback overrides from kwargs
            success_cb = kwargs.pop('on_success', on_success)
            error_cb = kwargs.pop('on_error', on_error)
            start_cb = kwargs.pop('on_start', on_start)
            complete_cb = kwargs.pop('on_complete', on_complete)
            
            # Create async operation instance
            async_op = AsyncDatabaseOperation()
            
            # Execute asynchronously
            async_op.execute_async(
                func,
                on_success=success_cb,
                on_error=error_cb,
                on_start=start_cb,
                on_complete=complete_cb,
                *args, **kwargs
            )
            
            return async_op
        
        return wrapper
    return decorator


class LoadingIndicator:
    """Manages loading indicators for async operations.

    Supports both pre-bound widget and dynamic widget per show() call.
    """

    def __init__(self, widget: Optional[Any] = None, loading_text: str = "Loading..."):
        self.widget = widget
        self.loading_text = loading_text
        self.original_text = None
        self.is_loading = False

    def show(self, widget: Optional[Any] = None, loading_text: Optional[str] = None):
        """Show loading indicator.

        Args:
            widget: Optional widget to apply indicator to (overrides pre-bound)
            loading_text: Optional loading text to display
        """
        if not self.is_loading:
            # Allow dynamic binding per call
            if widget is not None:
                self.widget = widget
            if loading_text is not None:
                self.loading_text = loading_text

            if self.widget is None:
                logger.debug("LoadingIndicator.show() called without a widget")
                return

            if hasattr(self.widget, 'text'):
                self.original_text = getattr(self.widget, 'text', None)
                try:
                    self.widget.text = self.loading_text
                except Exception as e:
                    logger.debug(f"Could not set widget.text: {e}")
            elif hasattr(self.widget, 'disabled'):
                try:
                    self.widget.disabled = True
                except Exception as e:
                    logger.debug(f"Could not set widget.disabled: {e}")
            self.is_loading = True
            logger.debug("Loading indicator shown")

    def hide(self):
        """Hide loading indicator."""
        if self.is_loading:
            if self.widget is not None:
                if hasattr(self.widget, 'text') and self.original_text is not None:
                    try:
                        self.widget.text = self.original_text
                    except Exception as e:
                        logger.debug(f"Could not restore widget.text: {e}")
                elif hasattr(self.widget, 'disabled'):
                    try:
                        self.widget.disabled = False
                    except Exception as e:
                        logger.debug(f"Could not restore widget.disabled: {e}")
            self.is_loading = False
            self.original_text = None
            logger.debug("Loading indicator hidden")


class AsyncQueryManager:
    """Manages multiple async database queries with loading states."""
    
    def __init__(self):
        self.active_operations = {}
        self.loading_indicators = {}
    
    def execute_query(self, 
                     query_id: str,
                     operation: Callable,
                     loading_widget=None,
                     loading_text="Loading...",
                     on_success=None,
                     on_error=None,
                     *args, **kwargs):
        """Execute a database query with loading management.
        
        Args:
            query_id: Unique identifier for this query
            operation: Database operation to execute
            loading_widget: Widget to show loading indicator on
            loading_text: Text to display during loading
            on_success: Success callback
            on_error: Error callback
            *args, **kwargs: Arguments for the operation
        """
        # Cancel existing operation with same ID
        if query_id in self.active_operations:
            self.active_operations[query_id].cancel()
        
        # Setup loading indicator
        loading_indicator = None
        if loading_widget:
            loading_indicator = LoadingIndicator(loading_widget, loading_text)
            self.loading_indicators[query_id] = loading_indicator

        timeout = kwargs.pop('timeout', None)

        def on_start_wrapper():
            if loading_indicator:
                loading_indicator.show()
        
        def on_success_wrapper(result):
            if on_success:
                on_success(result)
        
        def on_error_wrapper(error):
            if on_error:
                on_error(error)
        
        def on_complete_wrapper():
            if loading_indicator:
                loading_indicator.hide()
            # Clean up
            if query_id in self.active_operations:
                del self.active_operations[query_id]
            if query_id in self.loading_indicators:
                del self.loading_indicators[query_id]

        # Create and start async operation
        async_op = AsyncDatabaseOperation(timeout=timeout)
        self.active_operations[query_id] = async_op
        
        async_op.execute_async(
            operation,
            on_success=on_success_wrapper,
            on_error=on_error_wrapper,
            on_start=on_start_wrapper,
            on_complete=on_complete_wrapper,
            *args, **kwargs
        )
        
        return async_op
    
    def cancel_all(self):
        """Cancel all active operations."""
        for operation in self.active_operations.values():
            operation.cancel()
        
        # Hide all loading indicators
        for indicator in self.loading_indicators.values():
            indicator.hide()
        
        self.active_operations.clear()
        self.loading_indicators.clear()
        
        logger.info("All async operations cancelled")


# Global instance for the application
async_query_manager = AsyncQueryManager()
