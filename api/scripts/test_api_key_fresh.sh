#!/bin/bash

# Fresh API Key Testing Script
# This script creates fresh API keys by cleaning up old ones first

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

echo -e "${BLUE}🔑 Fresh API Key Testing Script${NC}"
echo "=================================================="
echo "This script will create fresh API keys and transactions"
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

# Step 3: Clean up existing API keys
print_step "3" "Clean Up Existing API Keys"
EXISTING_KEYS=$(curl -s -X GET "$BASE_URL/api/v1/external-auth/api-keys" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "$EXISTING_KEYS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f'Found {len(data)} existing API keys to clean up')
        for key in data:
            print(f'  - {key.get(\"client_name\", \"Unknown\")} ({key.get(\"client_id\", \"N/A\")})')
    else:
        print('No existing keys or unexpected format')
except:
    print('Error parsing existing keys')
"

# Delete existing keys
EXISTING_CLIENT_IDS=$(echo "$EXISTING_KEYS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        for key in data:
            print(key.get('client_id', ''))
except:
    pass
")

if [ -n "$EXISTING_CLIENT_IDS" ]; then
    echo "$EXISTING_CLIENT_IDS" | while read -r client_id; do
        if [ -n "$client_id" ]; then
            print_info "Deleting API key: $client_id"
            DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/api/v1/external-auth/api-keys/$client_id" \
                -H "Authorization: Bearer $JWT_TOKEN")
            if echo "$DELETE_RESPONSE" | grep -q "error\|detail"; then
                print_error "Failed to delete $client_id: $DELETE_RESPONSE"
            else
                print_success "Deleted API key: $client_id"
            fi
        fi
    done
else
    print_info "No existing API keys to clean up"
fi

# Step 4: Create fresh API key
print_step "4" "Create Fresh API Key"
API_KEY_REQUEST='{
    "client_name": "Fresh Test Client",
    "client_description": "Fresh API key created by test script",
    "allowed_transaction_types": ["income", "expense"],
    "allowed_currencies": ["USD", "EUR", "CAD"],
    "max_transaction_amount": 5000.00,
    "rate_limit_per_minute": 60,
    "rate_limit_per_hour": 1000,
    "rate_limit_per_day": 10000,
    "is_sandbox": true,
    "webhook_url": "https://webhook.site/fresh-test"
}'

API_KEY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/external-auth/api-keys" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "$API_KEY_REQUEST")

if echo "$API_KEY_RESPONSE" | grep -q "api_key"; then
    API_KEY=$(echo "$API_KEY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['api_key'])")
    CLIENT_ID=$(echo "$API_KEY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['client_id'])")
    print_success "Fresh API key created successfully"
    print_info "Client ID: $CLIENT_ID"
    print_info "API Key: ${API_KEY:0:15}..."
    
    # Pretty print the response
    echo "API Key details:"
    echo "$API_KEY_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  Name: {data.get(\"client_name\")}')
print(f'  Client ID: {data.get(\"client_id\")}')
print(f'  Prefix: {data.get(\"api_key_prefix\")}')
print(f'  Transaction Types: {data.get(\"allowed_transaction_types\")}')
print(f'  Rate Limits: {data.get(\"rate_limits\")}')
print(f'  Created: {data.get(\"created_at\")}')
"
else
    print_error "Failed to create fresh API key. Response: $API_KEY_RESPONSE"
    exit 1
fi

# Step 5: Test API key authentication
print_step "5" "Test Fresh API Key Authentication"
AUTH_TEST=$(curl -s -X GET "$BASE_URL/api/v1/external-transactions/transactions" \
    -H "X-API-Key: $API_KEY")

if echo "$AUTH_TEST" | grep -q "transactions" || echo "$AUTH_TEST" | grep -q "\[\]"; then
    print_success "Fresh API key authentication working"
else
    print_error "Fresh API key authentication failed. Response: $AUTH_TEST"
    exit 1
fi

# Step 6: Submit multiple test transactions
print_step "6" "Submit Multiple Test Transactions"

TRANSACTION_IDS=()

# Transaction 1: Expense
print_info "Creating expense transaction..."
TRANSACTION_DATA_1='{
    "transaction_type": "expense",
    "amount": 299.99,
    "currency": "USD",
    "date": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "description": "Fresh test expense transaction",
    "source_system": "Fresh Test Script",
    "category": "Software",
    "subcategory": "Development Tools",
    "business_purpose": "Testing fresh API key functionality",
    "vendor_name": "Software Vendor",
    "payment_method": "Credit Card",
    "sales_tax_amount": 25.00,
    "invoice_reference": "FRESH-EXP-001",
    "receipt_url": "https://example.com/receipt/fresh-001.pdf"
}'

TRANSACTION_RESPONSE_1=$(curl -s -X POST "$BASE_URL/api/v1/external-transactions/transactions" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$TRANSACTION_DATA_1")

if echo "$TRANSACTION_RESPONSE_1" | grep -q "external_transaction_id"; then
    TRANSACTION_ID_1=$(echo "$TRANSACTION_RESPONSE_1" | python3 -c "import sys, json; print(json.load(sys.stdin)['external_transaction_id'])")
    TRANSACTION_IDS+=("$TRANSACTION_ID_1")
    print_success "Expense transaction created: $TRANSACTION_ID_1"
else
    print_error "Expense transaction failed: $TRANSACTION_RESPONSE_1"
fi

# Transaction 2: Income
print_info "Creating income transaction..."
TRANSACTION_DATA_2='{
    "transaction_type": "income",
    "amount": 1250.00,
    "currency": "USD",
    "date": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "description": "Fresh test income transaction",
    "source_system": "Fresh Test Script",
    "category": "Consulting",
    "business_purpose": "Testing fresh API key with income",
    "vendor_name": "Client Company",
    "payment_method": "Bank Transfer",
    "invoice_reference": "FRESH-INC-001"
}'

TRANSACTION_RESPONSE_2=$(curl -s -X POST "$BASE_URL/api/v1/external-transactions/transactions" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$TRANSACTION_DATA_2")

if echo "$TRANSACTION_RESPONSE_2" | grep -q "external_transaction_id"; then
    TRANSACTION_ID_2=$(echo "$TRANSACTION_RESPONSE_2" | python3 -c "import sys, json; print(json.load(sys.stdin)['external_transaction_id'])")
    TRANSACTION_IDS+=("$TRANSACTION_ID_2")
    print_success "Income transaction created: $TRANSACTION_ID_2"
else
    print_error "Income transaction failed: $TRANSACTION_RESPONSE_2"
fi

# Transaction 3: Another expense with different currency
print_info "Creating EUR expense transaction..."
TRANSACTION_DATA_3='{
    "transaction_type": "expense",
    "amount": 89.50,
    "currency": "EUR",
    "date": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "description": "Fresh test EUR expense transaction",
    "source_system": "Fresh Test Script",
    "category": "Office Supplies",
    "business_purpose": "Testing multi-currency support",
    "vendor_name": "European Supplier",
    "payment_method": "Debit Card",
    "vat_amount": 15.50,
    "invoice_reference": "FRESH-EUR-001"
}'

TRANSACTION_RESPONSE_3=$(curl -s -X POST "$BASE_URL/api/v1/external-transactions/transactions" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$TRANSACTION_DATA_3")

if echo "$TRANSACTION_RESPONSE_3" | grep -q "external_transaction_id"; then
    TRANSACTION_ID_3=$(echo "$TRANSACTION_RESPONSE_3" | python3 -c "import sys, json; print(json.load(sys.stdin)['external_transaction_id'])")
    TRANSACTION_IDS+=("$TRANSACTION_ID_3")
    print_success "EUR transaction created: $TRANSACTION_ID_3"
else
    print_error "EUR transaction failed: $TRANSACTION_RESPONSE_3"
fi

print_info "Created ${#TRANSACTION_IDS[@]} transactions total"

# Step 7: List all transactions
print_step "7" "List All Fresh Transactions"
TRANSACTIONS_LIST=$(curl -s -X GET "$BASE_URL/api/v1/external-transactions/transactions" \
    -H "X-API-Key: $API_KEY")

echo "Fresh transactions for this API key:"
echo "$TRANSACTIONS_LIST" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, dict) and 'transactions' in data:
        transactions = data['transactions']
        print(f'Found {len(transactions)} transactions')
        for i, txn in enumerate(transactions):
            print(f'  {i+1}. {txn.get(\"description\", \"N/A\")} - {txn.get(\"amount\", \"0\")} {txn.get(\"currency\", \"\")} ({txn.get(\"status\", \"unknown\")})')
            print(f'      ID: {txn.get(\"external_transaction_id\", \"N/A\")}')
            print(f'      Created: {txn.get(\"created_at\", \"N/A\")}')
    elif isinstance(data, list):
        print(f'Found {len(data)} transactions')
        for i, txn in enumerate(data):
            print(f'  {i+1}. {txn.get(\"description\", \"N/A\")} - {txn.get(\"amount\", \"0\")} {txn.get(\"currency\", \"\")} ({txn.get(\"status\", \"unknown\")})')
    else:
        print(f'Unexpected response format: {type(data)}')
        if isinstance(data, dict):
            print(f'Keys: {list(data.keys())}')
        print(f'Raw response: {data}')
except Exception as e:
    print(f'Error parsing response: {e}')
    print(f'Raw response: {sys.stdin.read()}')
"

# Step 8: Get updated API key stats
print_step "8" "Check Updated API Key Statistics"
KEY_DETAILS=$(curl -s -X GET "$BASE_URL/api/v1/external-auth/api-keys/$CLIENT_ID" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "Updated API Key statistics:"
echo "$KEY_DETAILS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  Name: {data.get(\"client_name\", \"N/A\")}')
    print(f'  Total Requests: {data.get(\"total_requests\", 0)}')
    print(f'  Total Transactions: {data.get(\"total_transactions_submitted\", 0)}')
    print(f'  Last Used: {data.get(\"last_used_at\", \"Never\")}')
    print(f'  Active: {data.get(\"is_active\", False)}')
    print(f'  Sandbox: {data.get(\"is_sandbox\", False)}')
except Exception as e:
    print(f'Error parsing response: {e}')
"

# Step 9: Test individual transaction retrieval
if [ ${#TRANSACTION_IDS[@]} -gt 0 ]; then
    print_step "9" "Test Individual Transaction Retrieval"
    FIRST_TXN_ID="${TRANSACTION_IDS[0]}"
    print_info "Retrieving transaction: $FIRST_TXN_ID"
    
    TXN_DETAILS=$(curl -s -X GET "$BASE_URL/api/v1/external-transactions/transactions/$FIRST_TXN_ID" \
        -H "X-API-Key: $API_KEY")
    
    echo "Transaction details:"
    echo "$TXN_DETAILS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  ID: {data.get(\"external_transaction_id\", \"N/A\")}')
    print(f'  Type: {data.get(\"transaction_type\", \"N/A\")}')
    print(f'  Amount: {data.get(\"amount\", \"0\")} {data.get(\"currency\", \"\")}')
    print(f'  Description: {data.get(\"description\", \"N/A\")}')
    print(f'  Category: {data.get(\"category\", \"N/A\")}')
    print(f'  Vendor: {data.get(\"vendor_name\", \"N/A\")}')
    print(f'  Status: {data.get(\"status\", \"N/A\")}')
    print(f'  Created: {data.get(\"created_at\", \"N/A\")}')
except Exception as e:
    print(f'Error parsing response: {e}')
"
fi

# Summary
echo ""
echo "=================================================="
print_success "Fresh API Key Testing Complete!"
echo ""
echo "Summary:"
echo "  • API Server: $BASE_URL"
echo "  • Test User: $TEST_EMAIL"
echo "  • Fresh Client ID: $CLIENT_ID"
echo "  • Fresh API Key: ${API_KEY:0:15}... (truncated for security)"
echo "  • Transactions Created: ${#TRANSACTION_IDS[@]}"
echo ""

if [ ${#TRANSACTION_IDS[@]} -gt 0 ]; then
    echo "Created Transaction IDs:"
    for i in "${!TRANSACTION_IDS[@]}"; do
        echo "  $((i+1)). ${TRANSACTION_IDS[i]}"
    done
    echo ""
fi

print_info "The fresh API key and transactions are ready!"
echo ""
print_info "Access the web UI at: $UI_URL/settings (API Keys tab)"
echo ""
echo "Fresh API Key for testing:"
echo "$API_KEY"
