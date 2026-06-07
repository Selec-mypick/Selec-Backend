from fastapi import Request

from app.core.exceptions import BaseAPIException, ErrorCode


async def get_users_seq(request: Request) -> str:
    users_seq = getattr(request.state, "users_seq", None)
    if users_seq is None:
        raise BaseAPIException(ErrorCode.AUTHENTICATED_USER_NOT_FOUND)
    return users_seq
