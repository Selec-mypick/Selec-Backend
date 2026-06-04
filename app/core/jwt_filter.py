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

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        # allow_paths에 있는 경로 또는 특정 경로로 시작하는 경우 통과
        if path in self.allow_paths:
            await self.app(scope, receive, send)
            return

        # 와일드카드 패턴 처리: /auth/** 또는 /sms/** 같은 패턴
        for allowed_path in self.allow_paths:
            if allowed_path.endswith("/**"):
                prefix = allowed_path[:-3]  # /** 제거
                if path.startswith(prefix):
                    await self.app(scope, receive, send)
                    return

        # 기본 허용 경로들
        if (path.startswith("/docs") or
            path.startswith("/openapi") or
            path.startswith("/auth") or
            path.startswith("/actuator")):
            await self.app(scope, receive, send)
            return

        headers = dict((k.decode().lower(), v.decode()) for k, v in scope.get("headers", []))
        auth_header = headers.get("authorization")
        if not auth_header:
            resp = JSONResponse(status_code=401, content={"status": 401, "message": "Authorization 헤더가 필요합니다.", "data": None})
            await resp(scope, receive, send)
            return

        if not auth_header.startswith("Bearer "):
            resp = JSONResponse(status_code=401, content={"status": 401, "message": "Authorization 헤더 형식이 올바르지 않습니다. 'Bearer {token}' 형식이어야 합니다.", "data": None})
            await resp(scope, receive, send)
            return

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            sub = payload.get("sub")
            if not sub:
                raise JWTError("sub 누락")

            user_seq = int(sub)

            try:
                redis_client = await RedisClient.get_client()
                white_key = f"auth:white:{user_seq}"
                whitelisted_token = await redis_client.get(white_key)
                if whitelisted_token is None:
                    resp = JSONResponse(status_code=401, content={"status": 401, "message": "토큰이 whitelist에 등록되어 있지 않습니다. 로그인이 필요합니다.", "data": None})
                    await resp(scope, receive, send)
                    return
                if whitelisted_token != token:
                    resp = JSONResponse(status_code=401, content={"status": 401, "message": "토큰이 whitelist에 등록된 토큰과 일치하지 않습니다. 토큰이 재발급되었을 수 있습니다.", "data": None})
                    await resp(scope, receive, send)
                    return
            except Exception as e:
                resp = JSONResponse(status_code=401, content={"status": 401, "message": f"토큰 whitelist 확인 중 오류가 발생했습니다: {str(e)}", "data": None})
                await resp(scope, receive, send)
                return

            try:
                redis_client = await RedisClient.get_client()
                black_key = f"auth:black:{user_seq}"
                blacklisted_token = await redis_client.get(black_key)
                if blacklisted_token == token:
                    resp = JSONResponse(status_code=401, content={"status": 401, "message": "이미 무효화된 토큰입니다. 토큰이 재발급되어 이전 토큰은 사용할 수 없습니다.", "data": None})
                    await resp(scope, receive, send)
                    return
            except Exception:
                pass

            request = Request(scope, receive=receive)
            request.state.user_seq = user_seq
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
            token = authorization.split(" ", 1)[1].strip()

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise UnauthorizedException("토큰에 사용자 정보가 없습니다(sub).")
        return int(sub)
    except Exception as e:
        raise ServerException(f"토큰 파싱 실패: {e}")
