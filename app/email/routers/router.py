from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.email.schema.schemas import SendEmailVerificationRequest, VerifyEmailCodeRequest
from app.email.services.email_verification_service import send_verification_email, verify_email_code
from app.base.base_response import BaseResponse
from app.core.connection_config import get_db

router = APIRouter(prefix="/email", tags=["EMAIL"])


@router.post("/send", response_model=BaseResponse[dict])
async def send_verification_code_endpoint(request: SendEmailVerificationRequest):
    """
    이메일 인증번호 발송
    
    이메일 주소를 받아서 6자리 인증번호를 생성하고 이메일로 발송합니다.
    인증번호는 3분간 유효합니다.
    """
    await send_verification_email(request.email)
    return BaseResponse.of_success(status.HTTP_200_OK, {"message": "인증번호가 발송되었습니다."})


@router.post("/verify", response_model=BaseResponse[dict])
async def verify_code_endpoint(request: VerifyEmailCodeRequest, db: AsyncSession = Depends(get_db)):
    """
    이메일 인증번호 검증
    
    이메일 주소와 인증번호를 받아서 검증합니다.
    검증 성공 시 인증번호는 삭제되어 재사용할 수 없습니다.
    해당 이메일로 회원가입된 사용자가 있으면 user_id를 반환하고, 없으면 SUCCESS를 반환합니다.
    """
    result = await verify_email_code(request.email, request.verification_code, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)

