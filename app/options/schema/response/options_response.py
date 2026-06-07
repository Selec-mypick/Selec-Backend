from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.options.models.options import Options


class GetOptionResponse(BaseModel):
    options_seq: int
    question_seq: int
    content: str
    vote_count: int | None = None

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        if data.get("vote_count") is None:
            data.pop("vote_count", None)
        return data

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
            vote_count=vote_count,
        )
