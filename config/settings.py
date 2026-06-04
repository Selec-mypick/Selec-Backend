import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class Settings:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.active_profile = self._get_active_profile()
        self._load_environment_config()
    
    def _get_active_profile(self) -> str:
        profile = os.getenv('ACTIVE_PROFILE')
        if profile:
            return profile
        
        default_env_path = self.base_dir / 'default.env'
        if default_env_path.exists():
            load_dotenv(default_env_path)
            profile = os.getenv('ACTIVE_PROFILE')
            if profile:
                return profile
        
        return 'local'
    
    def _load_environment_config(self):
        env_file = self.base_dir / f'{self.active_profile}.env'
        
        if env_file.exists():
            load_dotenv(env_file)
        else:
            raise FileNotFoundError(f"환경 설정 파일을 찾을 수 없습니다: {env_file}")
    
    @property
    def database_url(self) -> str:
        url = os.getenv('DATABASE_URL')
        if not url:
            raise ValueError(f"DATABASE_URL이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return url
    
    @property
    def debug(self) -> bool:
        return os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    
    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def redis_host(self) -> str:
        host = self.get_env('REDIS_HOST')
        if not host:
            raise ValueError(f"REDIS_HOST이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return host
    
    @property
    def redis_port(self) -> int:
        port = self.get_env('REDIS_PORT')
        if not port:
            raise ValueError(f"REDIS_PORT이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return int(port)
    
    @property
    def redis_password(self) -> Optional[str]:
        return self.get_env('REDIS_PASSWORD')
    
    @property
    def redis_db(self) -> int:
        db = self.get_env('REDIS_DB', '0')
        return int(db)
    
    @property
    def solapi_api_key(self) -> str:
        api_key = self.get_env('SOLAPI_API_KEY')
        if not api_key:
            raise ValueError(f"SOLAPI_API_KEY이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return api_key
    
    @property
    def solapi_api_secret(self) -> str:
        api_secret = self.get_env('SOLAPI_API_SECRET')
        if not api_secret:
            raise ValueError(f"SOLAPI_API_SECRET이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return api_secret
    
    @property
    def solapi_from_number(self) -> str:
        from_number = self.get_env('SOLAPI_FROM_NUMBER')
        if not from_number:
            raise ValueError(f"SOLAPI_FROM_NUMBER이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return from_number
    
    @property
    def cors_origins(self) -> list[str]:
        """CORS 허용 origin 목록. 쉼표로 구분된 문자열을 리스트로 변환"""
        origins_str = self.get_env('CORS_ORIGINS', '*')
        if origins_str == '*':
            return ['*']
        return [origin.strip() for origin in origins_str.split(',') if origin.strip()]
    
    @property
    def smtp_host(self) -> str:
        host = self.get_env('SMTP_HOST')
        if not host:
            raise ValueError(f"SMTP_HOST이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return host
    
    @property
    def smtp_port(self) -> int:
        port = self.get_env('SMTP_PORT')
        if not port:
            raise ValueError(f"SMTP_PORT이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return int(port)
    
    @property
    def smtp_user(self) -> str:
        user = self.get_env('SMTP_USER')
        if not user:
            raise ValueError(f"SMTP_USER이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return user
    
    @property
    def smtp_password(self) -> str:
        password = self.get_env('SMTP_PASSWORD')
        if not password:
            raise ValueError(f"SMTP_PASSWORD이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return password
    
    @property
    def smtp_from_email(self) -> str:
        from_email = self.get_env('SMTP_FROM_EMAIL')
        if not from_email:
            raise ValueError(f"SMTP_FROM_EMAIL이 설정되지 않았습니다. ({self.active_profile} 환경)")
        return from_email
    
    @property
    def smtp_use_tls(self) -> bool:
        use_tls = self.get_env('SMTP_USE_TLS', 'True')
        return use_tls.lower() in ('true', '1', 'yes')
    
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)
    
    def __str__(self):
        return f"Settings(profile={self.active_profile}, debug={self.debug})"
