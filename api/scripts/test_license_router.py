#!/usr/bin/env python3
"""
Test script for License Management Router

This script tests all the license management endpoints:
- GET /license/status
- POST /license/activate
- POST /license/validate
- GET /license/features
- DELETE /license/deactivate
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime, timedelta, timezone
import jwt

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

# Load private key for generating test license
PRIVATE_KEY_PATH = os.path.join(os.path.dirname(__file__), "..", "keys", "private_key.pem")


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_response(response):
    """Pretty print response"""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def generate_test_license(features=None, days_valid=365):
    """Generate a test license key"""
    if features is None:
        features = ["ai_invoice", "ai_expense", "batch_processing", "inventory"]
    
    try:
        with open(PRIVATE_KEY_PATH, "r") as f:
            private_key = f.read()
    except FileNotFoundError:
        print(f"❌ Private key not found at {PRIVATE_KEY_PATH}")
        print("   Please run the key generation script first:")
        print("   python api/scripts/generate_license_keys.py")
        return None
    
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=days_valid)
    
    payload = {
        "customer_email": "test@example.com",
        "customer_name": "Test Customer",
        "organization_name": "Test Organization",
        "features": features,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "license_type": "commercial"
    }
    
    license_key = jwt.encode(payload, private_key, algorithm="RS256")
    return license_key


def login():
    """Login and get access token"""
    print_section("Logging in")
    
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        data={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful")
        return token
    else:
        print(f"❌ Login failed")
        print_response(response)
        return None


def test_license_status(token):
    """Test GET /license/status endpoint"""
    print_section("Test 1: Get License Status")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/license/status", headers=headers)
    
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ License status retrieved successfully")
        print(f"   License Status: {data['license_status']}")
        print(f"   Is Trial: {data['is_trial']}")
        print(f"   Is Licensed: {data['is_licensed']}")
        if data['trial_info']:
            print(f"   Trial Days Remaining: {data['trial_info']['days_remaining']}")
        return True
    else:
        print(f"\n❌ Failed to get license status")
        return False


def test_feature_availability(token):
    """Test GET /license/features endpoint"""
    print_section("Test 2: Get Feature Availability")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/license/features", headers=headers)
    
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Feature availability retrieved successfully")
        print(f"   License Status: {data['license_status']}")
        print(f"   Total Features: {len(data['features'])}")
        
        # Count enabled features
        enabled_count = sum(1 for f in data['features'] if f['enabled'])
        print(f"   Enabled Features: {enabled_count}")
        
        # Show some features
        print("\n   Sample Features:")
        for feature in data['features'][:5]:
            status = "✓" if feature['enabled'] else "✗"
            print(f"     {status} {feature['name']} ({feature['id']})")
        
        return True
    else:
        print(f"\n❌ Failed to get feature availability")
        return False


def test_validate_license(token):
    """Test POST /license/validate endpoint"""
    print_section("Test 3: Validate License Key")
    
    # Generate a test license
    print("Generating test license key...")
    license_key = generate_test_license()
    
    if not license_key:
        print("❌ Failed to generate test license")
        return False
    
    print(f"License Key: {license_key[:50]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE_URL}/license/validate",
        headers=headers,
        json={"license_key": license_key}
    )
    
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data['valid']:
            print(f"\n✅ License validation successful")
            print(f"   Customer: {data['payload']['customer_name']}")
            print(f"   Features: {', '.join(data['payload']['features'])}")
            return license_key
        else:
            print(f"\n❌ License validation failed: {data['message']}")
            return None
    else:
        print(f"\n❌ Failed to validate license")
        return None


def test_activate_license(token, license_key):
    """Test POST /license/activate endpoint"""
    print_section("Test 4: Activate License")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE_URL}/license/activate",
        headers=headers,
        json={"license_key": license_key}
    )
    
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"\n✅ License activation successful")
            print(f"   Features: {', '.join(data['features'])}")
            if data['expires_at']:
                print(f"   Expires: {data['expires_at']}")
            return True
        else:
            print(f"\n❌ License activation failed: {data['message']}")
            return False
    else:
        print(f"\n❌ Failed to activate license")
        return False


def test_license_status_after_activation(token):
    """Test GET /license/status after activation"""
    print_section("Test 5: Get License Status After Activation")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/license/status", headers=headers)
    
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ License status retrieved successfully")
        print(f"   License Status: {data['license_status']}")
        print(f"   Is Licensed: {data['is_licensed']}")
        if data['license_info']:
            print(f"   Customer: {data['license_info']['customer_name']}")
            print(f"   Organization: {data['license_info']['organization_name']}")
        return True
    else:
        print(f"\n❌ Failed to get license status")
        return False


def test_deactivate_license(token):
    """Test DELETE /license/deactivate endpoint"""
    print_section("Test 6: Deactivate License")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_BASE_URL}/license/deactivate", headers=headers)
    
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"\n✅ License deactivation successful")
            return True
        else:
            print(f"\n❌ License deactivation failed")
            return False
    else:
        print(f"\n❌ Failed to deactivate license")
        return False


def test_invalid_license(token):
    """Test validation with invalid license"""
    print_section("Test 7: Validate Invalid License")
    
    invalid_license = "invalid.license.key"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE_URL}/license/validate",
        headers=headers,
        json={"license_key": invalid_license}
    )
    
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        if not data['valid']:
            print(f"\n✅ Invalid license correctly rejected")
            print(f"   Error: {data['error']}")
            print(f"   Error Code: {data['error_code']}")
            return True
        else:
            print(f"\n❌ Invalid license was accepted (should have been rejected)")
            return False
    else:
        print(f"\n❌ Unexpected response")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  License Management Router Test Suite")
    print("=" * 80)
    
    # Login
    token = login()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        return
    
    # Run tests
    results = []
    
    # Test 1: Get initial license status
    results.append(("Get License Status", test_license_status(token)))
    
    # Test 2: Get feature availability
    results.append(("Get Feature Availability", test_feature_availability(token)))
    
    # Test 3: Validate license
    license_key = test_validate_license(token)
    results.append(("Validate License", license_key is not None))
    
    if license_key:
        # Test 4: Activate license
        results.append(("Activate License", test_activate_license(token, license_key)))
        
        # Test 5: Get license status after activation
        results.append(("Get Status After Activation", test_license_status_after_activation(token)))
        
        # Test 6: Deactivate license
        results.append(("Deactivate License", test_deactivate_license(token)))
    
    # Test 7: Test invalid license
    results.append(("Validate Invalid License", test_invalid_license(token)))
    
    # Print summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
