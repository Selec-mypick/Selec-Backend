from pydantic import BaseModel


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class CreateTestUserResponse(AuthTokenResponse):
    users_seq: int
    google_id: str
    nick_name: str | None
    email: str | None
    name: str | None
    profile_image: str | None
