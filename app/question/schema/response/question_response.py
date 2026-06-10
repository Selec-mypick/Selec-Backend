from datetime import datetime

from pydantic import BaseModel, Field


class QuestionOptionResponse(BaseModel):
    options_seq: int
    question_seq: str
    content: str
    percentage: float | None = Field(default=None, description="득표율")


class CreateQuestionResponse(BaseModel):
    question_seq: str
    share_url: str


class UpdateQuestionResponse(BaseModel):
    version: int


class GetQuestionResponse(BaseModel):
    question_seq: str
    share_url: str
    title: str
    description: str | None
    status: str
    version: int
    is_creator: bool
    created_at: datetime
    updated_at: datetime
    selected_option_seq: int | None = None
    options: list[QuestionOptionResponse]

    @classmethod
    def from_detail_dto(cls, detail, users_seq: str) -> "GetQuestionResponse":
        selected_option_seq = next(
            (
                row.selected_option_seq
                for row in detail.option_rows
                if row.selected_option_seq is not None
            ),
            None,
        )
        is_creator = detail.question.users_seq == users_seq
        can_view_percentage = is_creator or selected_option_seq is not None
        total_vote_count = sum(row.vote_count for row in detail.option_rows)

        return cls(
            question_seq=detail.question.question_seq,
            share_url=detail.question.share_url,
            title=detail.question.title,
            description=detail.question.description,
            status=detail.question.status,
            version=detail.question.version,
            is_creator=is_creator,
            created_at=detail.question.created_at,
            updated_at=detail.question.updated_at,
            selected_option_seq=selected_option_seq,
            options=[
                QuestionOptionResponse(
                    options_seq=row.option.options_seq,
                    question_seq=row.option.question_seq,
                    content=row.option.content,
                    percentage=(
                        _calculate_percentage(row.vote_count, total_vote_count)
                        if can_view_percentage
                        else None
                    ),
                )
                for row in detail.option_rows
            ],
        )


def _calculate_percentage(vote_count: int, total_vote_count: int) -> float:
    if total_vote_count == 0:
        return 0.0
    return round((vote_count / total_vote_count) * 100, 1)
