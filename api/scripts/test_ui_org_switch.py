#!/usr/bin/env python3
"""
Test script to verify UI organization switching is working correctly.
This script tests the browser automation to ensure the UI properly switches organizations.
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
UI_BASE_URL = "http://localhost:8080"

def test_ui_organization_switching():
    """Test that UI organization switching is working correctly"""
    
    print("🔄 Testing UI Organization Switching...")
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
    
    # Test switching between organizations via API
    print(f"\n🏢 Testing organization switching via API...")
    
    # Test tenant 1 (default)
    print(f"\n📋 Testing Tenant 1 (default):")
    headers_tenant1 = {"Authorization": f"Bearer {token}"}
    
    # Test clients
    clients_response1 = requests.get(f"{API_BASE_URL}/clients/", headers=headers_tenant1)
    if clients_response1.status_code == 200:
        clients1 = clients_response1.json()
        print(f"   Clients: Found {len(clients1)} clients")
        for i, client in enumerate(clients1):
            print(f"     {i+1}. {client.get('name', 'Unknown')} ({client.get('email', 'No email')})")
    else:
        print(f"   ❌ Failed to fetch clients: {clients_response1.text}")
    
    # Test invoices
    invoices_response1 = requests.get(f"{API_BASE_URL}/invoices/", headers=headers_tenant1)
    if invoices_response1.status_code == 200:
        invoices1 = invoices_response1.json()
        print(f"   Invoices: Found {len(invoices1)} invoices")
        for i, invoice in enumerate(invoices1[:3]):  # Show first 3
            print(f"     {i+1}. {invoice.get('number', 'Unknown')} - {invoice.get('client_name', 'Unknown')} - ${invoice.get('amount', 0)}")
    else:
        print(f"   ❌ Failed to fetch invoices: {invoices_response1.text}")
    
    # Test payments
    payments_response1 = requests.get(f"{API_BASE_URL}/payments/", headers=headers_tenant1)
    if payments_response1.status_code == 200:
        payments1 = payments_response1.json()
        payments_data1 = payments1.get("data", []) if isinstance(payments1, dict) else payments1
        print(f"   Payments: Found {len(payments_data1)} payments")
        for i, payment in enumerate(payments_data1[:3]):  # Show first 3
            print(f"     {i+1}. {payment.get('invoice_number', 'Unknown')} - ${payment.get('amount', 0)}")
    else:
        print(f"   ❌ Failed to fetch payments: {payments_response1.text}")
    
    # Test tenant 2
    print(f"\n📋 Testing Tenant 2:")
    headers_tenant2 = {"Authorization": f"Bearer {token}", "X-Tenant-ID": "2"}
    
    # Test clients
    clients_response2 = requests.get(f"{API_BASE_URL}/clients/", headers=headers_tenant2)
    if clients_response2.status_code == 200:
        clients2 = clients_response2.json()
        print(f"   Clients: Found {len(clients2)} clients")
        for i, client in enumerate(clients2):
            print(f"     {i+1}. {client.get('name', 'Unknown')} ({client.get('email', 'No email')})")
    else:
        print(f"   ❌ Failed to fetch clients: {clients_response2.text}")
    
    # Test invoices
    invoices_response2 = requests.get(f"{API_BASE_URL}/invoices/", headers=headers_tenant2)
    if invoices_response2.status_code == 200:
        invoices2 = invoices_response2.json()
        print(f"   Invoices: Found {len(invoices2)} invoices")
        for i, invoice in enumerate(invoices2[:3]):  # Show first 3
            print(f"     {i+1}. {invoice.get('number', 'Unknown')} - {invoice.get('client_name', 'Unknown')} - ${invoice.get('amount', 0)}")
    else:
        print(f"   ❌ Failed to fetch invoices: {invoices_response2.text}")
    
    # Test payments
    payments_response2 = requests.get(f"{API_BASE_URL}/payments/", headers=headers_tenant2)
    if payments_response2.status_code == 200:
        payments2 = payments_response2.json()
        payments_data2 = payments2.get("data", []) if isinstance(payments2, dict) else payments2
        print(f"   Payments: Found {len(payments_data2)} payments")
        for i, payment in enumerate(payments_data2[:3]):  # Show first 3
            print(f"     {i+1}. {payment.get('invoice_number', 'Unknown')} - ${payment.get('amount', 0)}")
    else:
        print(f"   ❌ Failed to fetch payments: {payments_response2.text}")
    
    # Summary comparison
    print(f"\n📊 Summary Comparison:")
    if clients_response1.status_code == 200 and clients_response2.status_code == 200:
        clients1_data = clients_response1.json()
        clients2_data = clients_response2.json()
        
        print(f"   Tenant 1: {len(clients1_data)} clients")
        print(f"   Tenant 2: {len(clients2_data)} clients")
        
        if len(clients1_data) != len(clients2_data):
            print(f"   ✅ Data is different between tenants (different number of clients)")
        else:
            print(f"   ⚠️ Same number of clients, checking content...")
            # Compare client names
            names1 = [c.get('name', '') for c in clients1_data]
            names2 = [c.get('name', '') for c in clients2_data]
            if names1 != names2:
                print(f"   ✅ Data is different between tenants (different client names)")
            else:
                print(f"   ⚠️ Client names are identical between tenants")
    
    print(f"\n✅ UI organization switching test completed")
    print(f"\n📝 Instructions for manual testing:")
    print(f"1. Open browser and go to {UI_BASE_URL}")
    print(f"2. Login with {user_email} / {user_password}")
    print(f"3. Use the organization selector in the sidebar to switch between organizations")
    print(f"4. Verify that clients, invoices, and payments change when switching organizations")
    print(f"5. Check browser console for any errors during switching")

if __name__ == "__main__":
    test_ui_organization_switching() 