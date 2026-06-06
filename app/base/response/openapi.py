from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    status: int = Field(..., description="HTTP 상태 코드")
    message: str = Field(..., description="에러 메시지")
    data: None = Field(None, description="에러 응답 데이터")


def _error(status: int, message: str, description: str) -> dict:
    return {
        "description": description,
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "status": status,
                    "message": message,
                    "data": None,
                }
            }
        },
    }


ERROR_400 = _error(400, "잘못된 요청입니다.", "Bad Request")
ERROR_401 = _error(401, "인증이 필요합니다.", "Unauthorized")
ERROR_403 = _error(403, "접근 권한이 없습니다.", "Forbidden")
ERROR_404 = _error(404, "리소스를 찾을 수 없습니다.", "Not Found")
ERROR_409 = _error(409, "리소스 충돌이 발생했습니다.", "Conflict")
ERROR_422 = _error(422, "요청 값이 올바르지 않습니다.", "Validation Error")
ERROR_500 = _error(500, "내부 서버 오류가 발생했습니다.", "Internal Server Error")

AUTH_RESPONSES = {
    400: ERROR_400,
    422: ERROR_422,
    500: ERROR_500,
}

REFRESH_TOKEN_RESPONSES = {
    401: ERROR_401,
    422: ERROR_422,
    500: ERROR_500,
}

AUTHENTICATED_RESPONSES = {
    400: ERROR_400,
    401: ERROR_401,
    403: ERROR_403,
    422: ERROR_422,
    500: ERROR_500,
}

QUESTION_READ_RESPONSES = {
    **AUTHENTICATED_RESPONSES,
    404: ERROR_404,
    500: ERROR_500,
}

QUESTION_WRITE_RESPONSES = {
    **AUTHENTICATED_RESPONSES,
    404: ERROR_404,
    409: ERROR_409,
}

VOTE_RESPONSES = {
    **AUTHENTICATED_RESPONSES,
    404: ERROR_404,
}
