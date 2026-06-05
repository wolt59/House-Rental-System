from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "House Rental System"
    SQLALCHEMY_DATABASE_URI: str = "mysql+pymysql://root:password@127.0.0.1:3306/house_rental"
    SECRET_KEY: str = "change-me-to-a-secure-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    BACKEND_PORT: int = 8000

    # Redis 缓存配置
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    CACHE_ENABLED: bool = True
    # 默认缓存过期时间（秒）
    CACHE_DEFAULT_TTL: int = 300
    CACHE_SHORT_TTL: int = 60
    CACHE_LONG_TTL: int = 3600
    # 缓存键前缀，用于多环境隔离
    CACHE_KEY_PREFIX: str = "hrs"

    class Config:
        env_file = ".env"
        extra = 'ignore'


settings = Settings()
