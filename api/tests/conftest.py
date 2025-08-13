import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

# Simple test setup without complex database fixtures
@pytest.fixture(scope="function")
def client():
    from main import app
    return TestClient(app)

# Registry to track created test users' emails
_test_created_users = []

@pytest.fixture(scope="session")
def test_user_registry():
    return _test_created_users

@pytest.fixture(scope="function", autouse=True)
def cleanup_test_users_after_test(client: TestClient, test_user_registry):
    yield
    # Best-effort cleanup for users created during tests
    try:
        for email in list(test_user_registry):
            try:
                # 1) Find user id via auth users listing
                list_resp = client.get("/api/v1/auth/users")
                if list_resp.status_code == 200:
                    users = list_resp.json() or []
                    match = next((u for u in users if (u.get("email") or "").lower() == email.lower()), None)
                    if match and match.get("id"):
                        uid = match["id"]
                        # 2) Delete via super-admin endpoint
                        del_resp = client.delete(f"/api/v1/super-admin/users/{uid}")
                        if del_resp.status_code in (200, 204):
                            test_user_registry.remove(email)
            except Exception:
                pass
    except Exception:
        pass