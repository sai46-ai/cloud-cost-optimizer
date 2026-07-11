"""
Automated RBAC and Admin Panel Verification Tests
Tests authentication, authorization, user role updates, enable/disable toggles,
self-modification prevention, and administrative audit logging.
"""
import logging
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db, SessionLocal
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

def run_rbac_tests():
    logger.info("Initializing DB for RBAC testing...")
    init_db()
    db = SessionLocal()
    
    # Explicitly seed the development admin for testing
    from app.core.seed import seed_development_admin
    seed_development_admin(db)

    try:
        # Create a unique regular test user
        uid = uuid.uuid4().hex[:6]
        user_email = f"user_{uid}@cloudwise.ai"
        user_password = f"Pass_{uid}!123"
        
        # 1. Register a regular user
        logger.info("Registering regular user...")
        reg_resp = client.post("/api/v1/auth/register", json={
            "email": user_email,
            "password": user_password,
            "full_name": "Standard User",
            "organization_name": f"Org_{uid}"
        })
        assert reg_resp.status_code == 200
        user_id = reg_resp.json()["user"]["id"]
        
        # Retrieve regular user token
        user_login = client.post("/api/v1/auth/login", json={
            "email": user_email,
            "password": user_password
        })
        assert user_login.status_code == 200
        user_token = user_login.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 2. Login with Seeded Admin
        logger.info("Verifying Seeded Admin...")
        admin_login = client.post("/api/v1/auth/login", json={
            "email": "admin@gmail.com",
            "password": "123456789"
        })
        assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        admin_id = admin_login.json()["user"]["id"]

        # 3. Test route protection (Admin Panel access)
        logger.info("Testing Admin Panel Route Protection...")
        # Regular user should get 403 Forbidden
        user_dash = client.get("/api/v1/admin/dashboard", headers=user_headers)
        assert user_dash.status_code == 403, f"Expected 403 Forbidden, got {user_dash.status_code}"
        
        # Admin should get 200 OK
        admin_dash = client.get("/api/v1/admin/dashboard", headers=admin_headers)
        assert admin_dash.status_code == 200
        stats = admin_dash.json()
        assert stats["total_users"] >= 2
        assert stats["active_users"] >= 2
        logger.info("Admin dashboard statistics verified: %s", stats)

        # 4. Test User list sorting, searching, and pagination
        logger.info("Testing User List Queries...")
        users_resp = client.get("/api/v1/admin/users?search=Standard", headers=admin_headers)
        assert users_resp.status_code == 200
        users_data = users_resp.json()
        assert users_data["total"] >= 1
        assert any(u["email"] == user_email for u in users_data["items"])

        # 5. Test Reviewer status assignment & removal
        logger.info("Testing Reviewer status assignment...")
        # Promote regular user to REVIEWER
        role_resp = client.put(
            f"/api/v1/admin/users/{user_id}/role",
            json={"role": "REVIEWER"},
            headers=admin_headers
        )
        assert role_resp.status_code == 200
        assert role_resp.json()["role"] == "REVIEWER"
        assert role_resp.json()["is_demo_mode"] is True

        # Log back in as the user to confirm is_demo_mode flag is updated in token
        user_login2 = client.post("/api/v1/auth/login", json={
            "email": user_email,
            "password": user_password
        })
        assert user_login2.status_code == 200
        assert user_login2.json()["user"]["is_demo_mode"] is True
        
        # Check that dashboard metrics now return demo metrics
        user_headers_reviewer = {"Authorization": f"Bearer {user_login2.json()['access_token']}"}
        dash_metrics = client.get("/api/v1/costs/dashboard", headers=user_headers_reviewer)
        assert dash_metrics.status_code == 200
        assert dash_metrics.json()["total_spend_mtd"] > 0, "Reviewer must receive seeded demo cost data."

        # Remove Reviewer status
        role_resp2 = client.put(
            f"/api/v1/admin/users/{user_id}/role",
            json={"role": "USER"},
            headers=admin_headers
        )
        assert role_resp2.status_code == 200
        assert role_resp2.json()["role"] == "USER"
        assert role_resp2.json()["is_demo_mode"] is False

        # 6. Test self-modification blocking (Privilege escalation / self lock-out prevention)
        logger.info("Testing Self-Modification Block...")
        self_role = client.put(
            f"/api/v1/admin/users/{admin_id}/role",
            json={"role": "USER"},
            headers=admin_headers
        )
        assert self_role.status_code == 400
        assert "privilege escalation" in self_role.json()["detail"].lower()

        self_status = client.put(
            f"/api/v1/admin/users/{admin_id}/status",
            json={"account_status": "disabled"},
            headers=admin_headers
        )
        assert self_status.status_code == 400
        assert "self-disablement" in self_status.json()["detail"].lower()

        # 7. Test disabling user and verifying login block
        logger.info("Testing user disablement & block...")
        disable_resp = client.put(
            f"/api/v1/admin/users/{user_id}/status",
            json={"account_status": "disabled"},
            headers=admin_headers
        )
        assert disable_resp.status_code == 200
        assert disable_resp.json()["account_status"] == "disabled"
        assert disable_resp.json()["is_active"] is False

        # Attempt to log in with disabled user — should be blocked
        disabled_login = client.post("/api/v1/auth/login", json={
            "email": user_email,
            "password": user_password
        })
        assert disabled_login.status_code == 401
        assert "disabled" in disabled_login.json()["detail"].lower()

        # Enable user again
        enable_resp = client.put(
            f"/api/v1/admin/users/{user_id}/status",
            json={"account_status": "active"},
            headers=admin_headers
        )
        assert enable_resp.status_code == 200
        assert enable_resp.json()["account_status"] == "active"
        assert enable_resp.json()["is_active"] is True

        # Re-verify login works after enablement
        enabled_login = client.post("/api/v1/auth/login", json={
            "email": user_email,
            "password": user_password
        })
        assert enabled_login.status_code == 200

        # 8. Test Audit Logs record administrative actions
        logger.info("Verifying Audit Logs...")
        audit_resp = client.get("/api/v1/admin/audit-logs", headers=admin_headers)
        assert audit_resp.status_code == 200
        logs = audit_resp.json()["items"]
        actions = [log["action"] for log in logs]
        
        # Verify specific actions are logged
        assert "reviewer_assigned" in actions or "user_role_changed" in actions
        assert "user_disabled" in actions
        assert "user_enabled" in actions
        assert "admin_login" in actions
        logger.info("Administrative audit log trails verified successfully.")

        logger.info("\nALL RBAC AND ADMIN PANEL TESTS PASSED SUCCESSFULLY!")

    finally:
        db.close()

if __name__ == "__main__":
    run_rbac_tests()
