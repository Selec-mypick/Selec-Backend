import hashlib
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import jwt, JWTError

from app.core.cache import RedisClient
from config import settings

AuthTokenStoreType = Literal["white", "black"]


def create_access_token(users_seq: str) -> tuple[str, int]:
    expires_in = settings.access_token_ttl_seconds
    now = datetime.now(timezone.utc)
    payload = {
        "users_seq": users_seq,
        "sub": str(users_seq),
        "type": "access",
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm), expires_in


def create_refresh_token(users_seq: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "users_seq": users_seq,
        "sub": str(users_seq),
        "type": "refresh",
        "exp": int((now + timedelta(days=settings.refresh_token_expire_days)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


async def store_auth_token(*, store_type: AuthTokenStoreType, token: str, users_seq: str | None = None) -> None:
    redis_client = await RedisClient.get_client()

    if store_type == "white":
        if users_seq is None:
            raise ValueError("white token 저장 시 users_seq가 필요합니다.")
        await redis_client.set(
            f"auth:white:{users_seq}",
            token,
            ex=settings.access_token_ttl_seconds,
        )
        return

    try:
        payload = jwt.get_unverified_claims(token)
    except JWTError:
        return

    exp = payload.get("exp")
    if not exp:
        return

    ttl = max(int(exp) - int(datetime.now(timezone.utc).timestamp()), 0)
    if ttl <= 0:
        return

    await redis_client.set(
        f"auth:black:{hashlib.sha256(token.encode()).hexdigest()}",
        "1",
        ex=ttl,
    )


async def get_white_token(users_seq: str) -> str | None:
    redis_client = await RedisClient.get_client()
    return await redis_client.get(f"auth:white:{users_seq}")


async def is_token_blacklisted(token: str) -> bool:
    redis_client = await RedisClient.get_client()
    return bool(await redis_client.exists(f"auth:black:{hashlib.sha256(token.encode()).hexdigest()}"))
