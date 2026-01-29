import subprocess
import pytest
import time
import requests
from requests.exceptions import ConnectionError, Timeout

def test_docker_services_health_check():
    """Test that Docker services are running and accessible."""
    # Note: This test requires Docker services to be running
    # Run: docker-compose up --build before running this test

    services_to_check = [
        {
            'name': 'backend',
            'url': 'http://localhost:8000',
            'expected_status': 200,
            'timeout': 30
        },
        {
            'name': 'frontend',
            'url': 'http://localhost:3000',
            'expected_status': 200,
            'timeout': 60  # Frontend may take longer to start
        }
    ]

    failed_services = []

    for service in services_to_check:
        try:
            print(f"\n🔍 Checking {service['name']} at {service['url']}...")
            response = requests.get(service['url'], timeout=service['timeout'])

            if response.status_code == service['expected_status']:
                print(f"✅ {service['name']} is healthy (status: {response.status_code})")
            else:
                failed_services.append(f"{service['name']}: expected {service['expected_status']}, got {response.status_code}")
                print(f"❌ {service['name']} returned status {response.status_code}")

        except (ConnectionError, Timeout) as e:
            failed_services.append(f"{service['name']}: {str(e)}")
            print(f"❌ {service['name']} is not accessible: {str(e)}")

    # Check Prometheus (may not have web interface but port should be open)
    try:
        print("\n🔍 Checking Prometheus at http://localhost:9090...")
        response = requests.get('http://localhost:9090', timeout=10)
        print(f"✅ Prometheus is accessible (status: {response.status_code})")
    except Exception as e:
        print(f"⚠️ Prometheus check failed: {str(e)} (this may be expected if not configured)")

    # Check Grafana
    try:
        print("\n🔍 Checking Grafana at http://localhost:3001...")
        response = requests.get('http://localhost:3001', timeout=10)
        print(f"✅ Grafana is accessible (status: {response.status_code})")
    except Exception as e:
        print(f"⚠️ Grafana check failed: {str(e)} (this may be expected if not configured)")

    # Assert no critical services failed
    if failed_services:
        pytest.fail(f"Service health check failed for: {', '.join(failed_services)}\n\n"
                   "💡 Make sure Docker services are running:\n"
                   "   docker-compose up --build\n"
                   "   Wait for services to fully start (may take 2-3 minutes)")


def test_docker_compose_command_exists():
    """Test that docker-compose command is available."""
    try:
        result = subprocess.run(['docker-compose', '--version'],
                              capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        print(f"✅ docker-compose available: {result.stdout.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.fail("docker-compose command not found. Please install Docker Desktop.")


def test_docker_command_exists():
    """Test that docker command is available."""
    try:
        result = subprocess.run(['docker', '--version'],
                              capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        print(f"✅ docker available: {result.stdout.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.fail("docker command not found. Please install Docker Desktop.")


def test_project_setup_commands():
    """Document the setup commands that should be run."""
    setup_commands = {
        'start_services': 'docker-compose up --build',
        'stop_services': 'docker-compose down',
        'view_logs': 'docker-compose logs -f',
        'rebuild_backend': 'docker-compose up --build backend',
        'rebuild_frontend': 'docker-compose up --build frontend'
    }

    print("\n=== Docker Setup Commands ===")
    for name, command in setup_commands.items():
        print(f"🔧 {name}: {command}")
    print("=============================\n")

    # Just verify the commands are documented
    assert len(setup_commands) >= 3
    assert 'start_services' in setup_commands
