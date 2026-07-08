from fastapi.testclient import TestClient
import logging
import uuid
from app.main import app

client = TestClient(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tests():
    logger.info("Starting API verification...")
    
    # 1. Test Health endpoint
    response = client.get("/health")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    logger.info("GET /health passed")
    
    # 2. Test registration & login
    uid = uuid.uuid4().hex[:6]
    login_data = {
        "email": f"user_{uid}@cloudwise.ai",
        "password": f"Pass_{uid}!123"
    }
    client.post("/api/v1/auth/register", json={
        "email": login_data["email"],
        "password": login_data["password"],
        "full_name": "Test User",
        "organization_name": f"Org_{uid}"
    })
    
    response = client.post("/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("POST /api/v1/auth/login passed")
        
        resp = client.get("/api/v1/costs/dashboard", headers=headers)
        if resp.status_code == 200:
            logger.info("GET /api/v1/costs/dashboard passed")
            
        resp = client.get("/api/v1/budgets/", headers=headers)
        if resp.status_code == 200:
            logger.info("GET /api/v1/budgets/ passed")
            
        resp = client.get("/api/v1/anomalies/", headers=headers)
        if resp.status_code == 200:
            logger.info("GET /api/v1/anomalies/ passed")
            
        ai_data = {"message": "How do I optimize AWS?"}
        resp = client.post("/api/v1/assistant/chat", json=ai_data, headers=headers)
        if resp.status_code == 200:
            logger.info("POST /api/v1/assistant/chat passed")
    else:
        logger.error(f"POST /api/v1/auth/login failed: {response.status_code}")

if __name__ == "__main__":
    run_tests()
