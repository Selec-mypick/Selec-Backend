from pydantic import BaseModel, Field
from typing import List


class GeminiPromptResponse(BaseModel):
    model: str = Field(..., description="사용한 Gemini 모델")
    title: str = Field(..., description="투표 제목")
    description: str = Field(..., description="투표 설명")
    is_anonymous: bool = Field(..., description="익명 여부")
    options: List[str] = Field(..., description="투표 선택지")