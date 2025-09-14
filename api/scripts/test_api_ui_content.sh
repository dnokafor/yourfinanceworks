#!/bin/bash

# API Test Script for UI-Visible Content
# This script creates expenses and invoices that are visible in the UI

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
JWT_TOKEN=""

echo -e "${BLUE}🎯 API Test Script for UI-Visible Content${NC}"
echo "=================================================="
echo "This script creates expenses and invoices visible in the UI"
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

# Step 3: Get available clients
print_step "3" "Get Available Clients"
CLIENTS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/clients" \
    -H "Authorization: Bearer $JWT_TOKEN")

print_info "Clients response: ${CLIENTS_RESPONSE:0:100}..."

CLIENT_ID=""
if [ -n "$CLIENTS_RESPONSE" ] && echo "$CLIENTS_RESPONSE" | grep -q "\["; then
    CLIENT_ID=$(echo "$CLIENTS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list) and len(data) > 0:
        client = data[0]
        print(client['id'])
        print(f'Using client: {client[\"name\"]} (ID: {client[\"id\"]})', file=sys.stderr)
    else:
        print('', file=sys.stderr)
        print('No clients found', file=sys.stderr)
except Exception as e:
    print('', file=sys.stderr)
    print(f'Error: {e}', file=sys.stderr)
")
    
    if [ -n "$CLIENT_ID" ]; then
        print_success "Found client to use for invoices: ID $CLIENT_ID"
    else
        print_error "No clients available for creating invoices"
        print_info "Creating a test client first..."
        
        # Create a test client
        CLIENT_CREATE_DATA='{
            "name": "Test Client for API",
            "email": "testclient@example.com",
            "phone": "+1-555-0123",
            "address": "123 Test Street, Test City, TC 12345",
            "company": "Test Company Inc."
        }'
        
        CLIENT_CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/clients" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -d "$CLIENT_CREATE_DATA")
        
        if echo "$CLIENT_CREATE_RESPONSE" | grep -q "id"; then
            CLIENT_ID=$(echo "$CLIENT_CREATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
            print_success "Created test client: ID $CLIENT_ID"
        else
            print_error "Failed to create test client: $CLIENT_CREATE_RESPONSE"
            exit 1
        fi
    fi
else
    print_error "Failed to get clients: $CLIENTS_RESPONSE"
    exit 1
fi

# Step 4: Create Multiple Expenses
print_step "4" "Create Multiple Expenses"

EXPENSE_IDS=()

# Expense 1: Software subscription
print_info "Creating software expense..."
EXPENSE_DATA_1='{
    "amount": 99.99,
    "currency": "USD",
    "expense_date": "'$(date +%Y-%m-%d)'",
    "category": "Software",
    "vendor": "Adobe Creative Suite",
    "labels": ["software", "design", "monthly"],
    "tax_rate": 8.5,
    "tax_amount": 8.50,
    "total_amount": 108.49,
    "payment_method": "Credit Card",
    "reference_number": "SUB-2024-001",
    "status": "recorded",
    "notes": "Monthly Adobe Creative Suite subscription for design team"
}'

EXPENSE_RESPONSE_1=$(curl -s -X POST "$BASE_URL/api/v1/expenses/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "$EXPENSE_DATA_1")

if echo "$EXPENSE_RESPONSE_1" | grep -q "id"; then
    EXPENSE_ID_1=$(echo "$EXPENSE_RESPONSE_1" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    EXPENSE_IDS+=("$EXPENSE_ID_1")
    print_success "Software expense created: ID $EXPENSE_ID_1"
else
    print_error "Software expense failed: $EXPENSE_RESPONSE_1"
fi

# Expense 2: Travel expense
print_info "Creating travel expense..."
EXPENSE_DATA_2='{
    "amount": 450.00,
    "currency": "USD",
    "expense_date": "'$(date -d '1 day ago' +%Y-%m-%d)'",
    "category": "Travel",
    "vendor": "Delta Airlines",
    "labels": ["travel", "flight", "business"],
    "tax_rate": 0,
    "tax_amount": 0,
    "total_amount": 450.00,
    "payment_method": "Corporate Card",
    "reference_number": "TRV-2024-002",
    "status": "recorded",
    "notes": "Flight to client meeting in San Francisco"
}'

EXPENSE_RESPONSE_2=$(curl -s -X POST "$BASE_URL/api/v1/expenses/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "$EXPENSE_DATA_2")

if echo "$EXPENSE_RESPONSE_2" | grep -q "id"; then
    EXPENSE_ID_2=$(echo "$EXPENSE_RESPONSE_2" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    EXPENSE_IDS+=("$EXPENSE_ID_2")
    print_success "Travel expense created: ID $EXPENSE_ID_2"
else
    print_error "Travel expense failed: $EXPENSE_RESPONSE_2"
fi

# Expense 3: Office supplies
print_info "Creating office supplies expense..."
EXPENSE_DATA_3='{
    "amount": 125.75,
    "currency": "USD",
    "expense_date": "'$(date -d '2 days ago' +%Y-%m-%d)'",
    "category": "Office Supplies",
    "vendor": "Staples",
    "labels": ["office", "supplies", "stationery"],
    "tax_rate": 8.5,
    "tax_amount": 10.69,
    "total_amount": 136.44,
    "payment_method": "Debit Card",
    "reference_number": "OFF-2024-003",
    "status": "recorded",
    "notes": "Monthly office supplies: paper, pens, folders, printer ink"
}'

EXPENSE_RESPONSE_3=$(curl -s -X POST "$BASE_URL/api/v1/expenses/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "$EXPENSE_DATA_3")

if echo "$EXPENSE_RESPONSE_3" | grep -q "id"; then
    EXPENSE_ID_3=$(echo "$EXPENSE_RESPONSE_3" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    EXPENSE_IDS+=("$EXPENSE_ID_3")
    print_success "Office supplies expense created: ID $EXPENSE_ID_3"
else
    print_error "Office supplies expense failed: $EXPENSE_RESPONSE_3"
fi

# Expense 4: Meals & Entertainment
print_info "Creating meals expense..."
EXPENSE_DATA_4='{
    "amount": 85.50,
    "currency": "USD",
    "expense_date": "'$(date -d '3 days ago' +%Y-%m-%d)'",
    "category": "Meals & Entertainment",
    "vendor": "The Business Bistro",
    "labels": ["meals", "client", "entertainment"],
    "tax_rate": 8.5,
    "tax_amount": 7.27,
    "total_amount": 92.77,
    "payment_method": "Credit Card",
    "reference_number": "MEL-2024-004",
    "status": "recorded",
    "notes": "Client dinner meeting - discussing Q1 project requirements"
}'

EXPENSE_RESPONSE_4=$(curl -s -X POST "$BASE_URL/api/v1/expenses/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "$EXPENSE_DATA_4")

if echo "$EXPENSE_RESPONSE_4" | grep -q "id"; then
    EXPENSE_ID_4=$(echo "$EXPENSE_RESPONSE_4" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    EXPENSE_IDS+=("$EXPENSE_ID_4")
    print_success "Meals expense created: ID $EXPENSE_ID_4"
else
    print_error "Meals expense failed: $EXPENSE_RESPONSE_4"
fi

print_info "Created ${#EXPENSE_IDS[@]} expenses total"

# Step 5: Create Multiple Invoices
print_step "5" "Create Multiple Invoices"

INVOICE_IDS=()

# Invoice 1: Consulting services
print_info "Creating consulting invoice..."
INVOICE_DATA_1='{
    "amount": 2500.00,
    "currency": "USD",
    "date": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "due_date": "'$(date -d '+30 days' -u +%Y-%m-%dT%H:%M:%SZ)'",
    "status": "draft",
    "description": "Consulting Services - Q1 2024",
    "notes": "Monthly consulting retainer for software development guidance",
    "client_id": '$CLIENT_ID',
    "discount_type": "percentage",
    "discount_value": 0,
    "subtotal": 2500.00,
    "items": [
        {
            "description": "Software Architecture Consulting",
            "quantity": 20,
            "unit_price": 125.00,
            "total": 2500.00
        }
    ]
}'

INVOICE_RESPONSE_1=$(curl -s -X POST "$BASE_URL/api/v1/invoices/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "$INVOICE_DATA_1")

if echo "$INVOICE_RESPONSE_1" | grep -q "id"; then
    INVOICE_ID_1=$(echo "$INVOICE_RESPONSE_1" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    INVOICE_IDS+=("$INVOICE_ID_1")
    print_success "Consulting invoice created: ID $INVOICE_ID_1"
else
    print_error "Consulting invoice failed: $INVOICE_RESPONSE_1"
fi

# Invoice 2: Web development project
print_info "Creating web development invoice..."
INVOICE_DATA_2='{
    "amount": 4200.00,
    "currency": "USD",
    "date": "'$(date -d '1 day ago' -u +%Y-%m-%dT%H:%M:%SZ)'",
    "due_date": "'$(date -d '+15 days' -u +%Y-%m-%dT%H:%M:%SZ)'",
    "status": "sent",
    "description": "Website Development Project",
    "notes": "Complete website redesign and development including responsive design and CMS integration",
    "client_id": '$CLIENT_ID',
    "discount_type": "fixed",
    "discount_value": 200.00,
    "subtotal": 4400.00,
    "items": [
        {
            "description": "Frontend Development",
            "quantity": 24,
            "unit_price": 100.00,
            "total": 2400.00
        },
        {
            "description": "Backend Development",
            "quantity": 16,
            "unit_price": 100.00,
            "total": 1600.00
        },
        {
            "description": "CMS Integration",
            "quantity": 4,
            "unit_price": 100.00,
            "total": 400.00
        }
    ]
}'

INVOICE_RESPONSE_2=$(curl -s -X POST "$BASE_URL/api/v1/invoices/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "$INVOICE_DATA_2")

if echo "$INVOICE_RESPONSE_2" | grep -q "id"; then
    INVOICE_ID_2=$(echo "$INVOICE_RESPONSE_2" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    INVOICE_IDS+=("$INVOICE_ID_2")
    print_success "Web development invoice created: ID $INVOICE_ID_2"
else
    print_error "Web development invoice failed: $INVOICE_RESPONSE_2"
fi

# Invoice 3: Maintenance contract
print_info "Creating maintenance invoice..."
INVOICE_DATA_3='{
    "amount": 800.00,
    "currency": "USD",
    "date": "'$(date -d '2 days ago' -u +%Y-%m-%dT%H:%M:%SZ)'",
    "due_date": "'$(date -d '+7 days' -u +%Y-%m-%dT%H:%M:%SZ)'",
    "paid_amount": 800.00,
    "status": "paid",
    "description": "Monthly Maintenance Contract",
    "notes": "Website maintenance, security updates, and technical support",
    "client_id": '$CLIENT_ID',
    "discount_type": "percentage",
    "discount_value": 0,
    "subtotal": 800.00,
    "items": [
        {
            "description": "Website Maintenance",
            "quantity": 1,
            "unit_price": 500.00,
            "total": 500.00
        },
        {
            "description": "Security Updates",
            "quantity": 1,
            "unit_price": 200.00,
            "total": 200.00
        },
        {
            "description": "Technical Support",
            "quantity": 1,
            "unit_price": 100.00,
            "total": 100.00
        }
    ]
}'

INVOICE_RESPONSE_3=$(curl -s -X POST "$BASE_URL/api/v1/invoices/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d "$INVOICE_DATA_3")

if echo "$INVOICE_RESPONSE_3" | grep -q "id"; then
    INVOICE_ID_3=$(echo "$INVOICE_RESPONSE_3" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    INVOICE_IDS+=("$INVOICE_ID_3")
    print_success "Maintenance invoice created: ID $INVOICE_ID_3"
else
    print_error "Maintenance invoice failed: $INVOICE_RESPONSE_3"
fi

print_info "Created ${#INVOICE_IDS[@]} invoices total"

# Step 6: List created expenses
print_step "6" "Verify Created Expenses"
EXPENSES_LIST=$(curl -s -X GET "$BASE_URL/api/v1/expenses/" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "Recent expenses:"
echo "$EXPENSES_LIST" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        # Show last 5 expenses
        recent = data[-5:] if len(data) > 5 else data
        print(f'Showing {len(recent)} most recent expenses (of {len(data)} total):')
        for i, exp in enumerate(reversed(recent)):
            print(f'  {i+1}. {exp.get(\"category\", \"N/A\")} - \${exp.get(\"amount\", \"0\")} {exp.get(\"currency\", \"\")} ({exp.get(\"vendor\", \"N/A\")})')
            print(f'      ID: {exp.get(\"id\", \"N/A\")}, Date: {exp.get(\"expense_date\", \"N/A\")}')
    else:
        print(f'Unexpected response format: {type(data)}')
except Exception as e:
    print(f'Error parsing response: {e}')
"

# Step 7: List created invoices
print_step "7" "Verify Created Invoices"
INVOICES_LIST=$(curl -s -X GET "$BASE_URL/api/v1/invoices/" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "Recent invoices:"
echo "$INVOICES_LIST" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        # Show last 5 invoices
        recent = data[-5:] if len(data) > 5 else data
        print(f'Showing {len(recent)} most recent invoices (of {len(data)} total):')
        for i, inv in enumerate(reversed(recent)):
            print(f'  {i+1}. {inv.get(\"description\", \"N/A\")} - \${inv.get(\"amount\", \"0\")} {inv.get(\"currency\", \"\")} ({inv.get(\"status\", \"N/A\")})')
            print(f'      ID: {inv.get(\"id\", \"N/A\")}, Due: {inv.get(\"due_date\", \"N/A\")}')
    else:
        print(f'Unexpected response format: {type(data)}')
except Exception as e:
    print(f'Error parsing response: {e}')
"

# Step 8: Show summary statistics
print_step "8" "Summary Statistics"

# Get expense totals
EXPENSE_TOTAL=$(echo "$EXPENSES_LIST" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        total = sum(float(exp.get('amount', 0)) for exp in data)
        count = len(data)
        print(f'{count} expenses totaling \${total:.2f}')
    else:
        print('0 expenses')
except:
    print('Error calculating expense total')
")

# Get invoice totals
INVOICE_TOTAL=$(echo "$INVOICES_LIST" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        total = sum(float(inv.get('amount', 0)) for inv in data)
        count = len(data)
        paid_count = sum(1 for inv in data if inv.get('status') == 'paid')
        print(f'{count} invoices totaling \${total:.2f} ({paid_count} paid)')
    else:
        print('0 invoices')
except:
    print('Error calculating invoice total')
")

echo "Database summary:"
echo "  • Expenses: $EXPENSE_TOTAL"
echo "  • Invoices: $INVOICE_TOTAL"

# Summary
echo ""
echo "=================================================="
print_success "UI Content Creation Complete!"
echo ""
echo "Summary of created content:"
echo "  • API Server: $BASE_URL"
echo "  • Test User: $TEST_EMAIL"
echo "  • Client ID: $CLIENT_ID"
echo "  • Expenses Created: ${#EXPENSE_IDS[@]}"
echo "  • Invoices Created: ${#INVOICE_IDS[@]}"
echo ""

if [ ${#EXPENSE_IDS[@]} -gt 0 ]; then
    echo "Created Expense IDs:"
    for i in "${!EXPENSE_IDS[@]}"; do
        echo "  $((i+1)). ${EXPENSE_IDS[i]}"
    done
    echo ""
fi

if [ ${#INVOICE_IDS[@]} -gt 0 ]; then
    echo "Created Invoice IDs:"
    for i in "${!INVOICE_IDS[@]}"; do
        echo "  $((i+1)). ${INVOICE_IDS[i]}"
    done
    echo ""
fi

print_info "Content is now visible in the UI!"
echo ""
echo "View your created content:"
echo "  • Expenses: $UI_URL/expenses"
echo "  • Invoices: $UI_URL/invoices"
echo "  • Clients: $UI_URL/clients"
echo ""
print_success "All content created successfully and ready to view in the UI! 🎉"
