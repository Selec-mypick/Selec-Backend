from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.response import BaseResponse, PageResponse, api_errors
from app.core.database import get_db
from app.core.exceptions import ErrorCode
from app.users.dependency.users_seq import get_access_token, get_users_seq
from app.users.schema.request.users_request import LogoutRequest
from app.users.schema.response.users_response import GetMyInfoResponse, MyQuestionResponse
from app.users.service.user_service import get_my_info, get_my_questions, logout

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
    내 프로필 정보를 조회합니다.
    """
    result = await get_my_info(users_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)


@router.get(
    "/question",
    response_model=BaseResponse[PageResponse[MyQuestionResponse]],
    status_code=status.HTTP_200_OK,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.INTERNAL_SERVER_ERROR,
        ),
    },
)
async def get_my_questions_endpoint(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(20, ge=1, le=100, description="페이지 크기"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    내가 만든 질문 목록을 페이지로 조회합니다.
    """
    result = await get_my_questions(users_seq, page, size, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)


@router.post(
    "/logout",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_200_OK,
    responses={
        **api_errors(
            *_AUTH_ERRORS,
            ErrorCode.AUTH_HEADER_INVALID_FORMAT,
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.TOKEN_STORE_FAILED,
        ),
    },
)
async def logout_endpoint(
        request: LogoutRequest,
        access_token: str = Depends(get_access_token),
        _users_seq: str = Depends(get_users_seq),
):
    """
    access token과 refresh token을 무효화합니다.
    """
    await logout(request, access_token)
    return BaseResponse.of_success(status.HTTP_200_OK)
