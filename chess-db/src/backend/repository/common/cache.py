# repository/common/cache.py
from typing import TypeVar, Generic, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

T = TypeVar('T')

class CacheManager(Generic[T]):
    """
    Generic cache manager with TTL support.
    
    Provides in-memory caching with automatic expiration and
    cleanup for repository query results.
    """
    
    def __init__(self, ttl_minutes: int = 15):
        """
        Initialize cache manager.
        
        Args:
            ttl_minutes: Cache TTL in minutes
        """
        if ttl_minutes <= 0:
            raise ValueError("TTL must be positive")
        
        self._cache: Dict[str, tuple[datetime, T]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self.logger = logging.getLogger(f"{__name__}.CacheManager")

    def get(self, key: str) -> Optional[T]:
        """
        Retrieve item from cache if not expired.
        
        Args:
            key: Cache key to lookup
            
        Returns:
            Cached value if present and not expired, None otherwise
        """
        if key not in self._cache:
            return None
            
        timestamp, value = self._cache[key]
        if datetime.now() - timestamp > self._ttl:
            del self._cache[key]
            return None
            
        self.logger.debug(f"Cache hit: {key}")
        return value

    def set(self, key: str, value: T) -> None:
        """
        Store item in cache with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (datetime.now(), value)
        self.logger.debug(f"Cache set: {key}")

    def invalidate(self, key: str) -> None:
        """
        Remove item from cache.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            self.logger.debug(f"Cache invalidated: {key}")

    def cleanup(self) -> None:
        """Remove all expired cache entries."""
        now = datetime.now()
        expired = [
            key for key, (timestamp, _) in self._cache.items()
            if now - timestamp > self._ttl
        ]
        for key in expired:
            del self._cache[key]
        if expired:
            self.logger.debug(f"Cleaned up {len(expired)} expired cache entries")