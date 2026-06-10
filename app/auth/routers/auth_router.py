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
    테스트 유저를 생성하고 토큰을 발급합니다.
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
    기존 테스트 유저의 토큰을 재발급합니다.
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
    Google id_token으로 로그인하고 토큰을 발급합니다.
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
    refresh token으로 토큰을 재발급합니다.
    """
    result = await refresh_access_token(request, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)
