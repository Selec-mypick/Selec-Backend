import secrets
from time import monotonic

from sqlalchemy.ext.asyncio import AsyncSession

from app.users.repository.users_repository import UsersRepository

NICKNAME_GENERATION_TIMEOUT_SECONDS = 3.0

ADJECTIVES = (
    "고요한", "날카로운", "눈부신", "느긋한", "단단한",
    "당당한", "반짝이는", "빠른", "산뜻한", "섬세한",
    "솔직한", "신중한", "영리한", "용감한", "유쾌한",
    "은근한", "재빠른", "차분한", "침착한", "푸른",
    "한결같은", "호기심많은", "활기찬", "흔들림없는",
)

TITLES = (
    "선택자", "결정자", "질문자", "투표자", "한표러",
    "소환사", "전략가", "탐색자", "기록자", "참여자",
    "분석가", "관찰자", "개척자", "해결사", "판단자",
)

TAG_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
TAG_LENGTH = 6


async def generate_unique_nickname(db: AsyncSession, fallback_nick_name: str) -> str:
    start_time = monotonic()

    while monotonic() - start_time <= NICKNAME_GENERATION_TIMEOUT_SECONDS:
        adjective = ADJECTIVES[secrets.randbelow(len(ADJECTIVES))]
        title = TITLES[secrets.randbelow(len(TITLES))]
        tag = "".join(
            TAG_ALPHABET[secrets.randbelow(len(TAG_ALPHABET))]
            for _ in range(TAG_LENGTH)
        )
        nick_name = f"{adjective}{title}#{tag}"
        if not await UsersRepository.exists_by_nick_name(db, nick_name):
            return nick_name

    return fallback_nick_name
