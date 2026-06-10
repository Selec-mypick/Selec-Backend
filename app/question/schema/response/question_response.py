from datetime import datetime

from pydantic import BaseModel, Field


class QuestionOptionResponse(BaseModel):
    options_seq: int
    question_seq: str
    content: str
    vote_count: int | None = Field(default=None, description="투표 수")


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
    def from_entity(
            cls,
            question,
            options: list,
            is_creator: bool,
            selected_option_seq: int | None = None,
            vote_counts: dict[int, int] | None = None,
    ) -> "GetQuestionResponse":
        return cls(
            question_seq=question.question_seq,
            share_url=question.share_url,
            title=question.title,
            description=question.description,
            status=question.status,
            version=question.version,
            is_creator=is_creator,
            created_at=question.created_at,
            updated_at=question.updated_at,
            selected_option_seq=selected_option_seq,
            options=[
                QuestionOptionResponse(
                    options_seq=option.options_seq,
                    question_seq=option.question_seq,
                    content=option.content,
                    vote_count=(
                        vote_counts.get(option.options_seq)
                        if vote_counts and option.options_seq in vote_counts
                        else None
                    ),
                )
                for option in options
            ],
        )

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
        can_view_vote_count = is_creator or selected_option_seq is not None

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
                    vote_count=row.vote_count if can_view_vote_count else None,
                )
                for row in detail.option_rows
            ],
        )
