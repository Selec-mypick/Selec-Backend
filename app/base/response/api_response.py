from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, ConfigDict
from app.base.constants import BaseUtil

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": 200,
                "code": BaseUtil.SUCCESS_CODE,
                "message": BaseUtil.SUCCESS,
                "data": None,
            }
        }
    )

    status: int
    code: str
    message: str
    data: Optional[T] = None

    @classmethod
    def of_success(cls, status: int, data: Optional[T] = None) -> "BaseResponse[T]":
        return cls(status=status, code=BaseUtil.SUCCESS_CODE, message=BaseUtil.SUCCESS, data=data)

    @classmethod
    def of_fail(cls, status: int, code: str, message: str) -> "BaseResponse[T]":
        return cls(status=status, code=code, message=message, data=None)
