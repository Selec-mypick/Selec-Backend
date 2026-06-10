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


class MyQuestionResponse(BaseModel):
    question_seq: str
    share_url: str
    title: str
    description: str | None
    version: int
    vote_count: int
    created_at: datetime

    @classmethod
    def from_entity(cls, question, vote_count: int) -> "MyQuestionResponse":
        return cls(
            question_seq=question.question_seq,
            share_url=question.share_url,
            title=question.title,
            description=question.description,
            version=question.version,
            vote_count=int(vote_count),
            created_at=question.created_at,
        )


class GetQuestionResponse(BaseModel):
    question_seq: str
    share_url: str
    title: str
    description: str | None
    version: int
    is_creator: bool
    vote_count: int | None = Field(default=None, description="전체 투표자 수")
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
            version=detail.question.version,
            is_creator=is_creator,
            vote_count=total_vote_count if is_creator else None,
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
