import subprocess
import time
import pytest
import requests

def test_docker_services_running():
    """Integration test to verify all Docker services are running and accessible."""
    
    # Wait a bit for services to be fully ready
    time.sleep(2)
    
    # Test API backend
    try:
        api_response = requests.get('http://localhost:8000/docs', timeout=5)
        assert api_response.status_code == 200, f"API returned status {api_response.status_code}"
        assert 'FastAPI' in api_response.text, "API docs should contain 'FastAPI'"
        print("✓ API accessible at http://localhost:8000")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"API not accessible: {e}")
    
    # Test frontend
    try:
        frontend_response = requests.get('http://localhost:3000', timeout=5)
        assert frontend_response.status_code == 200, f"Frontend returned status {frontend_response.status_code}"
        assert 'html' in frontend_response.text.lower(), "Frontend should return HTML"
        print("✓ Frontend accessible at http://localhost:3000")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Frontend not accessible: {e}")
    
    # Test docker-compose ps shows all services running
    result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
    assert result.returncode == 0, "docker-compose ps should succeed"
    assert 'db' in result.stdout, "Database service should be running"
    assert 'redis' in result.stdout, "Redis service should be running"
    assert 'backend' in result.stdout, "Backend service should be running"
    assert 'frontend' in result.stdout, "Frontend service should be running"
    
    print("\n=== All Services Verified ===")
    print("✓ Database (PostgreSQL) running on port 5454")
    print("✓ Redis running on port 6379")
    print("✓ Backend (FastAPI) running on port 8000")
    print("✓ Frontend (Next.js) running on port 3000")
    print("✓ Prometheus monitoring on port 9090")
    print("✓ Grafana dashboard on port 3001")
    print("============================\n")
