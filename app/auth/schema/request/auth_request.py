from pydantic import BaseModel, Field


class GoogleOAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1, description="Google Sign-In SDK에서 발급받은 id_token")


class DeviceAuthRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=121, description="웹 익명 사용자를 식별하는 device_id")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="재발급에 사용할 refresh token")


class IssueTestTokenRequest(BaseModel):
    users_seq: str = Field(..., min_length=1, description="테스트 토큰을 발급할 사용자 시퀀스")
