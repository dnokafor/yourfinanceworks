#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/invoice_master")

# Create engine
engine = create_engine(database_url)

try:
    inspector = inspect(engine)

    # Check master_users table
    if 'master_users' in inspector.get_table_names():
        columns = inspector.get_columns('master_users')
        print("master_users table columns:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")

        # Check if must_reset_password exists
        column_names = [col['name'] for col in columns]
        if 'must_reset_password' in column_names:
            print("✓ must_reset_password column exists in master_users")
        else:
            print("✗ must_reset_password column missing in master_users")
    else:
        print("master_users table does not exist")

except Exception as e:
    print(f"Error: {e}")
