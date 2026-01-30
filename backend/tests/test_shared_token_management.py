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
    """Mock successful token validation"""
    return {
        "valid": True,
        "message": "Token validation successful",
        "vendor_info": {"vendor": "bigmodel", "status_code": 200}
    }


# Test 1: Test disable shared token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_disable_shared_token(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test disabling a shared token"""
    mock_validate.return_value = mock_validation_success
    
    # Share a token first
    share_response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-token"
        },
        headers=auth_headers
    )
    assert share_response.status_code == 201
    token_id = share_response.json()["id"]
    
    # Disable the token
    disable_response = client.put(
        f"/api/tokens/disable/{token_id}",
        headers=auth_headers
    )
    assert disable_response.status_code == 200
    data = disable_response.json()
    assert data["id"] == token_id
    assert data["status"] == "inactive"


# Test 2: Test disable already inactive token (idempotent)
@patch("api.services.shared_token_service.validate_vendor_token")
def test_disable_already_inactive_token(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test disabling an already inactive token is idempotent"""
    mock_validate.return_value = mock_validation_success
    
    # Share a token
    share_response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-token"
        },
        headers=auth_headers
    )
    token_id = share_response.json()["id"]
    
    # Disable once
    client.put(f"/api/tokens/disable/{token_id}", headers=auth_headers)
    
    # Disable again
    disable_response = client.put(
        f"/api/tokens/disable/{token_id}",
        headers=auth_headers
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "inactive"


# Test 3: Test enable shared token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_enable_shared_token(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test enabling a disabled token"""
    mock_validate.return_value = mock_validation_success
    
    # Share and disable a token
    share_response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-token"
        },
        headers=auth_headers
    )
    token_id = share_response.json()["id"]
    client.put(f"/api/tokens/disable/{token_id}", headers=auth_headers)
    
    # Enable the token
    enable_response = client.put(
        f"/api/tokens/enable/{token_id}",
        headers=auth_headers
    )
    assert enable_response.status_code == 200
    data = enable_response.json()
    assert data["id"] == token_id
    assert data["status"] == "active"


# Test 4: Test enable already active token (idempotent)
@patch("api.services.shared_token_service.validate_vendor_token")
def test_enable_already_active_token(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test enabling an already active token is idempotent"""
    mock_validate.return_value = mock_validation_success
    
    # Share a token (active by default)
    share_response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-token"
        },
        headers=auth_headers
    )
    token_id = share_response.json()["id"]
    
    # Enable (should be no-op)
    enable_response = client.put(
        f"/api/tokens/enable/{token_id}",
        headers=auth_headers
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["status"] == "active"


# Test 5: Test cannot enable revoked token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_cannot_enable_revoked_token(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that revoked tokens cannot be enabled"""
    mock_validate.return_value = mock_validation_success
    
    # Share a token
    share_response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-token"
        },
        headers=auth_headers
    )
    token_id = share_response.json()["id"]
    
    # Manually set status to REVOKED
    token = session.get(SharedToken, token_id)
    token.status = TokenStatus.REVOKED
    session.add(token)
    session.commit()
    
    # Try to enable
    enable_response = client.put(
        f"/api/tokens/enable/{token_id}",
        headers=auth_headers
    )
    assert enable_response.status_code == 400
    assert "revoked" in enable_response.json()["detail"].lower()


# Test 6: Test delete shared token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_delete_shared_token(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test deleting a shared token"""
    mock_validate.return_value = mock_validation_success
    
    # Share a token
    share_response = client.post(
        "/api/tokens/share",
        json={
            "vendor": "bigmodel",
            "token": "test-token"
        },
        headers=auth_headers
    )
    token_id = share_response.json()["id"]
    
    # Delete the token
    delete_response = client.delete(
        f"/api/tokens/{token_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 204
    
    # Verify token is deleted
    get_response = client.get("/api/tokens/my-shared", headers=auth_headers)
    assert get_response.json()["total"] == 0


# Test 7: Test cannot disable other user's token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_cannot_disable_other_user_token(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that users cannot disable tokens they don't own"""
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
    
    # Create token for other user
    encrypted_token = encrypt_token("other-user-token")
    other_token = SharedToken(
        user_id=other_user.id,
        vendor=TokenVendor.BIGMODEL,
        encrypted_token=encrypted_token,
        status=TokenStatus.ACTIVE
    )
    session.add(other_token)
    session.commit()
    session.refresh(other_token)
    
    # Try to disable other user's token
    disable_response = client.put(
        f"/api/tokens/disable/{other_token.id}",
        headers=auth_headers
    )
    assert disable_response.status_code == 404


# Test 8: Test cannot enable other user's token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_cannot_enable_other_user_token(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that users cannot enable tokens they don't own"""
    mock_validate.return_value = mock_validation_success
    
    # Create another user with token
    other_user = User(
        email="otheruser@example.com",
        hashed_password="$2b$12$test_hash",
        is_active=True,
        litellm_user_id="otheruser@example.com"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)
    
    encrypted_token = encrypt_token("other-user-token")
    other_token = SharedToken(
        user_id=other_user.id,
        vendor=TokenVendor.BIGMODEL,
        encrypted_token=encrypted_token,
        status=TokenStatus.INACTIVE
    )
    session.add(other_token)
    session.commit()
    session.refresh(other_token)
    
    # Try to enable other user's token
    enable_response = client.put(
        f"/api/tokens/enable/{other_token.id}",
        headers=auth_headers
    )
    assert enable_response.status_code == 404


# Test 9: Test cannot delete other user's token
@patch("api.services.shared_token_service.validate_vendor_token")
def test_cannot_delete_other_user_token(
    mock_validate,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict,
    mock_validation_success
):
    """Test that users cannot delete tokens they don't own"""
    mock_validate.return_value = mock_validation_success
    
    # Create another user with token
    other_user = User(
        email="otheruser@example.com",
        hashed_password="$2b$12$test_hash",
        is_active=True,
        litellm_user_id="otheruser@example.com"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)
    
    encrypted_token = encrypt_token("other-user-token")
    other_token = SharedToken(
        user_id=other_user.id,
        vendor=TokenVendor.BIGMODEL,
        encrypted_token=encrypted_token,
        status=TokenStatus.ACTIVE
    )
    session.add(other_token)
    session.commit()
    session.refresh(other_token)
    
    # Try to delete other user's token
    delete_response = client.delete(
        f"/api/tokens/{other_token.id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 404
    
    # Verify token still exists
    token_check = session.get(SharedToken, other_token.id)
    assert token_check is not None
