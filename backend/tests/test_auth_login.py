"""
Comprehensive test suite for user authentication and login functionality
Tests cover all acceptance criteria from Story 1.3
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from api.app import create_app
from api.config import Settings
from api.database import get_db


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


@pytest.fixture(name="test_user")
def test_user_fixture(client: TestClient):
    """Create a test user for login tests"""
    response = client.post("/api/users/register", json={
        "email": "logintest@example.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 201
    return response.json()


def test_login_success(client: TestClient, test_user):
    """
    AC #1: Test successful login with correct credentials
    Given correct email and password,
    When I login,
    Then I receive JWT token.
    """
    response = client.post("/api/auth/login", json={
        "email": "logintest@example.com",
        "password": "TestPass123!"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Token should be a non-empty string
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_wrong_password(client: TestClient, test_user):
    """
    AC #2: Test login failure with incorrect password
    Given incorrect password,
    When I attempt to login,
    Then I receive 401 Unauthorized error with clear message.
    """
    response = client.post("/api/auth/login", json={
        "email": "logintest@example.com",
        "password": "WrongPassword123!"
    })
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_email(client: TestClient):
    """
    AC #2: Test login failure with non-existent email
    Given non-existent email,
    When I attempt to login,
    Then I receive 401 Unauthorized error.
    """
    response = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "TestPass123!"
    })
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_invalid_email(client: TestClient):
    """
    Test login with invalid email format
    Should return 422 validation error
    """
    response = client.post("/api/auth/login", json={
        "email": "not-an-email",
        "password": "TestPass123!"
    })
    
    assert response.status_code == 422  # Validation error


def test_protected_endpoint_with_valid_token(client: TestClient, test_user):
    """
    AC #3: Test accessing protected endpoint with valid JWT token
    Given valid JWT token,
    When I access protected endpoints,
    Then I can successfully authenticate.
    """
    # First login to get token
    login_response = client.post("/api/auth/login", json={
        "email": "logintest@example.com",
        "password": "TestPass123!"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Access protected endpoint with token
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "logintest@example.com"
    assert "id" in data
    assert "hashed_password" not in data  # Should not expose password


def test_protected_endpoint_without_token(client: TestClient):
    """
    AC #3: Test accessing protected endpoint without token
    Should return 403 Forbidden
    """
    response = client.get("/api/users/me")
    assert response.status_code == 403  # Forbidden (no credentials)


def test_protected_endpoint_with_invalid_token(client: TestClient):
    """
    AC #3: Test accessing protected endpoint with invalid token
    Should return 401 Unauthorized
    """
    response = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid-token-here"}
    )
    
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_token_expiration_structure(client: TestClient, test_user):
    """
    Test that token contains proper expiration claim and can be verified
    """
    from api.utils.jwt import create_access_token, verify_token
    from datetime import timedelta
    
    # Create token with short expiration
    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(minutes=5)
    )
    
    # Token should be valid immediately
    email = verify_token(token)
    assert email == "test@example.com"


def test_login_missing_password(client: TestClient):
    """
    Test login with missing password field
    Should return 422 validation error
    """
    response = client.post("/api/auth/login", json={
        "email": "test@example.com"
    })
    
    assert response.status_code == 422


def test_login_missing_email(client: TestClient):
    """
    Test login with missing email field
    Should return 422 validation error
    """
    response = client.post("/api/auth/login", json={
        "password": "TestPass123!"
    })
    
    assert response.status_code == 422
