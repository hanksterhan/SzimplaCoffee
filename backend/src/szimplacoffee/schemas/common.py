from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: int | None = None
    has_more: bool = False
