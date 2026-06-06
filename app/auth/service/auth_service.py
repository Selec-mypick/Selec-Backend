import aiohttp
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from app.auth.schema.request.google_oauth_request import GoogleOAuthRequest
from app.auth.schema.request.refresh_token_request import RefreshTokenRequest
from app.auth.schema.response.auth_response import AuthTokenResponse
from app.auth.domain.token_domain import create_access_token, create_refresh_token
from app.core.exception import BadRequestException, ServerException, UnauthorizedException
from app.core.redis_config import RedisClient
from app.users.dependency.dependency import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.users.repository.users_repository import UsersRepository

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
ACCESS_TOKEN_TTL_SECONDS = ACCESS_TOKEN_EXPIRE_MINUTES * 60
BLACKLIST_TTL_SECONDS = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


async def authenticate_google(request: GoogleOAuthRequest, db: AsyncSession) -> AuthTokenResponse:
    async with aiohttp.ClientSession() as session:
        async with session.get(GOOGLE_TOKENINFO_URL, params={"id_token": request.id_token}) as response:
            google_user = await response.json()
            if response.status != 200:
                message = google_user.get("error_description") or google_user.get("error") or "Google id_token 검증 실패"
                raise BadRequestException(message)

    if google_user.get("aud") != settings.google_client_id:
        raise BadRequestException("Google id_token audience가 일치하지 않습니다.")

    google_id = google_user.get("sub")
    if not google_id:
        raise BadRequestException("Google 사용자 정보를 확인할 수 없습니다.")

    try:
        users = await UsersRepository.upsert_by_google(
            db=db,
            google_id=google_id,
            email=google_user.get("email"),
            name=google_user.get("name"),
            profile_image=google_user.get("picture"),
        )

        access_token, expires_in = create_access_token(users.users_seq)
        refresh_token = create_refresh_token(users.users_seq)

        white_key = f"auth:white:{users.users_seq}"
        black_key = f"auth:black:{users.users_seq}"
        redis_client = await RedisClient.get_client()
        previous_token = await redis_client.get(white_key)

        pipe = redis_client.pipeline()
        if previous_token is not None:
            await pipe.set(black_key, previous_token, ex=BLACKLIST_TTL_SECONDS)
        await pipe.set(white_key, access_token, ex=ACCESS_TOKEN_TTL_SECONDS)
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
    )


async def refresh_access_token(request: RefreshTokenRequest, db: AsyncSession) -> AuthTokenResponse:
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("refresh token이 만료되었습니다.")
    except JWTError:
        raise UnauthorizedException("유효하지 않은 refresh token입니다.")

    if payload.get("type") != "refresh":
        raise UnauthorizedException("refresh token이 아닙니다.")

    users_seq = payload.get("users_seq") or payload.get("sub")
    if not users_seq:
        raise UnauthorizedException("refresh token에 사용자 정보가 없습니다.")

    users = await UsersRepository.find_by_users_seq(db, int(users_seq))
    if users is None:
        raise UnauthorizedException("존재하지 않는 사용자입니다.")
    if not users.active:
        raise UnauthorizedException("비활성화된 사용자입니다.")

    try:
        access_token, expires_in = create_access_token(users.users_seq)
        refresh_token = create_refresh_token(users.users_seq)

        white_key = f"auth:white:{users.users_seq}"
        black_key = f"auth:black:{users.users_seq}"
        redis_client = await RedisClient.get_client()
        previous_token = await redis_client.get(white_key)

        pipe = redis_client.pipeline()
        if previous_token is not None:
            await pipe.set(black_key, previous_token, ex=BLACKLIST_TTL_SECONDS)
        await pipe.set(white_key, access_token, ex=ACCESS_TOKEN_TTL_SECONDS)
        await pipe.execute()
    except Exception as e:
        raise ServerException(f"토큰 재발급 중 오류가 발생했습니다: {str(e)}")

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )
