import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import patch, AsyncMock

from api.app import create_app
from api.config import settings
from api.database import get_db
from api.models.user import User
from api.models.shared_api_key import SharedAPIKey, APIKeyProvider, APIKeyStatus
from api.utils.jwt import create_access_token
from api.utils.encryption import encrypt_token, decrypt_token

# Enable testing mode to skip LiteLLM calls
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


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """Create a test user"""
    user = User(
        email="testuser@example.com",
        hashed_password="$2b$12$test_hash",
        is_active=True,
        litellm_user_id="testuser@example.com"  # Add default LiteLLM user ID
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: User):
    """Create authentication headers with JWT token"""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(name="mock_validation_success")
def mock_validation_success_fixture():
    """Mock successful API key validation"""
    return {
        "valid": True,
        "message": "API key validation successful",
        "provider_info": {"provider": "bigmodel", "status_code": 200}
    }


@pytest.fixture(name="mock_validation_failure")
def mock_validation_failure_fixture():
    """Mock failed API key validation"""
    return {
        "valid": False,
        "message": "API key authentication failed - invalid credentials",
        "provider_info": None
    }


# Test 1: Successfully share an API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_share_api_key_success(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test successfully sharing an API key"""
    # Mock returns the success dict directly (not a coroutine)
    mock_validate.return_value = mock_validation_success
    
    response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-bigmodel-api-key-12345",
            "api_key_metadata": '{"name": "My BigModel API Key"}'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "bigmodel"
    assert data["status"] == "active"
    assert data["total_uses"] == 0
    assert "encrypted_api_key" not in data  # Should never expose encrypted API key


# Test 2: Reject duplicate provider API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_share_api_key_duplicate_provider(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test rejection of duplicate provider API key"""
    mock_validate.return_value = mock_validation_success
    
    # Share first API key
    client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-bigmodel-api-key-12345"
        },
        headers=auth_headers
    )
    
    # Try to share second API key for same provider
    response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "another-bigmodel-api-key"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already have an api key" in response.json()["detail"].lower()
    assert "bigmodel" in response.json()["detail"]


# Test 3: Reject invalid API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_share_api_key_invalid(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_failure
):
    """Test rejection of invalid API key"""
    mock_validate.return_value = mock_validation_failure
    
    response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "invalid-api-key-12345"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "validation failed" in response.json()["detail"].lower()


# Test 4: Require authentication for sharing
def test_share_api_key_without_auth(client: TestClient):
    """Test that sharing requires authentication"""
    response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        }
    )
    
    assert response.status_code in [401, 403]  # Either is acceptable for unauthenticated


# Test 5: Get my shared API keys (empty)
def test_get_my_shared_api_keys_empty(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test getting shared API keys when none exist"""
    response = client.get("/api/api-keys/my-shared", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


# Test 6: Get my shared API keys (with data)
@patch("api.services.shared_api_key_service.validate_api_key")
def test_get_my_shared_api_keys_with_data(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test getting shared API keys with existing data"""
    mock_validate.return_value = mock_validation_success
    
    # Share an API key
    client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        },
        headers=auth_headers
    )
    
    # Get shared API keys
    response = client.get("/api/api-keys/my-shared", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["provider"] == "bigmodel"
    assert data["items"][0]["status"] == "active"


# Test 7: Require authentication for getting shared API keys
def test_get_my_shared_api_keys_without_auth(client: TestClient):
    """Test that getting shared API keys requires authentication"""
    response = client.get("/api/api-keys/my-shared")
    
    assert response.status_code in [401, 403]  # Either is acceptable for unauthenticated


# Test 8: Test API key encryption/decryption
def test_api_key_encryption():
    """Test that API key encryption and decryption work correctly"""
    original_api_key = "test-secret-api-key-12345"
    
    # Encrypt
    encrypted = encrypt_token(original_api_key)
    assert encrypted != original_api_key
    assert len(encrypted) > len(original_api_key)
    
    # Decrypt
    decrypted = decrypt_token(encrypted)
    assert decrypted == original_api_key


# Test 9: Test sharing multiple providers
@patch("api.services.shared_api_key_service.validate_api_key")
def test_share_multiple_providers(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that user can share API keys from different providers"""
    mock_validate.return_value = mock_validation_success
    
    # Share bigmodel API key
    response1 = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-bigmodel-api-key"
        },
        headers=auth_headers
    )
    assert response1.status_code == 201
    
    # Share z.ai API key
    response2 = client.post(
        "/api/api-keys/share",
        json={
            "provider": "z.ai",
            "api_key": "test-zai-api-key"
        },
        headers=auth_headers
    )
    assert response2.status_code == 201
    
    # Check we have both
    response3 = client.get("/api/api-keys/my-shared", headers=auth_headers)
    assert response3.status_code == 200
    data = response3.json()
    assert data["total"] == 2
    providers = [item["provider"] for item in data["items"]]
    assert "bigmodel" in providers
    assert "z.ai" in providers


# Test 11: Test API key sharing logs usage history
@patch("api.services.shared_api_key_service.validate_api_key")
def test_share_api_key_logs_usage_history(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that API key sharing is logged in usage history"""
    mock_validate.return_value = mock_validation_success
    
    # Share API key
    response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    
    # Check usage history
    history_response = client.get("/api/users/me/api-key-usage", headers=auth_headers)
    assert history_response.status_code == 200
    history_data = history_response.json()
    
    # Should have one SHARED action (enum value is lowercase "shared")
    assert history_data["total"] >= 1
    shared_actions = [item for item in history_data["items"] if item["action"] == "shared"]
    assert len(shared_actions) >= 1


# Test 12: Test LiteLLM integration - successful sync with multiple models
@patch("api.services.shared_api_key_service.validate_api_key")
@patch("api.services.shared_api_key_service.httpx.AsyncClient")
@patch("api.config.settings.TESTING", False)
def test_share_api_key_litellm_success(
    mock_async_client,
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test successful LiteLLM credential and 3 model creation"""
    # Setup user with litellm_user_id
    test_user.litellm_user_id = "testuser@example.com"
    session.add(test_user)
    session.commit()

    # Mock validation
    mock_validate.return_value = mock_validation_success

    # Mock httpx responses
    # Credential check returns 404 (not exists)
    mock_credential_check_response = AsyncMock()
    mock_credential_check_response.status_code = 404
    mock_credential_check_response.text = '{"detail": "Credential not found"}'

    # Credential creation succeeds
    mock_credential_create_response = AsyncMock()
    mock_credential_create_response.status_code = 200
    mock_credential_create_response.text = '{"message": "Credential created"}'
    mock_credential_create_response.raise_for_status = lambda: None

    # 3 model creation responses (glm-4.7, glm-4.6, glm-4.5-air)
    mock_model_responses = []
    for i, model_name in enumerate(["glm-4.7", "glm-4.6", "glm-4.5-air"]):
        resp = AsyncMock()
        resp.status_code = 200
        resp.json = lambda idx=i, name=model_name: {"model_id": f"model-id-{idx+1}", "model_name": name}
        resp.raise_for_status = lambda: None
        resp.text = f'{{"model_id": "model-id-{i+1}"}}'
        mock_model_responses.append(resp)

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    # Chain: credential check, credential create, 3 model creates
    mock_client_instance.get = AsyncMock(return_value=mock_credential_check_response)
    mock_client_instance.post = AsyncMock(side_effect=[
        mock_credential_create_response,
        *mock_model_responses
    ])
    mock_async_client.return_value = mock_client_instance

    # Temporarily disable TESTING mode for this test
    from api import services
    original_testing = services.shared_api_key_service.settings.TESTING
    services.shared_api_key_service.settings.TESTING = False

    try:
        # Share API key
        response = client.post(
            "/api/api-keys/share",
            json={
                "provider": "bigmodel",
                "api_key": "test-bigmodel-api-key-12345"
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "bigmodel"
        assert data["status"] == "active"

        # Verify LiteLLM was called correctly:
        # 1 GET for credential check, 1 POST for credential create, 3 POST for models
        assert mock_client_instance.get.call_count == 1  # Credential check
        assert mock_client_instance.post.call_count == 4  # 1 credential + 3 models
    finally:
        services.shared_api_key_service.settings.TESTING = original_testing


# Test 13: Test LiteLLM integration - credential creation fails
@patch("api.services.shared_api_key_service.validate_api_key")
@patch("api.services.shared_api_key_service.httpx.AsyncClient")
def test_share_api_key_litellm_credential_failure(
    mock_async_client,
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test rollback when LiteLLM credential creation fails"""
    # Setup user with litellm_user_id
    test_user.litellm_user_id = "testuser@example.com"
    session.add(test_user)
    session.commit()
    
    # Mock validation
    mock_validate.return_value = mock_validation_success
    
    # Mock httpx failure
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_client_instance.post = AsyncMock(side_effect=Exception("LiteLLM service unavailable"))
    mock_async_client.return_value = mock_client_instance
    
    # Temporarily disable TESTING mode for this test
    from api import services
    original_testing = services.shared_api_key_service.settings.TESTING
    services.shared_api_key_service.settings.TESTING = False
    
    try:
        # Attempt to share API key
        response = client.post(
            "/api/api-keys/share",
            json={
                "provider": "bigmodel",
                "api_key": "test-bigmodel-api-key-12345"
            },
            headers=auth_headers
        )
        
        # Should fail with 500 error
        assert response.status_code == 500
        assert "Failed to sync API key with LiteLLM" in response.json()["detail"]
        
        # Verify no API key was created in database
        api_keys = session.query(SharedAPIKey).filter_by(user_id=test_user.id).all()
        assert len(api_keys) == 0
    finally:
        services.shared_api_key_service.settings.TESTING = original_testing


# Test 14: Test LiteLLM integration - model creation fails
@patch("api.services.shared_api_key_service.validate_api_key")
@patch("api.services.shared_api_key_service.httpx.AsyncClient")
def test_share_api_key_litellm_model_failure(
    mock_async_client,
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test rollback when LiteLLM model creation fails"""
    # Setup user with litellm_user_id
    test_user.litellm_user_id = "testuser@example.com"
    session.add(test_user)
    session.commit()
    
    # Mock validation
    mock_validate.return_value = mock_validation_success
    
    # Mock httpx - credential succeeds, model fails
    mock_credential_response = AsyncMock()
    mock_credential_response.status_code = 200
    mock_credential_response.raise_for_status = lambda: None  # Sync function, not async
    
    mock_model_response = AsyncMock()
    def raise_error():
        raise Exception("Model creation failed")
    mock_model_response.raise_for_status = raise_error  # Sync function that raises
    
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_client_instance.post = AsyncMock(side_effect=[mock_credential_response, mock_model_response])
    mock_async_client.return_value = mock_client_instance
    
    # Temporarily disable TESTING mode for this test
    from api import services
    original_testing = services.shared_api_key_service.settings.TESTING
    services.shared_api_key_service.settings.TESTING = False
    
    try:
        # Attempt to share API key
        response = client.post(
            "/api/api-keys/share",
            json={
                "provider": "bigmodel",
                "api_key": "test-bigmodel-api-key-12345"
            },
            headers=auth_headers
        )
        
        # Should fail with 500 error
        assert response.status_code == 500
        assert "Failed to sync API key with LiteLLM" in response.json()["detail"]
        
        # Verify no API key was created in database
        api_keys = session.query(SharedAPIKey).filter_by(user_id=test_user.id).all()
        assert len(api_keys) == 0
    finally:
        services.shared_api_key_service.settings.TESTING = original_testing


# Test 15: Test LiteLLM integration - network timeout
@patch("api.services.shared_api_key_service.validate_api_key")
@patch("api.services.shared_api_key_service.httpx.AsyncClient")
def test_share_api_key_litellm_timeout(
    mock_async_client,
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test handling of network timeout during LiteLLM sync"""
    # Setup user with litellm_user_id
    test_user.litellm_user_id = "testuser@example.com"
    session.add(test_user)
    session.commit()
    
    # Mock validation
    mock_validate.return_value = mock_validation_success
    
    # Mock httpx timeout
    import httpx as real_httpx
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_client_instance.post = AsyncMock(side_effect=real_httpx.TimeoutException("Request timeout"))
    mock_async_client.return_value = mock_client_instance
    
    # Temporarily disable TESTING mode for this test
    from api import services
    original_testing = services.shared_api_key_service.settings.TESTING
    services.shared_api_key_service.settings.TESTING = False
    
    try:
        # Attempt to share API key
        response = client.post(
            "/api/api-keys/share",
            json={
                "provider": "z.ai",
                "api_key": "test-zai-api-key-12345"
            },
            headers=auth_headers
        )
        
        # Should fail with 500 error
        assert response.status_code == 500
        assert "Failed to sync API key with LiteLLM" in response.json()["detail"]
        
        # Verify no API key was created in database
        api_keys = session.query(SharedAPIKey).filter_by(user_id=test_user.id).all()
        assert len(api_keys) == 0
    finally:
        services.shared_api_key_service.settings.TESTING = original_testing
