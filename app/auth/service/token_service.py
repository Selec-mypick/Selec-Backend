from jose import jwt, JWTError

from app.auth.domain.token_domain import create_access_token, create_refresh_token
from app.auth.schema.response.auth_response import AuthTokenResponse
from app.auth.service.token_scripts import ROTATE_ACCESS_TOKEN_SCRIPT
from app.core.cache import RedisClient
from app.core.exceptions import ServerException, UnauthorizedException
from config import settings


class AuthTokenIssuer:
    async def issue(self, users_seq: str, *, rotate_previous: bool = True) -> AuthTokenResponse:
        access_token, expires_in = create_access_token(users_seq)
        refresh_token = create_refresh_token(users_seq)

        try:
            await self.store_access_token(users_seq, access_token, rotate_previous=rotate_previous)
        except Exception as e:
            raise ServerException(f"토큰 저장 중 오류가 발생했습니다: {str(e)}")

        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    async def store_access_token(
            self,
            users_seq: str,
            access_token: str,
            *,
            rotate_previous: bool = True,
    ) -> None:
        white_key = f"auth:white:{users_seq}"
        redis_client = await RedisClient.get_client()

        if not rotate_previous:
            await redis_client.set(white_key, access_token, ex=settings.access_token_ttl_seconds)
            return

        black_key = f"auth:black:{users_seq}"
        await redis_client.eval(
            ROTATE_ACCESS_TOKEN_SCRIPT,
            2,
            white_key,
            black_key,
            access_token,
            settings.access_token_ttl_seconds,
            settings.refresh_token_ttl_seconds,
        )

    def decode_refresh_token(self, refresh_token: str) -> str:
        try:
            payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("refresh token이 만료되었습니다.")
        except JWTError:
            raise UnauthorizedException("유효하지 않은 refresh token입니다.")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("refresh token이 아닙니다.")

        users_seq = payload.get("users_seq") or payload.get("sub")
        if not users_seq:
            raise UnauthorizedException("refresh token에 사용자 정보가 없습니다.")

        return users_seq


auth_token_issuer = AuthTokenIssuer()
