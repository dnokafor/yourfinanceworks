#!/usr/bin/env python3
"""
Script to check if installation_info table exists and show its structure
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://invoice_user:invoice_password@localhost:5432/invoice_db')

def check_installation_info_table():
    """Check if installation_info table exists and show its structure"""
    
    print("=" * 70)
    print("Checking installation_info table in TENANT databases")
    print("=" * 70)
    print()
    
    # First check master database for tenants
    master_engine = create_engine(DATABASE_URL)
    
    with master_engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM tenants ORDER BY id"))
        tenant_ids = [row[0] for row in result.fetchall()]
    
    if not tenant_ids:
        print("❌ No tenants found in master database")
        print()
        print("You need to create a tenant first.")
        return False
    
    print(f"Found {len(tenant_ids)} tenant(s): {tenant_ids}")
    print()
    
    # Check first tenant database
    tenant_id = tenant_ids[0]
    print(f"Checking tenant {tenant_id} database...")
    print("-" * 70)
    
    # Build tenant database URL
    tenant_db_url = DATABASE_URL.rsplit('/', 1)[0] + f'/tenant_{tenant_id}'
    
    # Create engine for tenant database
    engine = create_engine(tenant_db_url)
    inspector = inspect(engine)
    
    # Check if table exists
    tables = inspector.get_table_names()
    
    if 'installation_info' not in tables:
        print("❌ installation_info table does NOT exist")
        print()
        print("Available tables:")
        for table in sorted(tables):
            print(f"  - {table}")
        print()
        print("You need to run the migration:")
        print("  cd api")
        print("  alembic upgrade head")
        return False
    
    print("✓ installation_info table EXISTS")
    print()
    
    # Get columns
    columns = inspector.get_columns('installation_info')
    
    print("Columns:")
    print("-" * 70)
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        print(f"  {col['name']:30s} {str(col['type']):20s} {nullable}{default}")
    
    print()
    
    # Check for new columns
    column_names = [col['name'] for col in columns]
    required_columns = ['usage_type', 'usage_type_selected_at']
    
    missing_columns = [col for col in required_columns if col not in column_names]
    
    if missing_columns:
        print("❌ Missing required columns:")
        for col in missing_columns:
            print(f"  - {col}")
        print()
        print("You need to run the migration:")
        print("  cd api")
        print("  alembic upgrade head")
        return False
    else:
        print("✓ All required columns exist")
        print()
    
    # Check if there are any records
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM installation_info"))
        count = result.scalar()
        print(f"Records in table: {count}")
        
        if count > 0:
            print()
            print("Sample record:")
            print("-" * 70)
            result = conn.execute(text("SELECT * FROM installation_info LIMIT 1"))
            row = result.fetchone()
            if row:
                for i, col in enumerate(columns):
                    value = row[i]
                    if value is not None and len(str(value)) > 50:
                        value = str(value)[:47] + "..."
                    print(f"  {col['name']:30s} = {value}")
    
    print()
    print("=" * 70)
    print("✓ Table structure is correct!")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    try:
        success = check_installation_info_table()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
