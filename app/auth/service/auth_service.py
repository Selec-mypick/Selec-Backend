import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from config import settings
from app.auth.schema.request.auth_request import GoogleOAuthRequest, IssueTestTokenRequest, RefreshTokenRequest
from app.auth.schema.response.auth_response import AuthTokenResponse, CreateTestUserResponse
from app.auth.service.token_service import auth_token_issuer
from app.core.database.transaction import run_in_transaction
from app.core.exceptions import BadRequestException, ConflictException, UnauthorizedException
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
    return await auth_token_issuer.issue(users_seq)


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
    tokens = await auth_token_issuer.issue(users.users_seq, rotate_previous=False)

    return CreateTestUserResponse(
        users_seq=users.users_seq,
        google_id=users.google_id,
        nick_name=users.nick_name,
        email=users.email,
        name=users.name,
        profile_image=users.profile_image,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


async def issue_test_token(request: IssueTestTokenRequest, db: AsyncSession) -> AuthTokenResponse:
    users = await UsersRepository.find_by_users_seq(db, request.users_seq)
    if users is None:
        raise UnauthorizedException("존재하지 않는 사용자입니다.")
    if not users.active:
        raise UnauthorizedException("비활성화된 사용자입니다.")

    return await auth_token_issuer.issue(users.users_seq, rotate_previous=False)


async def refresh_access_token(request: RefreshTokenRequest, db: AsyncSession) -> AuthTokenResponse:
    users_seq = auth_token_issuer.decode_refresh_token(request.refresh_token)

    users = await UsersRepository.find_by_users_seq(db, users_seq)
    if users is None:
        raise UnauthorizedException("존재하지 않는 사용자입니다.")
    if not users.active:
        raise UnauthorizedException("비활성화된 사용자입니다.")

    return await auth_token_issuer.issue(users.users_seq)
