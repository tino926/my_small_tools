"""Database query functions for the MMEX application - Step 1: QueryCache Core.

This file contains the QueryCache class for caching database query results.
"""

import logging
import hashlib
import time
import threading
from typing import Dict, Optional, Any
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Cache configuration
DEFAULT_CACHE_TTL_SECONDS = 300  # 5 minutes
DEFAULT_MAX_CACHE_SIZE = 100


class QueryCache:
    """Thread-safe LRU cache for database query results with TTL support."""

    def __init__(self, max_size: int = DEFAULT_MAX_CACHE_SIZE,
                 default_ttl: int = DEFAULT_CACHE_TTL_SECONDS):
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._lock = threading.Lock()

    def _get_key(self, query: str, params: Optional[tuple] = None) -> str:
        key_data = f"{query}:{params}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()

    def get(self, query: str, params: Optional[tuple] = None) -> Optional[Any]:
        key = self._get_key(query, params)
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            entry = self._cache[key]
            if time.time() > entry['expires_at']:
                del self._cache[key]
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return entry['result']

    def set(self, query: str, result: Any, params: Optional[tuple] = None,
            ttl: Optional[int] = None) -> None:
        key = self._get_key(query, params)
        ttl = ttl if ttl is not None else self._default_ttl
        with self._lock:
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
                self._evictions += 1
            self._cache[key] = {
                'result': result,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate_percent': round(hit_rate, 2),
                'default_ttl_seconds': self._default_ttl
            }


# Global cache instance
_query_cache = QueryCache()
