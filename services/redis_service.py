import redis
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

class RedisService:
    """Service class for Redis operations"""
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                socket_timeout=settings.redis_socket_timeout,
                health_check_interval=settings.redis_health_check_interval,
                retry_on_timeout=settings.redis_retry_on_timeout,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def key_exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        if not self.is_connected():
            logger.warning("Redis not connected, returning False for key existence check")
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key existence in Redis: {e}")
            return False
    
    def set_key(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """Set a key in Redis with optional expiration"""
        if not self.is_connected():
            logger.warning("Redis not connected, cannot set key")
            return False
        
        try:
            if expire_seconds:
                self.redis_client.setex(key, expire_seconds, value)
            else:
                self.redis_client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting key in Redis: {e}")
            return False
    
    def get_key(self, key: str) -> Optional[str]:
        """Get a key value from Redis"""
        if not self.is_connected():
            logger.warning("Redis not connected, cannot get key")
            return None
        
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Error getting key from Redis: {e}")
            return None
    
    def delete_key(self, key: str) -> bool:
        """Delete a key from Redis"""
        if not self.is_connected():
            logger.warning("Redis not connected, cannot delete key")
            return False
        
        try:
            return self.redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Error deleting key from Redis: {e}")
            return False
    
 