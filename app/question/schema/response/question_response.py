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
    version: int
    is_creator: bool
    created_at: datetime
    updated_at: datetime
    selected_option_seq: int | None = None
    options: list[GetOptionResponse]

    @classmethod
    def from_entity(
            cls,
            question: "Question",
            options: list["Options"],
            is_creator: bool,
            selected_option_seq: int | None = None,
            vote_counts: dict[int, int] | None = None,
    ) -> "GetQuestionResponse":
        return cls(
            question_seq=question.question_seq,
            title=question.title,
            description=question.description,
            is_anonymous=question.is_anonymous,
            status=question.status,
            version=question.version,
            is_creator=is_creator,
            created_at=question.created_at,
            updated_at=question.updated_at,
            selected_option_seq=selected_option_seq,
            options=[
                GetOptionResponse.from_entity(
                    option,
                    vote_count=vote_counts.get(option.options_seq) if vote_counts else None,
                )
                for option in options
            ],
        )

    @classmethod
    def from_detail_rows(
            cls,
            question: "Question",
            option_rows: list[tuple["Options", int, int | None]],
            users_seq: str,
    ) -> "GetQuestionResponse":
        selected_option_seq = next(
            (
                option_seq
                for _, _, option_seq in option_rows
                if option_seq is not None
            ),
            None,
        )

        return cls(
            question_seq=question.question_seq,
            title=question.title,
            description=question.description,
            is_anonymous=question.is_anonymous,
            status=question.status,
            version=question.version,
            is_creator=question.users_seq == users_seq,
            created_at=question.created_at,
            updated_at=question.updated_at,
            selected_option_seq=selected_option_seq,
            options=[
                GetOptionResponse.from_entity(
                    option,
                    vote_count=vote_count,
                )
                for option, vote_count, _ in option_rows
            ],
        )
