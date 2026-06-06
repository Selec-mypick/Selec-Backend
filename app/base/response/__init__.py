"""Common API response package."""

from app.base.response.base_response import BaseResponse
from app.base.response.openapi_responses import (
    AUTH_RESPONSES,
    AUTHENTICATED_RESPONSES,
    ERROR_500,
    QUESTION_READ_RESPONSES,
    QUESTION_WRITE_RESPONSES,
    REFRESH_TOKEN_RESPONSES,
    VOTE_RESPONSES,
)

__all__ = [
    "AUTH_RESPONSES",
    "AUTHENTICATED_RESPONSES",
    "BaseResponse",
    "ERROR_500",
    "QUESTION_READ_RESPONSES",
    "QUESTION_WRITE_RESPONSES",
    "REFRESH_TOKEN_RESPONSES",
    "VOTE_RESPONSES",
]
