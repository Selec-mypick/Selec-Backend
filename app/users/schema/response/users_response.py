from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.users.models.users import Users


class GetMyInfoResponse(BaseModel):
    google_id: str
    nick_name: str | None
    email: str | None
    name: str | None
    profile_image: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, users: "Users") -> "GetMyInfoResponse":
        return cls(
            google_id=users.google_id,
            nick_name=users.nick_name,
            email=users.email,
            name=users.name,
            profile_image=users.profile_image,
            created_at=users.created_at,
            updated_at=users.updated_at,
        )


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
