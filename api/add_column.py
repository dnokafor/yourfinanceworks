#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/invoice_master")

# Create engine
engine = create_engine(database_url)

try:
    with engine.connect() as conn:
        # Add must_reset_password column to master_users if it doesn't exist
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'master_users' AND column_name = 'must_reset_password'
            )
        """))
        exists = result.scalar()

        if not exists:
            print("Adding must_reset_password column to master_users...")
            conn.execute(text("""
                ALTER TABLE master_users
                ADD COLUMN must_reset_password BOOLEAN DEFAULT FALSE NOT NULL
            """))
            conn.commit()
            print("✓ must_reset_password column added successfully")
        else:
            print("✓ must_reset_password column already exists")

        # Add show_analytics column if it doesn't exist
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'master_users' AND column_name = 'show_analytics'
            )
        """))
        exists = result.scalar()

        if not exists:
            print("Adding show_analytics column to master_users...")
            conn.execute(text("""
                ALTER TABLE master_users
                ADD COLUMN show_analytics BOOLEAN DEFAULT FALSE NOT NULL
            """))
            conn.commit()
            print("✓ show_analytics column added successfully")
        else:
            print("✓ show_analytics column already exists")

except Exception as e:
    print(f"Error: {e}")
