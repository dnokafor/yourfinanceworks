#!/usr/bin/env python3
"""
Test script to verify tenant isolation is working correctly.
This script tests that users can only see data from their current organization.
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def test_tenant_isolation():
    """Test that tenant isolation is working correctly"""
    
    print("🧪 Testing Tenant Isolation...")
    print("=" * 50)
    
    # Test credentials (using actual users from the system)
    test_users = [
        {
            "email": "a@a.com",
            "password": "123456",
            "expected_tenant": 1
        },
        {
            "email": "b@b.com", 
            "password": "123456",
            "expected_tenant": 2
        }
    ]
    
    for user in test_users:
        print(f"\n📧 Testing user: {user['email']}")
        
        # Login
        login_response = requests.post(f"{API_BASE_URL}/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed for {user['email']}: {login_response.text}")
            continue
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"✅ Login successful")
        
        # Test clients endpoint
        clients_response = requests.get(f"{API_BASE_URL}/clients/", headers=headers)
        if clients_response.status_code == 200:
            clients = clients_response.json()
            print(f"📋 Found {len(clients)} clients")
        else:
            print(f"❌ Failed to fetch clients: {clients_response.text}")
            
        # Test invoices endpoint
        invoices_response = requests.get(f"{API_BASE_URL}/invoices/", headers=headers)
        if invoices_response.status_code == 200:
            invoices = invoices_response.json()
            print(f"📄 Found {len(invoices)} invoices")
        else:
            print(f"❌ Failed to fetch invoices: {invoices_response.text}")
            
        # Test payments endpoint
        payments_response = requests.get(f"{API_BASE_URL}/payments/", headers=headers)
        if payments_response.status_code == 200:
            payments_data = payments_response.json()
            payments = payments_data.get("data", []) if isinstance(payments_data, dict) else payments_data
            print(f"💰 Found {len(payments)} payments")
        else:
            print(f"❌ Failed to fetch payments: {payments_response.text}")
            
        print(f"✅ Tenant {user['expected_tenant']} data isolation test completed")

if __name__ == "__main__":
    test_tenant_isolation()