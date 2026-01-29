import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import patch, AsyncMock
from datetime import datetime

from api.app import create_app
from api.config import settings
from api.database import get_db
from api.models.user import User
from api.models.shared_token import SharedToken, TokenVendor, TokenStatus
from api.utils.jwt import create_access_token
from api.utils.encryption import encrypt_token


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


@pytest.fixture(name="users")
def users_fixture(session: Session):
    """Create test users"""
    user_a = User(
        email="usera@example.com",
        hashed_password="$2b$12$test_hash_a"
    )
    user_b = User(
        email="userb@example.com",
        hashed_password="$2b$12$test_hash_b"
    )
    user_c = User(
        email="userc@example.com",
        hashed_password="$2b$12$test_hash_c"
    )
    session.add(user_a)
    session.add(user_b)
    session.add(user_c)
    session.commit()
    session.refresh(user_a)
    session.refresh(user_b)
    session.refresh(user_c)
    return {"user_a": user_a, "user_b": user_b, "user_c": user_c}


@pytest.fixture(name="shared_tokens")
def shared_tokens_fixture(session: Session, users):
    """Create shared tokens from User B and User C"""
    # User B shares a bigmodel token
    token_b = SharedToken(
        user_id=users["user_b"].id,
        vendor=TokenVendor.BIGMODEL,
        encrypted_token=encrypt_token("userb-bigmodel-token"),
        status=TokenStatus.ACTIVE,
        total_uses=5,
        created_at=datetime.utcnow()
    )
    
    # User C shares a z.ai token
    token_c = SharedToken(
        user_id=users["user_c"].id,
        vendor=TokenVendor.ZAI,
        encrypted_token=encrypt_token("userc-zai-token"),
        status=TokenStatus.ACTIVE,
        total_uses=10,
        created_at=datetime.utcnow()
    )
    
    session.add(token_b)
    session.add(token_c)
    session.commit()
    session.refresh(token_b)
    session.refresh(token_c)
    return {"token_b": token_b, "token_c": token_c}


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(users):
    """Create authentication headers for each user"""
    return {
        "user_a": {"Authorization": f"Bearer {create_access_token(data={'sub': users['user_a'].email})}"},
        "user_b": {"Authorization": f"Bearer {create_access_token(data={'sub': users['user_b'].email})}"},
        "user_c": {"Authorization": f"Bearer {create_access_token(data={'sub': users['user_c'].email})}"}
    }


def test_discover_tokens_success(client, users, shared_tokens, auth_headers):
    """Test successful token discovery"""
    response = client.get(
        "/api/tokens/discover",
        headers=auth_headers["user_a"]
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have pagination fields
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    assert "items" in data
    
    # Should have 2 tokens (from User B and C)
    assert data["total"] == 2
    assert len(data["items"]) == 2
    
    # Check structure of items
    for item in data["items"]:
        assert "id" in item
        assert "vendor" in item
        assert "provider_username" in item
        assert "shared_duration_days" in item
        assert "total_uses" in item
        assert "created_at" in item
        
        # Should NOT contain token value
        assert "token" not in item
        assert "encrypted_token" not in item


def test_discover_excludes_own_tokens(client, users, shared_tokens, auth_headers):
    """Test that user's own tokens are excluded"""
    # User B should not see their own bigmodel token
    response = client.get(
        "/api/tokens/discover",
        headers=auth_headers["user_b"]
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only see User C's token (1 token)
    assert data["total"] == 1
    assert data["items"][0]["provider_username"] == "userc"


def test_discover_provider_username_anonymized(client, users, shared_tokens, auth_headers):
    """Test that provider username is anonymized (email prefix only)"""
    response = client.get(
        "/api/tokens/discover",
        headers=auth_headers["user_a"]
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check usernames are email prefixes
    usernames = [item["provider_username"] for item in data["items"]]
    assert "userb" in usernames
    assert "userc" in usernames
    
    # Should NOT contain full emails
    for item in data["items"]:
        assert "@" not in item["provider_username"]


def test_discover_pagination(client, users, shared_tokens, auth_headers):
    """Test pagination of token discovery"""
    # Request page 1 with page_size=1
    response = client.get(
        "/api/tokens/discover?page=1&page_size=1",
        headers=auth_headers["user_a"]
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert data["total"] == 2
    assert len(data["items"]) == 1  # Only 1 item per page
    
    # Request page 2
    response = client.get(
        "/api/tokens/discover?page=2&page_size=1",
        headers=auth_headers["user_a"]
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["page"] == 2
    assert len(data["items"]) == 1  # Second item


def test_discover_without_auth(client):
    """Test discovery without authentication"""
    response = client.get("/api/tokens/discover")
    assert response.status_code == 403


def test_discover_statistics_fields(client, users, shared_tokens, auth_headers):
    """Test that statistics fields are present and valid"""
    response = client.get(
        "/api/tokens/discover",
        headers=auth_headers["user_a"]
    )
    
    assert response.status_code == 200
    data = response.json()
    
    for item in data["items"]:
        # Sharing duration should be >= 0 days
        assert item["shared_duration_days"] >= 0
        
        # Total uses should be >= 0
        assert item["total_uses"] >= 0
        
        # Created_at should be a valid timestamp
        assert "created_at" in item
