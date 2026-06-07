from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.transaction import run_in_transaction
from app.core.exceptions import ConflictException, NotFoundException
from app.users.repository.users_repository import UsersRepository
from app.users.schema.request.users_request import UpdateMyInfoRequest
from app.users.schema.response.users_response import GetMyInfoResponse


async def get_my_info(users_seq: str, db: AsyncSession) -> GetMyInfoResponse:
    users = await UsersRepository.find_by_users_seq(db, users_seq)
    if users is None:
        raise NotFoundException("존재하지 않는 사용자입니다.")

    return GetMyInfoResponse.from_entity(users)


async def update_my_info(
        users_seq: str,
        request: UpdateMyInfoRequest,
        db: AsyncSession,
) -> GetMyInfoResponse:
    users = await UsersRepository.find_by_users_seq(db, users_seq)
    if users is None:
        raise NotFoundException("존재하지 않는 사용자입니다.")

    existing_users = await UsersRepository.find_by_nick_name(db, request.nick_name)
    if existing_users is not None and existing_users.users_seq != users_seq:
        raise ConflictException("이미 사용 중인 닉네임입니다.")

    async def update_my_info_action() -> GetMyInfoResponse:
        users.update_nick_name(request.nick_name)
        await db.flush()
        await db.refresh(users)
        return GetMyInfoResponse.from_entity(users)

    return await run_in_transaction(db, update_my_info_action, "회원 정보 수정 중 오류가 발생했습니다")
