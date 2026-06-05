from datetime import datetime, timedelta, timezone

from jose import jwt

from app.users.dependency.dependency import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


def create_access_token(users_seq: int) -> tuple[str, int]:
    expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    payload = {
        "users_seq": users_seq,
        "sub": str(users_seq),
        "type": "access",
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), expires_in


def create_refresh_token(users_seq: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "users_seq": users_seq,
        "sub": str(users_seq),
        "type": "refresh",
        "exp": int((now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
