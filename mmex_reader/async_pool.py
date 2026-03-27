"""Global thread pool for managing async operations efficiently."""

import logging
import atexit
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class GlobalAsyncPool:
    """Global thread pool to manage async operations efficiently."""

    def __init__(self, max_workers: int = 4):
        """Initialize the global thread pool.

        Args:
            max_workers: Maximum number of worker threads in the pool
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, fn, *args, **kwargs):
        """Submit a function to the thread pool."""
        return self.executor.submit(fn, *args, **kwargs)

    def shutdown(self, wait=True):
        """Shutdown the thread pool."""
        self.executor.shutdown(wait=wait)

# Global instance of the async pool
async_pool = GlobalAsyncPool()

def shutdown_async_pool():
    """Shutdown the global async pool when the application exits."""
    logger.info("Shutting down async pool...")
    async_pool.shutdown(wait=True)
    logger.info("Async pool shutdown complete.")

# Register shutdown function to be called when module is unloaded
atexit.register(shutdown_async_pool)
