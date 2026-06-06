from pydantic import BaseModel, Field


class UpdateMyInfoRequest(BaseModel):
    nick_name: str = Field(..., min_length=1, max_length=20, description="사용자 닉네임", example="selec_user")
