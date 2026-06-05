from datetime import datetime

from pydantic import BaseModel


class GetOptionResponse(BaseModel):
    options_seq: int
    question_seq: int
    content: str
    active: bool
    created_at: datetime
    updated_at: datetime
