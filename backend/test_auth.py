import httpx
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"
client = httpx.Client(timeout=30.0)

print("Starting Auth Tests...")

uid = uuid.uuid4().hex[:6]
email = f"test_user_{uid}@cloudwise.ai"
password = f"Pass_{uid}!123"

# 0. Register test user
print("\n--- 0. Register User ---")
resp = client.post(
    f"{BASE_URL}/auth/register",
    json={"email": email, "password": password, "full_name": "Test User", "organization_name": f"Org_{uid}"}
)
print(f"Status: {resp.status_code}")

# 1. Login with valid credentials
print("\n--- 1. Valid Login ---")
resp = client.post(
    f"{BASE_URL}/auth/login",
    json={"email": email, "password": password}
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    token = resp.json().get("access_token")
    print(f"Success. Token obtained.")
else:
    print(resp.text)
    token = None

# 2. Login with invalid credentials
print("\n--- 2. Invalid Login ---")
resp = client.post(
    f"{BASE_URL}/auth/login",
    json={"email": email, "password": "WrongPassword!"}
)
print(f"Status: {resp.status_code}")

# 3. Access protected route without token
print("\n--- 3. Protected Route (No Token) ---")
resp = client.get(f"{BASE_URL}/auth/me")
print(f"Status: {resp.status_code}")

# 4. Access protected route with token
if token:
    print("\n--- 4. Protected Route (With Token) ---")
    resp = client.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {resp.status_code}")
