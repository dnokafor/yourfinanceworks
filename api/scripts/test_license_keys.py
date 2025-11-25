#!/usr/bin/env python3
"""
Test script to verify RSA keys work correctly for license signing and verification.
"""

import jwt
import os
from datetime import datetime, timedelta

def test_license_keys():
    """Test that the generated keys can sign and verify JWT tokens"""
    
    keys_dir = os.path.join(os.path.dirname(__file__), '..', 'keys')
    private_key_path = os.path.join(keys_dir, 'private_key.pem')
    public_key_path = os.path.join(keys_dir, 'public_key.pem')
    
    # Check if keys exist
    if not os.path.exists(private_key_path):
        print("❌ Error: private_key.pem not found")
        print(f"   Expected at: {private_key_path}")
        return False
    
    if not os.path.exists(public_key_path):
        print("❌ Error: public_key.pem not found")
        print(f"   Expected at: {public_key_path}")
        return False
    
    print("✓ Keys found")
    
    # Load keys
    with open(private_key_path, 'rb') as f:
        private_key = f.read()
    
    with open(public_key_path, 'rb') as f:
        public_key = f.read()
    
    print("✓ Keys loaded")
    
    # Create a test license payload
    test_payload = {
        'customer_email': 'test@example.com',
        'customer_name': 'Test Customer',
        'features': ['ai_invoice', 'ai_expense', 'batch_processing'],
        'issued_at': datetime.utcnow().isoformat(),
        'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat(),
        'license_type': 'commercial'
    }
    
    # Sign the license with private key
    try:
        license_token = jwt.encode(
            test_payload,
            private_key,
            algorithm='RS256'
        )
        print("✓ License signed successfully")
        print(f"  Sample license token (first 50 chars): {license_token[:50]}...")
    except Exception as e:
        print(f"❌ Error signing license: {e}")
        return False
    
    # Verify the license with public key
    try:
        decoded_payload = jwt.decode(
            license_token,
            public_key,
            algorithms=['RS256']
        )
        print("✓ License verified successfully")
        print(f"  Decoded customer: {decoded_payload['customer_name']}")
        print(f"  Decoded features: {', '.join(decoded_payload['features'])}")
    except Exception as e:
        print(f"❌ Error verifying license: {e}")
        return False
    
    # Verify payload matches
    if decoded_payload['customer_email'] != test_payload['customer_email']:
        print("❌ Error: Decoded payload doesn't match original")
        return False
    
    print("✓ Payload integrity verified")
    
    # Test with tampered token (should fail)
    tampered_token = license_token[:-10] + "tampered00"
    try:
        jwt.decode(tampered_token, public_key, algorithms=['RS256'])
        print("❌ Error: Tampered token was accepted (should have been rejected)")
        return False
    except jwt.InvalidSignatureError:
        print("✓ Tampered token correctly rejected")
    except Exception as e:
        print(f"✓ Tampered token rejected with: {type(e).__name__}")
    
    print("\n" + "="*60)
    print("✅ All tests passed! License keys are working correctly.")
    print("="*60)
    return True


if __name__ == '__main__':
    success = test_license_keys()
    exit(0 if success else 1)
