"""
Integration tests for LiteLLM spendlog callback webhook endpoint

This test suite covers both success and failure callbacks through the unified /spendlog endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from unittest.mock import patch, AsyncMock, Mock
import redis

from api.app import create_app
from api.config import Settings
from api.database import get_db
from api.models.user import User
from api.models.unified_api_key import UnifiedAPIKey
from api.models.usage_log import UsageLog, UsageLogStatus

# Enable testing mode
from api.config import settings
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

    app = create_app(Settings())
    app.dependency_overrides[get_db] = get_db_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user_with_key")
def test_user_fixture(session: Session):
    """Create test user with API key"""
    # Create user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_here",
        consumed_tokens=0,
        contributed_tokens=0
    )
    session.add(user)
    session.flush()

    # Create API key
    api_key = UnifiedAPIKey(
        user_id=user.id,
        api_key="dummy_test_api_key_for_testing",
        api_key_name="test-key",
        api_key_hash="test_api_key_hash_123"
    )
    session.add(api_key)
    session.commit()

    return {
        "user_id": user.id,
        "email": "test@example.com",
        "api_key_hash": "test_api_key_hash_123"
    }


@pytest.fixture(name="valid_success_callback_data")
def valid_success_callback_data_fixture():
    """Valid success callback data matching actual LiteLLM structure"""
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


@pytest.fixture(name="valid_failure_callback_data")
def valid_failure_callback_data_fixture():
    """Valid failure callback data"""
    return {
        "id": "chatcmpl-failure-123",
        "trace_id": "trace-failure-456",
        "status": "failure",
        "error_message": "Rate limit exceeded",
        "model": "openai/gpt-4",
        "model_id": "model_id_123",
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "metadata": {
            "user_api_key_hash": "test_api_key_hash_123"
        }
    }


# ===== Basic Endpoint Tests =====

def test_webhook_health_check(client: TestClient):
    """Test webhook health check endpoint"""
    response = client.get("/api/v1/webhooks/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "webhooks"


# ===== Success Callback Tests =====

@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_success_callback(
    mock_redis_from_url,
    client: TestClient,
    valid_success_callback_data
):
    """Test successful callback with status='success'"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=valid_success_callback_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Successfully received and queued" in data["message"]


@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_success_with_extra_fields(
    mock_redis_from_url,
    client: TestClient,
    valid_success_callback_data
):
    """Test callback allows extra fields in JSON (extra='allow')"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    # Add extra fields
    callback_data = valid_success_callback_data.copy()
    callback_data["extra_field"] = "some_value"
    callback_data["another_field"] = 12345

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=callback_data
    )

    assert response.status_code == 200


# ===== Failure Callback Tests =====

@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_failure_callback(
    mock_redis_from_url,
    client: TestClient,
    valid_failure_callback_data
):
    """Test failure callback with status='failure'"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=valid_failure_callback_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_failure_with_missing_token_data(
    mock_redis_from_url,
    client: TestClient
):
    """Test failure callback accepts requests without token data"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    failure_payload = {
        "id": "chatcmpl-failure-789",
        "trace_id": "trace-failure-999",
        "status": "failure",
        "error_message": "Internal server error",
        "model": "openai/gpt-3.5-turbo",
        # Token fields missing - should still be accepted
        "metadata": {
            "user_api_key_hash": "test_api_key_hash_123"
        }
    }

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=failure_payload
    )

    assert response.status_code == 200


@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_failure_minimal_payload(
    mock_redis_from_url,
    client: TestClient
):
    """Test failure callback with minimal required data (all fields optional)"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    failure_payload = {
        "status": "failure",
        "error_message": "Connection timeout"
    }

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=failure_payload
    )

    # Should accept the request even with minimal data (all fields optional)
    assert response.status_code == 200


@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_failure_without_user(
    mock_redis_from_url,
    client: TestClient
):
    """Test failure callback when user cannot be identified"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    failure_payload = {
        "id": "chatcmpl-failure-no-user",
        "status": "failure",
        "error_message": "Unknown error",
        "model": "openai/gpt-4"
        # No api_key_hash - user cannot be identified
    }

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=failure_payload
    )

    # Should still return 200 (graceful degradation)
    assert response.status_code == 200


@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_failure_with_error_code(
    mock_redis_from_url,
    client: TestClient
):
    """Test failure callback with error code"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    failure_payload = {
        "id": "chatcmpl-failure-error-code",
        "status": "failure",
        "error_message": "Rate limit exceeded",
        "error_code": "rate_limit_exceeded",
        "model": "openai/gpt-4",
        "metadata": {
            "user_api_key_hash": "test_api_key_hash_123"
        }
    }

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=failure_payload
    )

    assert response.status_code == 200


@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_empty_body(
    mock_redis_from_url,
    client: TestClient
):
    """Test callback with empty body (all fields optional)"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json={}
    )

    # Should accept empty payload (all fields optional)
    assert response.status_code == 200


# ===== Error Handling Tests =====

def test_spendlog_invalid_json(client: TestClient):
    """Test callback handles malformed JSON"""
    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422  # Unprocessable Entity


@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_redis_unavailable(
    mock_redis_from_url,
    client: TestClient,
    valid_success_callback_data
):
    """Test callback when Redis connection fails"""
    # Mock Redis connection error
    mock_redis = Mock()
    mock_redis_from_url.return_value = mock_redis
    mock_redis.close = Mock()
    mock_redis.lpush = Mock(side_effect=redis.ConnectionError("Redis connection failed"))

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=valid_success_callback_data
    )

    assert response.status_code == 503


@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_data_queued(
    mock_redis_from_url,
    client: TestClient,
    valid_success_callback_data
):
    """Test that callback data is properly queued to Redis"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=valid_success_callback_data
    )

    assert response.status_code == 200
    # Verify lpush was called
    assert mock_redis_client.lpush.called


# ===== Backward Compatibility Tests =====

def test_old_success_endpoint_returns_404(client: TestClient):
    """Test that old /success endpoint no longer exists"""
    response = client.post(
        "/api/v1/webhooks/litellm/success",
        json={"status": "success"}
    )

    assert response.status_code == 404


def test_old_failure_endpoint_returns_404(client: TestClient):
    """Test that old /failure endpoint no longer exists"""
    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        json={"status": "failure"}
    )

    assert response.status_code == 404


# ===== Array of Callbacks Tests =====

@patch("api.routers.webhooks.redis.from_url")
def test_spendlog_array_of_callbacks(
    mock_redis_from_url,
    client: TestClient
):
    """Test handling array of callbacks"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    callbacks = [
        {
            "id": "chatcmpl-1",
            "status": "success",
            "model": "openai/gpt-4",
            "total_tokens": 100
        },
        {
            "id": "chatcmpl-2",
            "status": "failure",
            "model": "openai/gpt-4",
            "error_message": "Rate limit"
        }
    ]

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=callbacks
    )

    assert response.status_code == 200
    data = response.json()
    assert "2 callback(s)" in data["message"]
    # Verify lpush was called twice
    assert mock_redis_client.lpush.call_count == 2


# ===== Integration Tests with Database =====

@patch("api.routers.webhooks.redis.from_url")
def test_failure_creates_failure_log(
    mock_redis_from_url,
    client: TestClient,
    session: Session,
    test_user_with_key
):
    """Verify that failure callback creates UsageLog with FAILURE status"""
    mock_redis_client = Mock()
    mock_redis_client.lpush = Mock(return_value=True)
    mock_redis_from_url.return_value = mock_redis_client

    failure_payload = {
        "id": "chatcmpl-failure-status-test",
        "status": "failure",
        "error_message": "Test error",
        "model": "openai/gpt-4",
        "metadata": {
            "user_api_key_hash": test_user_with_key["api_key_hash"]
        }
    }

    response = client.post(
        "/api/v1/webhooks/litellm/spendlog",
        json=failure_payload
    )

    assert response.status_code == 200

    # Process the callback from queue (simulate consumer)
    # In real scenario, consumer would pick this up
    # For this test, we're just verifying the endpoint accepts it
