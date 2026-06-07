import aiohttp
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from config import settings
from app.auth.domain.token_domain import (
    create_access_token,
    create_refresh_token,
    get_white_token,
    is_token_blacklisted,
    store_auth_token,
)
from app.auth.schema.request.auth_request import GoogleOAuthRequest, IssueTestTokenRequest, RefreshTokenRequest
from app.auth.schema.response.auth_response import AuthTokenResponse, CreateTestUserResponse
from app.core.database.transaction import run_in_transaction
from app.core.exceptions import BadRequestException, ConflictException, ServerException, UnauthorizedException
from app.users.repository.users_repository import UsersRepository
from app.users.models.users import Users

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


async def authenticate_google(request: GoogleOAuthRequest, db: AsyncSession) -> AuthTokenResponse:
    async with aiohttp.ClientSession() as session:
        async with session.get(GOOGLE_TOKENINFO_URL, params={"id_token": request.id_token}) as response:
            google_user = await response.json()
            if response.status != 200:
                message = google_user.get("error_description") or google_user.get("error") or "Google id_token 검증 실패"
                raise BadRequestException(message)

    if google_user.get("aud") != settings.google_client_id:
        raise BadRequestException("Google id_token audience가 일치하지 않습니다.")

    google_id = google_user.get("sub")
    if not google_id:
        raise BadRequestException("Google 사용자 정보를 확인할 수 없습니다.")

    async def upsert_google_user() -> str:
        users = await UsersRepository.upsert_by_google(
            db=db,
            google_id=google_id,
            email=google_user.get("email"),
            name=google_user.get("name"),
            profile_image=google_user.get("picture"),
        )
        return users.users_seq

    users_seq = await run_in_transaction(
        db,
        upsert_google_user,
        "Google OAuth 로그인 처리 중 오류가 발생했습니다",
        integrity_exception=ConflictException("Google 계정 등록 중 충돌이 발생했습니다. 다시 시도해주세요."),
    )

    access_token, expires_in = create_access_token(users_seq)
    refresh_token = create_refresh_token(users_seq)

    try:
        previous_token = await get_white_token(users_seq)
        if previous_token is not None:
            await store_auth_token(store_type="black", token=previous_token)
        await store_auth_token(store_type="white", token=access_token, users_seq=users_seq)
    except Exception as e:
        raise ServerException(f"토큰 저장 중 오류가 발생했습니다: {str(e)}")

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


async def create_test_user(db: AsyncSession) -> CreateTestUserResponse:
    test_uuid = uuid4().hex
    google_id = f"test_{test_uuid[:12]}"
    nick_name = f"test_{test_uuid[:12]}"

    async def save_test_user() -> Users:
        users = Users.create_from_google(
            google_id=google_id,
            email=f"{google_id}@test.local",
            name="테스트 유저",
            profile_image=None,
        )
        users.nick_name = nick_name
        return await UsersRepository.save(db, users)

    users = await run_in_transaction(
        db,
        save_test_user,
        "테스트 유저 생성 중 오류가 발생했습니다",
        integrity_exception=ConflictException("테스트 유저 생성 중 충돌이 발생했습니다."),
    )

    access_token, expires_in = create_access_token(users.users_seq)
    refresh_token = create_refresh_token(users.users_seq)

    try:
        await store_auth_token(store_type="white", token=access_token, users_seq=users.users_seq)
    except Exception as e:
        raise ServerException(f"토큰 저장 중 오류가 발생했습니다: {str(e)}")

    return CreateTestUserResponse(
        users_seq=users.users_seq,
        google_id=users.google_id,
        nick_name=users.nick_name,
        email=users.email,
        name=users.name,
        profile_image=users.profile_image,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


async def issue_test_token(request: IssueTestTokenRequest, db: AsyncSession) -> AuthTokenResponse:
    users = await UsersRepository.find_by_users_seq(db, request.users_seq)
    if users is None:
        raise UnauthorizedException("존재하지 않는 사용자입니다.")
    if not users.active:
        raise UnauthorizedException("비활성화된 사용자입니다.")

    access_token, expires_in = create_access_token(users.users_seq)
    refresh_token = create_refresh_token(users.users_seq)

    try:
        previous_token = await get_white_token(users.users_seq)
        if previous_token is not None:
            await store_auth_token(store_type="black", token=previous_token)
        await store_auth_token(store_type="white", token=access_token, users_seq=users.users_seq)
    except Exception as e:
        raise ServerException(f"토큰 저장 중 오류가 발생했습니다: {str(e)}")

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


async def refresh_access_token(request: RefreshTokenRequest, db: AsyncSession) -> AuthTokenResponse:
    try:
        payload = jwt.decode(request.refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("refresh token이 만료되었습니다.")
    except JWTError:
        raise UnauthorizedException("유효하지 않은 refresh token입니다.")

    if payload.get("type") != "refresh":
        raise UnauthorizedException("refresh token이 아닙니다.")

    users_seq = payload.get("users_seq") or payload.get("sub")
    if not users_seq:
        raise UnauthorizedException("refresh token에 사용자 정보가 없습니다.")

    users = await UsersRepository.find_by_users_seq(db, users_seq)
    if users is None:
        raise UnauthorizedException("존재하지 않는 사용자입니다.")
    if not users.active:
        raise UnauthorizedException("비활성화된 사용자입니다.")

    access_token, expires_in = create_access_token(users.users_seq)
    refresh_token = create_refresh_token(users.users_seq)

    try:
        if await is_token_blacklisted(request.refresh_token):
            raise UnauthorizedException("이미 무효화된 refresh token입니다.")

        await store_auth_token(store_type="black", token=request.refresh_token)

        previous_token = await get_white_token(users.users_seq)
        if previous_token is not None:
            await store_auth_token(store_type="black", token=previous_token)
        await store_auth_token(store_type="white", token=access_token, users_seq=users.users_seq)
    except UnauthorizedException:
        raise
    except Exception as e:
        raise ServerException(f"토큰 재발급 중 오류가 발생했습니다: {str(e)}")

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )
