"""
Comprehensive test suite for API key usage history functionality
Tests cover all acceptance criteria from Story 1.5
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from api.app import create_app
from api.config import Settings
from api.database import get_db
from api.models.user import User
from api.utils.security import hash_password


# Create in-memory SQLite database for testing
@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh database for each test"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


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


@pytest.fixture(name="auth_setup")
def auth_setup_fixture(client: TestClient, session: Session):
    """Create user and login to get auth token"""
    # Create user directly in database
    user = User(
        email="usagetest@example.com",
        hashed_password=hash_password("TestPass123!"),
        litellm_user_id="usagetest@example.com"
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Login to get token
    response = client.post("/api/auth/login", json={
        "email": "usagetest@example.com",
        "password": "TestPass123!"
    })
    access_token = response.json()["access_token"]

    return {"access_token": access_token, "email": "usagetest@example.com"}


def test_get_empty_usage_history(client: TestClient, auth_setup):
    """
    AC #1: Test getting usage history when no history exists
    Given authenticated user with no usage history,
    When I request history,
    Then I receive empty list with pagination metadata.
    """
    response = client.get(
        "/api/users/me/api-key-usage",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["items"] == []


def test_get_empty_usage_statistics(client: TestClient, auth_setup):
    """
    AC #2: Test getting statistics when no history exists
    Given authenticated user with no usage history,
    When I request usage statistics,
    Then I receive zeroed statistics.
    """
    response = client.get(
        "/api/users/me/api-key-usage/stats",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_actions"] == 0
    assert data["api_keys_shared"] == 0
    assert data["api_keys_consumed"] == 0
    assert data["api_keys_generated"] == 0
    assert data["first_activity"] is None
    assert data["last_activity"] is None


def test_usage_history_without_auth(client: TestClient):
    """
    AC #3: Test accessing history without authentication
    Given unauthenticated user,
    When I attempt to view history,
    Then I receive 401/403 error.
    """
    response = client.get("/api/users/me/api-key-usage")
    assert response.status_code == 403


def test_usage_stats_without_auth(client: TestClient):
    """
    AC #3: Test accessing stats without authentication
    """
    response = client.get("/api/users/me/api-key-usage/stats")
    assert response.status_code == 403


def test_usage_history_with_invalid_api_key(client: TestClient):
    """
    AC #3: Test accessing history with invalid API key
    """
    response = client.get(
        "/api/users/me/api-key-usage",
        headers={"Authorization": "Bearer invalid-api-key"}
    )
    assert response.status_code == 401


def test_usage_history_pagination_defaults(client: TestClient, auth_setup):
    """
    Test that pagination uses correct default values
    """
    response = client.get(
        "/api/users/me/api-key-usage",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 20


def test_usage_history_custom_pagination(client: TestClient, auth_setup):
    """
    Test custom pagination parameters
    """
    response = client.get(
        "/api/users/me/api-key-usage?page=2&page_size=10",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 10


def test_usage_history_invalid_pagination(client: TestClient, auth_setup):
    """
    Test validation for invalid pagination parameters
    """
    # Invalid page (0 or negative)
    response = client.get(
        "/api/users/me/api-key-usage?page=0",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )
    assert response.status_code == 422  # Validation error

    # Invalid page_size (exceeds max 100)
    response = client.get(
        "/api/users/me/api-key-usage?page_size=101",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )
    assert response.status_code == 422  # Validation error


def test_statistics_authentication_requirement(client: TestClient):
    """
    Test that statistics endpoint requires authentication
    """
    response = client.get("/api/users/me/api-key-usage/stats")
    assert response.status_code == 403  # No credentials


def test_history_endpoint_structure(client: TestClient, auth_setup):
    """
    Test that history response has correct structure
    """
    response = client.get(
        "/api/users/me/api-key-usage",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Check required fields
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_statistics_endpoint_structure(client: TestClient, auth_setup):
    """
    Test that statistics response has correct structure
    """
    response = client.get(
        "/api/users/me/api-key-usage/stats",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Check required fields
    assert "total_actions" in data
    assert "api_keys_shared" in data
    assert "api_keys_consumed" in data
    assert "api_keys_generated" in data
    assert "first_activity" in data
    assert "last_activity" in data
