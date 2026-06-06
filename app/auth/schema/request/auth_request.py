from pydantic import BaseModel, Field


class GoogleOAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1, description="Google Sign-In SDK에서 발급받은 id_token")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="재발급에 사용할 refresh token")
