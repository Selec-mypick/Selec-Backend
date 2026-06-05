from typing import Iterable
from fastapi import Request, Header
from fastapi.responses import JSONResponse
from app.users.dependency.dependency import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from app.core.exception import UnauthorizedException, ServerException
from app.core.redis_config import RedisClient


class JWTAuthMiddleware:
    def __init__(self, app, allow_paths: Iterable[str] | None = None) -> None:
        self.app = app
        self.allow_paths = set(allow_paths or [])
        self.allow_prefixes = tuple(
            allowed_path[:-3]
            for allowed_path in self.allow_paths
            if allowed_path.endswith("/**")
        )

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self.allow_paths:
            await self.app(scope, receive, send)
            return

        for prefix in self.allow_prefixes:
            if path.startswith(prefix):
                await self.app(scope, receive, send)
                return

        if (path.startswith("/docs") or
            path.startswith("/openapi") or
            path.startswith("/auth") or
            path.startswith("/actuator")):
            await self.app(scope, receive, send)
            return

        auth_header = None
        for key, value in scope.get("headers", []):
            if key.decode().lower() == "authorization":
                auth_header = value.decode()
                break

        if not auth_header:
            resp = JSONResponse(status_code=401, content={"status": 401, "message": "Authorization 헤더가 필요합니다.", "data": None})
            await resp(scope, receive, send)
            return

        if not auth_header.startswith("Bearer "):
            resp = JSONResponse(status_code=401, content={"status": 401, "message": "Authorization 헤더 형식이 올바르지 않습니다. 'Bearer {token}' 형식이어야 합니다.", "data": None})
            await resp(scope, receive, send)
            return

        token = auth_header[7:].strip()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            users_seq = payload.get("users_seq") or payload.get("sub")
            if not users_seq:
                raise JWTError("users_seq 누락")

            users_seq = int(users_seq)

            try:
                redis_client = await RedisClient.get_client()
                white_key = f"auth:white:{users_seq}"
                black_key = f"auth:black:{users_seq}"
                whitelisted_token, blacklisted_token = await redis_client.mget(white_key, black_key)

                if whitelisted_token is None:
                    resp = JSONResponse(status_code=401, content={"status": 401, "message": "토큰이 whitelist에 등록되어 있지 않습니다. 로그인이 필요합니다.", "data": None})
                    await resp(scope, receive, send)
                    return
                if whitelisted_token != token:
                    resp = JSONResponse(status_code=401, content={"status": 401, "message": "토큰이 whitelist에 등록된 토큰과 일치하지 않습니다. 토큰이 재발급되었을 수 있습니다.", "data": None})
                    await resp(scope, receive, send)
                    return
                if blacklisted_token == token:
                    resp = JSONResponse(status_code=401, content={"status": 401, "message": "이미 무효화된 토큰입니다. 토큰이 재발급되어 이전 토큰은 사용할 수 없습니다.", "data": None})
                    await resp(scope, receive, send)
                    return
            except Exception as e:
                resp = JSONResponse(status_code=401, content={"status": 401, "message": f"토큰 whitelist 확인 중 오류가 발생했습니다: {str(e)}", "data": None})
                await resp(scope, receive, send)
                return

            request = Request(scope, receive=receive)
            request.state.users_seq = users_seq
            await self.app(scope, receive, send)
        except jwt.ExpiredSignatureError:
            resp = JSONResponse(status_code=401, content={"status": 401, "message": "토큰이 만료되었습니다. 토큰을 재발급해주세요.", "data": None})
            await resp(scope, receive, send)
            return
        except jwt.JWTError as e:
            resp = JSONResponse(status_code=401, content={"status": 401, "message": f"토큰 형식이 잘못되었거나 유효하지 않습니다: {str(e)}", "data": None})
            await resp(scope, receive, send)
            return
        except Exception as e:
            resp = JSONResponse(status_code=401, content={"status": 401, "message": f"토큰 검증 중 오류가 발생했습니다: {str(e)}", "data": None})
            await resp(scope, receive, send)
            return


async def get_user_seq(authorization: str = Header(None), token: str | None = None) -> int:
    try:
        if token is None:
            if not authorization or not authorization.startswith("Bearer "):
                raise UnauthorizedException("Authorization 헤더 누락 또는 형식 오류")
            token = authorization[7:].strip()

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        users_seq = payload.get("users_seq") or payload.get("sub")
        if not users_seq:
            raise UnauthorizedException("토큰에 사용자 정보가 없습니다(users_seq).")
        return int(users_seq)
    except Exception as e:
        raise ServerException(f"토큰 파싱 실패: {e}")
