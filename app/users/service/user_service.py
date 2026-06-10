from sqlalchemy.ext.asyncio import AsyncSession

from app.base.response import PageResponse
from app.auth.domain.token_domain import store_auth_token
from app.core.exceptions import BaseAPIException, ErrorCode
from app.question.repository.question_repository import QuestionRepository
from app.users.repository.users_repository import UsersRepository
from app.users.schema.request.users_request import LogoutRequest
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


async def logout(request: LogoutRequest, access_token: str) -> None:
    try:
        await store_auth_token(store_type="black", token=access_token)
        await store_auth_token(store_type="black", token=request.refresh_token)
    except Exception as e:
        raise BaseAPIException(ErrorCode.TOKEN_STORE_FAILED, message=f"{ErrorCode.TOKEN_STORE_FAILED.message}: {str(e)}")
