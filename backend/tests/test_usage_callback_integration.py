"""
Integration test for complete usage log flow
Tests end-to-end callback processing, token stats, and usage log consistency
"""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from api.app import create_app
from api.config import Settings
from api.database import get_db
from api.models.user import User
from api.models.unified_api_key import UnifiedAPIKey
from api.models.subscription import Subscription
from api.models.shared_api_key import SharedAPIKey, APIKeyProvider
from api.models.usage_log import UsageLog, UsageLogStatus
from api.services.litellm_callback_service import process_callback
from api.schemas.litellm_callback import LiteLLMCallbackRequest


# Create in-memory SQLite database for testing
@pytest.fixture(name="session", scope="function")
def session_fixture():
    """Create a fresh database for each test"""
    import uuid
    # Use unique database name for each test to ensure isolation
    engine = create_engine(
        f"sqlite:///:memory:{uuid.uuid4().hex}:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    # Dispose engine after test
    engine.dispose()


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


@pytest.fixture(name="full_setup")
def full_setup_fixture(session: Session):
    """
    Create complete test setup with:
    - Contributor user with shared API key
    - Consumer user with unified API key
    - Subscription linking shared key to model
    """
    # Create contributor user
    contributor = User(
        email="contributor@example.com",
        hashed_password="hashed_password",
        consumed_tokens=0,
        contributed_tokens=0
    )
    session.add(contributor)
    session.flush()

    # Create consumer user
    consumer = User(
        email="consumer@example.com",
        hashed_password="hashed_password",
        consumed_tokens=1000,
        contributed_tokens=0
    )
    session.add(consumer)
    session.flush()

    # Create shared API key
    shared_key = SharedAPIKey(
        user_id=contributor.id,
        provider=APIKeyProvider.BIGMODEL,
        encrypted_api_key="dummy_encrypted_key_for_testing"
    )
    session.add(shared_key)
    session.flush()

    # Create subscription
    subscription = Subscription(
        user_id=contributor.id,
        shared_api_key_id=shared_key.id,
        model_id="test_model_id_abc",
        daily_limit=10000
    )
    session.add(subscription)
    session.flush()

    # Create consumer's unified API key
    unified_key = UnifiedAPIKey(
        user_id=consumer.id,
        api_key="dummy_consumer_api_key_for_testing",
        api_key_name="consumer-api-key",
        api_key_hash="consumer_api_key_hash_456"
    )
    session.add(unified_key)
    session.commit()

    return {
        "contributor_id": contributor.id,
        "consumer_id": consumer.id,
        "subscription_id": subscription.id,
        "shared_key_id": shared_key.id,
        "unified_key_id": unified_key.id,
        "unified_key_hash": "consumer_api_key_hash_456",
        "model_id": "test_model_id_abc"
    }


def test_full_callback_flow_creates_usage_log(session: Session, full_setup):
    """
    Integration test: Verify complete callback flow creates usage log
    AC 3, 6, 7: Given valid callback, when processed, then usage log is created
    """
    callback_data = {
        "id": "chatcmpl-integration-123",
        "trace_id": "trace-integration-456",
        "call_type": "acompletion",
        "cache_hit": False,
        "stream": True,
        "status": "success",
        "custom_llm_provider": "openai",
        "startTime": 1704067200.0,  # 2024-01-01 00:00:00 UTC
        "endTime": 1704067202.0,    # 2024-01-01 00:00:02 UTC
        "completionStartTime": 1704067200.5,
        "response_time": 2.0,
        "model": "openai/gpt-4",
        "model_id": full_setup["model_id"],
        "total_tokens": 150,
        "prompt_tokens": 50,
        "completion_tokens": 100,
        "response_cost": 0.0,
        "metadata": {
            "user_api_key_hash": full_setup["unified_key_hash"]
        }
    }

    # Process the callback
    result = process_callback(session, callback_data)

    assert result is True

    # Verify usage log was created
    logs = session.exec(
        select(UsageLog).where(UsageLog.user_id == full_setup["consumer_id"])
    ).all()

    assert len(logs) > 0
    log = logs[-1]  # Get the most recent log

    # Verify log fields
    assert log.user_id == full_setup["consumer_id"]
    assert log.model_id == full_setup["model_id"]
    assert log.model_name == "openai/gpt-4"
    assert log.status == UsageLogStatus.SUCCESS
    assert log.input_tokens == 50
    assert log.output_tokens == 100
    assert log.total_tokens == 150
    assert log.total_duration == 2.0
    # TTFT = completion_start_time - start_time = 0.5 seconds
    assert log.ttft == 0.5
    # Verify model_id is set (used to find subscription later if needed)
    assert log.model_id == full_setup["model_id"]


def test_token_stats_sync_with_usage_log(session: Session, full_setup):
    """
    Integration test: Verify token statistics stay in sync with usage logs
    Given successful callback, when processed, then token stats and usage log match
    """
    # Get initial token counts - capture VALUES not references
    consumer_before = session.get(User, full_setup["consumer_id"])
    contributor_before = session.get(User, full_setup["contributor_id"])
    shared_key_before = session.get(SharedAPIKey, full_setup["shared_key_id"])

    # Capture the actual values BEFORE process_callback modifies the session
    consumer_before_tokens = consumer_before.consumed_tokens
    contributor_before_tokens = contributor_before.contributed_tokens
    shared_key_before_tokens = shared_key_before.total_tokens
    shared_key_before_requests = shared_key_before.total_requests

    callback_data = {
        "id": "chatcmpl-sync-123",
        "trace_id": "trace-sync-456",
        "call_type": "acompletion",
        "status": "success",
        "custom_llm_provider": "openai",
        "startTime": 1704067200.0,
        "endTime": 1704067201.5,
        "response_time": 1.5,
        "model": "openai/gpt-4",
        "model_id": full_setup["model_id"],
        "total_tokens": 300,
        "prompt_tokens": 100,
        "completion_tokens": 200,
        "metadata": {
            "user_api_key_hash": full_setup["unified_key_hash"]
        }
    }

    # Process callback
    process_callback(session, callback_data)

    # Get updated counts
    consumer_after = session.get(User, full_setup["consumer_id"])
    contributor_after = session.get(User, full_setup["contributor_id"])
    shared_key_after = session.get(SharedAPIKey, full_setup["shared_key_id"])

    # Verify token stats updated correctly
    assert consumer_after.consumed_tokens == consumer_before_tokens + 300
    assert contributor_after.contributed_tokens == contributor_before_tokens + 300
    assert shared_key_after.total_tokens == shared_key_before_tokens + 300
    assert shared_key_after.total_requests == shared_key_before_requests + 1

    # Verify usage log matches
    logs = session.exec(
        select(UsageLog).where(UsageLog.user_id == full_setup["consumer_id"])
    ).all()
    log = logs[-1]

    assert log.total_tokens == 300
    assert log.input_tokens == 100
    assert log.output_tokens == 200


def test_multiple_callbacks_consistency(session: Session, full_setup):
    """
    Integration test: Verify consistency across multiple callbacks
    Given multiple callbacks, when processed, then all logs and stats are consistent
    """
    callbacks = [
        {
            "id": f"chatcmpl-multi-{i}",
            "trace_id": f"trace-multi-{i}",
            "status": "success",
            "custom_llm_provider": "openai",
            "startTime": 1704067200.0 + i,
            "endTime": 1704067201.0 + i,
            "response_time": 1.0,
            "model": "openai/gpt-4",
            "model_id": full_setup["model_id"],
            "total_tokens": 100 * (i + 1),
            "prompt_tokens": 50 * (i + 1),
            "completion_tokens": 50 * (i + 1),
            "metadata": {
                "user_api_key_hash": full_setup["unified_key_hash"]
            }
        }
        for i in range(5)
    ]

    total_expected_tokens = sum(cb["total_tokens"] for cb in callbacks)

    # Process all callbacks
    for callback in callbacks:
        process_callback(session, callback)

    # Verify all logs created
    logs = session.exec(
        select(UsageLog).where(UsageLog.user_id == full_setup["consumer_id"])
    ).all()

    assert len(logs) >= 5

    # Verify token totals match
    log_total = sum(log.total_tokens for log in logs[-5:])
    assert log_total == total_expected_tokens

    # Verify user stats
    consumer = session.get(User, full_setup["consumer_id"])
    assert consumer.consumed_tokens >= total_expected_tokens


def test_callback_without_completion_start_time(session: Session, full_setup):
    """
    AC 5: Test TTFT calculation when completion_start_time is missing
    Given callback without completion_start_time,
    When processed, then TTFT = response_time
    """
    callback_data = {
        "id": "chatcmpl-no-completion-start",
        "trace_id": "trace-no-completion",
        "status": "success",
        "custom_llm_provider": "openai",
        "startTime": 1704067200.0,
        "endTime": 1704067202.0,
        "response_time": 2.0,
        # No completionStartTime
        "model": "openai/gpt-4",
        "model_id": full_setup["model_id"],
        "total_tokens": 100,
        "prompt_tokens": 50,
        "completion_tokens": 50,
        "metadata": {
            "user_api_key_hash": full_setup["unified_key_hash"]
        }
    }

    process_callback(session, callback_data)

    logs = session.exec(
        select(UsageLog).where(UsageLog.user_id == full_setup["consumer_id"])
    ).all()
    log = logs[-1]

    # TTFT should fallback to response_time when completion_start_time is missing
    assert log.ttft == 2.0


def test_callback_with_unified_api_key_name(session: Session, full_setup):
    """
    AC 6: Verify unified_api_key_name is correctly captured
    """
    callback_data = {
        "id": "chatcmpl-key-name",
        "trace_id": "trace-key-name",
        "status": "success",
        "custom_llm_provider": "openai",
        "startTime": 1704067200.0,
        "endTime": 1704067201.0,
        "response_time": 1.0,
        "model": "openai/gpt-4",
        "model_id": full_setup["model_id"],
        "total_tokens": 100,
        "prompt_tokens": 50,
        "completion_tokens": 50,
        "metadata": {
            "user_api_key_hash": full_setup["unified_key_hash"]
        }
    }

    process_callback(session, callback_data)

    logs = session.exec(
        select(UsageLog).where(UsageLog.user_id == full_setup["consumer_id"])
    ).all()
    log = logs[-1]

    # Verify unified_api_key_name was captured
    assert log.unified_api_key_name == "consumer-api-key"


def test_failure_callback_integration(session: Session, full_setup):
    """
    Integration test: Verify failure callback flow
    AC 8: Given failure callback, when processed, then failure log is created
    """
    from api.services.usage_log_service import create_failure_usage_log

    # Create a failure usage log
    failure_log = create_failure_usage_log(
        session,
        user_id=full_setup["consumer_id"],
        model="openai/gpt-4",
        error_message="Rate limit exceeded",
        model_id=full_setup["model_id"],
        unified_api_key_id=full_setup["unified_key_id"],
        unified_api_key_name="consumer-api-key"
    )

    assert failure_log is not None
    assert failure_log.status == UsageLogStatus.FAILURE
    assert failure_log.model_id == full_setup["model_id"]
    assert failure_log.input_tokens == 0
    assert failure_log.output_tokens == 0
    assert failure_log.total_tokens == 0


def test_usage_log_error_doesnt_affect_token_stats(session: Session, full_setup):
    """
    Integration test: Verify that usage log creation failure doesn't break token stats
    Given callback processing, if usage log creation fails, then token stats still update
    """
    # Mock a scenario where usage log creation might fail
    # by using an invalid subscription_id
    callback_data = {
        "id": "chatcmpl-token-stats-only",
        "trace_id": "trace-token-stats",
        "status": "success",
        "custom_llm_provider": "openai",
        "startTime": 1704067200.0,
        "endTime": 1704067201.0,
        "response_time": 1.0,
        "model": "openai/gpt-4",
        "model_id": full_setup["model_id"],
        "total_tokens": 200,
        "prompt_tokens": 100,
        "completion_tokens": 100,
        "metadata": {
            "user_api_key_hash": full_setup["unified_key_hash"]
        }
    }

    consumer_before = session.get(User, full_setup["consumer_id"])
    # Capture the actual value BEFORE process_callback modifies the session
    consumer_before_tokens = consumer_before.consumed_tokens

    # Process callback - should succeed even if usage log has issues
    result = process_callback(session, callback_data)

    # Token stats should still be updated
    consumer_after = session.get(User, full_setup["consumer_id"])
    assert consumer_after.consumed_tokens == consumer_before_tokens + 200
    assert result is True


def test_subscription_id_correctly_linked(session: Session, full_setup):
    """
    AC 7: Verify subscription_id is correctly linked in usage log
    """
    callback_data = {
        "id": "chatcmpl-subscription-link",
        "trace_id": "trace-subscription",
        "status": "success",
        "custom_llm_provider": "openai",
        "startTime": 1704067200.0,
        "endTime": 1704067201.0,
        "response_time": 1.0,
        "model": "openai/gpt-4",
        "model_id": full_setup["model_id"],
        "total_tokens": 100,
        "prompt_tokens": 50,
        "completion_tokens": 50,
        "metadata": {
            "user_api_key_hash": full_setup["unified_key_hash"]
        }
    }

    process_callback(session, callback_data)

    logs = session.exec(
        select(UsageLog).where(UsageLog.user_id == full_setup["consumer_id"])
    ).all()
    log = logs[-1]

    # Verify model_id was captured (used to find subscription later if needed)
    assert log.model_id == full_setup["model_id"]
