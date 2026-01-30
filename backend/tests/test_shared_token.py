import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import patch, AsyncMock

from api.app import create_app
from api.config import settings
from api.database import get_db
from api.models.user import User
from api.models.shared_token import SharedToken, TokenVendor, TokenStatus
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
    """Mock successful token validation"""
    return {
        "valid": True,
        "message": "Token validation successful",
        "vendor_info": {"vendor": "bigmodel", "status_code": 200}
    }


@pytest.fixture(name="mock_validation_failure")
def mock_validation_failure_fixture():
    """Mock failed token validation"""
    return {
        "valid": False,
        "message": "Token authentication failed - invalid credentials",
        "vendor_info": None
    }


# Test 1: Successfully share a token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_share_token_success(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test successfully sharing a token"""
    # Mock returns the success dict directly (not a coroutine)
    mock_validate.return_value = mock_validation_success
    
    response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-bigmodel-token-12345",
            "token_metadata": '{"name": "My BigModel Token"}'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["vendor"] == "bigmodel"
    assert data["status"] == "active"
    assert data["total_uses"] == 0
    assert "encrypted_token" not in data  # Should never expose encrypted token


# Test 2: Reject duplicate vendor token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_share_token_duplicate_vendor(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test rejection of duplicate vendor token"""
    mock_validate.return_value = mock_validation_success
    
    # Share first token
    client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-bigmodel-token-12345"
        },
        headers=auth_headers
    )
    
    # Try to share second token for same vendor
    response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "another-bigmodel-token"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already have a token" in response.json()["detail"].lower()
    assert "bigmodel" in response.json()["detail"]


# Test 3: Reject invalid token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_share_token_invalid(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_failure
):
    """Test rejection of invalid token"""
    mock_validate.return_value = mock_validation_failure
    
    response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "invalid-token-12345"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "validation failed" in response.json()["detail"].lower()


# Test 4: Require authentication for sharing
def test_share_token_without_auth(client: TestClient):
    """Test that sharing requires authentication"""
    response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-token"
        }
    )
    
    assert response.status_code in [401, 403]  # Either is acceptable for unauthenticated


# Test 5: Get my shared tokens (empty)
def test_get_my_shared_tokens_empty(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test getting shared tokens when none exist"""
    response = client.get("/api/tokens/my-shared", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


# Test 6: Get my shared tokens (with data)
@patch("api.services.shared_token_service.validate_vendor_token")
def test_get_my_shared_tokens_with_data(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test getting shared tokens with existing data"""
    mock_validate.return_value = mock_validation_success
    
    # Share a token
    client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-token"
        },
        headers=auth_headers
    )
    
    # Get shared tokens
    response = client.get("/api/tokens/my-shared", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["vendor"] == "bigmodel"
    assert data["items"][0]["status"] == "active"


# Test 7: Require authentication for getting shared tokens
def test_get_my_shared_tokens_without_auth(client: TestClient):
    """Test that getting shared tokens requires authentication"""
    response = client.get("/api/tokens/my-shared")
    
    assert response.status_code in [401, 403]  # Either is acceptable for unauthenticated


# Test 8: Test token encryption/decryption
def test_token_encryption():
    """Test that token encryption and decryption work correctly"""
    original_token = "test-secret-token-12345"
    
    # Encrypt
    encrypted = encrypt_token(original_token)
    assert encrypted != original_token
    assert len(encrypted) > len(original_token)
    
    # Decrypt
    decrypted = decrypt_token(encrypted)
    assert decrypted == original_token


# Test 9: Test sharing multiple vendors
@patch("api.services.shared_token_service.validate_vendor_token")
def test_share_multiple_vendors(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that user can share tokens from different vendors"""
    mock_validate.return_value = mock_validation_success
    
    # Share bigmodel token
    response1 = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-bigmodel-token"
        },
        headers=auth_headers
    )
    assert response1.status_code == 201
    
    # Share z.ai token
    response2 = client.post(
        "/api/tokens/share",
        json={
            "vendor": "z.ai",
            "token": "test-zai-token"
        },
        headers=auth_headers
    )
    assert response2.status_code == 201
    
    # Check we have both
    response3 = client.get("/api/tokens/my-shared", headers=auth_headers)
    assert response3.status_code == 200
    data = response3.json()
    assert data["total"] == 2
    vendors = [item["vendor"] for item in data["items"]]
    assert "bigmodel" in vendors
    assert "z.ai" in vendors


# Test 11: Test token sharing logs usage history
@patch("api.services.shared_token_service.validate_vendor_token")
def test_share_token_logs_usage_history(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that token sharing is logged in usage history"""
    mock_validate.return_value = mock_validation_success
    
    # Share token
    response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-token"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    
    # Check usage history
    history_response = client.get("/api/users/me/token-usage", headers=auth_headers)
    assert history_response.status_code == 200
    history_data = history_response.json()
    
    # Should have one SHARED action (enum value is lowercase "shared")
    assert history_data["total"] >= 1
    shared_actions = [item for item in history_data["items"] if item["action"] == "shared"]
    assert len(shared_actions) >= 1


# Test 12: Test LiteLLM integration - successful sync
@patch("api.services.shared_token_service.validate_vendor_token")
@patch("api.services.shared_token_service.httpx.AsyncClient")
@patch("api.config.settings.TESTING", False)
def test_share_token_litellm_success(
    mock_async_client,
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test successful LiteLLM credential and model creation"""
    # Setup user with litellm_user_id
    test_user.litellm_user_id = "testuser@example.com"
    session.add(test_user)
    session.commit()
    
    # Mock validation
    mock_validate.return_value = mock_validation_success
    
    # Mock httpx responses
    mock_credential_response = AsyncMock()
    mock_credential_response.status_code = 200
    mock_credential_response.raise_for_status = lambda: None  # Sync function, not async
    
    mock_model_response = AsyncMock()
    mock_model_response.status_code = 200
    mock_model_response.raise_for_status = lambda: None  # Sync function, not async
    
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_client_instance.post = AsyncMock(side_effect=[mock_credential_response, mock_model_response])
    mock_async_client.return_value = mock_client_instance
    
    # Temporarily disable TESTING mode for this test
    from api import services
    original_testing = services.shared_token_service.settings.TESTING
    services.shared_token_service.settings.TESTING = False
    
    try:
        # Share token
        response = client.post(
            "/api/tokens/share",
            json={
                "vendor": "bigmodel",
                "token": "test-bigmodel-token-12345"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["vendor"] == "bigmodel"
        assert data["status"] == "active"
        
        # Verify LiteLLM was called twice (credential + model)
        assert mock_client_instance.post.call_count == 2
    finally:
        services.shared_token_service.settings.TESTING = original_testing


# Test 13: Test LiteLLM integration - credential creation fails
@patch("api.services.shared_token_service.validate_vendor_token")
@patch("api.services.shared_token_service.httpx.AsyncClient")
def test_share_token_litellm_credential_failure(
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
    original_testing = services.shared_token_service.settings.TESTING
    services.shared_token_service.settings.TESTING = False
    
    try:
        # Attempt to share token
        response = client.post(
            "/api/tokens/share",
            json={
                "vendor": "bigmodel",
                "token": "test-bigmodel-token-12345"
            },
            headers=auth_headers
        )
        
        # Should fail with 500 error
        assert response.status_code == 500
        assert "Failed to sync token with LiteLLM" in response.json()["detail"]
        
        # Verify no token was created in database
        tokens = session.query(SharedToken).filter_by(user_id=test_user.id).all()
        assert len(tokens) == 0
    finally:
        services.shared_token_service.settings.TESTING = original_testing


# Test 14: Test LiteLLM integration - model creation fails
@patch("api.services.shared_token_service.validate_vendor_token")
@patch("api.services.shared_token_service.httpx.AsyncClient")
def test_share_token_litellm_model_failure(
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
    original_testing = services.shared_token_service.settings.TESTING
    services.shared_token_service.settings.TESTING = False
    
    try:
        # Attempt to share token
        response = client.post(
            "/api/tokens/share",
            json={
                "vendor": "bigmodel",
                "token": "test-bigmodel-token-12345"
            },
            headers=auth_headers
        )
        
        # Should fail with 500 error
        assert response.status_code == 500
        assert "Failed to sync token with LiteLLM" in response.json()["detail"]
        
        # Verify no token was created in database
        tokens = session.query(SharedToken).filter_by(user_id=test_user.id).all()
        assert len(tokens) == 0
    finally:
        services.shared_token_service.settings.TESTING = original_testing


# Test 15: Test LiteLLM integration - network timeout
@patch("api.services.shared_token_service.validate_vendor_token")
@patch("api.services.shared_token_service.httpx.AsyncClient")
def test_share_token_litellm_timeout(
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
    original_testing = services.shared_token_service.settings.TESTING
    services.shared_token_service.settings.TESTING = False
    
    try:
        # Attempt to share token
        response = client.post(
            "/api/tokens/share",
            json={
                "vendor": "z.ai",
                "token": "test-zai-token-12345"
            },
            headers=auth_headers
        )
        
        # Should fail with 500 error
        assert response.status_code == 500
        assert "Failed to sync token with LiteLLM" in response.json()["detail"]
        
        # Verify no token was created in database
        tokens = session.query(SharedToken).filter_by(user_id=test_user.id).all()
        assert len(tokens) == 0
    finally:
        services.shared_token_service.settings.TESTING = original_testing

