import os
import sys
import time
import warnings

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Get the current directory (where the test_towns.py file is located)
current_dir = os.path.dirname(os.path.realpath(__file__))

# Append the parent directory (project root) to the Python path
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from api.app import create_app
from api.config import Settings
from api.database import get_db

# Now you should be able to import your modules using absolute paths
from api.public.towns.models import *


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
    def get_session_override():
        return session

    settings = Settings()
    app = create_app(settings)
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_town(client: TestClient, session: Session):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

    # Generate a unique name using a timestamp
    town_name = f"Town_{int(time.time())}"

    town_data = {"name": town_name, "population": 10000, "country": "Country A"}

    # Don't pre-create in the session - let the endpoint create it
    # created_town = Town(**town_data)
    # session.add(created_town)
    # session.commit()

    response = client.post("/towns/", json=town_data)
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    assert response.status_code == 200

    fetched_town = response.json()
    assert fetched_town["status"] == "success"
    assert fetched_town["msg"] == "Town created successfully"
    assert fetched_town["data"]["name"] == town_name


def test_get_single_town(client: TestClient, session: Session):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

    town_name = f"Town_{int(time.time())}s"

    town_data = {"name": town_name, "population": 10000, "country": "Country A"}

    # Use the session from the fixture to interact with the database
    created_town = Town(**town_data)
    session.add(created_town)
    session.commit()

    response = client.get(f"/towns/{created_town.id}")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_get_all_towns(client: TestClient, session: Session):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

    response = client.get("/towns/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_existing_town(client: TestClient, session: Session):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

    # Create a town first
    town_name = f"Town_{int(time.time())}"
    town_data = {"name": town_name, "population": 10000, "country": "Country A"}
    created_town = Town(**town_data)
    session.add(created_town)
    session.commit()

    town_update_data = {
        "name": "Updated Town Name",
        "population": 15000,
        "country": "Updated Country",
    }
    response = client.put(f"/towns/{created_town.id}", json=town_update_data)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_delete_existing_town(client: TestClient, session: Session):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

    # Create a town first
    town_name = f"Town_{int(time.time())}"
    town_data = {"name": town_name, "population": 10000, "country": "Country A"}
    created_town = Town(**town_data)
    session.add(created_town)
    session.commit()

    response = client.delete(f"/towns/{created_town.id}")
    assert response.status_code == 200

