import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from app.auth.schema.request.google_oauth_request import GoogleOAuthRequest
from app.auth.schema.response.auth_response import AuthTokenResponse
from app.auth.domain.token_domain import create_access_token, create_refresh_token
from app.core.exception import BadRequestException, ServerException
from app.core.redis_config import RedisClient
from app.users.dependency.dependency import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.users.repository.users_repository import UsersRepository

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
ACCESS_TOKEN_TTL_SECONDS = ACCESS_TOKEN_EXPIRE_MINUTES * 60
BLACKLIST_TTL_SECONDS = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


async def authenticate_google(request: GoogleOAuthRequest, db: AsyncSession) -> AuthTokenResponse:
    async with aiohttp.ClientSession() as session:
        async with session.get(
                GOOGLE_TOKENINFO_URL,
                params={"id_token": request.id_token},
        ) as response:
            google_user = await response.json()
            if response.status != 200:
                message = google_user.get("error_description") or google_user.get("error") or "Google id_token 검증 실패"
                raise BadRequestException(message)

    if google_user.get("aud") != settings.google_client_id:
        raise BadRequestException("Google id_token audience가 일치하지 않습니다.")

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

        previous_token = await redis_client.get(white_key)
        pipe = redis_client.pipeline()
        if previous_token is not None:
            pipe.set(black_key, previous_token, ex=BLACKLIST_TTL_SECONDS)
        pipe.set(white_key, access_token, ex=ACCESS_TOKEN_TTL_SECONDS)
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
        expires_in=expires_in
    )
