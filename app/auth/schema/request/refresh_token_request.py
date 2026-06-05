from pydantic import BaseModel, Field


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="재발급에 사용할 refresh token")
