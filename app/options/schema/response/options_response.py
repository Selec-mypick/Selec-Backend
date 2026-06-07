from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.options.models.options import Options


class GetOptionResponse(BaseModel):
    options_seq: int
    question_seq: int
    content: str
    active: bool
    created_at: datetime
    updated_at: datetime
    vote_count: int | None = None

    @classmethod
    def from_entity(
            cls,
            option: "Options",
            vote_count: int | None = None,
    ) -> "GetOptionResponse":
        return cls(
            options_seq=option.options_seq,
            question_seq=option.question_seq,
            content=option.content,
            active=option.active,
            created_at=option.created_at,
            updated_at=option.updated_at,
            vote_count=vote_count,
        )
