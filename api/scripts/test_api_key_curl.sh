#!/bin/bash

# API Key Testing Script
# This script tests the complete API key functionality using curl

set -e  # Exit on any error

# Configuration
BASE_URL="http://localhost:8000"
UI_URL="http://localhost:8080"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${BLUE}📋 Step $1: $2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Test configuration
TEST_EMAIL="apitest@example.com"
TEST_PASSWORD="testpassword123"
API_KEY=""
CLIENT_ID=""
JWT_TOKEN=""

echo -e "${BLUE}🔑 API Key Testing Script${NC}"
echo "=================================================="
echo ""

# Step 1: Health Check
print_step "1" "Health Check"
if curl -s -f "$BASE_URL/health" > /dev/null; then
    print_success "API server is running"
else
    print_error "API server is not accessible at $BASE_URL"
    exit 1
fi

# Step 2: User Login
print_step "2" "User Authentication"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    JWT_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    print_success "User logged in successfully"
    print_info "JWT Token: ${JWT_TOKEN:0:20}..."
else
    print_error "Login failed. Response: $LOGIN_RESPONSE"
    print_info "Make sure user $TEST_EMAIL exists with password $TEST_PASSWORD"
    exit 1
fi

# Step 3: List existing API keys
print_step "3" "List Existing API Keys"
EXISTING_KEYS=$(curl -s -X GET "$BASE_URL/api/v1/external-auth/api-keys" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "Existing API keys:"
echo "$EXISTING_KEYS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f'Found {len(data)} existing API keys')
        for i, key in enumerate(data):
            print(f'  {i+1}. {key.get(\"client_name\", \"Unknown\")} ({key.get(\"api_key_prefix\", \"N/A\")})')
    else:
        print('Unexpected response format')
except:
    print('Error parsing response')
"

# Step 4: Create new API key
print_step "4" "Create New API Key"
API_KEY_REQUEST='{
    "client_name": "Test API Client",
    "client_description": "Testing API key functionality via curl",
    "allowed_transaction_types": ["income", "expense"],
    "allowed_currencies": ["USD", "EUR"],
    "max_transaction_amount": 10000.00,
    "rate_limit_per_minute": 60,
    "rate_limit_per_hour": 1000,
    "rate_limit_per_day": 10000,
    "is_sandbox": true,
    "webhook_url": "https://webhook.site/test"
}'

API_KEY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/external-auth/api-keys" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "$API_KEY_REQUEST")

if echo "$API_KEY_RESPONSE" | grep -q "api_key"; then
    API_KEY=$(echo "$API_KEY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['api_key'])")
    CLIENT_ID=$(echo "$API_KEY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['client_id'])")
    print_success "API key created successfully"
    print_info "Client ID: $CLIENT_ID"
    print_info "API Key: ${API_KEY:0:15}..."
else
    print_error "Failed to create API key. Response: $API_KEY_RESPONSE"
    
    # Check if it's a limit error
    if echo "$API_KEY_RESPONSE" | grep -q "Maximum of 2 API keys"; then
        print_info "Maximum API keys reached. Using existing key for testing..."
        
        # Get first existing key for testing
        FIRST_KEY_CLIENT_ID=$(echo "$EXISTING_KEYS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list) and len(data) > 0:
        print(data[0]['client_id'])
    else:
        print('')
except:
    print('')
")
        
        if [ -n "$FIRST_KEY_CLIENT_ID" ]; then
            CLIENT_ID="$FIRST_KEY_CLIENT_ID"
            print_info "Using existing client ID: $CLIENT_ID"
            
            # Regenerate the key to get a fresh API key
            print_step "4b" "Regenerate Existing API Key"
            REGEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/external-auth/api-keys/$CLIENT_ID/regenerate" \
                -H "Authorization: Bearer $JWT_TOKEN")
            
            if echo "$REGEN_RESPONSE" | grep -q "api_key"; then
                API_KEY=$(echo "$REGEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['api_key'])")
                print_success "API key regenerated successfully"
                print_info "New API Key: ${API_KEY:0:15}..."
            else
                print_error "Failed to regenerate API key. Response: $REGEN_RESPONSE"
                exit 1
            fi
        else
            exit 1
        fi
    else
        exit 1
    fi
fi

# Step 5: Test API key authentication
print_step "5" "Test API Key Authentication"
AUTH_TEST=$(curl -s -X GET "$BASE_URL/api/v1/external-transactions/transactions" \
    -H "X-API-Key: $API_KEY")

if echo "$AUTH_TEST" | grep -q "\[\]" || echo "$AUTH_TEST" | grep -q "external_transaction_id"; then
    print_success "API key authentication working"
else
    print_error "API key authentication failed. Response: $AUTH_TEST"
    exit 1
fi

# Step 6: Submit test transaction
print_step "6" "Submit Test Transaction"
TRANSACTION_DATA='{
    "transaction_type": "expense",
    "amount": 150.75,
    "currency": "USD",
    "date": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "description": "Test transaction via curl script",
    "source_system": "Curl Test Script",
    "category": "Testing",
    "subcategory": "API Testing",
    "business_purpose": "Testing API key functionality",
    "vendor_name": "Test Vendor",
    "payment_method": "Credit Card",
    "sales_tax_amount": 12.50,
    "vat_amount": 0.00,
    "other_tax_amount": 0.00,
    "invoice_reference": "TEST-INV-001",
    "receipt_url": "https://example.com/receipt/001.pdf"
}'

TRANSACTION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/external-transactions/transactions" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$TRANSACTION_DATA")

if echo "$TRANSACTION_RESPONSE" | grep -q "external_transaction_id"; then
    TRANSACTION_ID=$(echo "$TRANSACTION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['external_transaction_id'])")
    print_success "Transaction submitted successfully"
    print_info "Transaction ID: $TRANSACTION_ID"
    
    # Pretty print the response
    echo "Transaction details:"
    echo "$TRANSACTION_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  ID: {data.get(\"external_transaction_id\")}')
print(f'  Type: {data.get(\"transaction_type\")}')
print(f'  Amount: \${data.get(\"amount\")} {data.get(\"currency\")}')
print(f'  Description: {data.get(\"description\")}')
print(f'  Status: {data.get(\"status\")}')
print(f'  Created: {data.get(\"created_at\")}')
"
else
    print_error "Transaction submission failed. Response: $TRANSACTION_RESPONSE"
fi

# Step 7: List transactions
print_step "7" "List Transactions"
TRANSACTIONS_LIST=$(curl -s -X GET "$BASE_URL/api/v1/external-transactions/transactions" \
    -H "X-API-Key: $API_KEY")

echo "Transactions for this API key:"
echo "$TRANSACTIONS_LIST" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, dict) and 'transactions' in data:
        transactions = data['transactions']
        print(f'Found {len(transactions)} transactions')
        for i, txn in enumerate(transactions):
            print(f'  {i+1}. {txn.get(\"description\", \"N/A\")} - \${txn.get(\"amount\", \"0\")} {txn.get(\"currency\", \"\")} ({txn.get(\"status\", \"unknown\")})')
    elif isinstance(data, list):
        print(f'Found {len(data)} transactions')
        for i, txn in enumerate(data):
            print(f'  {i+1}. {txn.get(\"description\", \"N/A\")} - \${txn.get(\"amount\", \"0\")} {txn.get(\"currency\", \"\")} ({txn.get(\"status\", \"unknown\")})')
    else:
        print(f'Unexpected response format: {type(data)}')
        print(f'Keys: {list(data.keys()) if isinstance(data, dict) else \"Not a dict\"}')
except Exception as e:
    print(f'Error parsing response: {e}')
"

# Step 8: Test rate limiting (optional)
print_step "8" "Test Rate Limiting (Optional)"
print_info "Sending 5 rapid requests to test rate limiting..."

for i in {1..5}; do
    RATE_TEST=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/api/v1/external-transactions/transactions" \
        -H "X-API-Key: $API_KEY")
    HTTP_CODE="${RATE_TEST: -3}"
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  Request $i: ✅ Success (200)"
    elif [ "$HTTP_CODE" = "429" ]; then
        echo "  Request $i: ⚠️  Rate limited (429)"
    else
        echo "  Request $i: ❓ Unexpected response ($HTTP_CODE)"
    fi
    
    sleep 0.1  # Small delay between requests
done

# Step 9: Test invalid API key
print_step "9" "Test Invalid API Key"
INVALID_RESPONSE=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/api/v1/external-transactions/transactions" \
    -H "X-API-Key: ak_invalid_key_for_testing")

HTTP_CODE="${INVALID_RESPONSE: -3}"
if [ "$HTTP_CODE" = "401" ]; then
    print_success "Invalid API key correctly rejected (401)"
else
    print_error "Invalid API key not properly rejected. Got HTTP $HTTP_CODE"
fi

# Step 10: Test missing API key
print_step "10" "Test Missing API Key"
NO_KEY_RESPONSE=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/api/v1/external-transactions/transactions")

HTTP_CODE="${NO_KEY_RESPONSE: -3}"
if [ "$HTTP_CODE" = "401" ]; then
    print_success "Missing API key correctly rejected (401)"
else
    print_error "Missing API key not properly rejected. Got HTTP $HTTP_CODE"
fi

# Step 11: Get API key details
print_step "11" "Get API Key Details"
KEY_DETAILS=$(curl -s -X GET "$BASE_URL/api/v1/external-auth/api-keys/$CLIENT_ID" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "API Key details:"
echo "$KEY_DETAILS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  Name: {data.get(\"client_name\", \"N/A\")}')
    print(f'  Description: {data.get(\"client_description\", \"N/A\")}')
    print(f'  Prefix: {data.get(\"api_key_prefix\", \"N/A\")}')
    print(f'  Active: {data.get(\"is_active\", False)}')
    print(f'  Sandbox: {data.get(\"is_sandbox\", False)}')
    print(f'  Total Requests: {data.get(\"total_requests\", 0)}')
    print(f'  Total Transactions: {data.get(\"total_transactions_submitted\", 0)}')
    print(f'  Rate Limits: {data.get(\"rate_limit_per_minute\", 0)}/min, {data.get(\"rate_limit_per_hour\", 0)}/hour, {data.get(\"rate_limit_per_day\", 0)}/day')
    print(f'  Allowed Types: {data.get(\"allowed_transaction_types\", [])}')
    print(f'  Allowed Currencies: {data.get(\"allowed_currencies\", \"All\")}')
    if data.get(\"max_transaction_amount\"):
        print(f'  Max Amount: \${data.get(\"max_transaction_amount\")}')
    print(f'  Last Used: {data.get(\"last_used_at\", \"Never\")}')
    print(f'  Created: {data.get(\"created_at\", \"Unknown\")}')
except Exception as e:
    print(f'Error parsing response: {e}')
"

# Step 12: Test permissions endpoint
print_step "12" "Test Permissions Endpoint"
PERMISSIONS=$(curl -s -X GET "$BASE_URL/api/v1/external-auth/permissions" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "Available permissions:"
echo "$PERMISSIONS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, dict):
        for key, value in data.items():
            print(f'  {key}: {value}')
    else:
        print('Unexpected response format')
except Exception as e:
    print(f'Error parsing response: {e}')
"

# Summary
echo ""
echo "=================================================="
print_success "API Key Testing Complete!"
echo ""
echo "Summary:"
echo "  • API Server: $BASE_URL"
echo "  • Test User: $TEST_EMAIL"
echo "  • Client ID: $CLIENT_ID"
echo "  • API Key: ${API_KEY:0:15}... (truncated for security)"
echo ""
print_info "The API key is ready for use in your applications!"
echo ""
echo "Example usage:"
echo "curl -H 'X-API-Key: $API_KEY' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"transaction_type\":\"expense\",\"amount\":100,\"currency\":\"USD\",\"date\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"description\":\"Test\",\"source_system\":\"MyApp\"}' \\"
echo "     $BASE_URL/api/v1/external-transactions/transactions"
echo ""
print_info "Access the web UI at: $UI_URL/settings (API Keys tab)"
