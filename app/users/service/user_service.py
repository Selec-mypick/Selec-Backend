from sqlalchemy.ext.asyncio import AsyncSession

from app.base.response import PageResponse
from app.core.database.transaction import run_in_transaction
from app.core.exceptions import BaseAPIException, ErrorCode
from app.question.repository.question_repository import QuestionRepository
from app.users.repository.users_repository import UsersRepository
from app.users.schema.request.users_request import UpdateMyInfoRequest
from app.users.schema.response.users_response import GetMyInfoResponse, MyQuestionResponse


async def get_my_info(users_seq: str, db: AsyncSession) -> GetMyInfoResponse:
    users = await UsersRepository.find_by_users_seq(db, users_seq)
    if users is None:
        raise BaseAPIException(ErrorCode.USER_NOT_FOUND)

    return GetMyInfoResponse.from_entity(users)


async def get_my_questions(users_seq: str, page: int, size: int, db: AsyncSession) -> PageResponse[MyQuestionResponse]:
    total_elements = await QuestionRepository.count_by_users_seq(db, users_seq)
    questions = await QuestionRepository.find_all_by_users_seq_with_vote_count(db, users_seq, page, size)
    content = [
        MyQuestionResponse.from_entity(question, vote_count)
        for question, vote_count in questions
    ]
    return PageResponse.of(content, page, size, total_elements)


async def update_my_info(
        users_seq: str,
        request: UpdateMyInfoRequest,
        db: AsyncSession,
) -> GetMyInfoResponse:
    users = await UsersRepository.find_by_users_seq(db, users_seq)
    if users is None:
        raise BaseAPIException(ErrorCode.USER_NOT_FOUND)

    existing_users = await UsersRepository.find_by_nick_name(db, request.nick_name)
    if existing_users is not None and existing_users.users_seq != users_seq:
        raise BaseAPIException(ErrorCode.NICKNAME_ALREADY_USED)

    async def update_my_info_action() -> GetMyInfoResponse:
        users.update_nick_name(request.nick_name)
        await db.flush()
        await db.refresh(users)
        return GetMyInfoResponse.from_entity(users)

    return await run_in_transaction(
        db,
        update_my_info_action,
        "회원 정보 수정 중 오류가 발생했습니다",
        integrity_exception=BaseAPIException(ErrorCode.NICKNAME_ALREADY_USED),
    )
