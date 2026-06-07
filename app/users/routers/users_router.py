from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.response import BaseResponse, api_errors
from app.core.database import get_db
from app.core.exceptions import ErrorCode
from app.users.dependency.users_seq import get_users_seq
from app.users.schema.request.users_request import UpdateMyInfoRequest
from app.users.schema.response.users_response import GetMyInfoResponse
from app.users.service.user_service import get_my_info, update_my_info

router = APIRouter(prefix="/api/users", tags=["USERS"])

_AUTH_ERRORS = (
    ErrorCode.ACCESS_TOKEN_EXPIRED,
    ErrorCode.ACCESS_TOKEN_INVALID,
    ErrorCode.ACCESS_TOKEN_NOT_WHITELISTED,
    ErrorCode.ACCESS_TOKEN_WHITELIST_MISMATCH,
    ErrorCode.ACCESS_TOKEN_BLACKLISTED,
    ErrorCode.AUTHENTICATED_USER_NOT_FOUND,
)


@router.get(
    "/me",
    response_model=BaseResponse[GetMyInfoResponse],
    status_code=status.HTTP_200_OK,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.USER_NOT_FOUND,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    },
)
async def get_my_info_endpoint(
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    로그인한 사용자의 프로필 정보를 조회합니다.

    JWT에서 추출한 users_seq 기준으로 nick_name 등 내 정보를 반환합니다.
    """
    result = await get_my_info(users_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)


@router.put(
    "",
    response_model=BaseResponse[GetMyInfoResponse],
    status_code=status.HTTP_200_OK,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.USER_NOT_FOUND,
            ErrorCode.NICKNAME_ALREADY_USED,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    },
)
async def update_my_info_endpoint(
        request: UpdateMyInfoRequest,
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    로그인한 사용자의 닉네임을 수정합니다.

    다른 사용자가 이미 사용 중인 nick_name은 등록할 수 없습니다.
    """
    result = await update_my_info(users_seq, request, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)
