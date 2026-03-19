import os
import secrets
from typing import Literal, Any, Dict, Tuple

import pydantic
import yaml
from pydantic import field_validator, Field
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource

# Fallback configuration mapping for sensitive fields
# Format: {field_name: (env_var_name, default_value)}
_FALLBACK_CONFIG: Dict[str, Tuple[str, str]] = {
    "DATABASE_URI": ("DATABASE_URI", "postgresql://postgres:postgres@db:5432/sharinmod"),
    "SECRET_KEY": ("SECRET_KEY", ""),
    "GITHUB_CLIENT_ID": ("GITHUB_CLIENT_ID", ""),
    "GITHUB_CLIENT_SECRET": ("GITHUB_CLIENT_SECRET", ""),
    "GITLAB_CLIENT_ID": ("GITLAB_CLIENT_ID", ""),
    "GITLAB_CLIENT_SECRET": ("GITLAB_CLIENT_SECRET", ""),
    "LITELLM_BASE_URL": ("LITELLM_BASE_URL", "http://10.0.5.176:4000"),
    "LITELLM_MASTER_KEY": ("LITELLM_MASTER_KEY", "sk-1234"),
    "SHARINMOD_ADMIN_EMAIL": ("SHARINMOD_ADMIN_EMAIL", "admin@sharin.mod"),
    "SHARINMOD_ADMIN_PASSWORD": ("SHARINMOD_ADMIN_PASSWORD", "Aha12345!"),
}


def _get_fallback_value(field_name: str) -> str:
    """Get environment variable fallback value for a field.

    Args:
        field_name: The name of the Settings field.

    Returns:
        The fallback value from environment variable or default.
    """
    if field_name in _FALLBACK_CONFIG:
        env_var, default = _FALLBACK_CONFIG[field_name]
        return os.getenv(env_var, default)
    return ""


def _get_config_path() -> str:
    """Get the absolute path to the configuration file.

    Returns:
        str: Absolute path to config.yaml

    Raises:
        ValueError: If CONFIG_PATH environment variable is not set.
        FileNotFoundError: If config file doesn't exist.
    """
    config_path = os.getenv("CONFIG_PATH")
    if not config_path:
        raise ValueError(
            "CONFIG_PATH environment variable is not set. "
            "Please set it to the path of config.yaml (e.g., /app/config.yaml)"
        )

    # Resolve relative path - use __file__ as base for consistent resolution
    if not os.path.isabs(config_path):
        # Get the directory of this file (backend/api/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, config_path)
        # Normalize the path
        config_path = os.path.normpath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please create the file or set CONFIG_PATH environment variable."
        )

    return config_path


def _load_yaml_config() -> Dict[str, Any]:
    """Load configuration from YAML file.

    Returns:
        Dict[str, Any]: The 'app' section from config.yaml, or empty dict if not found.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config file is malformed.
    """
    config_path = _get_config_path()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            full_config = yaml.safe_load(f) or {}
    except Exception as e:
        raise ValueError(f"Failed to parse configuration file {config_path}: {e}")

    return full_config.get("app", {})


class YamlConfigSource(PydanticBaseSettingsSource):
    """Custom settings source for loading configuration from YAML file."""

    def __init__(self, settings_cls: type[BaseSettings]):
        super().__init__(settings_cls)
        # Load YAML config - let exceptions propagate to fail fast on config errors
        self.yaml_config: Dict[str, Any] = _load_yaml_config()

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> Tuple[Any, str, bool]:
        """Get field value from YAML config."""
        field_value = None

        # Convert field_name to YAML key format
        # Pydantic field names are uppercase (DATABASE_URI), YAML uses lowercase (database_uri)
        yaml_key = field_name.lower()

        if yaml_key in self.yaml_config:
            field_value = self.yaml_config[yaml_key]

        return field_value, yaml_key, False

    def __call__(self) -> Dict[str, Any]:
        """Return a dictionary of all field values from YAML."""
        result = {}

        for field_name, field_info in self.settings_cls.model_fields.items():
            field_value, _, _ = self.get_field_value(field_info, field_name)
            if field_value is not None:
                result[field_name] = field_value

        # Handle nested configs by checking for nested structures in yaml_config
        # This allows for any nested YAML configuration to be loaded properly
        for yaml_key, yaml_value in self.yaml_config.items():
            # Skip if already handled (simple field)
            field_key = yaml_key.upper()
            if field_key in result:
                continue

            # Handle nested dict values (e.g., vendor_base_urls)
            if isinstance(yaml_value, dict):
                result[field_key] = yaml_value

        return result


class Settings(BaseSettings):
    """Application settings loaded from YAML config file with environment variable fallback.

    The configuration is loaded from `etc/config.yaml` by default.
    The path can be overridden using the `CONFIG_PATH` environment variable.

    Sensitive configuration values support environment variable fallback:
    - If YAML value is null or empty string, the corresponding environment variable is used.
    - If YAML value exists, it takes precedence over environment variables.
    """

    PROJECT_NAME: str = Field(
        default_factory=lambda: f"FastAPI Server - {os.getenv('ENV', 'development').capitalize()}"
    )
    DESCRIPTION: str = "FastAPI + Nextjs Example"
    ENV: Literal["development", "staging", "production"] = "development"
    VERSION: str = "0.1"
    # SECRET_KEY supports environment variable fallback (SECRET_KEY env var)
    SECRET_KEY: str = Field(default="")
    TESTING: bool = False

    # Database (supports fallback to DATABASE_URI env var)
    DATABASE_URI: str = Field(
        default="",
        description="Database connection URI. Supports environment variable fallback."
    )

    # JWT Configuration
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days (7 * 24 * 60)

    # GitHub OAuth (supports fallback to GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET env vars)
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:28888/api/oauth/github/callback"

    # GitLab OAuth (supports fallback to GITLAB_CLIENT_ID, GITLAB_CLIENT_SECRET env vars)
    GITLAB_CLIENT_ID: str = ""
    GITLAB_CLIENT_SECRET: str = ""
    GITLAB_BASE_URL: str = "https://gitlab.com"
    GITLAB_REDIRECT_URI: str = "http://localhost:28888/api/oauth/gitlab/callback"

    # Website Base URL (for OAuth callback)
    WEBSITE_BASE_URL: str = "http://localhost:38888"

    # LiteLLM (supports fallback to LITELLM_BASE_URL, LITELLM_MASTER_KEY env vars)
    LITELLM_BASE_URL: str = ""
    LITELLM_MASTER_KEY: str = ""

    # Vendor API Base URLs
    VENDOR_BASE_URLS: dict = Field(
        default_factory=lambda: {
            "bigmodel": "https://open.bigmodel.cn/api/anthropic",
            "z.ai": "https://z.ai/api/anthropic",
            "volcengine": "https://ark.cn-beijing.volces.com/api/coding",
            "moonshot": "https://api.kimi.com/coding",
            "minimax": "https://api.minimaxi.com/anthropic",
            "openrouter": "https://openrouter.ai/api/v1"
        }
    )

    ASSETS_PATH: str = "/app/assets"
    CONFIG_PATH: str = Field(default="", description="Configuration file path")
    REDIS_DATABASE: str = "redis://redis:6379/"

    # Admin User (supports fallback to SHARINMOD_ADMIN_EMAIL, SHARINMOD_ADMIN_PASSWORD env vars)
    SHARINMOD_ADMIN_EMAIL: str = ""
    SHARINMOD_ADMIN_PASSWORD: str = ""

    # LiteLLM webhook IP whitelist (supports exact IPs and CIDR ranges)
    LITELLM_WEBHOOK_IP_WHITELIST: list[str] = []

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to load YAML config with fallback logic."""
        return (
            init_settings,
            YamlConfigSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    # Individual field validators for sensitive config fallback logic
    @field_validator("DATABASE_URI", mode="before")
    @classmethod
    def database_uri_fallback(cls, v: str) -> str:
        """Fallback to DATABASE_URI environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("DATABASE_URI")
        return v

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def secret_key_fallback(cls, v: str) -> str:
        """Fallback to SECRET_KEY environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("SECRET_KEY")
        return v

    @field_validator("GITHUB_CLIENT_ID", mode="before")
    @classmethod
    def github_client_id_fallback(cls, v: str) -> str:
        """Fallback to GITHUB_CLIENT_ID environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("GITHUB_CLIENT_ID")
        return v

    @field_validator("GITHUB_CLIENT_SECRET", mode="before")
    @classmethod
    def github_client_secret_fallback(cls, v: str) -> str:
        """Fallback to GITHUB_CLIENT_SECRET environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("GITHUB_CLIENT_SECRET")
        return v

    @field_validator("GITLAB_CLIENT_ID", mode="before")
    @classmethod
    def gitlab_client_id_fallback(cls, v: str) -> str:
        """Fallback to GITLAB_CLIENT_ID environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("GITLAB_CLIENT_ID")
        return v

    @field_validator("GITLAB_CLIENT_SECRET", mode="before")
    @classmethod
    def gitlab_client_secret_fallback(cls, v: str) -> str:
        """Fallback to GITLAB_CLIENT_SECRET environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("GITLAB_CLIENT_SECRET")
        return v

    @field_validator("LITELLM_BASE_URL", mode="before")
    @classmethod
    def litellm_base_url_fallback(cls, v: str) -> str:
        """Fallback to LITELLM_BASE_URL environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("LITELLM_BASE_URL")
        return v

    @field_validator("LITELLM_MASTER_KEY", mode="before")
    @classmethod
    def litellm_master_key_fallback(cls, v: str) -> str:
        """Fallback to LITELLM_MASTER_KEY environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("LITELLM_MASTER_KEY")
        return v

    @field_validator("SHARINMOD_ADMIN_EMAIL", mode="before")
    @classmethod
    def admin_email_fallback(cls, v: str) -> str:
        """Fallback to SHARINMOD_ADMIN_EMAIL environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("SHARINMOD_ADMIN_EMAIL")
        return v

    @field_validator("SHARINMOD_ADMIN_PASSWORD", mode="before")
    @classmethod
    def admin_password_fallback(cls, v: str) -> str:
        """Fallback to SHARINMOD_ADMIN_PASSWORD environment variable if YAML value is empty."""
        if not v:
            return _get_fallback_value("SHARINMOD_ADMIN_PASSWORD")
        return v

    @field_validator("LITELLM_WEBHOOK_IP_WHITELIST", mode="before")
    @classmethod
    def parse_whitelist(cls, v: str | list) -> list[str]:
        """Parse and validate IP whitelist, supporting exact IPs and CIDR ranges."""
        import ipaddress
        import logging
        _logger = logging.getLogger(__name__)

        raw_entries: list[str] = []
        if isinstance(v, list):
            raw_entries = [str(ip).strip() for ip in v if str(ip).strip()]
        elif isinstance(v, str):
            # Support space- or comma-separated env var value
            raw_entries = [ip.strip() for ip in v.replace(",", " ").split() if ip.strip()]

        validated: list[str] = []
        for entry in raw_entries:
            try:
                ipaddress.ip_network(entry, strict=False)
                validated.append(entry)
            except ValueError:
                _logger.warning(f"[IP_WHITELIST] Invalid whitelist entry skipped: {entry}")
        return validated

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix=""
    )


class TestSettings(Settings):
    DATABASE_URI: str = "sqlite+aiosqlite://"
    TESTING: bool = True

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix=""
    )


# Singleton instances
settings = Settings()
test_settings = TestSettings()