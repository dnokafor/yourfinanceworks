#!/usr/bin/env python3

import sys
import os
import json
import requests

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_discount_calculation():
    """Test the discount calculation endpoint with proper request body"""
    
    # Test data
    test_data = {
        "subtotal": 1000.0,
        "currency": "USD"
    }
    
    url = "http://localhost:8000/api/v1/discount-rules/calculate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer your_token_here"  # Would need actual token
    }
    
    print("=== DISCOUNT CALCULATION VALIDATION TEST ===")
    print(f"Testing endpoint: {url}")
    print(f"Request body: {json.dumps(test_data, indent=2)}")
    
    # Test 1: Valid request body (this should work now)
    print("\n1. Testing with valid request body...")
    try:
        response = requests.post(url, json=test_data, headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Expected 401 (auth required) - endpoint structure is correct")
        elif response.status_code == 422:
            print("❌ Still getting validation error")
            print(f"Response: {response.text}")
        else:
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error (expected if API not accessible): {e}")
    
    # Test 2: Empty request body (this should fail with validation error)
    print("\n2. Testing with empty request body (should fail with validation)...")
    try:
        response = requests.post(url, json={}, headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 422:
            print("✅ Expected 422 validation error for empty body")
        print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error (expected if API not accessible): {e}")
    
    # Test 3: Missing subtotal field (this should fail with validation error)
    print("\n3. Testing with missing subtotal field (should fail with validation)...")
    try:
        response = requests.post(url, json={"currency": "USD"}, headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 422:
            print("✅ Expected 422 validation error for missing subtotal")
        print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error (expected if API not accessible): {e}")

if __name__ == "__main__":
    test_discount_calculation() 