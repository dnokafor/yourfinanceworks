#!/usr/bin/env python3
"""
Test script to verify organization switching is working correctly.
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def test_organization_switching():
    """Test that organization switching is working correctly"""
    
    print("🔄 Testing Organization Switching...")
    print("=" * 50)
    
    # Use the test user that has access to multiple organizations
    user_email = "test@example.com"
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
    
    # Get user info to see organizations
    print(f"\n👤 Getting user info...")
    me_response = requests.get(f"{API_BASE_URL}/auth/me", headers=base_headers)
    if me_response.status_code == 200:
        user_info = me_response.json()
        organizations = user_info.get('organizations', [])
        print(f"📋 User has access to {len(organizations)} organizations:")
        for org in organizations:
            print(f"   - {org['name']} (ID: {org['id']})")
    else:
        print(f"❌ Failed to get user info: {me_response.text}")
        return
    
    # Test default tenant (no X-Tenant-ID header)
    print(f"\n🏢 Testing default organization...")
    clients_response = requests.get(f"{API_BASE_URL}/clients/", headers=base_headers)
    if clients_response.status_code == 200:
        clients = clients_response.json()
        print(f"📋 Default org - Found {len(clients)} clients")
    else:
        print(f"❌ Failed to fetch clients from default org: {clients_response.text}")
    
    # Test switching to each organization the user has access to
    for org in organizations:
        tenant_id = org['id']
        org_name = org['name']
        
        print(f"\n🏢 Testing organization switch to '{org_name}' (ID: {tenant_id})...")
        
        # Add X-Tenant-ID header to switch organization
        headers = base_headers.copy()
        headers["X-Tenant-ID"] = str(tenant_id)
        
        # Test clients endpoint with tenant switching
        clients_response = requests.get(f"{API_BASE_URL}/clients/", headers=headers)
        if clients_response.status_code == 200:
            clients = clients_response.json()
            print(f"📋 {org_name} - Found {len(clients)} clients")
        elif clients_response.status_code == 401:
            print(f"🚫 {org_name} - Access denied: {clients_response.text}")
        else:
            print(f"❌ {org_name} - Failed to fetch clients: {clients_response.text}")
            
        # Test invoices endpoint with tenant switching
        invoices_response = requests.get(f"{API_BASE_URL}/invoices/", headers=headers)
        if invoices_response.status_code == 200:
            invoices = invoices_response.json()
            print(f"📄 {org_name} - Found {len(invoices)} invoices")
        elif invoices_response.status_code == 401:
            print(f"🚫 {org_name} - Access denied for invoices")
        else:
            print(f"❌ {org_name} - Failed to fetch invoices: {invoices_response.text}")
            
        # Test payments endpoint with tenant switching
        payments_response = requests.get(f"{API_BASE_URL}/payments/", headers=headers)
        if payments_response.status_code == 200:
            payments_data = payments_response.json()
            payments = payments_data.get("data", []) if isinstance(payments_data, dict) else payments_data
            print(f"💰 {org_name} - Found {len(payments)} payments")
        elif payments_response.status_code == 401:
            print(f"🚫 {org_name} - Access denied for payments")
        else:
            print(f"❌ {org_name} - Failed to fetch payments: {payments_response.text}")

    print(f"\n✅ Organization switching test completed")

if __name__ == "__main__":
    test_organization_switching()