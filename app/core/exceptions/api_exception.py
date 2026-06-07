import logging
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from app.base.response import BaseResponse
from app.core.exceptions.error_code import ErrorCode

logger = logging.getLogger(__name__)


class BaseAPIException(Exception):
    def __init__(
            self,
            error_code: ErrorCode,
            *,
            message: str | None = None,
            details: Optional[dict] = None,
    ):
        self.error_code = error_code
        self.status_code = error_code.status_code
        self.code = error_code.code
        self.message = message or error_code.message
        self.details = details or {}
        super().__init__(self.message)


def setup_exception_handlers(app):
    @app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(exc: BaseAPIException):
        return JSONResponse(
            status_code=exc.status_code,
            content=BaseResponse.of_fail(exc.status_code, exc.code, exc.message).to_content(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unexpected exception occurred",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error": str(exc),
            },
            exc_info=True,
        )

        error = ErrorCode.INTERNAL_SERVER_ERROR
        return JSONResponse(
            status_code=error.status_code,
            content=BaseResponse.of_fail(error.status_code, error.code, error.message).to_content(),
        )
