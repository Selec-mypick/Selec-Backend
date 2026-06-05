from pydantic import BaseModel, Field


class CreateVoteRequest(BaseModel):
    question_seq: int = Field(..., gt=0, description="질문 시퀀스", example=1)
    options_seq: int = Field(..., gt=0, description="선택지 시퀀스", example=1)


class DeleteVoteRequest(BaseModel):
    question_seq: int = Field(..., gt=0, description="질문 시퀀스", example=1)
