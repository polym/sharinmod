import os
import pytest

def test_repository_cloned():
    """Test that the fastapi-nextjs repository has been cloned successfully."""
    # Check that backend directory exists
    assert os.path.exists('backend'), "Backend directory should exist after cloning"

    # Check that frontend directory exists
    assert os.path.exists('frontend'), "Frontend directory should exist after cloning"

    # Check that docker-compose.yml exists
    assert os.path.exists('docker-compose.yml'), "Docker compose file should exist"

    # Check that backend/api exists and has Python files
    assert os.path.exists('backend/api'), "Backend API directory should exist"
    api_files = os.listdir('backend/api')
    assert any(f.endswith('.py') for f in api_files), f"Backend API should contain Python files, found: {api_files}"

    # Check that frontend/src/app exists and has TS/JS files
    assert os.path.exists('frontend/src/app'), "Frontend src/app directory should exist"
    app_files = os.listdir('frontend/src/app')
    assert any(f.endswith(('.js', '.ts', '.jsx', '.tsx')) for f in app_files), f"Frontend app should contain JS/TS files, found: {app_files}"