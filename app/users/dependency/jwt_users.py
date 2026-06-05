import json
from datetime import datetime

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection_config import get_db
from app.core.exception import UnauthorizedException
from app.core.redis_config import RedisClient
from app.users.repository.users_repository import UsersRepository
from app.users.schema.jwt_users import JwtUsers


async def get_jwt_users(
        request: Request,
        db: AsyncSession = Depends(get_db),
) -> JwtUsers:
    users_seq = getattr(request.state, "users_seq", None)
    if users_seq is None:
        raise UnauthorizedException("인증된 사용자 정보가 없습니다.")

    redis_client = await RedisClient.get_client()
    cached_user = await redis_client.get(f"auth:user:{users_seq}")
    if cached_user is not None:
        user_data = json.loads(cached_user)
        user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
        user_data["updated_at"] = datetime.fromisoformat(user_data["updated_at"])
        jwt_users = JwtUsers(**user_data)
        if not jwt_users.active:
            raise UnauthorizedException("비활성화된 사용자입니다.")
        return jwt_users

    users = await UsersRepository.find_by_user_seq(db, users_seq)
    if users is None:
        raise UnauthorizedException("존재하지 않는 사용자입니다.")
    if not users.active:
        raise UnauthorizedException("비활성화된 사용자입니다.")

    return JwtUsers.from_entity(users)
