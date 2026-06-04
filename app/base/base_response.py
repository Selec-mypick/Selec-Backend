from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from .base_util import BaseUtil

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    status: int
    message: str
    data: Optional[T] = None

    @classmethod
    def of_success(cls, status: int, data: T) -> "BaseResponse[T]":
        return cls(status=status, message=BaseUtil.SUCCESS, data=data)
    
    @classmethod
    def of_fail(cls, status: int, message: str) -> "BaseResponse[T]":
        return cls(status=status, message=message, data=None)
    
    @classmethod
    def of(cls, status: int, message: str, data: Optional[T] = None) -> "BaseResponse[T]":
        return cls(status=status, message=message, data=data)
