from datetime import datetime

from pydantic import BaseModel

from app.options.schema.response.options_response import GetOptionResponse


class GetQuestionResponse(BaseModel):
    question_seq: int
    user_seq: int
    title: str
    description: str | None
    is_multiple: bool
    is_anonymous: bool
    status: str
    active: bool
    created_at: datetime
    updated_at: datetime
    options: list[GetOptionResponse]
