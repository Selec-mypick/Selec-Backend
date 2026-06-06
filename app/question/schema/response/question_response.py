from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.options.schema.response.options_response import GetOptionResponse

if TYPE_CHECKING:
    from app.options.models.options import Options
    from app.question.models.question import Question


class CreateQuestionResponse(BaseModel):
    question_seq: int


class GetQuestionResponse(BaseModel):
    question_seq: int
    title: str
    description: str | None
    is_anonymous: bool
    status: str
    active: bool
    version: int
    created_at: datetime
    updated_at: datetime
    voted_options_seq: int | None = None
    options: list[GetOptionResponse]

    @classmethod
    def from_entity(
            cls,
            question: "Question",
            options: list["Options"],
            voted_options_seq: int | None = None,
            vote_counts: dict[int, int] | None = None,
    ) -> "GetQuestionResponse":
        return cls(
            question_seq=question.question_seq,
            title=question.title,
            description=question.description,
            is_anonymous=question.is_anonymous,
            status=question.status,
            active=question.active,
            version=question.version,
            created_at=question.created_at,
            updated_at=question.updated_at,
            voted_options_seq=voted_options_seq,
            options=[
                GetOptionResponse.from_entity(
                    option,
                    vote_count=vote_counts.get(option.options_seq) if vote_counts else None,
                    is_selected=option.options_seq == voted_options_seq if voted_options_seq is not None else None,
                )
                for option in options
            ],
        )

    @classmethod
    def from_detail_rows(
            cls,
            question: "Question",
            option_rows: list[tuple["Options", int, bool]],
    ) -> "GetQuestionResponse":
        voted_options_seq = next(
            (
                option.options_seq
                for option, _, is_selected in option_rows
                if is_selected
            ),
            None,
        )

        return cls(
            question_seq=question.question_seq,
            title=question.title,
            description=question.description,
            is_anonymous=question.is_anonymous,
            status=question.status,
            active=question.active,
            version=question.version,
            created_at=question.created_at,
            updated_at=question.updated_at,
            voted_options_seq=voted_options_seq,
            options=[
                GetOptionResponse.from_entity(
                    option,
                    vote_count=vote_count,
                    is_selected=is_selected,
                )
                for option, vote_count, is_selected in option_rows
            ],
        )
