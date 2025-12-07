
import pytest
from uuid import uuid4
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

@pytest.fixture
def auth_headers_with_name(client: TestClient):
    unique_email = f"creator_{uuid4().hex}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "first_name": "Creator",
            "last_name": "Person"
        }
    )
    
    response = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_client_id(client: TestClient, auth_headers_with_name):
    unique_email = f"client_{uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Test Client",
            "email": unique_email
        },
        headers=auth_headers_with_name
    )
    # If client creation fails (e.g. need auth), we'll see it in tests
    return response.json()["id"]

def test_invoice_creator_name_display(client: TestClient, auth_headers_with_name, test_client_id):
    # 1. Create Invoice
    create_resp = client.post(
        "/api/v1/invoices/",
        json={
            "client_id": test_client_id,
            "amount": 500.00,
            "description": "Service Work",
            "status": "draft"
        },
        headers=auth_headers_with_name
    )
    assert create_resp.status_code == 201
    invoice_id = create_resp.json()["id"]
    
    # Check simple response (create endpoint return)
    assert create_resp.json()["created_by_username"] == "Creator Person"

    # 2. Get Invoice Detail (View Invoice Page)
    get_resp = client.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers_with_name)
    assert get_resp.status_code == 200
    data = get_resp.json()
    
    print(f"DEBUG: Detail Response Created By: {data.get('created_by_username')}")
    assert data["created_by_username"] == "Creator Person"
    assert data["created_by_email"].endswith("@example.com")

    # 3. Get Invoice List (Invoices Page)
    list_resp = client.get("/api/v1/invoices/", headers=auth_headers_with_name)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    
    # Find our invoice
    target_invoice = next((i for i in list_data if i["id"] == invoice_id), None)
    assert target_invoice is not None
    print(f"DEBUG: List Response Created By: {target_invoice.get('created_by_username')}")
    assert target_invoice["created_by_username"] == "Creator Person"
