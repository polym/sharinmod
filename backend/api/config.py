import os
import secrets
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


def load_env():
    from dotenv import load_dotenv

    env_path = "../.env"
    load_dotenv(env_path)


class Settings(BaseSettings):
    PROJECT_NAME: str = (
        f"FastAPI Server - {os.getenv('ENV', 'development').capitalize()}"
    )
    DESCRIPTION: str = "FastAPI + Nextjs Example"
    ENV: Literal["development", "staging", "production"] = "development"
    VERSION: str = "0.1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DATABASE_URI: str = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@db:5432/sharinmod")
    TESTING: bool = False
    
    # JWT Configuration
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LiteLLM Configuration
    LITELLM_BASE_URL: str = os.getenv("LITELLM_BASE_URL", "http://10.0.5.176:4000")
    LITELLM_MASTER_KEY: str = os.getenv("LITELLM_MASTER_KEY", "sk-1234")
    
    # Vendor API Base URLs
    VENDOR_BASE_URLS: dict = {
        "bigmodel": "https://open.bigmodel.cn/api/anthropic",
        "z.ai": "https://z.ai/api/anthropic"
    }

    class Config:
        case_sensitive = True


class TestSettings(Settings):
    DATABASE_URI: str = os.getenv("TEST_DATABASE_URI", "sqlite+aiosqlite://")

    class Config:
        case_sensitive = True


settings = Settings()
test_settings = TestSettings()
