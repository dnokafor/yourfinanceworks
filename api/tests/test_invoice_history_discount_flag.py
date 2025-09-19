import pytest
from uuid import uuid4
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient):
    unique_email = f"histflag_{uuid4().hex}@example.com"
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


def test_history_includes_show_discount_in_pdf_previous_and_current(client: TestClient, auth_headers):
    # Create a client
    c = client.post(
        "/api/v1/clients/",
        json={"name": "Flag Client", "email": "flag@example.com"},
        headers=auth_headers,
    )
    assert c.status_code == 201
    client_id = c.json()["id"]

    # Create an invoice with show_discount_in_pdf True
    inv = client.post(
        "/api/v1/invoices/",
        json={
            "client_id": client_id,
            "amount": 100.0,
            "status": "draft",
            "show_discount_in_pdf": True
        },
        headers=auth_headers,
    )
    assert inv.status_code == 201
    invoice_id = inv.json()["id"]

    # Update: toggle show_discount_in_pdf to False
    upd = client.put(
        f"/api/v1/invoices/{invoice_id}",
        json={"show_discount_in_pdf": False},
        headers=auth_headers,
    )
    assert upd.status_code == 200

    # Fetch history and check the latest entry includes previous/current values
    hist = client.get(f"/api/v1/invoices/{invoice_id}/history", headers=auth_headers)
    assert hist.status_code == 200
    history = hist.json()
    assert any(
        (h.get('previous_values') or {}).get('show_discount_in_pdf') is True and
        (h.get('current_values') or {}).get('show_discount_in_pdf') is False
        for h in history
    ), f"Expected show_discount_in_pdf transition True -> False in history. Got: {history}"


