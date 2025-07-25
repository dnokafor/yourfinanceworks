#!/bin/bash

# Quick setup script for Slack integration

echo "🤖 Setting up Slack Integration for Invoice App"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "api/main.py" ]; then
    echo "❌ Please run this script from the invoice-app root directory"
    exit 1
fi

# Check if Docker is available
if command -v docker-compose &> /dev/null; then
    echo "🐳 Using Docker environment..."
    
    # Run the setup script in container
    echo "📝 Generating Slack configuration files..."
    docker-compose exec api python scripts/setup_slack_integration.py
    
    echo ""
    echo "🧪 Running integration tests..."
    docker-compose exec api python scripts/test_slack_integration.py
else
    echo "💻 Using local environment..."
    
    # Run the setup script locally
    echo "📝 Generating Slack configuration files..."
    cd api
    python scripts/setup_slack_integration.py
    
    echo ""
    echo "🧪 Running integration tests..."
    python scripts/test_slack_integration.py
fi

echo ""
echo "✅ Slack integration setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit api/.env.slack with your Slack app credentials"
echo "2. Create a Slack app using api/slack_app_manifest.json"
echo "3. Create a bot user account in your invoice app"
echo "4. Add Slack environment variables to your main .env file"
echo "5. Deploy and test with /invoice help"
echo ""
echo "📖 Full documentation: api/docs/SLACK_INTEGRATION.md"