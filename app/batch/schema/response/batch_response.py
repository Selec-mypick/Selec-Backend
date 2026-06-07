from pydantic import BaseModel


class GeminiPromptResponse(BaseModel):
    model: str
    text: str
