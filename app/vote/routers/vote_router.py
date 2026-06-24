from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.response import BaseResponse, api_errors
from app.core.database import get_db
from app.core.exceptions import ErrorCode
from app.question.schema.response.question_response import GetQuestionResponse
from app.users.dependency.users_seq import get_users_seq
from app.vote.schema.request.vote_request import CreateVoteRequest
from app.vote.service.vote_service import create_vote, delete_vote

router = APIRouter(prefix="/api/vote", tags=["VOTE"])

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
    "/{question_seq}",
    response_model=BaseResponse[GetQuestionResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.OPTION_NOT_IN_QUESTION,
            ErrorCode.QUESTION_NOT_FOUND,
            ErrorCode.RESOURCE_CONFLICT,
            ErrorCode.TRANSACTION_FAILED,
        ),
    },
)
async def create_vote_endpoint(
        request: CreateVoteRequest,
        question_seq: UUID = Path(..., description="질문 UUID"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    질문에 투표하거나 선택지를 변경합니다.
    """
    result = await create_vote(str(question_seq), request, users_seq, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, result)


@router.delete(
    "/{question_seq}",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.VOTE_NOT_FOUND,
            ErrorCode.TRANSACTION_FAILED,
        ),
    },
)
async def delete_vote_endpoint(
        question_seq: UUID = Path(..., description="질문 UUID"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    내 투표를 취소합니다.
    """
    await delete_vote(str(question_seq), users_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK)
