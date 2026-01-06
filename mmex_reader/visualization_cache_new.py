"""
Visualization cache for the MMEX Kivy application.

This module provides caching functionality for visualization charts to reduce redundant computations.
"""

import time
import logging
from typing import Dict, Any, Optional

# Configure logging for visualization module
logger = logging.getLogger(__name__)

# Configure caching for visualization
class VisualizationCache:
    """Simple cache for visualization charts to reduce redundant computations."""

    def __init__(self, max_size: int = 10, ttl_seconds: int = 300):
        """
        Initialize the visualization cache.

        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time-to-live for cached items in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get an item from the cache if it exists and hasn't expired."""
        if key in self._cache:
            cached = self._cache[key]
            current_time = time.time()

            if current_time - cached['timestamp'] < self.ttl_seconds:
                logger.debug(f"Cache hit for key: {key}")
                return cached['data']
            else:
                # Remove expired item
                del self._cache[key]
                logger.debug(f"Cache miss for key: {key} (expired)")

        logger.debug(f"Cache miss for key: {key}")
        return None

    def set(self, key: str, data: Any) -> None:
        """Set an item in the cache, evicting oldest if at max capacity."""
        current_time = time.time()

        # Remove oldest items if at max capacity
        while len(self._cache) >= self.max_size:
            # Find and remove the oldest item
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['timestamp'])
            del self._cache[oldest_key]
            logger.debug(f"Evicted oldest cache item: {oldest_key}")

        self._cache[key] = {
            'data': data,
            'timestamp': current_time
        }
        logger.debug(f"Added to cache: {key}")

    def clear(self) -> None:
        """Clear all items from the cache."""
        self._cache.clear()
        logger.debug("Cleared visualization cache")