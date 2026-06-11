from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    redis = get_redis()
    await redis.aclose()
    get_redis.cache_clear()
