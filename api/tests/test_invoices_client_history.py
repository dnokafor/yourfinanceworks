import pytest
from uuid import uuid4
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient):
    unique_email = f"hist_{uuid4().hex}@example.com"
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


def test_update_client_creates_history_entry(client: TestClient, auth_headers):
    # Create two clients
    resp_a = client.post(
        "/api/v1/clients/",
        json={"name": "Client A", "email": "a@example.com"},
        headers=auth_headers,
    )
    assert resp_a.status_code == 201
    client_a_id = resp_a.json()["id"]

    resp_b = client.post(
        "/api/v1/clients/",
        json={"name": "Client B", "email": "b@example.com"},
        headers=auth_headers,
    )
    assert resp_b.status_code == 201
    client_b_id = resp_b.json()["id"]

    # Create an invoice for Client A
    inv_resp = client.post(
        "/api/v1/invoices/",
        json={
            "client_id": client_a_id,
            "amount": 100.0,
            "status": "draft",
            "description": "Test"
        },
        headers=auth_headers,
    )
    assert inv_resp.status_code == 201
    invoice_id = inv_resp.json()["id"]

    # Update invoice to switch client to Client B
    upd_resp = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={"client_id": client_b_id},
        headers=auth_headers,
    )
    assert upd_resp.status_code == 200

    # Fetch history and ensure a client change entry exists
    hist_resp = client.get(f"/api/v1/invoices/{invoice_id}/history", headers=auth_headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()

    assert any(
        ('Client changed from' in (h.get('details') or ''))
        and ('Client A' in (h.get('details') or ''))
        and ('Client B' in (h.get('details') or ''))
        for h in history
    ), f"No client change entry found in history: {history}"


