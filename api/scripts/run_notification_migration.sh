#!/bin/bash

# Script to run notification settings migration in Docker container

echo "Running notification settings migration..."

# Check if we're in Docker environment
if [ -f /.dockerenv ]; then
    echo "Running inside Docker container"
    cd /app
    python scripts/add_notification_settings_table.py
else
    echo "Running migration via Docker exec"
    docker-compose exec api python scripts/add_notification_settings_table.py
fi

echo "Migration completed"