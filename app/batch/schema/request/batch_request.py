from pydantic import BaseModel, Field


class GeminiPromptRequest(BaseModel):
    model: str | None = Field(None, description="사용할 Gemini 모델. 미입력 시 설정값을 사용합니다.")
