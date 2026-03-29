"""Management classes for high-level asynchronous queries and UI feedback."""

import logging
from typing import Callable, Any, Optional

from mmex_reader.async_operation import AsyncDatabaseOperation

logger = logging.getLogger(__name__)

class LoadingIndicator:
    """Manages loading indicators for async operations."""

    def __init__(self, widget: Optional[Any] = None, loading_text: str = "Loading..."):
        self.widget = widget
        self.loading_text = loading_text
        self.original_text = None
        self.is_loading = False

    def show(self, widget: Optional[Any] = None, loading_text: Optional[str] = None):
        if not self.is_loading:
            if widget is not None:
                self.widget = widget
            if loading_text is not None:
                self.loading_text = loading_text
            if self.widget is None:
                return
            if hasattr(self.widget, 'text'):
                self.original_text = getattr(self.widget, 'text', None)
                try:
                    self.widget.text = self.loading_text
                except Exception:
                    pass
            elif hasattr(self.widget, 'disabled'):
                try:
                    self.widget.disabled = True
                except Exception:
                    pass
            self.is_loading = True

    def hide(self):
        if self.is_loading:
            if self.widget is not None:
                if hasattr(self.widget, 'text') and self.original_text is not None:
                    try:
                        self.widget.text = self.original_text
                    except Exception:
                        pass
                elif hasattr(self.widget, 'disabled'):
                    try:
                        self.widget.disabled = False
                    except Exception:
                        pass
            self.is_loading = False
            self.original_text = None


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
        if query_id in self.active_operations:
            self.active_operations[query_id].cancel()
        
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
            if query_id in self.active_operations:
                del self.active_operations[query_id]
            if query_id in self.loading_indicators:
                del self.loading_indicators[query_id]

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
        for operation in self.active_operations.values():
            operation.cancel()
        for indicator in self.loading_indicators.values():
            indicator.hide()
        self.active_operations.clear()
        self.loading_indicators.clear()
