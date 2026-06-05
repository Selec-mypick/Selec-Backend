from pydantic import BaseModel, Field, root_validator


class GoogleOAuthRequest(BaseModel):
    id_token: str | None = Field(None, description="Google Sign-In SDK에서 발급받은 id_token")
    code: str | None = Field(None, description="Google authorization code")
    redirect_uri: str | None = Field(None, description="code 교환 시 사용할 redirect URI")

    @root_validator
    def validate_oauth_credentials(cls, values):
        id_token = values.get("id_token")
        code = values.get("code")
        if not id_token and not code:
            raise ValueError("id_token 또는 code 중 하나는 필수입니다.")
        if id_token and code:
            raise ValueError("id_token과 code는 동시에 전달할 수 없습니다.")
        if code and not values.get("redirect_uri"):
            raise ValueError("code 사용 시 redirect_uri는 필수입니다.")
        return values
