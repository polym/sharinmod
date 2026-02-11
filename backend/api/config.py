import os
import secrets
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days (7 * 24 * 60)

    # GitHub OAuth Configuration
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI: str = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:28888/api/oauth/github/callback")

    # Website Base URL (for OAuth callback)
    WEBSITE_BASE_URL: str = os.getenv("WEBSITE_BASE_URL", "http://localhost:38888")

    # LiteLLM Configuration
    LITELLM_BASE_URL: str = os.getenv("LITELLM_BASE_URL", "http://10.0.5.176:4000")
    LITELLM_MASTER_KEY: str = os.getenv("LITELLM_MASTER_KEY", "sk-1234")
    
    # Vendor API Base URLs
    VENDOR_BASE_URLS: dict = {
        "bigmodel": "https://open.bigmodel.cn/api/anthropic",
        "z.ai": "https://z.ai/api/anthropic",
        "volcengine": "https://ark.cn-beijing.volces.com/api/coding",
        "moonshot": "https://api.kimi.com/coding",
        "minimax": "https://api.minimaxi.com/anthropic",
        "openrouter": "https://openrouter.ai/api/v1"
    }

    # Redis Configuration
    REDIS_DATABASE: str = os.getenv("REDIS_DATABASE", "redis://redis:6379/")

    # LiteLLM webhook IP whitelist (comma-separated string, will be parsed to list)
    LITELLM_WEBHOOK_IP_WHITELIST_STR: str = ""
    LITELLM_WEBHOOK_IP_WHITELIST: list[str] = []

    @field_validator("LITELLM_WEBHOOK_IP_WHITELIST", mode="before")
    @classmethod
    def parse_whitelist(cls, v: str | list, info) -> list[str]:
        """Parse IP whitelist from environment variable"""
        # If already a list (from default), return as is
        if isinstance(v, list):
            return [ip.strip() for ip in v if ip.strip()]
        # If string, split by comma
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",") if ip.strip()]
        return []

    class Config:
        case_sensitive = True


class TestSettings(Settings):
    DATABASE_URI: str = os.getenv("TEST_DATABASE_URI", "sqlite+aiosqlite://")

    class Config:
        case_sensitive = True


settings = Settings()
test_settings = TestSettings()
