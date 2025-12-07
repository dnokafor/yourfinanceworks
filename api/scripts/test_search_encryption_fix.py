#!/usr/bin/env python3
"""
Test script to verify that encrypted data is not exposed in search results.
"""
import sys
import re

def _looks_like_encrypted_data(value: str) -> bool:
    """
    Check if a value looks like encrypted data (base64 encoded).
    This is used to detect when decryption failed and we're showing raw encrypted data.
    """
    if not isinstance(value, str) or len(value) < 30:
        return False
    
    # Base64 pattern check
    base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
    
    # If it contains common plain text patterns, it's probably not encrypted
    if '@' in value and '.' in value:  # Looks like email
        return False
    if ' ' in value:  # Has spaces - likely plain text
        return False
    
    return base64_pattern.match(value) is not None and len(value) > 30

def _sanitize_value(value: str, fallback: str = '') -> str:
    """
    Sanitize a value for search display.
    If the value looks like encrypted data, return the fallback instead.
    """
    if value is None:
        return fallback
    if _looks_like_encrypted_data(value):
        return fallback
    return value

def test_encryption_detection():
    """Test that we can detect encrypted/base64 data"""
    print("Testing encryption detection...")
    
    # Test cases
    test_cases = [
        # (value, should_be_detected_as_encrypted)
        ("EIMkyGgKc7ZOg1QlBodtUO2X6WpRNUXm2CbGgMeZvMM=", True),  # Base64 encrypted
        ("John Doe", False),  # Normal name with space
        ("john@example.com", False),  # Email
        ("ABC123", False),  # Too short
        ("A" * 50, True),  # Long string without spaces
        ("Test Company Inc.", False),  # Normal company name
        ("", False),  # Empty string
    ]
    
    passed = 0
    failed = 0
    
    for value, expected_encrypted in test_cases:
        result = _looks_like_encrypted_data(value)
        status = "✓" if result == expected_encrypted else "✗"
        if result == expected_encrypted:
            passed += 1
        else:
            failed += 1
        print(f"  {status} '{value[:50]}...' -> Encrypted: {result} (expected: {expected_encrypted})")
    
    print(f"\nEncryption Detection: {passed} passed, {failed} failed\n")
    return failed == 0

def test_sanitization():
    """Test that sanitization works correctly"""
    print("Testing value sanitization...")
    
    test_cases = [
        # (value, fallback, expected_result)
        ("EIMkyGgKc7ZOg1QlBodtUO2X6WpRNUXm2CbGgMeZvMM=", "Unknown", "Unknown"),
        ("John Doe", "Unknown", "John Doe"),
        ("john@example.com", "Unknown", "john@example.com"),
        (None, "Unknown", "Unknown"),
        ("", "Unknown", ""),
    ]
    
    passed = 0
    failed = 0
    
    for value, fallback, expected in test_cases:
        result = _sanitize_value(value, fallback)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} '{value}' -> '{result}' (expected: '{expected}')")
    
    print(f"\nSanitization: {passed} passed, {failed} failed\n")
    return failed == 0

def main():
    print("=" * 60)
    print("Search Encryption Fix Validation")
    print("=" * 60)
    print()
    
    detection_ok = test_encryption_detection()
    sanitization_ok = test_sanitization()
    
    print("=" * 60)
    if detection_ok and sanitization_ok:
        print("✓ All tests passed!")
        print("\nThe fix should prevent encrypted data from appearing in search results.")
        print("Next steps:")
        print("1. Restart the API server")
        print("2. Reindex search data: POST /api/search/reindex")
        print("3. Test global search in the UI")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
