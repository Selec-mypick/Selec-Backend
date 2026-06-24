from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.response import BaseResponse, PageResponse, api_errors
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
    get_invited_questions,
    get_question,
    update_question,
)

router = APIRouter(prefix="/api/question", tags=["QUESTION"])

_AUTH_ERRORS = (
    ErrorCode.AUTH_HEADER_REQUIRED,
    ErrorCode.AUTH_HEADER_INVALID_FORMAT,
    ErrorCode.ACCESS_TOKEN_EXPIRED,
    ErrorCode.ACCESS_TOKEN_INVALID,
    ErrorCode.ACCESS_TOKEN_MISSING_USER,
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
            ErrorCode.RESOURCE_CONFLICT,
            ErrorCode.TRANSACTION_FAILED,
        ),
    },
)
async def create_question_endpoint(
        request: CreateQuestionRequest,
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    질문과 선택지를 생성합니다.
    """
    result = await create_question(request, users_seq, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, result)


@router.get(
    "/invited",
    response_model=BaseResponse[PageResponse[GetQuestionResponse]],
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    },
)
async def get_invited_questions_endpoint(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(20, ge=1, le=100, description="페이지 크기"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    초대된 질문 목록을 페이지로 조회합니다.
    """
    result = await get_invited_questions(users_seq, page, size, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)


@router.get(
    "/{question_seq}",
    response_model=BaseResponse[GetQuestionResponse],
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.QUESTION_NOT_FOUND,
            ErrorCode.RESOURCE_CONFLICT,
            ErrorCode.TRANSACTION_FAILED,
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

    조회한 사용자는 질문 초대 목록에 기록됩니다.
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
            ErrorCode.DUPLICATE_OPTION_SEQ,
            ErrorCode.OPTION_NOT_IN_QUESTION,
            ErrorCode.OPTION_HAS_VOTES,
            ErrorCode.QUESTION_UPDATE_FORBIDDEN,
            ErrorCode.QUESTION_NOT_FOUND,
            ErrorCode.QUESTION_STALE,
            ErrorCode.RESOURCE_CONFLICT,
            ErrorCode.TRANSACTION_FAILED,
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

    낙관적 락(version)으로 동시 수정을 막고, 이미 투표된 선택지는 수정할 수 없습니다.
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
            ErrorCode.TRANSACTION_FAILED,
        ),
    },
)
async def delete_question_endpoint(
        question_seq: UUID = Path(..., description="질문 UUID"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 작성자가 질문을 삭제합니다.

    연결된 선택지, 투표, 초대 기록도 함께 비활성화됩니다.
    """
    await delete_question(str(question_seq), users_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK)
