#!/bin/bash

# Environment Switcher Script for Invoice App Mobile
# Usage: ./switch-env.sh [local|development|staging|production]

ENV=$1

if [ -z "$ENV" ]; then
    echo "Usage: $0 [local|development|staging|production]"
    echo "Available environments:"
    echo "  local       - Use localhost:8000 (for local API server)"
    echo "  development - Use Docker IP (for containerized development)"
    echo "  staging     - Use staging API"
    echo "  production  - Use production API"
    exit 1
fi

ENV_FILE=".env.${ENV}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found!"
    exit 1
fi

# Copy the environment file to .env
cp "$ENV_FILE" .env

echo "✅ Switched to $ENV environment"
echo "📄 Active configuration:"
cat .env
echo ""
echo "🔄 Please restart your Expo development server:"
echo "   npm start"
