#!/usr/bin/env python3
"""
Debug script to test tenant isolation and identify issues with organization switching.
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def test_tenant_isolation_debug():
    """Debug tenant isolation issues"""
    
    print("🔍 Debugging Tenant Isolation...")
    print("=" * 50)
    
    # Use user a@a.com who has access to tenant 1 (primary) and tenant 2 (via association)
    user_email = "a@a.com"
    user_password = "123456"
    
    print(f"📧 Testing user: {user_email}")
    
    # Login to get token
    login_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "email": user_email,
        "password": user_password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Login successful")
    
    # Test with explicit tenant IDs
    print(f"\n🏢 Testing with explicit tenant IDs...")
    
    # Test tenant 1 explicitly
    print(f"\n📋 Testing Tenant 1 (explicit):")
    headers_tenant1 = {"Authorization": f"Bearer {token}", "X-Tenant-ID": "1"}
    
    clients_response1 = requests.get(f"{API_BASE_URL}/clients/", headers=headers_tenant1)
    print(f"   Response status: {clients_response1.status_code}")
    print(f"   Response headers: {dict(clients_response1.headers)}")
    
    if clients_response1.status_code == 200:
        clients1 = clients_response1.json()
        print(f"   Clients: Found {len(clients1)} clients")
        for i, client in enumerate(clients1):
            print(f"     {i+1}. ID: {client.get('id')} - {client.get('name', 'Unknown')} ({client.get('email', 'No email')})")
    else:
        print(f"   ❌ Failed: {clients_response1.text}")
    
    # Test tenant 2 explicitly
    print(f"\n📋 Testing Tenant 2 (explicit):")
    headers_tenant2 = {"Authorization": f"Bearer {token}", "X-Tenant-ID": "2"}
    
    clients_response2 = requests.get(f"{API_BASE_URL}/clients/", headers=headers_tenant2)
    print(f"   Response status: {clients_response2.status_code}")
    print(f"   Response headers: {dict(clients_response2.headers)}")
    
    if clients_response2.status_code == 200:
        clients2 = clients_response2.json()
        print(f"   Clients: Found {len(clients2)} clients")
        for i, client in enumerate(clients2):
            print(f"     {i+1}. ID: {client.get('id')} - {client.get('name', 'Unknown')} ({client.get('email', 'No email')})")
    else:
        print(f"   ❌ Failed: {clients_response2.text}")
    
    # Test without X-Tenant-ID header (should use default tenant)
    print(f"\n📋 Testing Default Tenant (no X-Tenant-ID header):")
    headers_default = {"Authorization": f"Bearer {token}"}
    
    clients_response_default = requests.get(f"{API_BASE_URL}/clients/", headers=headers_default)
    print(f"   Response status: {clients_response_default.status_code}")
    
    if clients_response_default.status_code == 200:
        clients_default = clients_response_default.json()
        print(f"   Clients: Found {len(clients_default)} clients")
        for i, client in enumerate(clients_default):
            print(f"     {i+1}. ID: {client.get('id')} - {client.get('name', 'Unknown')} ({client.get('email', 'No email')})")
    else:
        print(f"   ❌ Failed: {clients_response_default.text}")
    
    # Test tenant 3 (should be denied)
    print(f"\n📋 Testing Tenant 3 (should be denied):")
    headers_tenant3 = {"Authorization": f"Bearer {token}", "X-Tenant-ID": "3"}
    
    clients_response3 = requests.get(f"{API_BASE_URL}/clients/", headers=headers_tenant3)
    print(f"   Response status: {clients_response3.status_code}")
    
    if clients_response3.status_code == 401:
        print(f"   ✅ Correctly denied access to tenant 3")
    else:
        print(f"   ⚠️ Unexpected response: {clients_response3.text}")
    
    print(f"\n✅ Tenant isolation debug completed")

if __name__ == "__main__":
    test_tenant_isolation_debug() 