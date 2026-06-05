from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.options.schema.response.options_response import GetOptionResponse

if TYPE_CHECKING:
    from app.options.models.options import Options
    from app.question.models.question import Question


class GetQuestionResponse(BaseModel):
    question_seq: int
    user_seq: int
    title: str
    description: str | None
    is_multiple: bool
    is_anonymous: bool
    status: str
    active: bool
    version: int
    created_at: datetime
    updated_at: datetime
    options: list[GetOptionResponse]

    @classmethod
    def from_entity(cls, question: "Question", options: list["Options"]) -> "GetQuestionResponse":
        return cls(
            question_seq=question.question_seq,
            user_seq=question.user_seq,
            title=question.title,
            description=question.description,
            is_multiple=question.is_multiple,
            is_anonymous=question.is_anonymous,
            status=question.status,
            active=question.active,
            version=question.version,
            created_at=question.created_at,
            updated_at=question.updated_at,
            options=[
                GetOptionResponse.from_entity(option)
                for option in options
            ],
        )
