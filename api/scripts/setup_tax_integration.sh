#!/bin/bash

# Setup script for Tax Service Integration
# This script helps configure environment variables for the integration

echo "🧾 Tax Service Integration Setup"
echo "================================"

# Check if .env file exists
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Creating .env file..."
    touch "$ENV_FILE"
fi

echo ""
echo "🔧 Configure the following environment variables:"
echo ""

# Function to prompt for input
prompt_env_var() {
    local var_name=$1
    local description=$2
    local current_value=$3

    if [ -n "$current_value" ]; then
        echo "$description"
        echo "Current value: $current_value"
        read -p "New value (press Enter to keep current): " value
        if [ -z "$value" ]; then
            value=$current_value
        fi
    else
        read -p "$description: " value
    fi

    if [ -n "$value" ]; then
        # Remove existing line if it exists
        sed -i "/^$var_name=/d" "$ENV_FILE"
        # Add new line
        echo "$var_name=$value" >> "$ENV_FILE"
        echo "✅ Set $var_name"
    fi
}

# Tax Service Configuration
echo "📊 Tax Service Settings:"
prompt_env_var "TAX_SERVICE_ENABLED" "Enable tax service integration? (true/false)" "$(grep '^TAX_SERVICE_ENABLED=' $ENV_FILE | cut -d'=' -f2)"
prompt_env_var "TAX_SERVICE_BASE_URL" "Tax service base URL (e.g., http://localhost:8000)" "$(grep '^TAX_SERVICE_BASE_URL=' $ENV_FILE | cut -d'=' -f2)"
prompt_env_var "TAX_SERVICE_API_KEY" "Tax service API key" "$(grep '^TAX_SERVICE_API_KEY=' $ENV_FILE | cut -d'=' -f2)"
prompt_env_var "TAX_SERVICE_TIMEOUT" "Request timeout in seconds (default: 30)" "$(grep '^TAX_SERVICE_TIMEOUT=' $ENV_FILE | cut -d'=' -f2)"
prompt_env_var "TAX_SERVICE_RETRY_ATTEMPTS" "Number of retry attempts (default: 3)" "$(grep '^TAX_SERVICE_RETRY_ATTEMPTS=' $ENV_FILE | cut -d'=' -f2)"

echo ""
echo "🎉 Configuration complete!"
echo ""
echo "📋 Next steps:"
echo "1. Restart your invoice app server"
echo "2. Test the connection: curl http://localhost:8000/api/v1/tax-integration/test-connection"
echo "3. Check integration status: curl http://localhost:8000/api/v1/tax-integration/status"
echo ""
echo "📖 API Endpoints:"
echo "• GET  /api/v1/tax-integration/status - Check integration status"
echo "• POST /api/v1/tax-integration/test-connection - Test connection"
echo "• POST /api/v1/tax-integration/send - Send expense/invoice to tax service"
echo "• POST /api/v1/tax-integration/send-bulk - Send multiple items"
echo ""
echo "🔍 For debugging:"
echo "• GET /api/v1/tax-integration/expenses/{id}/tax-transaction - Preview expense mapping"
echo "• GET /api/v1/tax-integration/invoices/{id}/tax-transaction - Preview invoice mapping"
