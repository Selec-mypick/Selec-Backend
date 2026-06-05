from pydantic import BaseModel, Field


class UpdateOptionRequest(BaseModel):
    options_seq: int | None = Field(None, gt=0, description="기존 선택지 시퀀스", example=1)
    content: str = Field(..., min_length=1, max_length=1024, description="선택지 내용", example="김치찌개")
