import pytest
from uuid import uuid4
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient):
    unique_email = f"clone_{uuid4().hex}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_client_id(client: TestClient, auth_headers):
    response = client.post(
        "/api/v1/clients/",
        json={
            "name": "Clone Test Client",
            "email": "client_clone@example.com"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_clone_invoice_success(client: TestClient, auth_headers, test_client_id):
    # Create an invoice with items, discount, due_date and custom_fields
    due_date = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    create_resp = client.post(
        "/api/v1/invoices/",
        json={
            "client_id": test_client_id,
            "amount": 0,
            "currency": "USD",
            "description": "Original Invoice",
            "status": "draft",
            "due_date": due_date,
            "discount_type": "percentage",
            "discount_value": 10,
            "custom_fields": {"po": "PO-123"},
            "show_discount_in_pdf": True,
            "items": [
                {"description": "Item A", "quantity": 2, "price": 50},
                {"description": "Item B", "quantity": 1, "price": 100}
            ]
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    original = create_resp.json()

    # Clone it
    clone_resp = client.post(f"/api/v1/invoices/{original['id']}/clone", headers=auth_headers)
    assert clone_resp.status_code == 201, clone_resp.text
    cloned = clone_resp.json()

    # Assertions
    assert cloned["id"] != original["id"]
    assert cloned["number"] != original["number"]
    assert cloned["status"] == "draft"
    assert cloned["client_id"] == original["client_id"]
    assert cloned["currency"] == "USD"
    assert cloned["due_date"] == original["due_date"]
    assert cloned["custom_fields"] == {"po": "PO-123"}
    assert cloned["show_discount_in_pdf"] is True
    # Optional fields may be filtered by response schema
    assert cloned.get("has_attachment", False) is False
    assert cloned.get("attachment_filename") is None

    # Items copied
    assert isinstance(cloned.get("items"), list)
    assert len(cloned["items"]) == 2
    # Subtotal and amount recalculated with 10% discount on (2*50 + 1*100) = 200 -> amount 180
    assert pytest.approx(cloned["subtotal"], rel=1e-6) == 200.0
    assert pytest.approx(cloned["amount"], rel=1e-6) == 180.0


def test_clone_invoice_not_found(client: TestClient, auth_headers):
    resp = client.post("/api/v1/invoices/9999999/clone", headers=auth_headers)
    assert resp.status_code == 404

