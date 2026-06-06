from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schema.request.auth_request import GoogleOAuthRequest, RefreshTokenRequest
from app.auth.schema.response.auth_response import AuthTokenResponse, CreateTestUserResponse
from app.auth.service.auth_service import authenticate_google, create_test_user, refresh_access_token
from app.base.constants import BaseUtil
from app.base.response import BaseResponse
from app.base.response import AUTH_RESPONSES, REFRESH_TOKEN_RESPONSES
from app.core.database import get_db

router = APIRouter(prefix="/api/auth", tags=["AUTH"])


@router.post(
    "/test/users",
    response_model=BaseResponse[CreateTestUserResponse],
    status_code=status.HTTP_201_CREATED,
    responses=AUTH_RESPONSES,
)
async def create_test_user_endpoint(
        db: AsyncSession = Depends(get_db),
):
    """
    테스트 유저 생성

    Google OAuth 없이 실제 users row를 만들고 테스트용 JWT를 발급합니다.
    """
    result = await create_test_user(db)
    return BaseResponse.of(status.HTTP_201_CREATED, BaseUtil.SUCCESS, result)


@router.post(
    "/oauth/google",
    response_model=BaseResponse[AuthTokenResponse],
    status_code=status.HTTP_201_CREATED,
    responses=AUTH_RESPONSES,
)
async def google_oauth_endpoint(
        request: GoogleOAuthRequest,
        db: AsyncSession = Depends(get_db),
):
    """
    Google OAuth 로그인

    앱에서 Google Sign-In SDK로 받은 id_token을 전달하면 Google에 검증 후 JWT를 발급합니다.

    **Response**
    - `201`: JWT 발급 성공
    - `400`: Google 토큰 검증 실패, 잘못된 요청
    - `500`: 서버 오류
    """
    result = await authenticate_google(request, db)
    return BaseResponse.of(status.HTTP_201_CREATED, BaseUtil.SUCCESS, result)


@router.post(
    "/token/refresh",
    response_model=BaseResponse[AuthTokenResponse],
    status_code=status.HTTP_200_OK,
    responses=REFRESH_TOKEN_RESPONSES,
)
async def refresh_token_endpoint(
        request: RefreshTokenRequest,
        db: AsyncSession = Depends(get_db),
):
    """
    토큰 재발급

    refresh token으로 새 access token과 refresh token을 발급합니다.

    **Response**
    - `200`: 토큰 재발급 성공
    - `401`: 유효하지 않거나 만료된 refresh token
    - `500`: 서버 오류
    """
    result = await refresh_access_token(request, db)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS, result)
