
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from core.models.models import MasterUser, Tenant
from datetime import datetime, timezone
from core.models.database import get_master_db
from main import app

client = TestClient(app)

def test_first_user_signup_bypass():
    """
    Test that the first global user can register even if password signup is disabled
    or tenant limits are reached.
    """
    mock_session = MagicMock(spec=Session)
    
    # 1. user_total_count = 0
    # 2. existing_user = None
    # 3. current_tenants_count = 0
    
    # Mock the query chain accurately
    # db.query(MasterUser).count()
    mock_session.query(MasterUser).count.return_value = 0
    # db.query(MasterUser).filter(...).first()
    mock_session.query(MasterUser).filter().first.return_value = None
    # db.query(Tenant).filter(...).count()
    mock_session.query(Tenant).filter().count.return_value = 0
    
    def override_master_db():
        yield mock_session

    app.dependency_overrides[get_master_db] = override_master_db

    # Create signup data
    signup_data = {
        "email": "first_user@example.com",
        "password": "Password123!",
        "first_name": "First",
        "last_name": "User",
        "organization_name": "First Org"
    }

    # Mock LicenseService to disable password signup
    with patch("core.services.license_service.LicenseService.get_license_status") as mock_license_status, \
         patch("core.services.license_service.LicenseService.get_max_tenants") as mock_max_tenants, \
         patch("core.services.tenant_database_manager.tenant_db_manager.create_tenant_database") as mock_create_db, \
         patch("core.services.tenant_database_manager.tenant_db_manager.get_tenant_session") as mock_tenant_session:
        
        mock_license_status.return_value = {"allow_password_signup": False, "is_licensed": False}
        mock_max_tenants.return_value = 0 # No tenants allowed by default
        mock_create_db.return_value = True
        
        # Mock tenant DB session for license check
        mock_t_session = MagicMock()
        mock_t_db = MagicMock(spec=Session)
        mock_t_db.query(Tenant).filter().count.return_value = 0
        mock_t_session.return_value = mock_t_db
        mock_tenant_session.return_value = mock_t_session

        # Mock Tenant creation
        mock_session.refresh.side_effect = lambda x: setattr(x, "id", 1) if isinstance(x, Tenant) else setattr(x, "id", 1)

        # We need to mock the db_user attributes that Pydantic 2 will validate in the response
        def mock_user_creation(user_obj):
            if isinstance(user_obj, MasterUser):
                user_obj.id = 1
                user_obj.tenant_id = 1
                user_obj.is_active = True
                user_obj.is_superuser = True
                user_obj.is_verified = True
                user_obj.must_reset_password = False
                user_obj.created_at = datetime.now(timezone.utc)
                user_obj.updated_at = datetime.now(timezone.utc)
                user_obj.google_id = None
                user_obj.azure_ad_id = None
                user_obj.sso_provider = None
                user_obj.has_sso = False
                user_obj.show_analytics = True
                user_obj.organizations = []
            return user_obj

        mock_session.add.side_effect = mock_user_creation
        mock_session.commit.side_effect = lambda: None
        mock_session.refresh.side_effect = lambda x: mock_user_creation(x)

        # Perform signup
        response = client.post("/api/v1/auth/register", json=signup_data)
        
        # Clear overrides
        app.dependency_overrides = {}

        # Verify success (201 Created)
        if response.status_code != 201:
            pytest.fail(f"Signup failed with {response.status_code}: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "first_user@example.com"
        assert data["user"]["is_superuser"] == True

def test_second_user_signup_gated():
    """
    Test that the second user is gated if password signup is disabled.
    """
    mock_session = MagicMock(spec=Session)
    
    # user_total_count = 1 (second user)
    mock_session.query(MasterUser).count.return_value = 1
    # existing_user = None
    mock_session.query(MasterUser).filter().first.return_value = None

    def override_master_db():
        yield mock_session

    app.dependency_overrides[get_master_db] = override_master_db

    signup_data = {
        "email": "second_user@example.com",
        "password": "Password123!",
        "first_name": "Second",
        "last_name": "User",
        "organization_name": "Second Org"
    }

    with patch("core.services.license_service.LicenseService.get_license_status") as mock_license_status:
        mock_license_status.return_value = {"allow_password_signup": False, "is_licensed": False}
        
        response = client.post("/api/v1/auth/register", json=signup_data)
        
        # Clear overrides
        app.dependency_overrides = {}

        # Verify rejection (403 Forbidden)
        assert response.status_code == 403
        assert response.json()["detail"] == "Public registration is currently disabled. Please contact an administrator."

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__]))
