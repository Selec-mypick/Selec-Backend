from config import settings

SECRET_KEY = settings.get_env("SECRET_KEY")
ALGORITHM = settings.get_env("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.get_env("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(settings.get_env("REFRESH_TOKEN_EXPIRE_DAYS"))
