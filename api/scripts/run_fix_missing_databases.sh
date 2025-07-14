#!/bin/bash
# Script to fix missing tenant databases from Docker container

echo "🐳 Running tenant database fix from Docker container"
echo "=================================================="

# Set up environment
export PYTHONPATH=/app:$PYTHONPATH

# Run the fix script
cd /app
python scripts/fix_missing_tenant_databases.py check

echo ""
echo "✅ Fix process completed"
echo "You can now restart your application" 