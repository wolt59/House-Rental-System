from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "House Rental System"
    SQLALCHEMY_DATABASE_URI: str = "mysql+pymysql://root:password@127.0.0.1:3306/house_rental"
    SECRET_KEY: str = "change-me-to-a-secure-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()
