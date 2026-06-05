from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schema.request.google_oauth_request import GoogleOAuthRequest
from app.auth.schema.response.auth_response import AuthTokenResponse
from app.auth.service.auth_service import authenticate_google
from app.base.base_response import BaseResponse
from app.core.connection_config import get_db

router = APIRouter(prefix="/auth", tags=["AUTH"])


@router.post("/oauth/google", response_model=BaseResponse[AuthTokenResponse], status_code=status.HTTP_201_CREATED)
async def google_oauth_endpoint(
        request: GoogleOAuthRequest,
        db: AsyncSession = Depends(get_db),
):
    """
    Google OAuth 로그인

    앱에서 Google Sign-In SDK로 받은 id_token 또는 authorization code를 전달하면 JWT를 발급합니다.
    """
    result = await authenticate_google(request, db)
    return BaseResponse.of(status.HTTP_201_CREATED, "SUCCESS", result)
