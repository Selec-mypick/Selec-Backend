from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import NotFoundException
from app.users.repository.users_repository import UsersRepository
from app.users.schema.response.users_response import GetMyInfoResponse


async def get_my_info(users_seq: int, db: AsyncSession) -> GetMyInfoResponse:
    users = await UsersRepository.find_by_users_seq(db, users_seq)
    if users is None:
        raise NotFoundException("존재하지 않는 사용자입니다.")

    return GetMyInfoResponse.from_entity(users)
