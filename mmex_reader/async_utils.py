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
    """Handles asynchronous database operations with UI callbacks."""
    
    def __init__(self):
        self.is_running = False
        self.current_thread = None
    
    def execute_async(self, 
                     operation: Callable,
                     on_success: Optional[Callable] = None,
                     on_error: Optional[Callable] = None,
                     on_start: Optional[Callable] = None,
                     on_complete: Optional[Callable] = None,
                     *args, **kwargs):
        """Execute a database operation asynchronously.
        
        Args:
            operation: The database operation function to execute
            on_success: Callback for successful operation (called with result)
            on_error: Callback for error handling (called with error message)
            on_start: Callback called when operation starts
            on_complete: Callback called when operation completes (success or error)
            *args, **kwargs: Arguments to pass to the operation function
        """
        if self.is_running:
            logger.warning("Another async operation is already running")
            return
        
        self.is_running = True
        
        # Call start callback on main thread
        if on_start:
            Clock.schedule_once(lambda dt: on_start(), 0)
        
        def worker():
            """Worker function that runs in background thread."""
            try:
                logger.debug(f"Starting async operation: {operation.__name__}")
                result = operation(*args, **kwargs)
                
                # Schedule success callback on main thread
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(result), 0)
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Async operation failed: {error_msg}")
                
                # Schedule error callback on main thread
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(error_msg), 0)
                    
            finally:
                # Mark operation as complete
                self.is_running = False
                
                # Schedule complete callback on main thread
                if on_complete:
                    Clock.schedule_once(lambda dt: on_complete(), 0)
        
        # Start the worker thread
        self.current_thread = threading.Thread(target=worker, daemon=True)
        self.current_thread.start()
    
    def cancel(self):
        """Cancel the current operation if possible."""
        if self.is_running and self.current_thread:
            logger.info("Attempting to cancel async operation")
            # Note: Python threads cannot be forcefully cancelled
            # This just marks the operation as not running
            self.is_running = False


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
    """Manages loading indicators for async operations."""
    
    def __init__(self, widget, loading_text="Loading..."):
        self.widget = widget
        self.loading_text = loading_text
        self.original_text = None
        self.is_loading = False
    
    def show(self):
        """Show loading indicator."""
        if not self.is_loading:
            if hasattr(self.widget, 'text'):
                self.original_text = self.widget.text
                self.widget.text = self.loading_text
            elif hasattr(self.widget, 'disabled'):
                self.widget.disabled = True
            self.is_loading = True
            logger.debug("Loading indicator shown")
    
    def hide(self):
        """Hide loading indicator."""
        if self.is_loading:
            if hasattr(self.widget, 'text') and self.original_text is not None:
                self.widget.text = self.original_text
            elif hasattr(self.widget, 'disabled'):
                self.widget.disabled = False
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
        async_op = AsyncDatabaseOperation()
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