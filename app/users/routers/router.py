from fastapi import APIRouter, Depends, status

from app.users.schema.request.user_request import (
    UserLogin, PersonalSignupRequest, CorporateSignupRequest,
    UseridDuplicateRequest, ReissueTokenRequest, EmailDuplicateRequest,
)
from app.base.base_response import BaseResponse
from app.core.connection_config import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.services.user_service import (
    create_personal_user, create_corporate_user, login_user,
    user_id_duplicate, reissue_token, email_duplicate
)

router = APIRouter(tags=["USER"])


@router.post("/auth/signup/personal", response_model=BaseResponse[dict])
async def signup_personal(request: PersonalSignupRequest, db: AsyncSession = Depends(get_db)):
    """
    개인 회원가입
    
    개인 사용자 회원가입을 처리합니다.
    사용자 ID, 비밀번호, 이름, 전화번호를 입력받아 회원가입을 진행합니다.
    """
    await create_personal_user(request, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, "SUCCESS")


@router.post("/auth/signup/corporate", response_model=BaseResponse[dict])
async def signup_corporate(request: CorporateSignupRequest, db: AsyncSession = Depends(get_db)):
    """
    법인 회원가입
    
    법인 사용자 회원가입을 처리합니다.
    사용자 ID, 비밀번호, 법인명, 사업자등록번호, 전화번호를 입력받아 회원가입을 진행합니다.
    """
    await create_corporate_user(request, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, "SUCCESS")


@router.post("/auth/reissue-token", response_model=BaseResponse[dict])
async def reissue_token_endpoint(request: ReissueTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    토큰 재발급
    
    리프레시 토큰을 사용하여 새로운 액세스 토큰과 리프레시 토큰을 발급받습니다.
    기존 액세스 토큰은 blacklist에 등록되어 더 이상 사용할 수 없습니다.
    """
    result = await reissue_token(request, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)


@router.post("/auth/login", response_model=BaseResponse[dict])
async def login(request: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    로그인
    
    사용자 ID와 비밀번호를 입력받아 로그인을 처리합니다.
    로그인 성공 시 액세스 토큰과 리프레시 토큰을 발급받습니다.
    액세스 토큰은 Redis whitelist에 등록됩니다.
    """
    result = await login_user(request, db)
    return BaseResponse.of_success(status.HTTP_200_OK, result)


@router.post("/auth/user_id/duplicate", response_model=BaseResponse[dict])
async def user_id_duplicate_check(request: UseridDuplicateRequest, db: AsyncSession = Depends(get_db)):
    """
    사용자 ID 중복 확인
    
    회원가입 전 사용자 ID의 중복 여부를 확인합니다.
    이미 사용 중인 ID인 경우 에러를 반환합니다.
    """
    await user_id_duplicate(request, db)
    return BaseResponse.of_success(status.HTTP_200_OK, "SUCCESS")


@router.post("/auth/user_email/duplicate", response_model=BaseResponse[dict])
async def user_id_duplicate_check(request: EmailDuplicateRequest, db: AsyncSession = Depends(get_db)):
    """
    사용자 이메일 중복 확인

    회원가입 전 사용자 이메일의 중복 여부를 확인합니다.
    이미 사용 중인 이메일인 경우 에러를 반환합니다.
    """
    await email_duplicate(request, db)
    return BaseResponse.of_success(status.HTTP_200_OK, "SUCCESS")


