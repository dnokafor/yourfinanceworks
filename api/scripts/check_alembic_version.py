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
        # Check if alembic_version table exists
        result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version')"))
        exists = result.scalar()

        if exists:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"Current Alembic version: {version}")
        else:
            print("alembic_version table does not exist")

        # Also check the structure of the alembic_version table
        result = conn.execute(text("SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = 'alembic_version'"))
        columns = result.fetchall()
        for col in columns:
            print(f"Column: {col[0]}, Type: {col[1]}, Max Length: {col[2]}")

except Exception as e:
    print(f"Error: {e}")
