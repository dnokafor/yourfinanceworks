#!/usr/bin/env python3
"""
Example script demonstrating how to use the migration system.
This script shows common migration workflows.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.manage_migrations import (
    create_migration,
    upgrade_database,
    upgrade_all_tenants,
    show_current_revision,
    create_initial_migrations,
    setup_database_schema
)

def example_initial_setup():
    """Example: Initial setup of migration system"""
    print("=== Initial Migration Setup ===")
    
    # Step 1: Create initial migrations
    print("\n1. Creating initial migrations...")
    if create_initial_migrations():
        print("✓ Initial migrations created successfully")
    else:
        print("✗ Failed to create initial migrations")
        return False
    
    # Step 2: Set up database schema
    print("\n2. Setting up database schema...")
    if setup_database_schema():
        print("✓ Database schema setup completed")
    else:
        print("✗ Failed to set up database schema")
        return False
    
    return True

def example_add_new_feature():
    """Example: Adding a new feature that requires database changes"""
    print("\n=== Adding New Feature ===")
    
    # Step 1: Create migration for master database (if needed)
    print("\n1. Creating master database migration...")
    if create_migration("Add feature configuration table", "master"):
        print("✓ Master migration created")
    else:
        print("✗ Failed to create master migration")
        return False
    
    # Step 2: Create migration for tenant databases
    print("\n2. Creating tenant database migration...")
    if create_migration("Add feature data tables", "tenant"):
        print("✓ Tenant migration created")
    else:
        print("✗ Failed to create tenant migration")
        return False
    
    # Step 3: Apply master migration
    print("\n3. Applying master migration...")
    if upgrade_database("master"):
        print("✓ Master database upgraded")
    else:
        print("✗ Failed to upgrade master database")
        return False
    
    # Step 4: Apply tenant migrations to all tenants
    print("\n4. Applying tenant migrations to all tenants...")
    if upgrade_all_tenants():
        print("✓ All tenant databases upgraded")
    else:
        print("✗ Failed to upgrade some tenant databases")
        return False
    
    return True

def example_check_status():
    """Example: Checking migration status"""
    print("\n=== Checking Migration Status ===")
    
    # Check master database status
    print("\n1. Master database status:")
    show_current_revision("master")
    
    # Check specific tenant status (example with tenant ID 1)
    print("\n2. Tenant 1 database status:")
    show_current_revision("tenant", 1)
    
    print("\n✓ Status check completed")

def example_emergency_rollback():
    """Example: Emergency rollback procedure"""
    print("\n=== Emergency Rollback Example ===")
    print("This is a demonstration of rollback commands (not executed)")
    
    print("\nTo rollback master database:")
    print("  python scripts/manage_migrations.py downgrade --type master --revision -1")
    
    print("\nTo rollback specific tenant:")
    print("  python scripts/manage_migrations.py downgrade --type tenant --tenant-id 1 --revision -1")
    
    print("\nTo rollback to specific revision:")
    print("  python scripts/manage_migrations.py downgrade --type master --revision abc123")

def main():
    """Main function demonstrating migration workflows"""
    print("Migration System Usage Examples")
    print("=" * 50)
    
    # Check if this is a demonstration run
    demo_mode = len(sys.argv) > 1 and sys.argv[1] == "--demo"
    
    if demo_mode:
        print("Running in DEMO mode - no actual migrations will be performed")
        example_check_status()
        example_emergency_rollback()
        return
    
    # Interactive menu
    while True:
        print("\nSelect an example to run:")
        print("1. Initial migration setup")
        print("2. Add new feature (create and apply migrations)")
        print("3. Check migration status")
        print("4. Show rollback examples")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            example_initial_setup()
        elif choice == "2":
            example_add_new_feature()
        elif choice == "3":
            example_check_status()
        elif choice == "4":
            example_emergency_rollback()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()