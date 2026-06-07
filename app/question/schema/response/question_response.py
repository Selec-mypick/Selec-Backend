from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.options.models.options import Options
    from app.question.models.question import Question
    from app.users.models.users import Users


class CreateQuestionResponse(BaseModel):
    question_seq: int


class UpdateQuestionResponse(BaseModel):
    version: int


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
    options: list[dict]

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
                {
                    **{
                        "options_seq": option.options_seq,
                        "question_seq": option.question_seq,
                        "content": option.content,
                    },
                    **(
                        {"vote_count": vote_counts[option.options_seq]}
                        if vote_counts and option.options_seq in vote_counts
                        else {}
                    ),
                }
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
        is_creator = question.users_seq == users_seq
        can_view_vote_count = is_creator or selected_option_seq is not None

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
                {
                    **{
                        "options_seq": option.options_seq,
                        "question_seq": option.question_seq,
                        "content": option.content,
                    },
                    **({"vote_count": vote_count} if can_view_vote_count else {}),
                }
                for option, vote_count, _ in option_rows
            ],
        )


class GetQuestionVoteResultResponse(BaseModel):
    options: list[dict]

    @classmethod
    def from_result_rows(
            cls,
            option_rows: list[tuple["Options", Optional["Users"]]],
    ) -> "GetQuestionVoteResultResponse":
        options_by_seq: dict[int, dict] = {}

        for option, voter in option_rows:
            if option.options_seq not in options_by_seq:
                options_by_seq[option.options_seq] = {
                    "options_seq": option.options_seq,
                    "content": option.content,
                    "vote_count": 0,
                    "voters": [],
                }

            if voter is not None:
                result_option = options_by_seq[option.options_seq]
                result_option["voters"].append({
                    "google_id": voter.google_id,
                    "nick_name": voter.nick_name,
                    "email": voter.email,
                    "name": voter.name,
                    "profile_image": voter.profile_image,
                })
                result_option["vote_count"] += 1

        return cls(
            options=list(options_by_seq.values()),
        )
