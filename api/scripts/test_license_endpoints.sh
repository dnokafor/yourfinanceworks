#!/bin/bash
# Simple curl-based test for license endpoints

API_BASE="http://localhost:8000/api/v1"

echo "=================================="
echo "License Management Endpoint Tests"
echo "=================================="
echo ""

# First, we need to login to get a token
# Let's try to create a test user first
echo "1. Creating test user..."
curl -s -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "license-test@example.com",
    "password": "TestPassword123!",
    "full_name": "License Test User",
    "organization_name": "Test Org"
  }' | jq '.' 2>/dev/null || echo "User may already exist"

echo ""
echo "2. Logging in..."
RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "license-test@example.com",
    "password": "TestPassword123!"
  }')

TOKEN=$(echo "$RESPONSE" | jq -r '.access_token' 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ Failed to get authentication token"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Got authentication token"
echo ""

# Test 1: Get license status
echo "3. Testing GET /license/status"
echo "-----------------------------------"
curl -s -X GET "$API_BASE/license/status" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Test 2: Get feature availability
echo "4. Testing GET /license/features"
echo "-----------------------------------"
curl -s -X GET "$API_BASE/license/features" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Test 3: Validate a test license (will fail without valid key)
echo "5. Testing POST /license/validate (with invalid key)"
echo "-----------------------------------"
curl -s -X POST "$API_BASE/license/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"license_key": "invalid.test.key"}' | jq '.'
echo ""

echo "=================================="
echo "Tests completed!"
echo "=================================="
