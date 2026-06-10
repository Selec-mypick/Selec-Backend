from typing import Any, Generic, Optional, TypeVar

from pydantic.generics import GenericModel

from app.base.constants import BaseUtil

T = TypeVar("T")


class BaseResponse(GenericModel, Generic[T]):
    status: int
    code: str
    message: str
    data: Optional[T] = None

    class Config:
        schema_extra = {
            "example": {
                "status": 200,
                "code": BaseUtil.SUCCESS_CODE,
                "message": BaseUtil.SUCCESS,
                "data": None,
            }
        }

    @classmethod
    def of_success(cls, status: int, data: Optional[T] = None) -> "BaseResponse[T]":
        return cls(status=status, code=BaseUtil.SUCCESS_CODE, message=BaseUtil.SUCCESS, data=data)

    @classmethod
    def of_fail(cls, status: int, code: str, message: str) -> "BaseResponse[T]":
        return cls(status=status, code=code, message=message, data=None)

    def to_content(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "code": self.code,
            "message": self.message,
            "data": self.data,
        }
