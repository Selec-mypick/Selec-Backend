from datetime import datetime, timedelta, timezone

from jose import jwt

from config import settings


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
