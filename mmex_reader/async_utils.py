"""Asynchronous utilities for the MMEX Kivy application - Step 2 Refactor.

This step extracts AsyncDatabaseOperation and async_database_operation to async_operation.py.
"""

import logging
from typing import Callable, Any, Optional

# Import from new modules
from mmex_reader.async_pool import async_pool, shutdown_async_pool
from mmex_reader.async_operation import AsyncDatabaseOperation, async_database_operation

logger = logging.getLogger(__name__)


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
