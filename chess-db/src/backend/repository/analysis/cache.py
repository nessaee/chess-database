
# repository/analysis/cache.py
from typing import Optional, Any
from datetime import timedelta

from ..common.cache import CacheManager

class AnalysisCacheManager(CacheManager[Any]):
    """Specialized cache manager for analysis results."""
    
    def __init__(self):
        super().__init__()
        # Configure TTLs for different types of analysis
        self._ttl_config = {
            'move_distribution': timedelta(hours=12),
            'opening_analysis': timedelta(hours=6),
            'player_performance': timedelta(hours=4),
            'db_metrics': timedelta(minutes=5)
        }
        
    def set(
        self,
        key: str,
        value: Any,
        ttl_minutes: Optional[int] = None
    ) -> None:
        """
        Store item in cache with configurable TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_minutes: Optional specific TTL in minutes
        """
        if ttl_minutes is not None:
            ttl = timedelta(minutes=ttl_minutes)
        else:
            ttl = self._get_ttl(key)
            
        super().set(key, value, ttl)
        
    def _get_ttl(self, key: str) -> timedelta:
        """Get TTL for specific analysis type."""
        for prefix, ttl in self._ttl_config.items():
            if key.startswith(prefix):
                return ttl
        return timedelta(hours=1)  # Default TTL