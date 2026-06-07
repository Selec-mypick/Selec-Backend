from fastapi import Request

from app.core.exceptions import UnauthorizedException


async def get_users_seq(request: Request) -> str:
    users_seq = getattr(request.state, "users_seq", None)
    if users_seq is None:
        raise UnauthorizedException("인증된 사용자 정보가 없습니다.")
    return users_seq
