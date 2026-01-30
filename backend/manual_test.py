"""
Manual test script to verify registration endpoint
Run this from within the Docker container
"""
import httpx

base_url = "http://localhost:8000"

# Test 1: Successful registration
print("Test 1: Successful registration...")
response = httpx.post(
    f"{base_url}/api/users/register",
    json={"email": "unique@example.com", "password": "SecurePass123!"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 2: Duplicate email
print("Test 2: Duplicate email...")
response = httpx.post(
    f"{base_url}/api/users/register",
    json={"email": "unique@example.com", "password": "AnotherPass123!"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 3: Invalid email
print("Test 3: Invalid email...")
response = httpx.post(
    f"{base_url}/api/users/register",
    json={"email": "not-an-email", "password": "SecurePass123!"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 4: Weak password (no uppercase)
print("Test 4: Weak password (no uppercase)...")
response = httpx.post(
    f"{base_url}/api/users/register",
    json={"email": "test2@example.com", "password": "nouppercase1!"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Test 5: Successful login
print("Test 5: Successful login...")
response = httpx.post(
    f"{base_url}/api/auth/login",
    json={"email": "unique@example.com", "password": "SecurePass123!"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")
