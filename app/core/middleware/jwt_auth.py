from typing import Iterable

from fastapi.responses import JSONResponse
from jose import jwt
from app.auth.domain.token_domain import get_white_token, is_token_blacklisted
from app.base.response import BaseResponse
from app.core.exceptions import BaseAPIException, ErrorCode
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
                raise BaseAPIException(ErrorCode.AUTH_HEADER_REQUIRED)
            if not auth_header.startswith("Bearer "):
                raise BaseAPIException(ErrorCode.AUTH_HEADER_INVALID_FORMAT)

            token = auth_header[7:].strip()
            try:
                payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            except jwt.ExpiredSignatureError:
                raise BaseAPIException(ErrorCode.ACCESS_TOKEN_EXPIRED)
            except jwt.JWTError as e:
                raise BaseAPIException(
                    ErrorCode.ACCESS_TOKEN_INVALID,
                    message=f"{ErrorCode.ACCESS_TOKEN_INVALID.message}: {str(e)}",
                )

            users_seq = payload.get("users_seq") or payload.get("sub")
            if not users_seq:
                raise BaseAPIException(ErrorCode.ACCESS_TOKEN_MISSING_USER)

            whitelisted_token = await get_white_token(users_seq)

            if whitelisted_token is None:
                raise BaseAPIException(ErrorCode.ACCESS_TOKEN_NOT_WHITELISTED)
            if whitelisted_token != token:
                raise BaseAPIException(ErrorCode.ACCESS_TOKEN_WHITELIST_MISMATCH)
            if await is_token_blacklisted(token):
                raise BaseAPIException(ErrorCode.ACCESS_TOKEN_BLACKLISTED)

            scope.setdefault("state", {})["users_seq"] = users_seq
            await self.app(scope, receive, send)

        except BaseAPIException as e:
            await JSONResponse(
                status_code=e.status_code,
                content=BaseResponse.of_fail(e.status_code, e.code, e.message).to_content(),
            )(scope, receive, send)
