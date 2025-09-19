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
    
    # Use user a@a.com who has access to tenant 1 (primary) and tenant 2 (via association)
    user_email = "a@a.com"
    user_password = "123456"  # Try common passwords
    
    print(f"📧 Testing user: {user_email}")
    
    # Login
    login_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "email": user_email,
        "password": user_password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        # Try different password
        login_response = requests.post(f"{API_BASE_URL}/auth/login", json={
            "email": user_email,
            "password": "testpass123"
        })
        if login_response.status_code != 200:
            print(f"❌ Login failed with second password: {login_response.text}")
            return
        
    token = login_response.json()["access_token"]
    base_headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✅ Login successful")
    
    # Get user info to see organizations
    print(f"\n👤 Getting user info...")
    me_response = requests.get(f"{API_BASE_URL}/auth/me", headers=base_headers)
    if me_response.status_code == 200:
        user_info = me_response.json()
        print(f"📋 User has access to organizations: {user_info.get('organizations', [])}")
    else:
        print(f"❌ Failed to get user info: {me_response.text}")
    
    # Test default tenant (no X-Tenant-ID header)
    print(f"\n🏢 Testing default organization (tenant 1)...")
    clients_response = requests.get(f"{API_BASE_URL}/clients/", headers=base_headers)
    if clients_response.status_code == 200:
        clients = clients_response.json()
        print(f"📋 Default org - Found {len(clients)} clients")
    else:
        print(f"❌ Failed to fetch clients from default org: {clients_response.text}")
    
    # Test switching to tenant 2 (user should have access via association)
    print(f"\n🏢 Testing organization switch to tenant 2...")
    
    # Add X-Tenant-ID header to switch organization
    headers = base_headers.copy()
    headers["X-Tenant-ID"] = "2"
    
    # Test clients endpoint with tenant switching
    clients_response = requests.get(f"{API_BASE_URL}/clients/", headers=headers)
    if clients_response.status_code == 200:
        clients = clients_response.json()
        print(f"📋 Tenant 2 - Found {len(clients)} clients")
    elif clients_response.status_code == 401:
        print(f"🚫 Tenant 2 - Access denied: {clients_response.text}")
    else:
        print(f"❌ Tenant 2 - Failed to fetch clients: {clients_response.text}")
        
    # Test invoices endpoint with tenant switching
    invoices_response = requests.get(f"{API_BASE_URL}/invoices/", headers=headers)
    if invoices_response.status_code == 200:
        invoices = invoices_response.json()
        print(f"📄 Tenant 2 - Found {len(invoices)} invoices")
    elif invoices_response.status_code == 401:
        print(f"🚫 Tenant 2 - Access denied for invoices: {invoices_response.text}")
    else:
        print(f"❌ Tenant 2 - Failed to fetch invoices: {invoices_response.text}")
        
    # Test payments endpoint with tenant switching
    payments_response = requests.get(f"{API_BASE_URL}/payments/", headers=headers)
    if payments_response.status_code == 200:
        payments_data = payments_response.json()
        payments = payments_data.get("data", []) if isinstance(payments_data, dict) else payments_data
        print(f"💰 Tenant 2 - Found {len(payments)} payments")
    elif payments_response.status_code == 401:
        print(f"🚫 Tenant 2 - Access denied for payments: {payments_response.text}")
    else:
        print(f"❌ Tenant 2 - Failed to fetch payments: {payments_response.text}")

    # Test switching to tenant 3 (user should NOT have access)
    print(f"\n🏢 Testing organization switch to tenant 3 (should be denied)...")
    
    headers["X-Tenant-ID"] = "3"
    
    clients_response = requests.get(f"{API_BASE_URL}/clients/", headers=headers)
    if clients_response.status_code == 401:
        print(f"✅ Tenant 3 - Access correctly denied")
    else:
        print(f"❌ Tenant 3 - Should have been denied but got: {clients_response.status_code}")

    print(f"\n✅ Organization switching test completed")

if __name__ == "__main__":
    test_organization_switching()