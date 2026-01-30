"""
Tests for LiteLLM integration in unified tokens

Test Coverage:
- LiteLLM key generation on token creation
- LiteLLM key blocking on token block
- LiteLLM key deletion on token deletion  
- LiteLLM key regeneration
- Error handling for missing litellm_user_id
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool
from datetime import datetime
from unittest.mock import AsyncMock, patch

from api.app import create_app
from api.config import Settings
from api.models.user import User
from api.models.unified_token import UnifiedToken, UnifiedTokenStatus
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

@patch('api.services.unified_token_service.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_create_unified_token_with_litellm_key(
    mock_client,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test creating unified token generates LiteLLM key"""
    # Mock LiteLLM API response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "sk-litellm-test-key-12345"}
    mock_response.raise_for_status = AsyncMock()
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance
    
    # Create unified token
    response = client.post(
        "/api/tokens/unified",
        json={"token_name": "Test Token"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "litellm_key" in data
    assert data["litellm_key"] == "sk-litellm-test-key-12345"


@patch('api.services.unified_token_service.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_block_unified_token(
    mock_client,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test blocking a unified token blocks LiteLLM key"""
    # First create a token
    token = UnifiedToken(
        user_id=test_user.id,
        token="test_token_123",
        status=UnifiedTokenStatus.ACTIVE,
        token_name="Test Token",
        litellm_key="sk-litellm-test-key-12345"
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    
    # Mock LiteLLM API response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance
    
    # Block the token
    response = client.put(
        f"/api/tokens/unified/{token.id}/block",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify token is revoked in database
    session.refresh(token)
    assert token.status == UnifiedTokenStatus.REVOKED
    assert token.revoked_at is not None


@patch('api.services.unified_token_service.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_delete_unified_token(
    mock_client,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test deleting a revoked unified token deletes LiteLLM key"""
    # Create a revoked token
    token = UnifiedToken(
        user_id=test_user.id,
        token="test_token_456",
        status=UnifiedTokenStatus.REVOKED,
        token_name="Test Token",
        litellm_key="sk-litellm-test-key-67890",
        revoked_at=datetime.utcnow()
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    token_id = token.id
    
    # Mock LiteLLM API response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client.return_value.__aenter__.return_value = mock_client_instance
    
    # Delete the token
    response = client.delete(
        f"/api/tokens/unified/{token_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify token is deleted from database
    statement = select(UnifiedToken).where(UnifiedToken.id == token_id)
    result = session.exec(statement).first()
    assert result is None


@patch('api.services.unified_token_service.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_regenerate_unified_token(
    mock_client,
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test regenerating LiteLLM key for a unified token"""
    # Create a token
    token = UnifiedToken(
        user_id=test_user.id,
        token="test_token_789",
        status=UnifiedTokenStatus.ACTIVE,
        token_name="Test Token",
        litellm_key="sk-litellm-old-key-11111"
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    
    # Mock LiteLLM API responses (delete old + generate new)
    mock_delete_response = AsyncMock()
    mock_delete_response.status_code = 200
    mock_delete_response.raise_for_status = AsyncMock()
    
    mock_generate_response = AsyncMock()
    mock_generate_response.status_code = 200
    mock_generate_response.json.return_value = {"key": "sk-litellm-new-key-22222"}
    mock_generate_response.raise_for_status = AsyncMock()
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(side_effect=[mock_delete_response, mock_generate_response])
    mock_client.return_value.__aenter__.return_value = mock_client_instance
    
    # Regenerate the key
    response = client.post(
        f"/api/tokens/unified/{token.id}/regenerate",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["litellm_key"] == "sk-litellm-new-key-22222"
    assert data["litellm_key"] != "sk-litellm-old-key-11111"


def test_create_token_without_litellm_user_id(
    client: TestClient,
    session: Session
):
    """Test that token creation fails if user has no litellm_user_id"""
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
    
    # Try to create unified token
    response = client.post(
        "/api/tokens/unified",
        json={"token_name": "Test Token"},
        headers=headers
    )
    
    assert response.status_code == 400
    assert "litellm" in response.json()["detail"].lower()
