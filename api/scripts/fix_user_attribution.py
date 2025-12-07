#!/usr/bin/env python3
"""
Script to fix user attribution by syncing users to their tenants.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.models.database import get_master_db
from core.models.models import MasterUser, Tenant
from core.utils.user_sync import sync_user_to_tenant_database

def fix_attribution():
    """Sync all users to their primary tenant"""
    
    master_db = next(get_master_db())
    
    try:
        # Get all users
        users = master_db.query(MasterUser).all()
        print(f"\n=== Syncing Users to Tenants ===")
        
        for user in users:
            print(f"\nUser: {user.email} (ID: {user.id})")
            print(f"  Primary tenant_id: {user.tenant_id}")
            
            if user.tenant_id:
                # Sync user to their primary tenant
                print(f"  Syncing to tenant {user.tenant_id}...")
                success = sync_user_to_tenant_database(user, user.tenant_id, user.role)
                
                if success:
                    print(f"  ✓ Successfully synced to tenant {user.tenant_id}")
                else:
                    print(f"  ✗ Failed to sync to tenant {user.tenant_id}")
            else:
                print(f"  ⚠ User has no primary tenant_id set")
                
                # Check if there are any tenants
                tenants = master_db.query(Tenant).all()
                if tenants:
                    print(f"  Available tenants: {[t.id for t in tenants]}")
                    print(f"  You may need to assign this user to a tenant")
                else:
                    print(f"  No tenants found in the system")
        
        print(f"\n=== Sync Complete ===")
        
    finally:
        master_db.close()

if __name__ == "__main__":
    fix_attribution()
