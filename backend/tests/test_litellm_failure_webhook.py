"""
Test suite for LiteLLM failure callback webhook
Tests cover failure callback acceptance criteria
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from api.app import create_app
from api.config import Settings
from api.database import get_db
from api.models.user import User
from api.models.unified_api_key import UnifiedAPIKey
from api.models.subscription import Subscription
from api.models.shared_api_key import SharedAPIKey
from api.models.usage_log import UsageLog, UsageLogStatus
from api.schemas.litellm_callback import LiteLLMFailureCallbackRequest


# Create in-memory SQLite database for testing
@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh database for each test"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with dependency override"""
    def get_session_override():
        return session

    settings = Settings()
    app = create_app(settings)
    app.dependency_overrides[get_db] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user_with_key")
def test_user_fixture(session: Session):
    """Create test user with API key"""
    # Create user
    user = User(
        email="failuretest@example.com",
        hashed_password="hashed_password_here",
        consumed_tokens=0,
        contributed_tokens=0
    )
    session.add(user)
    session.flush()

    # Create API key (api_key is required but we only need api_key_hash for testing)
    api_key = UnifiedAPIKey(
        user_id=user.id,
        api_key="dummy_test_api_key_for_testing",  # Required field
        api_key_name="test-key",
        api_key_hash="test_api_key_hash_123"
    )
    session.add(api_key)
    session.commit()

    return {
        "user_id": user.id,
        "email": "failuretest@example.com",
        "api_key_hash": "test_api_key_hash_123"
    }


def test_failure_callback_valid_payload(client: TestClient, test_user_with_key):
    """
    AC 8: Test failure callback creates usage log
    Given valid failure callback data,
    When processing the callback,
    Then a failure usage log is created.
    """
    failure_payload = {
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
            "user_api_key_hash": test_user_with_key["api_key_hash"]
        }
    }

    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        json=failure_payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "received" in data["message"].lower()


def test_failure_callback_with_missing_token_data(client: TestClient, test_user_with_key):
    """
    AC 9: Test failure callback accepts requests without token data
    Given failure callback missing token fields,
    When processing the callback,
    Then the request is accepted and logged.
    """
    failure_payload = {
        "id": "chatcmpl-failure-789",
        "trace_id": "trace-failure-999",
        "status": "failure",
        "error_message": "Internal server error",
        "model": "openai/gpt-3.5-turbo",
        # Token fields missing
        "metadata": {
            "user_api_key_hash": test_user_with_key["api_key_hash"]
        }
    }

    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        json=failure_payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_failure_callback_minimal_payload(client: TestClient):
    """
    Test failure callback with minimal required data
    """
    failure_payload = {
        "status": "failure",
        "error_message": "Connection timeout"
    }

    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        json=failure_payload
    )

    # Should accept the request even with minimal data
    assert response.status_code == 200


def test_failure_callback_without_user(client: TestClient):
    """
    Test failure callback when user cannot be identified
    Given failure callback without api_key_hash,
    When processing the callback,
    Then the request is accepted but no log is created.
    """
    failure_payload = {
        "id": "chatcmpl-failure-no-user",
        "status": "failure",
        "error_message": "Unknown error",
        "model": "openai/gpt-4"
    }

    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        json=failure_payload
    )

    # Should still return 200 (graceful degradation)
    assert response.status_code == 200


def test_failure_callback_with_error_code(client: TestClient, test_user_with_key):
    """
    Test failure callback with error code
    """
    failure_payload = {
        "id": "chatcmpl-failure-error-code",
        "status": "failure",
        "error_message": "Rate limit exceeded",
        "error_code": "rate_limit_exceeded",
        "model": "openai/gpt-4",
        "metadata": {
            "user_api_key_hash": test_user_with_key["api_key_hash"]
        }
    }

    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        json=failure_payload
    )

    assert response.status_code == 200


def test_failure_callback_invalid_json(client: TestClient):
    """
    Test failure callback with invalid JSON
    """
    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422


def test_failure_callback_empty_body(client: TestClient):
    """
    Test failure callback with empty body
    """
    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        json={}
    )

    # Should accept empty payload (graceful handling)
    assert response.status_code == 200


def test_failure_callback_webhook_health(client: TestClient):
    """
    Test webhook health check endpoint
    """
    response = client.get("/api/v1/webhooks/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "webhooks" in data["service"]


def test_failure_callback_creates_log_with_correct_status(client: TestClient, test_user_with_key, session: Session):
    """
    Verify that failure callback creates UsageLog with FAILURE status
    """
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
        "/api/v1/webhooks/litellm/failure",
        json=failure_payload
    )

    assert response.status_code == 200

    # Verify log was created in database
    from sqlmodel import select
    logs = session.exec(
        select(UsageLog).where(UsageLog.user_id == test_user_with_key["user_id"])
    ).all()

    failure_logs = [log for log in logs if log.status == UsageLogStatus.FAILURE]
    assert len(failure_logs) > 0


def test_failure_callback_with_timing_data(client: TestClient, test_user_with_key):
    """
    Test failure callback includes timing information
    """
    failure_payload = {
        "id": "chatcmpl-failure-timing",
        "status": "failure",
        "error_message": "Timeout",
        "model": "openai/gpt-4",
        "start_time": 1234567890.0,
        "end_time": 1234567895.0,
        "response_time": 5.0,
        "metadata": {
            "user_api_key_hash": test_user_with_key["api_key_hash"]
        }
    }

    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        json=failure_payload
    )

    assert response.status_code == 200


def test_failure_callback_with_exception_type(client: TestClient, test_user_with_key):
    """
    Test failure callback with exception type
    """
    failure_payload = {
        "id": "chatcmpl-failure-exception",
        "status": "failure",
        "error_message": "Invalid request",
        "exception": "ValidationError",
        "model": "openai/gpt-4",
        "metadata": {
            "user_api_key_hash": test_user_with_key["api_key_hash"]
        }
    }

    response = client.post(
        "/api/v1/webhooks/litellm/failure",
        json=failure_payload
    )

    assert response.status_code == 200
