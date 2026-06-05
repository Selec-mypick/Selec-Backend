import json

import aiohttp
from jose import jwt as jose_jwt
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from app.auth.schema.request.google_oauth_request import GoogleOAuthRequest
from app.auth.schema.response.auth_response import AuthTokenResponse
from app.auth.domain.token_domain import create_access_token, create_refresh_token
from app.core.exception import BadRequestException, ServerException
from app.core.redis_config import RedisClient
from app.users.dependency.dependency import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.users.repository.users_repository import UsersRepository

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
ACCESS_TOKEN_TTL_SECONDS = ACCESS_TOKEN_EXPIRE_MINUTES * 60
BLACKLIST_TTL_SECONDS = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


async def authenticate_google(request: GoogleOAuthRequest, db: AsyncSession) -> AuthTokenResponse:
    if request.id_token:
        google_user = jose_jwt.get_unverified_claims(request.id_token)
        if google_user.get("aud") != settings.google_client_id:
            raise BadRequestException("Google id_token audience가 일치하지 않습니다.")
        if google_user.get("iss") not in ("https://accounts.google.com", "accounts.google.com"):
            raise BadRequestException("Google id_token issuer가 유효하지 않습니다.")
    else:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "code": request.code,
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "redirect_uri": request.redirect_uri,
                        "grant_type": "authorization_code",
                    },
            ) as response:
                google_token = await response.json()
                if response.status != 200:
                    message = google_token.get("error_description") or google_token.get("error") or "Google 토큰 교환 실패"
                    raise BadRequestException(message)

            id_token = google_token.get("id_token")
            if id_token:
                google_user = jose_jwt.get_unverified_claims(id_token)
                if google_user.get("aud") != settings.google_client_id:
                    raise BadRequestException("Google id_token audience가 일치하지 않습니다.")
                if google_user.get("iss") not in ("https://accounts.google.com", "accounts.google.com"):
                    raise BadRequestException("Google id_token issuer가 유효하지 않습니다.")
            else:
                access_token = google_token.get("access_token")
                if not access_token:
                    raise BadRequestException("Google access_token이 없습니다.")
                async with session.get(
                        GOOGLE_USERINFO_URL,
                        headers={"Authorization": f"Bearer {access_token}"},
                ) as response:
                    google_user = await response.json()
                    if response.status != 200:
                        message = google_user.get("error_description") or google_user.get("error") or "Google 사용자 정보 조회 실패"
                        raise BadRequestException(message)

    google_id = google_user.get("sub")
    if not google_id:
        raise BadRequestException("Google 사용자 정보를 확인할 수 없습니다.")

    email = google_user.get("email")
    name = google_user.get("name")
    profile_image = google_user.get("picture")
    redis_client = await RedisClient.get_client()

    try:
        users = await UsersRepository.upsert_by_google(
            db=db,
            google_id=google_id,
            email=email,
            name=name,
            profile_image=profile_image,
        )

        access_token, expires_in = create_access_token(users.users_seq)
        refresh_token = create_refresh_token(users.users_seq)

        white_key = f"auth:white:{users.users_seq}"
        black_key = f"auth:black:{users.users_seq}"
        user_key = f"auth:user:{users.users_seq}"
        user_cache = json.dumps({
            "users_seq": users.users_seq,
            "active": users.active,
            "created_at": users.created_at.isoformat(),
            "updated_at": users.updated_at.isoformat(),
        })

        previous_token = await redis_client.get(white_key)
        pipe = redis_client.pipeline()
        if previous_token is not None:
            pipe.set(black_key, previous_token, ex=BLACKLIST_TTL_SECONDS)
        pipe.set(white_key, access_token, ex=ACCESS_TOKEN_TTL_SECONDS)
        pipe.set(user_key, user_cache, ex=ACCESS_TOKEN_TTL_SECONDS)
        await pipe.execute()

        await db.commit()
    except BadRequestException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ServerException(f"Google OAuth 로그인 처리 중 오류가 발생했습니다: {str(e)}")

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        users_seq=users.users_seq,
    )
