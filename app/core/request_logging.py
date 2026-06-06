import json
import logging
from typing import Any, Optional
from uuid import uuid4

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging_config import request_id_context


logger = logging.getLogger("app.request")

BODY_LOG_LIMIT = 4096
LOGGED_REQUEST_HEADERS = {"user-agent", "content-type"}
LOGGED_RESPONSE_HEADERS = {"content-type"}
SYSTEM_PATHS = {"/actuator/health", "/openapi.json", "/docs", "/redoc"}


def body_to_log(body: bytes, content_type: Optional[str], truncated: bool = False) -> Any:
    if not body:
        return None

    content_type = (content_type or "").lower()
    if (
        content_type
        and "application/json" not in content_type
        and "application/x-www-form-urlencoded" not in content_type
        and not content_type.startswith("text/")
    ):
        return {"omitted": True, "content_type": content_type}

    text = body.decode("utf-8", errors="replace")

    if "application/json" in content_type:
        try:
            text = json.loads(text)
        except json.JSONDecodeError:
            pass

    if truncated:
        return {"truncated": True, "body": text}
    return text


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        request_headers = Headers(scope=scope)
        request_id = request_headers.get("X-Request-ID") or str(uuid4())
        token = request_id_context.set(request_id)

        request_body: list[bytes] = []
        response_body: list[bytes] = []
        request_body_size = 0
        response_body_size = 0
        request_body_truncated = False
        response_body_truncated = False
        response_status_code = 500
        response_headers = Headers()

        async def receive_wrapper() -> Message:
            nonlocal request_body_size, request_body_truncated

            message = await receive()
            if message["type"] == "http.request":
                chunk = message.get("body", b"")
                if chunk and request_body_size < BODY_LOG_LIMIT:
                    remaining = BODY_LOG_LIMIT - request_body_size
                    request_body.append(chunk[:remaining])
                    request_body_size += len(chunk[:remaining])
                    request_body_truncated = len(chunk) > remaining
                elif chunk:
                    request_body_truncated = True
            return message

        async def send_wrapper(message: Message) -> None:
            nonlocal response_body_size
            nonlocal response_body_truncated
            nonlocal response_status_code
            nonlocal response_headers

            if message["type"] == "http.response.start":
                response_status_code = message["status"]
                raw_headers = list(message.get("headers", []))
                raw_headers.append((b"x-request-id", request_id.encode("utf-8")))
                message["headers"] = raw_headers
                response_headers = Headers(raw=raw_headers)

            if message["type"] == "http.response.body":
                chunk = message.get("body", b"")
                if chunk and response_body_size < BODY_LOG_LIMIT:
                    remaining = BODY_LOG_LIMIT - response_body_size
                    response_body.append(chunk[:remaining])
                    response_body_size += len(chunk[:remaining])
                    response_body_truncated = len(chunk) > remaining
                elif chunk:
                    response_body_truncated = True

            await send(message)

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        finally:
            request = {
                "method": scope["method"],
                "path": path,
                "query": scope["query_string"].decode("utf-8", errors="replace"),
                "headers": {
                    key: value
                    for key, value in request_headers.items()
                    if key.lower() in LOGGED_REQUEST_HEADERS
                },
                "client_ip": scope["client"][0] if scope.get("client") else None,
                "body": None if path in SYSTEM_PATHS else body_to_log(
                    b"".join(request_body),
                    request_headers.get("content-type"),
                    request_body_truncated,
                ),
            }
            response = {
                "status_code": response_status_code,
                "headers": {
                    key: value
                    for key, value in response_headers.items()
                    if key.lower() in LOGGED_RESPONSE_HEADERS
                },
                "body": None if path in SYSTEM_PATHS else body_to_log(
                    b"".join(response_body),
                    response_headers.get("content-type"),
                    response_body_truncated,
                ),
            }

            if response_status_code >= 400:
                logger.error(
                    "",
                    extra={
                        "request_id": request_id,
                        "request": request,
                        "response": response,
                    },
                )
            else:
                logger.info(
                    "",
                    extra={
                        "request_id": request_id,
                        "request": request,
                        "response": response,
                    },
                )
            request_id_context.reset(token)
