import secrets
from time import monotonic

from sqlalchemy.ext.asyncio import AsyncSession

from app.users.repository.users_repository import UsersRepository

NICKNAME_GENERATION_TIMEOUT_SECONDS = 3.0

ADJECTIVES = (
    "용감한", "빠른", "조용한", "빛나는", "행복한",
    "졸린", "귀여운", "차가운", "따뜻한", "신비한",
    "강한", "날쌘", "엉뚱한", "멋진", "작은",
    "커다란", "푸른", "붉은", "하얀", "검은",
)

NOUNS = (
    "고양이", "강아지", "여우", "늑대", "호랑이",
    "판다", "토끼", "다람쥐", "수달", "펭귄",
    "독수리", "고래", "상어", "사자", "곰",
    "부엉이", "용", "기사", "마법사", "전사",
)


async def generate_unique_nickname(db: AsyncSession, fallback_nick_name: str) -> str:
    start_time = monotonic()

    while monotonic() - start_time <= NICKNAME_GENERATION_TIMEOUT_SECONDS:
        adjective = ADJECTIVES[secrets.randbelow(len(ADJECTIVES))]
        noun = NOUNS[secrets.randbelow(len(NOUNS))]
        number = secrets.randbelow(1000)
        nick_name = f"{adjective}{noun}{number:03d}"
        if not await UsersRepository.exists_by_nick_name(db, nick_name):
            return nick_name

    return fallback_nick_name
