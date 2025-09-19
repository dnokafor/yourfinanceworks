#!/bin/bash

# Test script for Tax Service Integration
# This script demonstrates how to use the integration endpoints

API_BASE="http://localhost:8000/api/v1"
AUTH_TOKEN=""  # You'll need to set this with a valid JWT token

echo "🧪 Testing Tax Service Integration"
echo "==================================="

# Function to make authenticated request
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ "$method" = "GET" ]; then
        curl -s -X GET \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            "$API_BASE$endpoint"
    else
        curl -s -X $method \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_BASE$endpoint"
    fi
}

echo ""
echo "🔑 Step 1: Check integration status"
echo "-----------------------------------"
STATUS_RESPONSE=$(make_request "GET" "/tax-integration/status")
echo "$STATUS_RESPONSE" | jq '.' 2>/dev/null || echo "$STATUS_RESPONSE"

echo ""
echo "🔗 Step 2: Test connection to tax service"
echo "------------------------------------------"
CONNECTION_RESPONSE=$(make_request "POST" "/tax-integration/test-connection")
echo "$CONNECTION_RESPONSE" | jq '.' 2>/dev/null || echo "$CONNECTION_RESPONSE"

echo ""
echo "📊 Step 3: Get integration settings"
echo "-----------------------------------"
SETTINGS_RESPONSE=$(make_request "GET" "/tax-integration/settings")
echo "$SETTINGS_RESPONSE" | jq '.' 2>/dev/null || echo "$SETTINGS_RESPONSE"

echo ""
echo "💰 Step 4: Example - Send expense to tax service"
echo "------------------------------------------------"
# This is an example - replace with actual expense ID
EXPENSE_ID="1"
echo "Sending expense ID: $EXPENSE_ID"

EXPENSE_DATA='{
    "item_id": '$EXPENSE_ID',
    "item_type": "expense"
}'

EXPENSE_RESPONSE=$(make_request "POST" "/tax-integration/send" "$EXPENSE_DATA")
echo "$EXPENSE_RESPONSE" | jq '.' 2>/dev/null || echo "$EXPENSE_RESPONSE"

echo ""
echo "📄 Step 5: Example - Send invoice to tax service"
echo "------------------------------------------------"
# This is an example - replace with actual invoice ID
INVOICE_ID="1"
echo "Sending invoice ID: $INVOICE_ID"

INVOICE_DATA='{
    "item_id": '$INVOICE_ID',
    "item_type": "invoice"
}'

INVOICE_RESPONSE=$(make_request "POST" "/tax-integration/send" "$INVOICE_DATA")
echo "$INVOICE_RESPONSE" | jq '.' 2>/dev/null || echo "$INVOICE_RESPONSE"

echo ""
echo "🔍 Step 6: Preview expense mapping (for debugging)"
echo "---------------------------------------------------"
PREVIEW_EXPENSE_RESPONSE=$(make_request "GET" "/tax-integration/expenses/$EXPENSE_ID/tax-transaction")
echo "$PREVIEW_EXPENSE_RESPONSE" | jq '.' 2>/dev/null || echo "$PREVIEW_EXPENSE_RESPONSE"

echo ""
echo "🔍 Step 7: Preview invoice mapping (for debugging)"
echo "---------------------------------------------------"
PREVIEW_INVOICE_RESPONSE=$(make_request "GET" "/tax-integration/invoices/$INVOICE_ID/tax-transaction")
echo "$PREVIEW_INVOICE_RESPONSE" | jq '.' 2>/dev/null || echo "$PREVIEW_INVOICE_RESPONSE"

echo ""
echo "📋 Usage Tips:"
echo "--------------"
echo "1. Set your AUTH_TOKEN variable with a valid JWT token first"
echo "2. Replace expense/invoice IDs with actual values from your database"
echo "3. Use the preview endpoints to see how data will be mapped before sending"
echo "4. Check the tax service logs to verify transactions were created"
echo ""
echo "🎯 Bulk Operations:"
echo "• Use /tax-integration/send-bulk for multiple items"
echo "• Send array of item IDs in the request body"
echo ""
echo "⚠️  Important: Make sure your tax service is running and accessible"
