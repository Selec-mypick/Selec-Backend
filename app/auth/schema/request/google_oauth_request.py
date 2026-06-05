from pydantic import BaseModel, Field


class GoogleOAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1, description="Google Sign-In SDK에서 발급받은 id_token")
