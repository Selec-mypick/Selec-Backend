from math import ceil
from typing import Generic, TypeVar

from pydantic.generics import GenericModel

T = TypeVar("T")


class PageResponse(GenericModel, Generic[T]):
    content: list[T]
    page: int
    size: int
    total_elements: int
    total_pages: int
    has_next: bool
    has_previous: bool
    first: bool
    last: bool

    @classmethod
    def of(cls, content: list[T], page: int, size: int, total_elements: int) -> "PageResponse[T]":
        total_pages = ceil(total_elements / size) if total_elements > 0 else 0
        return cls(
            content=content,
            page=page,
            size=size,
            total_elements=total_elements,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1 and total_pages > 0,
            first=page <= 1,
            last=page >= total_pages,
        )
