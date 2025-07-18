#!/usr/bin/env python3
"""
Test script to verify tenant context error handling.
This script tests that missing tenant context returns 401 instead of 400.
"""

import requests
import json
import sys
import os

# Add the parent directory to the path so we can import from the api module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_tenant_context_handling():
    """Test that missing tenant context returns 401 status code"""
    
    # API base URL - adjust as needed
    base_url = "http://localhost:8000/api/v1"
    
    print("Testing tenant context error handling...")
    print(f"API Base URL: {base_url}")
    print("-" * 50)
    
    # Test 1: Request without authentication token
    print("Test 1: Request without authentication token")
    try:
        response = requests.get(f"{base_url}/clients/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ PASS: Correctly returned 401 for missing authentication")
        else:
            print(f"❌ FAIL: Expected 401, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print()
    
    # Test 2: Request with invalid token
    print("Test 2: Request with invalid token")
    try:
        headers = {
            "Authorization": "Bearer invalid_token_here",
            "Content-Type": "application/json"
        }
        response = requests.get(f"{base_url}/clients/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ PASS: Correctly returned 401 for invalid token")
        else:
            print(f"❌ FAIL: Expected 401, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print()
    
    # Test 3: Request with valid token but missing tenant context
    print("Test 3: Request with valid token but missing tenant context")
    print("Note: This test requires a valid token. If you don't have one, this will fail.")
    
    # You can set a valid token here for testing
    valid_token = os.getenv("TEST_TOKEN", "")
    
    if valid_token:
        try:
            headers = {
                "Authorization": f"Bearer {valid_token}",
                "Content-Type": "application/json"
                # Note: No X-Tenant-ID header
            }
            response = requests.get(f"{base_url}/clients/", headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 401:
                print("✅ PASS: Correctly returned 401 for missing tenant context")
            else:
                print(f"❌ FAIL: Expected 401, got {response.status_code}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    else:
        print("⚠️  SKIP: No valid token provided. Set TEST_TOKEN environment variable to test this.")
    
    print()
    print("Test completed!")

if __name__ == "__main__":
    test_tenant_context_handling() 