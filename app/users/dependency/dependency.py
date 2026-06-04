from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.core.connection_config import AsyncSessionLocal
from config import settings

SECRET_KEY = settings.get_env("SECRET_KEY")
ALGORITHM = settings.get_env("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.get_env("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(settings.get_env("REFRESH_TOKEN_EXPIRE_DAYS"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        await session.commit()
