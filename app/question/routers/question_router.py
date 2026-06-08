from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.response import BaseResponse, api_errors
from app.core.database import get_db
from app.core.exceptions import ErrorCode
from app.users.dependency.users_seq import get_users_seq
from app.question.schema.request.question_request import CreateQuestionRequest, UpdateQuestionRequest
from app.question.schema.response.question_response import (
    CreateQuestionResponse,
    GetQuestionResponse,
    UpdateQuestionResponse,
)
from app.question.service.question_service import (
    create_question,
    delete_question,
    get_question,
    update_question,
)

router = APIRouter(prefix="/api/question", tags=["QUESTION"])

_AUTH_ERRORS = (
    ErrorCode.ACCESS_TOKEN_EXPIRED,
    ErrorCode.ACCESS_TOKEN_INVALID,
    ErrorCode.ACCESS_TOKEN_NOT_WHITELISTED,
    ErrorCode.ACCESS_TOKEN_WHITELIST_MISMATCH,
    ErrorCode.ACCESS_TOKEN_BLACKLISTED,
    ErrorCode.AUTHENTICATED_USER_NOT_FOUND,
)


@router.post(
    "",
    response_model=BaseResponse[CreateQuestionResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    },
)
async def create_question_endpoint(
        request: CreateQuestionRequest,
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    투표 질문과 선택지를 생성합니다.

    질문 작성자는 JWT의 users_seq로 저장되며, 익명/공개 여부와 선택지 목록을 함께 등록합니다.
    """
    result = await create_question(request, users_seq, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, result)


@router.get(
    "/{question_seq}",
    response_model=BaseResponse[GetQuestionResponse],
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.QUESTION_NOT_FOUND,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    },
)
async def get_question_endpoint(
        question_seq: UUID = Path(..., description="질문 UUID"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 상세와 선택지 목록을 조회합니다.

    작성자이거나 해당 질문에 투표한 사용자에게만 선택지별 vote_count가 노출됩니다.
    """
    result = await get_question(str(question_seq), users_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)


@router.put(
    "/{question_seq}",
    response_model=BaseResponse[UpdateQuestionResponse],
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.VOTE_ALREADY_CLOSED,
            ErrorCode.DUPLICATE_OPTION_SEQ,
            ErrorCode.OPTION_NOT_IN_QUESTION,
            ErrorCode.OPTION_HAS_VOTES,
            ErrorCode.QUESTION_UPDATE_FORBIDDEN,
            ErrorCode.QUESTION_NOT_FOUND,
            ErrorCode.QUESTION_STALE,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    },
)
async def update_question_endpoint(
        request: UpdateQuestionRequest,
        question_seq: UUID = Path(..., description="질문 UUID"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 작성자가 질문/선택지를 수정합니다.

    낙관적 락(version)으로 동시 수정을 막고, 종료된 투표나 이미 투표된 선택지는 수정할 수 없습니다.
    """
    result = await update_question(str(question_seq), request, users_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)


@router.delete(
    "/{question_seq}",
    response_model=BaseResponse,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.QUESTION_DELETE_FORBIDDEN,
            ErrorCode.QUESTION_NOT_FOUND,
            ErrorCode.QUESTION_STALE,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    },
)
async def delete_question_endpoint(
        question_seq: UUID = Path(..., description="질문 UUID"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 작성자가 질문을 삭제(soft delete)합니다.

    연결된 선택지와 투표도 함께 비활성화됩니다.
    """
    await delete_question(str(question_seq), users_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK)
