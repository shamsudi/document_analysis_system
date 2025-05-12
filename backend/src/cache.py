from redis import Redis
from datetime import timedelta
from typing import Optional
from .config import settings
import logging

logger = logging.getLogger(__name__)

class Cache:
    """
    Redis-based caching layer implementation.
    
    Provides methods for storing and retrieving cached values with automatic TTL.
    
    Attributes:
        redis (Redis): Redis client instance
        ttl (int): Time to live in seconds for cached items
        hits (int): Number of cache hits
        misses (int): Number of cache misses
    """
    def __init__(self):
        """
        Initialize cache instance with Redis connection.
        """
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.ttl = int(timedelta(hours=24).total_seconds())
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[str]:
        """
        Retrieve a cached value by key.
        
        Args:
            key (str): Cache key to retrieve
            
        Returns:
            Optional[str]: Cached value as string, or None if not found
        """
        try:
            value = self.redis.get(key)
            if value:
                self.hits += 1
                return value.decode('utf-8')
            self.misses += 1
            return None
        except Exception as e:
            logger.error(f"Error retrieving cache value: {str(e)}")
            return None

    def set(self, key: str, value: str) -> None:
        """
        Store a value in cache with TTL.
        
        Args:
            key (str): Cache key to store under
            value (str): Value to store
        """
        self.redis.setex(key, self.ttl, value)

    def hit_ratio(self) -> float:
        """
        Calculate the cache hit ratio.
        
        Returns:
            float: Ratio of hits to total requests (hits + misses), or 0.0 if no requests
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0