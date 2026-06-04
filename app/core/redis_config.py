import redis.asyncio as redis
from typing import Optional
from config import settings
from app.core.exception import ServerException


class RedisClient:
    _instance: Optional[redis.Redis] = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        if cls._instance is None:
            try:
                if settings.redis_password:
                    redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
                else:
                    redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"

                cls._instance = await redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
                await cls._instance.ping()
            except Exception as e:
                raise ServerException(f"Redis 연결 실패: {str(e)}")
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

    @classmethod
    async def ping(cls) -> bool:
        try:
            client = await cls.get_client()
            await client.ping()
            return True
        except Exception:
            return False


async def get_redis() -> redis.Redis:
    return await RedisClient.get_client()

