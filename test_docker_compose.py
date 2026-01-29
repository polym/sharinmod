import os
import yaml
import pytest

def test_docker_compose_configured():
    """Test that docker-compose.yml has been properly configured for sharinmod."""
    compose_path = 'docker-compose.yml'
    
    # Check that docker-compose.yml exists
    assert os.path.exists(compose_path), "docker-compose.yml should exist in project root"
    
    # Read and parse docker-compose.yml
    with open(compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    # Check that required services exist
    assert 'services' in compose_config, "docker-compose.yml should have services section"
    services = compose_config['services']
    
    required_services = ['frontend', 'backend', 'db', 'redis']
    for service in required_services:
        assert service in services, f"{service} service should be defined"
    
    # Check frontend port is 3000
    assert 'ports' in services['frontend'], "Frontend should expose ports"
    frontend_ports = services['frontend']['ports']
    assert any('3000' in str(port) for port in frontend_ports), "Frontend should expose port 3000"
    
    # Check backend port is 8000
    assert 'ports' in services['backend'], "Backend should expose ports"
    backend_ports = services['backend']['ports']
    assert any('8000' in str(port) for port in backend_ports), "Backend should expose port 8000"
    
    # Check database is configured for sharinmod
    db_env = services['db'].get('environment', [])
    # Convert list or dict to string for checking
    db_env_str = str(db_env)
    assert 'sharinmod' in db_env_str, "Database should be configured for sharinmod database"
    
    # Check backend environment references correct database
    backend_env = services['backend'].get('environment', [])
    backend_env_str = str(backend_env)
    assert 'db:5432' in backend_env_str or 'postgres' in backend_env_str, \
        "Backend should reference database service"
