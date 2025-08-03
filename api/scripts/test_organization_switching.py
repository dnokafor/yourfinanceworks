#!/usr/bin/env python3
"""
Test script to verify organization switching is working correctly.
This script tests that users can switch between organizations they have access to.
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def test_organization_switching():
    """Test that organization switching is working correctly"""
    
    print("🔄 Testing Organization Switching...")
    print("=" * 50)
    
    # Use a user that should have access to multiple organizations
    user_email = "test@tenant1.com"
    user_password = "testpass123"
    
    print(f"📧 Testing user: {user_email}")
    
    # Login
    login_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "email": user_email,
        "password": user_password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
        
    token = login_response.json()["access_token"]
    base_headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✅ Login successful")
    
    # Test default tenant (no X-Tenant-ID header)
    print(f"\n🏢 Testing default organization...")
    clients_response = requests.get(f"{API_BASE_URL}/clients/", headers=base_headers)
    if clients_response.status_code == 200:
        clients = clients_response.json()
        print(f"📋 Default org - Found {len(clients)} clients")
    else:
        print(f"❌ Failed to fetch clients from default org: {clients_response.text}")
    
    # Test switching to different tenants
    test_tenants = [1, 2, 3]
    
    for tenant_id in test_tenants:
        print(f"\n🏢 Testing organization switch to tenant {tenant_id}...")
        
        # Add X-Tenant-ID header to switch organization
        headers = base_headers.copy()
        headers["X-Tenant-ID"] = str(tenant_id)
        
        # Test clients endpoint with tenant switching
        clients_response = requests.get(f"{API_BASE_URL}/clients/", headers=headers)
        if clients_response.status_code == 200:
            clients = clients_response.json()
            print(f"📋 Tenant {tenant_id} - Found {len(clients)} clients")
        elif clients_response.status_code == 401:
            print(f"🚫 Tenant {tenant_id} - Access denied (expected if user doesn't have access)")
        else:
            print(f"❌ Tenant {tenant_id} - Failed to fetch clients: {clients_response.text}")
            
        # Test invoices endpoint with tenant switching
        invoices_response = requests.get(f"{API_BASE_URL}/invoices/", headers=headers)
        if invoices_response.status_code == 200:
            invoices = invoices_response.json()
            print(f"📄 Tenant {tenant_id} - Found {len(invoices)} invoices")
        elif invoices_response.status_code == 401:
            print(f"🚫 Tenant {tenant_id} - Access denied for invoices")
        else:
            print(f"❌ Tenant {tenant_id} - Failed to fetch invoices: {invoices_response.text}")
            
        # Test payments endpoint with tenant switching
        payments_response = requests.get(f"{API_BASE_URL}/payments/", headers=headers)
        if payments_response.status_code == 200:
            payments_data = payments_response.json()
            payments = payments_data.get("data", []) if isinstance(payments_data, dict) else payments_data
            print(f"💰 Tenant {tenant_id} - Found {len(payments)} payments")
        elif payments_response.status_code == 401:
            print(f"🚫 Tenant {tenant_id} - Access denied for payments")
        else:
            print(f"❌ Tenant {tenant_id} - Failed to fetch payments: {payments_response.text}")

    print(f"\n✅ Organization switching test completed")

if __name__ == "__main__":
    test_organization_switching()