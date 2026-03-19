"""
Unit and integration tests for IP whitelist middleware

Covers:
- _ip_in_whitelist helper: exact IP, CIDR, out-of-range, invalid IP, invalid entry
- Middleware integration: whitelist disabled (empty), CIDR allow, CIDR reject, exact IP allow
- Non-webhook paths bypass the whitelist check
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from api.middleware.ip_whitelist import _ip_in_whitelist
from api.config import Settings
from api.app import create_app


# ---------------------------------------------------------------------------
# Unit tests for _ip_in_whitelist
# ---------------------------------------------------------------------------

class TestIpInWhitelist:
    def test_exact_ip_match(self):
        assert _ip_in_whitelist("192.168.1.10", ["192.168.1.10"]) is True

    def test_cidr_match(self):
        assert _ip_in_whitelist("10.1.2.3", ["10.0.0.0/8"]) is True

    def test_ip_not_in_cidr(self):
        assert _ip_in_whitelist("192.168.1.5", ["10.0.0.0/8"]) is False

    def test_exact_ip_no_match(self):
        assert _ip_in_whitelist("1.2.3.4", ["192.168.1.10"]) is False

    def test_mixed_exact_and_cidr_exact_hits(self):
        assert _ip_in_whitelist("192.168.1.10", ["192.168.1.10", "10.0.0.0/8"]) is True

    def test_mixed_exact_and_cidr_cidr_hits(self):
        assert _ip_in_whitelist("10.5.6.7", ["192.168.1.10", "10.0.0.0/8"]) is True

    def test_empty_whitelist(self):
        assert _ip_in_whitelist("1.2.3.4", []) is False

    def test_invalid_client_ip(self):
        assert _ip_in_whitelist("not-an-ip", ["192.168.1.0/24"]) is False

    def test_invalid_whitelist_entry_skipped(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING, logger="api.middleware.ip_whitelist"):
            result = _ip_in_whitelist("192.168.1.5", ["not-an-ip", "192.168.1.5"])
        assert result is True  # valid entry still matches
        assert "Invalid whitelist entry skipped" in caplog.text

    def test_cidr_with_host_bits(self):
        # strict=False should accept 192.168.1.5/24
        assert _ip_in_whitelist("192.168.1.100", ["192.168.1.5/24"]) is True


# ---------------------------------------------------------------------------
# Middleware integration tests via TestClient
# ---------------------------------------------------------------------------

@pytest.fixture
def webhook_path():
    return "/api/v1/webhooks/litellm/spendlog"


class TestIpWhitelistMiddleware:
    def test_empty_whitelist_allows_any_ip(self, webhook_path):
        app_settings = Settings()
        app_settings.LITELLM_WEBHOOK_IP_WHITELIST = []
        app = create_app(app_settings)
        with patch("api.middleware.ip_whitelist.settings", app_settings):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(webhook_path, json={})
        # Empty whitelist → check disabled; endpoint may return 422/404, but never 403
        assert response.status_code != 403

    def test_whitelist_rejects_unlisted_ip(self, webhook_path):
        # Non-empty whitelist: TestClient's host "testclient" is not a valid IP → rejected
        app_settings = Settings()
        app_settings.LITELLM_WEBHOOK_IP_WHITELIST = ["10.0.0.0/8"]
        app = create_app(app_settings)
        with patch("api.middleware.ip_whitelist.settings", app_settings):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(webhook_path, json={})
        assert response.status_code == 403

    def test_cidr_allows_matching_forwarded_ip(self, webhook_path):
        # Patch TRUSTED_PROXIES to include "testclient" so X-Forwarded-For is honoured
        app_settings = Settings()
        app_settings.LITELLM_WEBHOOK_IP_WHITELIST = ["10.0.0.0/8"]
        app = create_app(app_settings)
        with patch("api.middleware.ip_whitelist.settings", app_settings):
            with patch("api.middleware.ip_whitelist.TRUSTED_PROXIES",
                       {"127.0.0.1", "::1", "localhost", "testclient"}):
                client = TestClient(app, raise_server_exceptions=False)
                response = client.post(
                    webhook_path,
                    json={},
                    headers={"X-Forwarded-For": "10.1.2.3"},
                )
        assert response.status_code != 403

    def test_cidr_rejects_forwarded_ip_outside_range(self, webhook_path):
        app_settings = Settings()
        app_settings.LITELLM_WEBHOOK_IP_WHITELIST = ["10.0.0.0/8"]
        app = create_app(app_settings)
        with patch("api.middleware.ip_whitelist.settings", app_settings):
            with patch("api.middleware.ip_whitelist.TRUSTED_PROXIES",
                       {"127.0.0.1", "::1", "localhost", "testclient"}):
                client = TestClient(app, raise_server_exceptions=False)
                response = client.post(
                    webhook_path,
                    json={},
                    headers={"X-Forwarded-For": "192.168.1.5"},
                )
        assert response.status_code == 403

    def test_exact_ip_allows_matching_forwarded(self, webhook_path):
        app_settings = Settings()
        app_settings.LITELLM_WEBHOOK_IP_WHITELIST = ["192.168.1.10"]
        app = create_app(app_settings)
        with patch("api.middleware.ip_whitelist.settings", app_settings):
            with patch("api.middleware.ip_whitelist.TRUSTED_PROXIES",
                       {"127.0.0.1", "::1", "localhost", "testclient"}):
                client = TestClient(app, raise_server_exceptions=False)
                response = client.post(
                    webhook_path,
                    json={},
                    headers={"X-Forwarded-For": "192.168.1.10"},
                )
        assert response.status_code != 403

    def test_non_webhook_path_bypasses_whitelist(self):
        app_settings = Settings()
        # Even with a restrictive whitelist the health endpoint must be reachable
        app_settings.LITELLM_WEBHOOK_IP_WHITELIST = ["10.0.0.0/8"]
        app = create_app(app_settings)
        with patch("api.middleware.ip_whitelist.settings", app_settings):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/api/health")
        assert response.status_code != 403

    def test_invalid_whitelist_entry_does_not_crash_service(self, webhook_path):
        # Invalid entries are skipped at runtime; service returns 403 (not 500)
        app_settings = Settings()
        # Bypass validator by setting directly to test runtime _ip_in_whitelist behaviour
        app_settings.LITELLM_WEBHOOK_IP_WHITELIST = ["not-an-ip", "192.168.1.10"]
        app = create_app(app_settings)
        with patch("api.middleware.ip_whitelist.settings", app_settings):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(webhook_path, json={})
        # Service must not crash (500); invalid entry is silently skipped with a warning
        assert response.status_code != 500

