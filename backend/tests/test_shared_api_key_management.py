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
from api.utils.encryption import encrypt_token

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
        litellm_user_id="testuser@example.com"
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


# Test 1: Test disable shared API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_disable_shared_api_key(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test disabling a shared API key"""
    mock_validate.return_value = mock_validation_success
    
    # Share an API key first
    share_response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        },
        headers=auth_headers
    )
    assert share_response.status_code == 201
    api_key_id = share_response.json()["id"]
    
    # Disable the API key
    disable_response = client.put(
        f"/api/api-keys/disable/{api_key_id}",
        headers=auth_headers
    )
    assert disable_response.status_code == 200
    data = disable_response.json()
    assert data["id"] == api_key_id
    assert data["status"] == "inactive"


# Test 2: Test disable already inactive API key (idempotent)
@patch("api.services.shared_api_key_service.validate_api_key")
def test_disable_already_inactive_api_key(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test disabling an already inactive API key is idempotent"""
    mock_validate.return_value = mock_validation_success
    
    # Share an API key
    share_response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        },
        headers=auth_headers
    )
    api_key_id = share_response.json()["id"]
    
    # Disable once
    client.put(f"/api/api-keys/disable/{api_key_id}", headers=auth_headers)
    
    # Disable again
    disable_response = client.put(
        f"/api/api-keys/disable/{api_key_id}",
        headers=auth_headers
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "inactive"


# Test 3: Test enable shared API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_enable_shared_api_key(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test enabling a disabled API key"""
    mock_validate.return_value = mock_validation_success
    
    # Share and disable an API key
    share_response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        },
        headers=auth_headers
    )
    api_key_id = share_response.json()["id"]
    client.put(f"/api/api-keys/disable/{api_key_id}", headers=auth_headers)
    
    # Enable the API key
    enable_response = client.put(
        f"/api/api-keys/enable/{api_key_id}",
        headers=auth_headers
    )
    assert enable_response.status_code == 200
    data = enable_response.json()
    assert data["id"] == api_key_id
    assert data["status"] == "active"


# Test 4: Test enable already active API key (idempotent)
@patch("api.services.shared_api_key_service.validate_api_key")
def test_enable_already_active_api_key(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test enabling an already active API key is idempotent"""
    mock_validate.return_value = mock_validation_success
    
    # Share an API key (active by default)
    share_response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        },
        headers=auth_headers
    )
    api_key_id = share_response.json()["id"]
    
    # Enable (should be no-op)
    enable_response = client.put(
        f"/api/api-keys/enable/{api_key_id}",
        headers=auth_headers
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["status"] == "active"


# Test 5: Test cannot enable revoked API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_cannot_enable_revoked_api_key(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that revoked API keys cannot be enabled"""
    mock_validate.return_value = mock_validation_success
    
    # Share an API key
    share_response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        },
        headers=auth_headers
    )
    api_key_id = share_response.json()["id"]
    
    # Manually set status to REVOKED
    api_key = session.get(SharedAPIKey, api_key_id)
    api_key.status = APIKeyStatus.REVOKED
    session.add(api_key)
    session.commit()
    
    # Try to enable
    enable_response = client.put(
        f"/api/api-keys/enable/{api_key_id}",
        headers=auth_headers
    )
    assert enable_response.status_code == 400
    assert "revoked" in enable_response.json()["detail"].lower()


# Test 6: Test delete shared API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_delete_shared_api_key(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test deleting a shared API key"""
    mock_validate.return_value = mock_validation_success
    
    # Share an API key
    share_response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        },
        headers=auth_headers
    )
    api_key_id = share_response.json()["id"]
    
    # Delete the API key
    delete_response = client.delete(
        f"/api/api-keys/{api_key_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 204
    
    # Verify API key is deleted
    get_response = client.get("/api/api-keys/my-shared", headers=auth_headers)
    assert get_response.json()["total"] == 0


# Test 7: Test cannot disable other user's API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_cannot_disable_other_user_api_key(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that users cannot disable API keys they don't own"""
    mock_validate.return_value = mock_validation_success
    
    # Create another user
    other_user = User(
        email="otheruser@example.com",
        hashed_password="$2b$12$test_hash",
        is_active=True,
        litellm_user_id="otheruser@example.com"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)
    
    # Create API key for other user
    encrypted_api_key = encrypt_token("other-user-api-key")
    other_api_key = SharedAPIKey(
        user_id=other_user.id,
        provider=APIKeyProvider.BIGMODEL,
        encrypted_api_key=encrypted_api_key,
        status=APIKeyStatus.ACTIVE
    )
    session.add(other_api_key)
    session.commit()
    session.refresh(other_api_key)
    
    # Try to disable other user's API key
    disable_response = client.put(
        f"/api/api-keys/disable/{other_api_key.id}",
        headers=auth_headers
    )
    assert disable_response.status_code == 404


# Test 8: Test cannot enable other user's API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_cannot_enable_other_user_api_key(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that users cannot enable API keys they don't own"""
    mock_validate.return_value = mock_validation_success
    
    # Create another user with API key
    other_user = User(
        email="otheruser@example.com",
        hashed_password="$2b$12$test_hash",
        is_active=True,
        litellm_user_id="otheruser@example.com"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)
    
    encrypted_api_key = encrypt_token("other-user-api-key")
    other_api_key = SharedAPIKey(
        user_id=other_user.id,
        provider=APIKeyProvider.BIGMODEL,
        encrypted_api_key=encrypted_api_key,
        status=APIKeyStatus.INACTIVE
    )
    session.add(other_api_key)
    session.commit()
    session.refresh(other_api_key)
    
    # Try to enable other user's API key
    enable_response = client.put(
        f"/api/api-keys/enable/{other_api_key.id}",
        headers=auth_headers
    )
    assert enable_response.status_code == 404


# Test 9: Test cannot delete other user's API key
@patch("api.services.shared_api_key_service.validate_api_key")
def test_cannot_delete_other_user_api_key(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that users cannot delete API keys they don't own"""
    mock_validate.return_value = mock_validation_success
    
    # Create another user with API key
    other_user = User(
        email="otheruser@example.com",
        hashed_password="$2b$12$test_hash",
        is_active=True,
        litellm_user_id="otheruser@example.com"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)
    
    encrypted_api_key = encrypt_token("other-user-api-key")
    other_api_key = SharedAPIKey(
        user_id=other_user.id,
        provider=APIKeyProvider.BIGMODEL,
        encrypted_api_key=encrypted_api_key,
        status=APIKeyStatus.ACTIVE
    )
    session.add(other_api_key)
    session.commit()
    session.refresh(other_api_key)
    
    # Try to delete other user's API key
    delete_response = client.delete(
        f"/api/api-keys/{other_api_key.id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 404
    
    # Verify API key still exists
    api_key_check = session.get(SharedAPIKey, other_api_key.id)
    assert api_key_check is not None


# Test 10: Test disable deletes models but keeps credential (LiteLLM integration)
@patch("api.services.shared_api_key_service.validate_api_key")
@patch("api.services.shared_api_key_service.httpx.AsyncClient")
def test_disable_shared_api_key_deletes_models_only(
    mock_async_client,
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that disable deletes models but preserves credential"""
    mock_validate.return_value = mock_validation_success

    # Share an API key first
    share_response = client.post(
        "/api/api-keys/share",
        json={
            "provider": "bigmodel",
            "api_key": "test-api-key"
        },
        headers=auth_headers
    )
    assert share_response.status_code == 201
    api_key_id = share_response.json()["id"]

    # Set up the model IDs for the API key
    api_key = session.get(SharedAPIKey, api_key_id)
    api_key.litellm_model_ids = '{"glm-4.7": "model-id-1", "glm-4.6": "model-id-2", "glm-4.5-air": "model-id-3"}'
    api_key.litellm_model_id = "model-id-1"
    session.add(api_key)
    session.commit()

    # Mock model deletion responses (3 models)
    mock_delete_responses = []
    for i in range(3):
        resp = AsyncMock()
        resp.status_code = 200
        resp.text = '{"message": "Model deleted"}'
        resp.raise_for_status = lambda: None
        mock_delete_responses.append(resp)

    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_client_instance.post = AsyncMock(side_effect=mock_delete_responses)
    mock_async_client.return_value = mock_client_instance

    # Temporarily disable TESTING mode for this test
    from api import services
    original_testing = services.shared_api_key_service.settings.TESTING
    services.shared_api_key_service.settings.TESTING = False

    try:
        # Disable the API key
        disable_response = client.put(
            f"/api/api-keys/disable/{api_key_id}",
            headers=auth_headers
        )
        assert disable_response.status_code == 200
        data = disable_response.json()
        assert data["status"] == "inactive"

        # Verify models were deleted (3 POST calls for model deletions)
        assert mock_client_instance.post.call_count == 3

        # Verify litellm_model_ids was cleared
        session.refresh(api_key)
        assert api_key.litellm_model_ids is None
        assert api_key.litellm_model_id is None

    finally:
        services.shared_api_key_service.settings.TESTING = original_testing
