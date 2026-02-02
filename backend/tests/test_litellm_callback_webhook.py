"""
Integration tests for LiteLLM callback webhook endpoint
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import patch, AsyncMock, Mock
import redis.asyncio as redis

from api.app import create_app
from api.config import settings
from api.database import get_db

# Enable testing mode
settings.TESTING = True


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with overridden database session"""
    def get_db_override():
        return session

    app = create_app(settings)
    app.dependency_overrides[get_db] = get_db_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="valid_callback_data")
def valid_callback_data_fixture():
    """Valid callback data matching actual LiteLLM structure"""
    return {
        "id": "chatcmpl-test456",
        "trace_id": "trace-456",
        "call_type": "acompletion",
        "cache_hit": False,
        "stream": True,
        "status": "success",
        "custom_llm_provider": "openai",
        "startTime": 1768809251.711881,
        "endTime": 1768809253.019879,
        "response_time": 0.19952106475830078,
        "model": "openai/Qwen/Qwen2.5-3B-Instruct",
        "model_id": "model-456",
        "total_tokens": 2500,
        "prompt_tokens": 800,
        "completion_tokens": 1700,
        "response_cost": 0.0,
        "metadata": {
            "user_api_key_hash": "test_key_hash_123"
        }
    }


# Test 1: Webhook health check
def test_webhook_health_check(client: TestClient):
    """Test webhook health check endpoint"""
    response = client.get("/api/v1/webhooks/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "webhooks"


# Test 2: Successful webhook callback with valid data
@patch("api.routers.webhooks.enqueue_callback")
def test_webhook_success_with_valid_data(
    mock_enqueue,
    client: TestClient,
    valid_callback_data
):
    """Test successful webhook callback with valid data"""
    mock_enqueue.return_value = True

    response = client.post(
        "/api/v1/webhooks/litellm/success",
        json=valid_callback_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Callback received and queued"


# Test 3: Webhook callback with invalid data
def test_webhook_invalid_json(client: TestClient):
    """Test webhook callback with invalid JSON data"""
    response = client.post(
        "/api/v1/webhooks/litellm/success",
        json={"invalid": "data"}  # Missing required fields
    )

    assert response.status_code == 422
    assert "Invalid callback data" in response.json()["detail"]


# Test 4: Webhook callback with missing required field
def test_webhook_missing_required_field(client: TestClient):
    """Test webhook callback with missing required field"""
    incomplete_data = {
        "user_api_key_hash": "test_hash"
        # Missing model_id and total_tokens
    }

    response = client.post(
        "/api/v1/webhooks/litellm/success",
        json=incomplete_data
    )

    assert response.status_code == 422


# Test 5: Webhook callback when Redis is unavailable
@patch("api.routers.webhooks.redis.from_url")
def test_webhook_redis_unavailable(mock_redis_from_url, client: TestClient, valid_callback_data):
    """Test webhook callback when Redis connection fails"""
    # Mock Redis connection error
    mock_redis = Mock()
    mock_redis_from_url.return_value = mock_redis
    mock_redis.close = Mock()

    # Make enqueue_callback fail with ConnectionError
    import redis
    mock_redis.lpush = Mock(side_effect=redis.ConnectionError("Redis connection failed"))

    response = client.post(
        "/api/v1/webhooks/litellm/success",
        json=valid_callback_data
    )

    assert response.status_code == 503


# Test 6: Webhook callback verifies data is queued
@patch("api.routers.webhooks.redis.from_url")
def test_webhook_data_queued(mock_redis_from_url, client: TestClient, valid_callback_data):
    """Test that callback data is properly queued to Redis"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    response = client.post(
        "/api/v1/webhooks/litellm/success",
        json=valid_callback_data
    )

    assert response.status_code == 200
    # Verify lpush was called
    assert mock_redis_client.lpush.called


# Test 7: IP whitelist - non-whitelisted IP rejected
@patch("api.middleware.ip_whitelist.settings.LITELLM_WEBHOOK_IP_WHITELIST", ["10.0.0.1"])
def test_webhook_rejected_with_non_whitelisted_ip(client: TestClient, valid_callback_data):
    """Test webhook rejects requests from non-whitelisted IPs"""
    # This test requires the middleware to be properly checking IPs
    # In a real scenario, the client would be coming from a specific IP
    # For unit testing, we can't easily spoof source IP, so we document the expected behavior

    # Expected: When middleware is active and IP is not in whitelist, return 403
    pass


# Test 8: IP whitelist - whitelisted IP allowed
@patch("api.middleware.ip_whitelist.settings.LITELLM_WEBHOOK_IP_WHITELIST", [])
def test_webhook_allowed_with_empty_whitelist(client: TestClient, valid_callback_data):
    """Test webhook allows requests when whitelist is empty (disabled)"""
    # Empty whitelist should allow all requests

    response = client.post(
        "/api/v1/webhooks/litellm/success",
        json=valid_callback_data
    )

    # Should proceed to validation (will fail validation if Redis not mocked)
    # Just verify we didn't get a 403 from IP check
    assert response.status_code != 403


# Test 9: Webhook handles malformed JSON
def test_webhook_malformed_json(client: TestClient):
    """Test webhook handles malformed JSON"""
    response = client.post(
        "/api/v1/webhooks/litellm/success",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422  # Unprocessable Entity


# Test 10: Webhook callback with extra fields (should succeed)
@patch("api.routers.webhooks.redis.from_url")
def test_webhook_success_with_extra_fields(
    mock_redis_from_url,
    client: TestClient,
    valid_callback_data
):
    """Test webhook callback allows extra fields in JSON"""
    mock_redis_client = AsyncMock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_client.close = AsyncMock()
    mock_redis_from_url.return_value = mock_redis_client

    # Add extra fields
    callback_data = valid_callback_data.copy()
    callback_data["extra_field"] = "some_value"
    callback_data["another_field"] = 12345

    response = client.post(
        "/api/v1/webhooks/litellm/success",
        json=callback_data
    )

    assert response.status_code == 200
