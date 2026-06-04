from pydantic import BaseModel, Field


class SendEmailVerificationRequest(BaseModel):
    email: str = Field(..., description="인증번호를 받을 이메일 주소", example="user@example.com")


class VerifyEmailCodeRequest(BaseModel):
    email: str = Field(..., description="인증번호를 받은 이메일 주소", example="user@example.com")
    verification_code: str = Field(..., description="인증번호", example="123456", min_length=6, max_length=6)

