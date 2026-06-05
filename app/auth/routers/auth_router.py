from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schema.request.google_oauth_request import GoogleOAuthRequest
from app.auth.schema.request.refresh_token_request import RefreshTokenRequest
from app.auth.schema.response.auth_response import AuthTokenResponse
from app.auth.service.auth_service import authenticate_google, refresh_access_token
from app.base.base_response import BaseResponse
from app.base.openapi_responses import AUTH_RESPONSES, REFRESH_TOKEN_RESPONSES
from app.core.connection_config import get_db

router = APIRouter(prefix="/api/auth", tags=["AUTH"])


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
    return BaseResponse.of(status.HTTP_201_CREATED, "SUCCESS", result)


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
    return BaseResponse.of(status.HTTP_200_OK, "SUCCESS", result)
