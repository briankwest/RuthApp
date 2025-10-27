"""
Redis connection and utilities for caching and token blacklisting
"""
import logging
from typing import Optional
from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[Redis] = None


async def init_redis() -> None:
    """
    Initialize Redis connection pool
    Called during application startup
    """
    global _redis_pool, _redis_client

    try:
        _redis_pool = ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=10
        )
        _redis_client = Redis(connection_pool=_redis_pool)

        # Test connection
        await _redis_client.ping()
        logger.info(f"Redis connected successfully: {settings.redis_url}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        _redis_pool = None
        _redis_client = None


async def close_redis() -> None:
    """
    Close Redis connection
    Called during application shutdown
    """
    global _redis_pool, _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None

    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None

    logger.info("Redis connection closed")


async def get_redis() -> Optional[Redis]:
    """
    Get Redis client instance
    Returns None if Redis is not available (fail gracefully)
    """
    global _redis_client

    if _redis_client is None:
        logger.warning("Redis client not initialized, attempting to initialize...")
        await init_redis()

    return _redis_client
