"""
Caching utilities for coffee brewing services
"""

import functools
import hashlib
import pickle
from typing import Any, Callable, Dict, Optional
import pandas as pd


class ServiceCache:
    """Simple in-memory cache for service results"""
    
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, Any] = {}
        self._max_size = max_size
        self._access_order: list = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with LRU eviction"""
        if key in self._cache:
            # Update existing
            self._cache[key] = value
            self._access_order.remove(key)
            self._access_order.append(key)
        else:
            # Add new
            if len(self._cache) >= self._max_size:
                # Evict least recently used
                lru_key = self._access_order.pop(0)
                del self._cache[lru_key]
            
            self._cache[key] = value
            self._access_order.append(key)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self._access_order.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)


# Global cache instance
_service_cache = ServiceCache()


def cache_dataframe_result(expire_minutes: int = 5):
    """
    Decorator to cache DataFrame-based function results
    
    Args:
        expire_minutes: Cache expiration time in minutes
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and DataFrame hash
            df_hash = ""
            for arg in args:
                if isinstance(arg, pd.DataFrame) and not arg.empty:
                    # Hash DataFrame contents
                    df_hash += hashlib.md5(
                        pickle.dumps(arg.values.tobytes())
                    ).hexdigest()[:8]
            
            cache_key = f"{func.__name__}_{df_hash}_{hash(str(kwargs))}"
            
            # Try to get from cache
            cached_result = _service_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Calculate and cache result
            result = func(*args, **kwargs)
            _service_cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


def clear_service_cache():
    """Clear the global service cache"""
    _service_cache.clear()