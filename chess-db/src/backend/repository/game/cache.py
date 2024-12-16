
# repository/game/cache.py
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..common.cache import CacheManager
from .types import GameData, GameStats

class GameCacheManager(CacheManager[Any]):
    """
    Cache manager specialized for chess game data.
    
    Implements different caching strategies and TTLs for:
    - Individual games
    - Game lists
    - Statistics
    - Analysis results
    """
    
    def __init__(self):
        super().__init__()
        self._ttl_config = {
            'game_': timedelta(minutes=60),  # Individual games
            'games_': timedelta(minutes=15), # Game lists
            'stats_': timedelta(minutes=30), # Statistics
            'analysis_': timedelta(minutes=45)  # Analysis results
        }
        
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve item from cache with TTL checking.
        
        Args:
            key: Cache key to lookup
            
        Returns:
            Cached value if present and not expired, None otherwise
        """
        if key not in self._cache:
            return None
            
        timestamp, value = self._cache[key]
        ttl = self._get_ttl(key)
        
        if datetime.now() - timestamp > ttl:
            del self._cache[key]
            return None
            
        self.logger.debug(f"Cache hit: {key}")
        return value
        
    def _get_ttl(self, key: str) -> timedelta:
        """Get TTL for specific key type."""
        for prefix, ttl in self._ttl_config.items():
            if key.startswith(prefix):
                return ttl
        return timedelta(minutes=15)  # Default TTL

