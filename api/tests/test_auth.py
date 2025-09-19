import pytest
from uuid import uuid4
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

def test_signup(client: TestClient, test_user_registry):
    email = f"test_{uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == email
    assert "access_token" in data
    test_user_registry.append(email)

def test_login(client: TestClient, test_user_registry):
    email = f"test_{uuid4().hex}@example.com"
    # First create a user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    test_user_registry.append(email)
    
    # Then login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data