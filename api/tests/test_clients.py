import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

@pytest.fixture
def auth_headers(client: TestClient):
    # Create and login user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
    )
    
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_client(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Test Client",
            "email": "client@example.com",
            "phone": "123-456-7890"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Client"
    assert data["email"] == "client@example.com"

def test_get_clients(client: TestClient, auth_headers):
    # Create a client first
    client.post(
        "/api/v1/clients/",
        json={
            "name": "Test Client",
            "email": "client@example.com"
        },
        headers=auth_headers
    )
    
    response = client.get("/api/v1/clients/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Client"

def test_delete_client_with_invoices(client: TestClient, auth_headers):
    # Create a client
    client_response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Test Client",
            "email": "client@example.com"
        },
        headers=auth_headers
    )
    client_id = client_response.json()["id"]
    
    # Create an invoice for the client
    client.post(
        "/api/v1/invoices/",
        json={
            "client_id": client_id,
            "amount": 100.0,
            "due_date": "2024-12-31",
            "items": [{"description": "Test item", "quantity": 1, "price": 100.0}]
        },
        headers=auth_headers
    )
    
    # Try to delete the client - should fail
    response = client.delete(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "CLIENT_HAS_INVOICES"

def test_delete_client_without_invoices(client: TestClient, auth_headers):
    # Create a client
    client_response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Test Client",
            "email": "client@example.com"
        },
        headers=auth_headers
    )
    client_id = client_response.json()["id"]
    
    # Delete the client - should succeed
    response = client.delete(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert response.status_code == 204