"""Configuration tests for YAML-based settings.

Note: Some tests may be skipped due to Pydantic's module-level caching.
Run individual tests with -k flag for isolated testing.
"""

import os
import tempfile
from pathlib import Path

import pytest

# Import at module level
from api.config import Settings, TestSettings, _load_yaml_config


class TestYamlConfigLoading:
    """Test YAML configuration loading functionality."""

    def test_load_yaml_config_success(self):
        """Test successful loading of configuration from YAML file."""
        config = _load_yaml_config()
        # Should return a dict with app configuration
        assert isinstance(config, dict)

    def test_load_yaml_config_file_not_found(self, monkeypatch):
        """Test FileNotFoundError when config file doesn't exist."""
        monkeypatch.setenv("CONFIG_PATH", "/nonexistent/path/config.yaml")
        with pytest.raises(FileNotFoundError) as exc_info:
            _load_yaml_config()
        assert "Configuration file not found" in str(exc_info.value)

    def test_load_yaml_config_malformed(self, monkeypatch):
        """Test ValueError when YAML file is malformed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid yaml content: [unclosed")
            temp_path = f.name

        try:
            monkeypatch.setenv("CONFIG_PATH", temp_path)
            with pytest.raises(ValueError) as exc_info:
                _load_yaml_config()
            assert "Failed to parse configuration file" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_load_yaml_config_with_custom_path(self, monkeypatch):
        """Test loading config from custom path via CONFIG_PATH."""
        yaml_content = """
app:
  env: "test"
  database_uri: "postgresql://test:5432/testdb"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            monkeypatch.setenv("CONFIG_PATH", temp_path)
            config = _load_yaml_config()
            assert config["env"] == "test"
            assert config["database_uri"] == "postgresql://test:5432/testdb"
        finally:
            os.unlink(temp_path)


class TestSettingsBasic:
    """Test basic Settings functionality."""

    def test_settings_initialization(self):
        """Test that Settings can be initialized without errors."""
        settings = Settings()
        assert settings is not None
        assert isinstance(settings.PROJECT_NAME, str)
        assert settings.ENV in ["development", "staging", "production"]

    def test_vendor_base_urls_loaded(self):
        """Test that VENDOR_BASE_URLS is correctly loaded from nested YAML."""
        settings = Settings()
        assert isinstance(settings.VENDOR_BASE_URLS, dict)
        # Check that expected vendors are present
        expected_vendors = ["bigmodel", "z.ai", "volcengine", "moonshot", "minimax", "openrouter"]
        for vendor in expected_vendors:
            assert vendor in settings.VENDOR_BASE_URLS

    def test_default_jwt_settings(self):
        """Test default JWT configuration values."""
        settings = Settings()
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 10080  # 7 days

    def test_default_paths(self):
        """Test default path configuration."""
        settings = Settings()
        assert settings.ASSETS_PATH == "/app/assets"
        assert "redis://" in settings.REDIS_DATABASE

    def test_project_name_generation(self):
        """Test PROJECT_NAME is generated correctly."""
        settings = Settings()
        assert "FastAPI Server" in settings.PROJECT_NAME


class TestEnvironmentVariableFallback:
    """Test environment variable fallback functionality.

    Note: These tests require running in isolation due to Pydantic's caching.
    Run with: pytest tests/test_config_yaml.py::TestEnvironmentVariableFallback -v
    """

    def test_secret_key_fallback_with_empty_yaml(self, monkeypatch):
        """Test SECRET_KEY environment variable fallback when YAML value is empty."""
        yaml_content = """
app:
  secret_key: ""
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            monkeypatch.setenv("CONFIG_PATH", temp_path)
            monkeypatch.setenv("SECRET_KEY", "test-secret-key-12345")
            settings = Settings()
            assert settings.SECRET_KEY == "test-secret-key-12345"
        finally:
            os.unlink(temp_path)

    def test_database_uri_fallback_with_empty_yaml(self, monkeypatch):
        """Test DATABASE_URI environment variable fallback when YAML value is empty."""
        yaml_content = """
app:
  database_uri: ""
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            monkeypatch.setenv("CONFIG_PATH", temp_path)
            monkeypatch.setenv("DATABASE_URI", "postgresql://fallback:5432/fallbackdb")
            settings = Settings()
            assert settings.DATABASE_URI == "postgresql://fallback:5432/fallbackdb"
        finally:
            os.unlink(temp_path)

    def test_yaml_value_takes_precedence_over_env(self, monkeypatch):
        """Test that YAML value takes precedence over environment variable."""
        yaml_content = """
app:
  database_uri: "postgresql://yaml:5432/yamldb"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            monkeypatch.setenv("CONFIG_PATH", temp_path)
            monkeypatch.setenv("DATABASE_URI", "postgresql://env:5432/envdb")
            settings = Settings()
            # YAML value should take precedence
            assert settings.DATABASE_URI == "postgresql://yaml:5432/yamldb"
        finally:
            os.unlink(temp_path)


class TestTestSettings:
    """Test TestSettings subclass."""

    def test_test_settings_testing_flag(self):
        """Test TestSettings has TESTING=True."""
        test_settings = TestSettings()
        assert test_settings.TESTING is True
