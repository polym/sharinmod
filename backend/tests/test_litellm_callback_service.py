"""
Unit tests for LiteLLM callback service
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import Mock, MagicMock

from api.services.litellm_callback_service import (
    parse_callback_data,
    find_user_by_api_key_hash,
    find_subscription_by_model_id,
    update_token_statistics,
    enqueue_callback,
    process_callback
)
from api.models.user import User
from api.models.shared_api_key import SharedAPIKey, APIKeyProvider
from api.models.subscription import Subscription
from api.models.unified_api_key import UnifiedAPIKey
from api.schemas.litellm_callback import LiteLLMCallbackRequest


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


@pytest.fixture(name="test_user_consumer")
def test_user_consumer_fixture(session: Session):
    """Create a test user who consumes tokens"""
    user = User(
        email="consumer@example.com",
        hashed_password="$2b$12$test_hash",
        litellm_user_id="consumer@example.com",
        consumed_tokens=0,
        contributed_tokens=0
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_user_contributor")
def test_user_contributor_fixture(session: Session):
    """Create a test user who contributes tokens"""
    user = User(
        email="contributor@example.com",
        hashed_password="$2b$12$test_hash",
        litellm_user_id="contributor@example.com",
        consumed_tokens=0,
        contributed_tokens=0
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_shared_api_key")
def test_shared_api_key_fixture(session: Session, test_user_contributor: User):
    """Create a test shared API key"""
    api_key = SharedAPIKey(
        user_id=test_user_contributor.id,
        provider=APIKeyProvider.BIGMODEL,
        encrypted_api_key="encrypted_key",
        total_requests=0,
        total_tokens=0
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return api_key


@pytest.fixture(name="test_subscription")
def test_subscription_fixture(session: Session, test_shared_api_key: SharedAPIKey, test_user_contributor: User):
    """Create a test subscription"""
    subscription = Subscription(
        model_id="model-123",
        shared_api_key_id=test_shared_api_key.id,
        user_id=test_user_contributor.id
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


@pytest.fixture(name="test_unified_api_key")
def test_unified_api_key_fixture(session: Session, test_user_consumer: User):
    """Create a test unified API key"""
    unified_key = UnifiedAPIKey(
        user_id=test_user_consumer.id,
        api_key="sk_test_key_12345",
        litellm_key="litellm_key_hash",
        api_key_hash="litellm_key_hash"
    )
    session.add(unified_key)
    session.commit()
    session.refresh(unified_key)
    return unified_key


@pytest.fixture(name="valid_callback_data")
def valid_callback_data_fixture():
    """Valid callback data"""
    return {
        "user_api_key_hash": "litellm_key_hash",
        "model_id": "model-123",
        "total_tokens": 1500,
        "start_time": "2026-02-01T10:00:00Z",
        "end_time": "2026-02-01T10:00:05Z"
    }


# Test 1: Parse valid callback data
def test_parse_callback_data_success(valid_callback_data):
    """Test parsing valid callback data"""
    result = parse_callback_data(valid_callback_data)
    assert result is not None
    assert isinstance(result, LiteLLMCallbackRequest)
    assert result.user_api_key_hash == "litellm_key_hash"
    assert result.model_id == "model-123"
    assert result.total_tokens == 1500


# Test 2: Parse callback data with missing fields
def test_parse_callback_data_missing_fields():
    """Test parsing callback data with missing fields"""
    invalid_data = {
        "user_api_key_hash": "test_hash"
        # Missing model_id and total_tokens
    }
    result = parse_callback_data(invalid_data)
    assert result is None


# Test 3: Find user by api_key_hash - success
def test_find_user_by_api_key_hash_success(session: Session, test_unified_api_key: UnifiedAPIKey, test_user_consumer: User):
    """Test finding user by api_key_hash"""
    result = find_user_by_api_key_hash(session, "litellm_key_hash")
    assert result is not None
    assert result.id == test_user_consumer.id
    assert result.email == "consumer@example.com"


# Test 4: Find user by api_key_hash - not found
def test_find_user_by_api_key_hash_not_found(session: Session):
    """Test finding user with non-existent api_key_hash"""
    result = find_user_by_api_key_hash(session, "nonexistent_hash")
    assert result is None


# Test 5: Find subscription by model_id - success
def test_find_subscription_by_model_id_success(session: Session, test_subscription: Subscription):
    """Test finding subscription by model_id"""
    result = find_subscription_by_model_id(session, "model-123")
    assert result is not None
    assert result.id == test_subscription.id
    assert result.model_id == "model-123"


# Test 6: Find subscription by model_id - not found
def test_find_subscription_by_model_id_not_found(session: Session):
    """Test finding subscription with non-existent model_id"""
    result = find_subscription_by_model_id(session, "nonexistent_model")
    assert result is None


# Test 7: Update token statistics - consumer only
def test_update_token_statistics_consumer_only(
    session: Session,
    test_user_consumer: User,
    valid_callback_data
):
    """Test updating token statistics for consumer only (no subscription)"""
    callback = LiteLLMCallbackRequest(**valid_callback_data)

    result = update_token_statistics(session, callback, test_user_consumer, subscription=None)

    assert result is True
    # Refresh user from database
    session.refresh(test_user_consumer)
    assert test_user_consumer.consumed_tokens == 1500
    assert test_user_consumer.contributed_tokens == 0


# Test 8: Update token statistics - consumer and contributor
def test_update_token_statistics_consumer_and_contributor(
    session: Session,
    test_user_consumer: User,
    test_user_contributor: User,
    test_shared_api_key: SharedAPIKey,
    test_subscription: Subscription,
    valid_callback_data
):
    """Test updating token statistics for both consumer and contributor"""
    callback = LiteLLMCallbackRequest(**valid_callback_data)

    result = update_token_statistics(session, callback, test_user_consumer, test_subscription)

    assert result is True

    # Refresh from database
    session.refresh(test_user_consumer)
    session.refresh(test_user_contributor)
    session.refresh(test_shared_api_key)

    # Consumer stats
    assert test_user_consumer.consumed_tokens == 1500

    # Contributor stats
    assert test_user_contributor.contributed_tokens == 1500

    # Shared API key stats
    assert test_shared_api_key.total_requests == 1
    assert test_shared_api_key.total_tokens == 1500


# Test 9: Enqueue callback to Redis
def test_enqueue_callback_success(valid_callback_data):
    """Test enqueuing callback to Redis"""
    mock_redis = Mock()
    mock_redis.lpush = Mock(return_value=True)

    result = enqueue_callback(mock_redis, valid_callback_data)

    assert result is True
    mock_redis.lpush.assert_called_once()


# Test 10: Process callback - end to end
def test_process_callback_success(
    session: Session,
    test_unified_api_key: UnifiedAPIKey,
    test_user_consumer: User,
    test_user_contributor: User,
    test_shared_api_key: SharedAPIKey,
    test_subscription: Subscription,
    valid_callback_data
):
    """Test processing a callback end to end"""
    result = process_callback(session, valid_callback_data)

    assert result is True

    # Verify statistics were updated
    session.refresh(test_user_consumer)
    session.refresh(test_user_contributor)
    session.refresh(test_shared_api_key)

    assert test_user_consumer.consumed_tokens == 1500
    assert test_user_contributor.contributed_tokens == 1500
    assert test_shared_api_key.total_requests == 1
    assert test_shared_api_key.total_tokens == 1500


# Test 11: Process callback - invalid data
def test_process_callback_invalid_data(session: Session):
    """Test processing invalid callback data"""
    invalid_data = {"invalid": "data"}

    result = process_callback(session, invalid_data)

    # Should return False (processing failed)
    assert result is False


# Test 12: Process callback - missing subscription (graceful handling)
def test_process_callback_missing_subscription(
    session: Session,
    test_unified_api_key: UnifiedAPIKey,
    test_user_consumer: User,
    valid_callback_data
):
    """Test processing callback when subscription doesn't exist (should not fail)"""
    # Use a model_id that doesn't have a subscription
    callback_data = valid_callback_data.copy()
    callback_data["model_id"] = "nonexistent_model"

    result = process_callback(session, callback_data)

    # Should still succeed (just log warning)
    assert result is True

    # Consumer stats should still be updated
    session.refresh(test_user_consumer)
    assert test_user_consumer.consumed_tokens == 1500
