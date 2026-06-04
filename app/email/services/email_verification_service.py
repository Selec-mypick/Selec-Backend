import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.redis_config import RedisClient
from app.core.exception import BadRequestException, UnauthorizedException, ServerException
from app.email.services.email_client import EmailClient
from app.email.services.email_templates import get_verification_email_html
from app.users.models.user import User


def generate_verification_code() -> str:
    """6자리 인증번호 생성"""
    return f"{secrets.randbelow(1000000):06d}"


async def send_verification_email(email: str) -> None:
    """
    이메일 인증번호 발송
    
    Args:
        email: 인증번호를 받을 이메일 주소
    """
    # 인증번호 생성
    verification_code = generate_verification_code()

    # Redis에 저장 (3분 TTL)
    try:
        redis_client = await RedisClient.get_client()
        redis_key = f"email:verification:{email}"
        ttl_seconds = 180  # 3분
        await redis_client.setex(redis_key, ttl_seconds, verification_code)
    except Exception as e:
        raise ServerException(f"인증번호를 Redis에 저장하는 중 오류가 발생했습니다: {str(e)}")

    # 이메일 발송
    subject = "[AdEdge] 이메일 인증번호"
    html_content = get_verification_email_html(verification_code)
    text_content = f"[AdEdge] 인증번호는 {verification_code}입니다. 3분 내에 입력해주세요."

    try:
        email_client = EmailClient()
        await email_client.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    except Exception as e:
        # 이메일 발송 실패 시 Redis에서도 삭제
        try:
            redis_client = await RedisClient.get_client()
            redis_key = f"email:verification:{email}"
            await redis_client.delete(redis_key)
        except Exception:
            pass
        raise ServerException(f"인증번호 이메일 발송 중 오류가 발생했습니다: {str(e)}")


async def verify_email_code(email: str, verification_code: str, db: AsyncSession) -> dict:
    """
    이메일 인증번호 검증
    
    Args:
        email: 인증번호를 받은 이메일 주소
        verification_code: 인증번호
        db: 데이터베이스 세션
        
    Returns:
        dict: 검증 결과 및 사용자 정보
            - message: 성공 메시지
            - user_id: 해당 이메일로 가입된 사용자가 있으면 user_id, 없으면 None
    """
    if not email or not verification_code:
        raise BadRequestException("이메일과 인증번호를 모두 입력해주세요.")

    if len(verification_code) != 6:
        raise BadRequestException("인증번호는 6자리입니다.")

    try:
        redis_client = await RedisClient.get_client()
        redis_key = f"email:verification:{email}"
        stored_code = await redis_client.get(redis_key)

        if stored_code is None:
            raise UnauthorizedException("인증번호가 만료되었거나 존재하지 않습니다. 다시 발송해주세요.")

        if stored_code != verification_code:
            raise UnauthorizedException("인증번호가 일치하지 않습니다. 다시 확인해주세요.")

        # 검증 성공 시 Redis에서 삭제 (1회용)
        await redis_client.delete(redis_key)

        # 해당 이메일로 가입된 사용자 조회
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            return {"message": "인증번호가 확인되었습니다.", "user_id": user.user_id}
        else:
            return {"message": "SUCCESS"}

    except UnauthorizedException:
        raise
    except Exception as e:
        raise ServerException(f"인증번호 검증 중 오류가 발생했습니다: {str(e)}")
