from typing import Iterable

from fastapi.responses import JSONResponse
from jose import jwt
from app.auth.domain.token_domain import get_white_token, is_token_blacklisted
from app.base.response import BaseResponse
from app.core.exceptions import UnauthorizedException
from config import settings


class JWTAuthMiddleware:
    def __init__(self, app, allow_paths: Iterable[str] | None = None) -> None:
        self.app = app
        self.allow_paths = set(allow_paths or [])
        self.allow_prefixes = tuple(path[:-3] for path in self.allow_paths if path.endswith("/**"))

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if (path in self.allow_paths
                or path.startswith(("/docs", "/openapi"))
                or any(path.startswith(prefix) for prefix in self.allow_prefixes)):
            await self.app(scope, receive, send)
            return

        try:
            auth_header = next(
                (value.decode() for key, value in scope.get("headers", []) if key.decode().lower() == "authorization"),
                None,
            )
            if not auth_header:
                raise UnauthorizedException("Authorization 헤더가 필요합니다.")
            if not auth_header.startswith("Bearer "):
                raise UnauthorizedException("Authorization 헤더 형식이 올바르지 않습니다. 'Bearer {token}' 형식이어야 합니다.")

            token = auth_header[7:].strip()
            try:
                payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            except jwt.ExpiredSignatureError:
                raise UnauthorizedException("토큰이 만료되었습니다. 토큰을 재발급해주세요.")
            except jwt.JWTError as e:
                raise UnauthorizedException(f"토큰 형식이 잘못되었거나 유효하지 않습니다: {str(e)}")

            users_seq = payload.get("users_seq") or payload.get("sub")
            if not users_seq:
                raise UnauthorizedException("토큰에 사용자 정보가 없습니다(users_seq).")

            whitelisted_token = await get_white_token(users_seq)

            if whitelisted_token is None:
                raise UnauthorizedException("토큰이 whitelist에 등록되어 있지 않습니다. 로그인이 필요합니다.")
            if whitelisted_token != token:
                raise UnauthorizedException("토큰이 whitelist에 등록된 토큰과 일치하지 않습니다. 토큰이 재발급되었을 수 있습니다.")
            if await is_token_blacklisted(token):
                raise UnauthorizedException("이미 무효화된 토큰입니다. 토큰이 재발급되어 이전 토큰은 사용할 수 없습니다.")

            scope.setdefault("state", {})["users_seq"] = users_seq
            await self.app(scope, receive, send)

        except UnauthorizedException as e:
            await JSONResponse(
                status_code=e.status_code,
                content=BaseResponse.of_fail(e.status_code, e.message).dict(),
            )(scope, receive, send)
