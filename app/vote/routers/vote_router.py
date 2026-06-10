from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.response import BaseResponse, api_errors
from app.core.database import get_db
from app.core.exceptions import ErrorCode
from app.users.dependency.users_seq import get_users_seq
from app.vote.schema.request.vote_request import CreateVoteRequest
from app.vote.service.vote_service import create_vote, delete_vote

router = APIRouter(prefix="/api/vote", tags=["VOTE"])

_AUTH_ERRORS = (
    ErrorCode.ACCESS_TOKEN_EXPIRED,
    ErrorCode.ACCESS_TOKEN_INVALID,
    ErrorCode.ACCESS_TOKEN_NOT_WHITELISTED,
    ErrorCode.ACCESS_TOKEN_WHITELIST_MISMATCH,
    ErrorCode.ACCESS_TOKEN_BLACKLISTED,
    ErrorCode.AUTHENTICATED_USER_NOT_FOUND,
)


@router.post(
    "/{question_seq}",
    response_model=BaseResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.VOTE_ALREADY_CLOSED,
            ErrorCode.OPTION_NOT_IN_QUESTION,
            ErrorCode.QUESTION_NOT_FOUND,
            ErrorCode.INTERNAL_SERVER_ERROR,
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

    동일 질문에 다시 투표하면 기존 선택지가 upsert로 갱신됩니다.
    """
    await create_vote(str(question_seq), request, users_seq, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED)


@router.delete(
    "/{question_seq}",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.VOTE_NOT_FOUND,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    },
)
async def delete_vote_endpoint(
        question_seq: UUID = Path(..., description="질문 UUID"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    본인이 남긴 투표를 취소(soft delete)합니다.
    """
    await delete_vote(str(question_seq), users_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK)
