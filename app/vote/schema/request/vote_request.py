from pydantic import BaseModel, Field


class CreateVoteRequest(BaseModel):
    options_seq: int = Field(..., gt=0, description="선택지 시퀀스", example=1)
