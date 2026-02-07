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
    process_callback,
    extract_api_key_hash,
    extract_model_id
)
from api.models.user import User
from api.models.shared_api_key import SharedAPIKey, APIKeyProvider
from api.models.subscription import Subscription
from api.models.unified_api_key import UnifiedAPIKey
from api.schemas.litellm_callback import LiteLLMSpendlogCallbackRequest


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
    """Valid callback data matching actual LiteLLM structure"""
    return {
        "id": "chatcmpl-test123",
        "trace_id": "trace-123",
        "call_type": "acompletion",
        "cache_hit": False,
        "stream": True,
        "status": "success",
        "custom_llm_provider": "openai",
        "startTime": 1768809251.711881,
        "endTime": 1768809253.019879,
        "completionStartTime": 1768809251.911402,
        "response_time": 0.19952106475830078,
        "model": "openai/Qwen/Qwen2.5-3B-Instruct",
        "model_id": "model-123",
        "total_tokens": 1500,
        "prompt_tokens": 500,
        "completion_tokens": 1000,
        "response_cost": 0.0,
        "metadata": {
            "user_api_key_hash": "litellm_key_hash"
        },
        "hidden_params": {
            "model_id": "model-123",
            "api_base": "http://localhost:8000/v1"
        }
    }


# Test 1: Parse valid callback data
def test_parse_callback_data_success(valid_callback_data):
    """Test parsing valid callback data"""
    result = parse_callback_data(valid_callback_data)
    assert result is not None
    assert isinstance(result, LiteLLMSpendlogCallbackRequest)
    assert result.metadata.user_api_key_hash == "litellm_key_hash"
    assert result.model_id == "model-123"
    assert result.total_tokens == 1500


# Test 2: Extract api_key_hash from callback
def test_extract_api_key_hash_success(valid_callback_data):
    """Test extracting api_key_hash from callback"""
    callback = parse_callback_data(valid_callback_data)
    result = extract_api_key_hash(callback)
    assert result == "litellm_key_hash"


# Test 3: Extract api_key_hash when missing
def test_extract_api_key_hash_missing():
    """Test extracting api_key_hash when metadata is None"""
    from api.schemas.litellm_callback import LiteLLMSpendlogCallbackRequest
    callback_data = {
        "id": "chatcmpl-test",
        "trace_id": "trace-test",
        "call_type": "acompletion",
        "custom_llm_provider": "openai",
        "startTime": 1768809251.711881,
        "endTime": 1768809253.019879,
        "response_time": 0.199,
        "model": "openai/gpt-4",
        "total_tokens": 100,
        "prompt_tokens": 50,
        "completion_tokens": 50,
        "response_cost": 0.0
    }
    callback = LiteLLMSpendlogCallbackRequest(**callback_data)
    result = extract_api_key_hash(callback)
    assert result is None


# Test 4: Extract model_id from callback (root level)
def test_extract_model_id_root_level(valid_callback_data):
    """Test extracting model_id from root level"""
    callback = parse_callback_data(valid_callback_data)
    result = extract_model_id(callback)
    assert result == "model-123"


# Test 5: Extract model_id from callback (hidden_params)
def test_extract_model_id_hidden_params():
    """Test extracting model_id from hidden_params when root is None"""
    from api.schemas.litellm_callback import LiteLLMSpendlogCallbackRequest, LiteLLMHiddenParams
    callback_data = {
        "id": "chatcmpl-test",
        "trace_id": "trace-test",
        "call_type": "acompletion",
        "custom_llm_provider": "openai",
        "startTime": 1768809251.711881,
        "endTime": 1768809253.019879,
        "response_time": 0.199,
        "model": "openai/gpt-4",
        "total_tokens": 100,
        "prompt_tokens": 50,
        "completion_tokens": 50,
        "response_cost": 0.0,
        "hidden_params": {
            "model_id": "model-from-hidden"
        }
    }
    callback = LiteLLMSpendlogCallbackRequest(**callback_data)
    result = extract_model_id(callback)
    assert result == "model-from-hidden"


# Test 6: Parse callback data with missing fields
def test_parse_callback_data_missing_fields():
    """Test parsing callback data with missing required fields"""
    invalid_data = {
        "id": "test"
        # Missing many required fields like trace_id, custom_llm_provider, total_tokens, etc.
    }
    result = parse_callback_data(invalid_data)
    assert result is None


# Test 7: Find user by api_key_hash - success
def test_find_user_by_api_key_hash_success(session: Session, test_unified_api_key: UnifiedAPIKey, test_user_consumer: User):
    """Test finding user by api_key_hash"""
    result = find_user_by_api_key_hash(session, "litellm_key_hash")
    assert result is not None
    assert result.id == test_user_consumer.id
    assert result.email == "consumer@example.com"


# Test 8: Find user by api_key_hash - not found
def test_find_user_by_api_key_hash_not_found(session: Session):
    """Test finding user with non-existent api_key_hash"""
    result = find_user_by_api_key_hash(session, "nonexistent_hash")
    assert result is None


# Test 9: Find subscription by model_id - success
def test_find_subscription_by_model_id_success(session: Session, test_subscription: Subscription):
    """Test finding subscription by model_id"""
    result = find_subscription_by_model_id(session, "model-123")
    assert result is not None
    assert result.id == test_subscription.id
    assert result.model_id == "model-123"


# Test 10: Find subscription by model_id - not found
def test_find_subscription_by_model_id_not_found(session: Session):
    """Test finding subscription with non-existent model_id"""
    result = find_subscription_by_model_id(session, "nonexistent_model")
    assert result is None


# Test 11: Update token statistics - consumer only
def test_update_token_statistics_consumer_only(
    session: Session,
    test_user_consumer: User,
    valid_callback_data
):
    """Test updating token statistics for consumer only (no subscription)"""
    callback = LiteLLMSpendlogCallbackRequest(**valid_callback_data)

    result = update_token_statistics(session, callback, test_user_consumer, subscription=None)

    assert result is True
    # Refresh user from database
    session.refresh(test_user_consumer)
    assert test_user_consumer.consumed_tokens == 1500
    assert test_user_consumer.contributed_tokens == 0


# Test 12: Update token statistics - consumer and contributor
def test_update_token_statistics_consumer_and_contributor(
    session: Session,
    test_user_consumer: User,
    test_user_contributor: User,
    test_shared_api_key: SharedAPIKey,
    test_subscription: Subscription,
    valid_callback_data
):
    """Test updating token statistics for both consumer and contributor"""
    callback = LiteLLMSpendlogCallbackRequest(**valid_callback_data)

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


# Test 13: Enqueue callback to Redis
def test_enqueue_callback_success(valid_callback_data):
    """Test enqueuing callback to Redis"""
    mock_redis = Mock()
    mock_redis.lpush = Mock(return_value=True)

    result = enqueue_callback(mock_redis, valid_callback_data)

    assert result is True
    mock_redis.lpush.assert_called_once()


# Test 14: Process callback - end to end
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


# Test 15: Process callback - invalid data
def test_process_callback_invalid_data(session: Session):
    """Test processing invalid callback data"""
    invalid_data = {"invalid": "data"}

    result = process_callback(session, invalid_data)

    # Should return False (processing failed)
    assert result is False


# Test 16: Process callback - missing subscription (graceful handling)
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
