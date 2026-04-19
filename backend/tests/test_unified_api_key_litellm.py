"""
Tests for LiteLLM integration in unified API keys

Test Coverage:
- LiteLLM key generation on API key creation
- LiteLLM key blocking on API key block
- LiteLLM key deletion on API key deletion
- LiteLLM key regeneration
- Error handling for missing litellm_user_id
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from api.app import create_app
from api.config import Settings
from api.models.user import User
from api.models.unified_api_key import UnifiedAPIKey, UnifiedAPIKeyStatus
from api.services.auth_service import create_access_token
from api.database import get_db


# Test database setup
@pytest.fixture(name="session")
def session_fixture():
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
    def get_session_override():
        return session

    settings = Settings()
    app = create_app(settings)
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    user = User(
        email="testuser@example.com",
        hashed_password="$2b$12$test_hash",
        litellm_user_id="test_litellm_user_123"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: User):
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


# ==================== LiteLLM Integration Tests ====================

@patch('api.services.unified_api_key_service.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_create_unified_api_key_with_litellm_key(
    mock_client,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test creating unified API key generates LiteLLM key"""
    # Mock LiteLLM API response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    # Use a regular callable for json() instead of AsyncMock
    mock_response.json = lambda: {"key": "sk-litellm-test-key-12345"}
    mock_response.raise_for_status = lambda: None

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    # Create unified API key
    response = client.post(
        "/api/api-keys/unified",
        json={"api_key_name": "Test API Key"},
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert "litellm_key" in data
    assert data["litellm_key"] == "sk-litellm-test-key-12345"


@patch('api.services.unified_api_key_service.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_block_unified_api_key(
    mock_client,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test blocking a unified API key blocks LiteLLM key"""
    # First create an API key
    api_key = UnifiedAPIKey(
        user_id=test_user.id,
        api_key="test_api_key_123",
        status=UnifiedAPIKeyStatus.ACTIVE,
        api_key_name="Test API Key",
        litellm_key="sk-litellm-test-key-12345"
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)

    # Mock LiteLLM API response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    # Block the API key
    response = client.put(
        f"/api/api-keys/unified/{api_key.id}/block",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify API key is revoked in database
    session.refresh(api_key)
    assert api_key.status == UnifiedAPIKeyStatus.REVOKED
    assert api_key.revoked_at is not None


@patch('api.services.unified_api_key_service.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_delete_unified_api_key(
    mock_client,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test deleting a revoked unified API key deletes LiteLLM key"""
    # Create a revoked API key
    api_key = UnifiedAPIKey(
        user_id=test_user.id,
        api_key="test_api_key_456",
        status=UnifiedAPIKeyStatus.REVOKED,
        api_key_name="Test API Key",
        litellm_key="sk-litellm-test-key-67890",
        revoked_at=datetime.now(timezone.utc)
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    api_key_id = api_key.id

    # Mock LiteLLM API response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    # Delete the API key
    response = client.delete(
        f"/api/api-keys/unified/{api_key_id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify API key is deleted from database
    statement = select(UnifiedAPIKey).where(UnifiedAPIKey.id == api_key_id)
    result = session.exec(statement).first()
    assert result is None


@patch('api.services.unified_api_key_service.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_regenerate_unified_api_key(
    mock_client,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test regenerating LiteLLM key for a unified API key"""
    # Create an API key
    api_key = UnifiedAPIKey(
        user_id=test_user.id,
        api_key="test_api_key_789",
        status=UnifiedAPIKeyStatus.ACTIVE,
        api_key_name="Test API Key",
        litellm_key="sk-litellm-old-key-11111"
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)

    # Mock LiteLLM API responses (delete old + generate new)
    mock_delete_response = AsyncMock()
    mock_delete_response.status_code = 200
    mock_delete_response.raise_for_status = lambda: None

    mock_generate_response = AsyncMock()
    mock_generate_response.status_code = 200
    # Use a regular callable for json() instead of AsyncMock
    mock_generate_response.json = lambda: {"key": "sk-litellm-new-key-22222"}
    mock_generate_response.raise_for_status = lambda: None

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(side_effect=[mock_delete_response, mock_generate_response])
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    # Regenerate the key
    response = client.post(
        f"/api/api-keys/unified/{api_key.id}/regenerate",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["litellm_key"] == "sk-litellm-new-key-22222"
    assert data["litellm_key"] != "sk-litellm-old-key-11111"


def test_create_api_key_without_litellm_user_id(
    client: TestClient,
    session: Session
):
    """Test that API key creation fails if user has no litellm_user_id"""
    # Create user without litellm_user_id
    user = User(
        email="nolitellm@example.com",
        hashed_password="$2b$12$test_hash"
    )
    session.add(user)
    session.commit()
    
    # Create auth token for this user
    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Try to create unified API key
    response = client.post(
        "/api/api-keys/unified",
        json={"api_key_name": "Test API Key"},
        headers=headers
    )
    
    assert response.status_code == 400
    assert "litellm" in response.json()["detail"].lower()
