#!/usr/bin/env python3
"""
Script to test tenant switching functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

def test_tenant_switching():
    """Test tenant switching with API calls"""
    base_url = "http://localhost:8000/api/v1"
    
    # First, login to get a token
    login_data = {
        "email": "test@example.com",  # Test user with access to multiple tenants
        "password": "testpass123"  # Test password
    }
    
    print("1. Logging in...")
    login_response = requests.post(f"{base_url}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    token_data = login_response.json()
    token = token_data["access_token"]
    user = token_data["user"]
    
    print(f"Login successful! User: {user['email']}, Primary Tenant: {user['tenant_id']}")
    
    # Get user's organizations
    print("\n2. Getting user organizations...")
    headers = {"Authorization": f"Bearer {token}"}
    
    me_response = requests.get(f"{base_url}/auth/me", headers=headers)
    if me_response.status_code == 200:
        me_data = me_response.json()
        organizations = me_data.get("organizations", [])
        print(f"User has access to {len(organizations)} organizations:")
        for org in organizations:
            print(f"  - {org['name']} (ID: {org['id']})")
    else:
        print(f"Failed to get user info: {me_response.status_code} - {me_response.text}")
        return
    
    # Test API calls with different tenant IDs
    print("\n3. Testing API calls with different tenant contexts...")
    
    for org in organizations:
        tenant_id = org['id']
        tenant_name = org['name']
        
        print(f"\n--- Testing with tenant {tenant_id} ({tenant_name}) ---")
        
        # Make API call with X-Tenant-ID header
        tenant_headers = {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id)
        }
        
        # Test getting clients for this tenant
        clients_response = requests.get(f"{base_url}/clients/", headers=tenant_headers)
        if clients_response.status_code == 200:
            clients = clients_response.json()
            print(f"  Clients in {tenant_name}: {len(clients)}")
            for client in clients[:3]:  # Show first 3 clients
                print(f"    - {client['name']} ({client['email']})")
        else:
            print(f"  Failed to get clients: {clients_response.status_code} - {clients_response.text}")
        
        # Test getting invoices for this tenant
        invoices_response = requests.get(f"{base_url}/invoices/", headers=tenant_headers)
        if invoices_response.status_code == 200:
            invoices = invoices_response.json()
            print(f"  Invoices in {tenant_name}: {len(invoices)}")
            for invoice in invoices[:3]:  # Show first 3 invoices
                print(f"    - {invoice['number']} - {invoice['client_name']} - ${invoice['amount']}")
        else:
            print(f"  Failed to get invoices: {invoices_response.status_code} - {invoices_response.text}")
        
        # Test getting settings for this tenant
        settings_response = requests.get(f"{base_url}/settings/", headers=tenant_headers)
        if settings_response.status_code == 200:
            settings = settings_response.json()
            company_name = settings.get('company_info', {}).get('name', 'Unknown')
            print(f"  Company name in settings: {company_name}")
        else:
            print(f"  Failed to get settings: {settings_response.status_code} - {settings_response.text}")

if __name__ == "__main__":
    test_tenant_switching()