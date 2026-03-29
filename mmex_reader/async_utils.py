"""Asynchronous utilities for the MMEX Kivy application - Final Refactor.

This module now serves as a clean interface to the asynchronous system,
with concerns separated into pool, operation, and manager modules.
"""

# Re-export from specialized modules for backward compatibility
from mmex_reader.async_pool import async_pool, shutdown_async_pool
from mmex_reader.async_operation import AsyncDatabaseOperation, async_database_operation
from mmex_reader.async_manager import LoadingIndicator, AsyncQueryManager

# Global instance for the application
async_query_manager = AsyncQueryManager()
