from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.users.models.user import User
from app.users.schema.request.user_request import (
    UserLogin,
    PersonalSignupRequest,
    CorporateSignupRequest, UseridDuplicateRequest, ReissueTokenRequest, EmailDuplicateRequest,
)
from app.users.dependency.dependency import pwd_context
from datetime import datetime, timedelta
from jose import jwt
from app.users.dependency.dependency import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from app.core.exception import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    ServerException,
    UnauthorizedException
)
from app.core.redis_config import RedisClient


async def create_personal_user(request: PersonalSignupRequest, db: AsyncSession) -> None:
    if request.password_confirm != request.password:
        raise BadRequestException("비밀번호와 비밀번호 확인이 일치하지 않습니다. 다시 확인해주세요.")

    result = await db.execute(select(User).where(User.user_id == request.user_id))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ConflictException(f"이미 등록된 사용자입니다. 사용자 ID '{request.user_id}'는 이미 사용 중입니다.")

    result = await db.execute(select(User).where(User.phone_number == request.phone_number))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ConflictException(f"이미 등록된 사용자입니다. 사용자 전화번호 '{request.phone_number}'는 이미 사용 중입니다.")

    new_user = User(
        account_type="PERSONAL",
        user_name=request.user_name,
        phone_number=request.phone_number,
        email=request.email,
        user_id=request.user_id,
        hashed_password=pwd_context.hash(request.password)
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        raise ServerException(f"사용자 생성 중 오류가 발생했습니다: {str(e)}")


async def create_corporate_user(request: CorporateSignupRequest, db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.user_id == request.user_id))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ConflictException(f"이미 등록된 사용자입니다. 사용자 ID '{request.user_id}'는 이미 사용 중입니다.")

    result = await db.execute(select(User).where(User.phone_number == request.phone_number))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ConflictException(f"이미 등록된 사용자입니다. 사용자 전화번호 '{request.phone_number}'는 이미 사용 중입니다.")

    result = await db.execute(select(User).where(User.business_number == request.business_number))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ConflictException(f"이미 등록된 사용자입니다. 사용자 사업자 번호 '{request.business_number}'는 이미 사용 중입니다.")

    new_user = User(
        account_type="CORPORATE",
        business_name=request.business_name,
        business_number=request.business_number,
        phone_number=request.phone_number,
        email=request.email,
        user_id=request.user_id,
        hashed_password=pwd_context.hash(request.password),
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        raise ServerException(f"사용자 생성 중 오류가 발생했습니다: {str(e)}")


async def login_user(request: UserLogin, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.user_id == request.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException(f"사용자 ID '{request.user_id}'로 등록된 사용자를 찾을 수 없습니다.")

    if not pwd_context.verify(request.password, user.hashed_password):
        raise UnauthorizedException("비밀번호가 일치하지 않습니다. 다시 확인해주세요.")

    access_payload = {
        "sub": str(user.user_seq),
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)

    refresh_payload = {
        "sub": str(user.user_seq),
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)

    try:
        redis_client = await RedisClient.get_client()
        redis_key = f"auth:white:{user.user_seq}"
        ttl_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        await redis_client.setex(redis_key, ttl_seconds, access_token)
    except Exception as e:
        raise ServerException(f"로그인 후 토큰을 Redis에 저장하는 중 오류가 발생했습니다: {str(e)}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


async def reissue_token(request: ReissueTokenRequest, db: AsyncSession) -> dict:
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != "refresh":
            raise UnauthorizedException("refresh token이 아닌 토큰입니다. refresh token을 사용해주세요.")

        user_seq = int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("refresh token이 만료되었습니다. 다시 로그인해주세요.")
    except jwt.JWTError as e:
        raise UnauthorizedException(f"refresh token 형식이 잘못되었거나 유효하지 않습니다: {str(e)}")
    except Exception as e:
        raise UnauthorizedException(f"refresh token 검증 중 오류가 발생했습니다: {str(e)}")

    result = await db.execute(select(User).where(User.user_seq == user_seq))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException(f"토큰에 해당하는 사용자(user_seq: {user_seq})를 찾을 수 없습니다.")

    access_payload = {
        "sub": str(user.user_seq),
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)

    refresh_payload = {
        "sub": str(user.user_seq),
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)

    try:
        redis_client = await RedisClient.get_client()

        white_key = f"auth:white:{user.user_seq}"
        old_access_token = await redis_client.get(white_key)
        if old_access_token:
            black_key = f"auth:black:{user.user_seq}"
            ttl_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
            await redis_client.setex(black_key, ttl_seconds, old_access_token)

        ttl_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        await redis_client.setex(white_key, ttl_seconds, access_token)
    except Exception as e:
        raise ServerException(f"토큰 재발급 후 Redis에 저장하는 중 오류가 발생했습니다: {str(e)}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


async def user_id_duplicate(request: UseridDuplicateRequest, db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.user_id == request.user_id))
    user = result.scalar_one_or_none()

    if user:
        raise BadRequestException(f"이미 사용 중인 사용자 ID입니다. '{request.user_id}'는 다른 사용자가 사용 중입니다.")


async def email_duplicate(request: EmailDuplicateRequest, db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user:
        raise BadRequestException(f"이미 사용 중인 사용자 이메일입니다. '{request.email}'는 다른 사용자가 사용 중입니다.")
