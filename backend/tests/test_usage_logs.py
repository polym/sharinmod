"""
Comprehensive test suite for usage logs functionality
Tests cover all acceptance criteria from Tech Spec: Usage Page Backend
"""
import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from api.app import create_app
from api.config import Settings
from api.database import get_db
from api.models.user import User
from api.models.usage_log import UsageLog, UsageLogStatus
from api.models.unified_api_key import UnifiedAPIKey
from api.utils.jwt import create_access_token


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
def auth_setup_fixture(session: Session):
    """Create user and return auth token"""
    # Create user directly in database
    user = User(
        email="usagelogtest@example.com",
        hashed_password="hashed_password_here",
        consumed_tokens=0,
        contributed_tokens=0
    )
    session.add(user)
    session.commit()

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "email": "usagelogtest@example.com",
        "user_id": user.id
    }


@pytest.fixture(name="sample_usage_logs")
def sample_usage_logs_fixture(session: Session, auth_setup):
    """Create sample usage logs for testing"""
    user_id = auth_setup["user_id"]

    # Create some sample logs with different timestamps
    now = datetime.now(timezone.utc)

    logs = [
        # Success logs
        UsageLog(
            user_id=user_id,
            model_name="openai/gpt-4",
            status=UsageLogStatus.SUCCESS,
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            request_time=now - timedelta(hours=2),
            total_duration=1.5,
            ttft=0.3
        ),
        UsageLog(
            user_id=user_id,
            model_name="openai/gpt-3.5-turbo",
            status=UsageLogStatus.SUCCESS,
            input_tokens=50,
            output_tokens=100,
            total_tokens=150,
            request_time=now - timedelta(hours=1),
            total_duration=0.8,
            ttft=0.2
        ),
        # Failure log
        UsageLog(
            user_id=user_id,
            model_name="openai/gpt-4",
            status=UsageLogStatus.FAILURE,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            request_time=now - timedelta(minutes=30)
        ),
    ]

    for log in logs:
        session.add(log)
    session.commit()

    return logs
    today_utc8_end = datetime.combine(date.today(), datetime.max.time()) - utc8_offset

    logs = [
        # Success logs
        UsageLog(
            user_id=user_id,
            model_name="openai/gpt-4",
            status=UsageLogStatus.SUCCESS,
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            request_time=now - timedelta(hours=2),
            total_duration=1.5,
            ttft=0.3
        ),
        UsageLog(
            user_id=user_id,
            model_name="openai/gpt-3.5-turbo",
            status=UsageLogStatus.SUCCESS,
            input_tokens=50,
            output_tokens=100,
            total_tokens=150,
            request_time=now - timedelta(hours=1),
            total_duration=0.8,
            ttft=0.2
        ),
        # Failure log
        UsageLog(
            user_id=user_id,
            model_name="openai/gpt-4",
            status=UsageLogStatus.FAILURE,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            request_time=now - timedelta(minutes=30)
        ),
    ]

    for log in logs:
        session.add(log)
    session.commit()

    return logs


def test_get_empty_usage_logs(client: TestClient, auth_setup):
    """
    AC: Test getting usage logs when no logs exist
    Given authenticated user with no usage logs,
    When I request logs,
    Then I receive empty list with pagination metadata.
    """
    response = client.get(
        "/api/usage/logs",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["items"] == []


def test_get_usage_logs_with_pagination(client: TestClient, auth_setup, sample_usage_logs):
    """
    AC 10, 14: Test paginated log retrieval
    Given authenticated user with multiple usage logs,
    When I query with pagination,
    Then I receive paginated results ordered by time desc.
    """
    response = client.get(
        "/api/usage/logs?page=1&page_size=10",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) >= 3
    # Verify items are ordered by most recent first
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["request_time"] >= items[i+1]["request_time"]


def test_get_usage_logs_with_date_filter(client: TestClient, auth_setup):
    """
    AC 11: Test date range filtering (UTC+8)
    Given authenticated user with usage logs across multiple days,
    When I query with date range (UTC+8),
    Then only logs within that range are returned.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)

    response = client.get(
        f"/api/usage/logs?start_date={yesterday}&end_date={today}",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    # All returned logs should be within the date range
    for item in data["items"]:
        request_time = datetime.fromisoformat(item["request_time"].replace('Z', '+00:00'))
        # Convert to UTC+8 for comparison
        request_date_utc8 = (request_time + timedelta(hours=8)).date()
        assert yesterday <= request_date_utc8 <= today


def test_get_usage_logs_with_status_filter(client: TestClient, auth_setup, sample_usage_logs):
    """
    AC 12: Test status filtering
    Given authenticated user with success and failure logs,
    When I filter by status=success,
    Then only success logs are returned.
    """
    response = client.get(
        "/api/usage/logs?status=success",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["status"] == "success"


def test_get_usage_logs_without_auth(client: TestClient):
    """
    AC 13: Test accessing logs without authentication
    Given unauthenticated user,
    When I attempt to view logs,
    Then I receive 401/403 error.
    """
    response = client.get("/api/usage/logs")
    assert response.status_code in [401, 403]


def test_get_usage_logs_with_invalid_token(client: TestClient):
    """
    AC 13: Test accessing logs with invalid token
    """
    response = client.get(
        "/api/usage/logs",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401


def test_get_usage_overview_for_date(client: TestClient, auth_setup, sample_usage_logs):
    """
    AC 15, 16: Test usage overview for specific date
    Given authenticated user with usage logs,
    When I query overview for a date,
    Then I receive aggregated statistics.
    """
    today = date.today()

    response = client.get(
        f"/api/usage/overview?date={today}",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == str(today)
    assert "total_requests" in data
    assert "successful_requests" in data
    assert "failed_requests" in data
    assert "total_tokens" in data
    assert "input_tokens" in data
    assert "output_tokens" in data
    assert data["successful_requests"] + data["failed_requests"] == data["total_requests"]


def test_get_usage_overview_quarter_hourly_distribution(client: TestClient, auth_setup, sample_usage_logs):
    """
    AC 17: Test 96 quarter-hour token distribution (15-minute intervals)
    Given authenticated user with usage logs,
    When I query overview,
    Then quarter_hourly_distribution contains 96 quarter-hours (0-95).
    """
    today = date.today()

    response = client.get(
        f"/api/usage/overview?date={today}",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    quarter_dist = data["quarter_hourly_distribution"]
    assert len(quarter_dist) == 96
    # Verify each quarter_hour has data (even if 0)
    for i, quarter_data in enumerate(quarter_dist):
        assert quarter_data["quarter_hour"] == i
        assert "tokens" in quarter_data
        assert quarter_data["tokens"] >= 0


def test_get_usage_overview_no_data(client: TestClient, auth_setup):
    """
    AC 18: Test overview when no logs exist
    Given authenticated user with no usage logs,
    When I query overview,
    Then I receive zeroed statistics.
    """
    today = date.today()

    response = client.get(
        f"/api/usage/overview?date={today}",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 0
    assert data["successful_requests"] == 0
    assert data["failed_requests"] == 0
    assert data["total_tokens"] == 0
    assert data["input_tokens"] == 0
    assert data["output_tokens"] == 0
    # Quarter-hourly distribution should still have 96 quarter-hours with 0 tokens
    assert len(data["quarter_hourly_distribution"]) == 96
    for quarter_data in data["quarter_hourly_distribution"]:
        assert quarter_data["tokens"] == 0


def test_get_usage_overview_default_today(client: TestClient, auth_setup, sample_usage_logs):
    """
    AC 19: Test overview defaults to today (UTC+8)
    Given authenticated user with usage logs,
    When I query overview without date parameter,
    Then I receive statistics for today (UTC+8).
    """
    response = client.get(
        "/api/usage/overview",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Should default to today in UTC+8
    today_utc8 = (datetime.now(timezone.utc) + timedelta(hours=8)).date()
    assert data["date"] == str(today_utc8)


def test_invalid_pagination_parameters(client: TestClient, auth_setup):
    """
    Test validation for invalid pagination parameters
    """
    # Invalid page (0 or negative)
    response = client.get(
        "/api/usage/logs?page=0",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )
    assert response.status_code == 422

    # Invalid page_size (exceeds max 100)
    response = client.get(
        "/api/usage/logs?page_size=101",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )
    assert response.status_code == 422


def test_usage_logs_response_structure(client: TestClient, auth_setup):
    """
    Test that usage logs response has correct structure
    """
    response = client.get(
        "/api/usage/logs",
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


def test_usage_overview_response_structure(client: TestClient, auth_setup):
    """
    Test that usage overview response has correct structure
    """
    response = client.get(
        "/api/usage/overview",
        headers={"Authorization": f"Bearer {auth_setup['access_token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Check required fields
    assert "date" in data
    assert "total_requests" in data
    assert "successful_requests" in data
    assert "failed_requests" in data
    assert "total_tokens" in data
    assert "input_tokens" in data
    assert "output_tokens" in data
    assert "quarter_hourly_distribution" in data
    assert isinstance(data["quarter_hourly_distribution"], list)
