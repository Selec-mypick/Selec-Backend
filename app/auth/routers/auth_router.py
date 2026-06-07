from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schema.request.auth_request import GoogleOAuthRequest, IssueTestTokenRequest, RefreshTokenRequest
from app.auth.schema.response.auth_response import AuthTokenResponse, CreateTestUserResponse
from app.auth.service.auth_service import authenticate_google, create_test_user, issue_test_token, refresh_access_token
from app.base.response import BaseResponse, api_errors
from app.core.database import get_db
from app.core.exceptions import ErrorCode

router = APIRouter(prefix="/api/auth", tags=["AUTH"])


@router.post(
    "/test/users",
    response_model=BaseResponse[CreateTestUserResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        **api_errors(
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.TEST_USER_CREATE_CONFLICT,
            ErrorCode.TOKEN_STORE_FAILED,
        ),
    },
)
async def create_test_user_endpoint(
        db: AsyncSession = Depends(get_db),
):
    """
    개발/테스트용 사용자 계정을 생성하고 즉시 로그인 가능한 JWT를 발급합니다.

    Google OAuth 없이 users 테이블에 테스트 유저를 저장한 뒤,
    access token과 refresh token을 함께 반환합니다.
    """
    result = await create_test_user(db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, result)


@router.post(
    "/test/token",
    response_model=BaseResponse[AuthTokenResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        **api_errors(
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.AUTH_USER_NOT_FOUND,
            ErrorCode.AUTH_USER_INACTIVE,
            ErrorCode.TOKEN_STORE_FAILED,
        ),
    },
)
async def issue_test_token_endpoint(
        request: IssueTestTokenRequest,
        db: AsyncSession = Depends(get_db),
):
    """
    이미 존재하는 users_seq에 대해 테스트용 JWT를 재발급합니다.

    기존 access token은 blacklist 처리되고, 새 access/refresh token이 발급됩니다.
    """
    result = await issue_test_token(request, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, result)


@router.post(
    "/oauth/google",
    response_model=BaseResponse[AuthTokenResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        **api_errors(
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.GOOGLE_TOKEN_VERIFY_FAILED,
            ErrorCode.GOOGLE_TOKEN_AUDIENCE_MISMATCH,
            ErrorCode.GOOGLE_USER_NOT_FOUND,
            ErrorCode.GOOGLE_REGISTER_CONFLICT,
            ErrorCode.TOKEN_STORE_FAILED,
        ),
    },
)
async def google_oauth_endpoint(
        request: GoogleOAuthRequest,
        db: AsyncSession = Depends(get_db),
):
    """
    Google id_token으로 로그인하고 Selec JWT를 발급합니다.

    Google 계정 정보로 users를 upsert한 뒤 access/refresh token을 발급합니다.
    재로그인 시 이전 access token은 무효화됩니다.
    """
    result = await authenticate_google(request, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, result)


@router.post(
    "/token/refresh",
    response_model=BaseResponse[AuthTokenResponse],
    status_code=status.HTTP_200_OK,
    responses={
        **api_errors(
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.REFRESH_TOKEN_EXPIRED,
            ErrorCode.REFRESH_TOKEN_INVALID,
            ErrorCode.REFRESH_TOKEN_TYPE_INVALID,
            ErrorCode.REFRESH_TOKEN_MISSING_USER,
            ErrorCode.REFRESH_TOKEN_BLACKLISTED,
            ErrorCode.AUTH_USER_NOT_FOUND,
            ErrorCode.AUTH_USER_INACTIVE,
            ErrorCode.TOKEN_REFRESH_FAILED,
        ),
    },
)
async def refresh_token_endpoint(
        request: RefreshTokenRequest,
        db: AsyncSession = Depends(get_db),
):
    """
    refresh token으로 access/refresh token을 재발급합니다.

    사용한 refresh token과 기존 access token은 blacklist 처리되며,
    새 token pair가 발급됩니다.
    """
    result = await refresh_access_token(request, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)
