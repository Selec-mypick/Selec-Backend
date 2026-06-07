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
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ErrorCode,
    ServerException,
    UnauthorizedException,
)
from app.users.repository.users_repository import UsersRepository
from app.users.models.users import Users

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


async def authenticate_google(request: GoogleOAuthRequest, db: AsyncSession) -> AuthTokenResponse:
    async with aiohttp.ClientSession() as session:
        async with session.get(GOOGLE_TOKENINFO_URL, params={"id_token": request.id_token}) as response:
            google_user = await response.json()
            if response.status != 200:
                message = google_user.get("error_description") or google_user.get("error") or ErrorCode.GOOGLE_TOKEN_VERIFY_FAILED.message
                raise BadRequestException(ErrorCode.GOOGLE_TOKEN_VERIFY_FAILED, message=message)

    if google_user.get("aud") != settings.google_client_id:
        raise BadRequestException(ErrorCode.GOOGLE_TOKEN_AUDIENCE_MISMATCH)

    google_id = google_user.get("sub")
    if not google_id:
        raise BadRequestException(ErrorCode.GOOGLE_USER_NOT_FOUND)

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
        integrity_exception=ConflictException(ErrorCode.GOOGLE_REGISTER_CONFLICT),
    )

    access_token, expires_in = create_access_token(users_seq)
    refresh_token = create_refresh_token(users_seq)

    try:
        previous_token = await get_white_token(users_seq)
        if previous_token is not None:
            await store_auth_token(store_type="black", token=previous_token)
        await store_auth_token(store_type="white", token=access_token, users_seq=users_seq)
    except Exception as e:
        raise ServerException(ErrorCode.TOKEN_STORE_FAILED, message=f"{ErrorCode.TOKEN_STORE_FAILED.message}: {str(e)}")

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
        integrity_exception=ConflictException(ErrorCode.TEST_USER_CREATE_CONFLICT),
    )

    access_token, expires_in = create_access_token(users.users_seq)
    refresh_token = create_refresh_token(users.users_seq)

    try:
        await store_auth_token(store_type="white", token=access_token, users_seq=users.users_seq)
    except Exception as e:
        raise ServerException(ErrorCode.TOKEN_STORE_FAILED, message=f"{ErrorCode.TOKEN_STORE_FAILED.message}: {str(e)}")

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
        raise UnauthorizedException(ErrorCode.AUTH_USER_NOT_FOUND)
    if not users.active:
        raise UnauthorizedException(ErrorCode.AUTH_USER_INACTIVE)

    access_token, expires_in = create_access_token(users.users_seq)
    refresh_token = create_refresh_token(users.users_seq)

    try:
        previous_token = await get_white_token(users.users_seq)
        if previous_token is not None:
            await store_auth_token(store_type="black", token=previous_token)
        await store_auth_token(store_type="white", token=access_token, users_seq=users.users_seq)
    except Exception as e:
        raise ServerException(ErrorCode.TOKEN_STORE_FAILED, message=f"{ErrorCode.TOKEN_STORE_FAILED.message}: {str(e)}")

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


async def refresh_access_token(request: RefreshTokenRequest, db: AsyncSession) -> AuthTokenResponse:
    try:
        payload = jwt.decode(request.refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(ErrorCode.REFRESH_TOKEN_EXPIRED)
    except JWTError:
        raise UnauthorizedException(ErrorCode.REFRESH_TOKEN_INVALID)

    if payload.get("type") != "refresh":
        raise UnauthorizedException(ErrorCode.REFRESH_TOKEN_TYPE_INVALID)

    users_seq = payload.get("users_seq") or payload.get("sub")
    if not users_seq:
        raise UnauthorizedException(ErrorCode.REFRESH_TOKEN_MISSING_USER)

    users = await UsersRepository.find_by_users_seq(db, users_seq)
    if users is None:
        raise UnauthorizedException(ErrorCode.AUTH_USER_NOT_FOUND)
    if not users.active:
        raise UnauthorizedException(ErrorCode.AUTH_USER_INACTIVE)

    access_token, expires_in = create_access_token(users.users_seq)
    refresh_token = create_refresh_token(users.users_seq)

    try:
        if await is_token_blacklisted(request.refresh_token):
            raise UnauthorizedException(ErrorCode.REFRESH_TOKEN_BLACKLISTED)

        await store_auth_token(store_type="black", token=request.refresh_token)

        previous_token = await get_white_token(users.users_seq)
        if previous_token is not None:
            await store_auth_token(store_type="black", token=previous_token)
        await store_auth_token(store_type="white", token=access_token, users_seq=users.users_seq)
    except UnauthorizedException:
        raise
    except Exception as e:
        raise ServerException(ErrorCode.TOKEN_REFRESH_FAILED, message=f"{ErrorCode.TOKEN_REFRESH_FAILED.message}: {str(e)}")

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )
