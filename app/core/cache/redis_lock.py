import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from app.core.cache import RedisClient

logger = logging.getLogger(__name__)


class RedisLock:
    @staticmethod
    @asynccontextmanager
    async def hold(lock_key: str, ttl_seconds: int = 300) -> AsyncIterator[bool]:
        token = uuid4().hex
        redis_client = await RedisClient.get_client()
        acquired = await redis_client.set(lock_key, token, nx=True, ex=ttl_seconds)

        if not acquired:
            logger.info("Redis lock not acquired. lock_key=%s", lock_key)
            yield False
            return

        try:
            yield True
        finally:
            current_token = await redis_client.get(lock_key)
            if current_token == token:
                await redis_client.delete(lock_key)
