from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    user_id: str = Field(..., description="사용자 ID", example="user123")
    password: str = Field(..., description="비밀번호", example="password123")


class PersonalSignupRequest(BaseModel):
    user_name: str = Field(..., description="이름", example="홍길동")
    phone_number: str = Field(..., description="전화번호", example="01012345678")
    email: str = Field(..., description="이메일", example="adedge@gmail.com")
    user_id: str = Field(..., description="사용자 ID", example="user123")
    password: str = Field(..., description="비밀번호", example="password123")
    password_confirm: str = Field(..., description="비밀번호 확인", example="password123")


class ReissueTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="리프레시 토큰", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")


class CorporateSignupRequest(BaseModel):
    business_name: str = Field(..., description="법인명", example="(주)테스트")
    business_number: str = Field(..., description="사업자등록번호", example="123-45-67890")
    phone_number: str = Field(..., description="전화번호", example="01012345678")
    email: str = Field(..., description="이메일", example="adedge@gmail.com")
    user_id: str = Field(..., description="사용자 ID", example="corp123")
    password: str = Field(..., description="비밀번호", example="password123")
    password_confirm: str = Field(..., description="비밀번호 확인", example="password123")


class UseridDuplicateRequest(BaseModel):
    user_id: str = Field(..., description="중복 확인할 사용자 ID", example="user123")


class EmailDuplicateRequest(BaseModel):
    email: str = Field(..., description="중복 확인할 사용자 EMAIL", example="user123@gmail.com")
