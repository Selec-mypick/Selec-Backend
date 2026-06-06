from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection_config import get_db
from app.core.exception import UnauthorizedException
from app.users.repository.users_repository import UsersRepository
from app.users.schema.dto.jwt_users import JwtUsers


async def get_jwt_users(request: Request, db: AsyncSession = Depends(get_db)) -> JwtUsers:
    users_seq = getattr(request.state, "users_seq", None)
    if users_seq is None:
        raise UnauthorizedException("인증된 사용자 정보가 없습니다.")

    users = await UsersRepository.find_by_users_seq(db, users_seq)
    if users is None:
        raise UnauthorizedException("존재하지 않는 사용자입니다.")
    if not users.active:
        raise UnauthorizedException("비활성화된 사용자입니다.")

    return JwtUsers.from_entity(users)
