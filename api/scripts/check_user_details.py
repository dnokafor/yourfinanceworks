#!/usr/bin/env python3
"""
Script to check user details in both master and tenant databases.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.models.database import get_master_db
from core.models.models import MasterUser
from core.models.models_per_tenant import User as TenantUser
from core.services.tenant_database_manager import tenant_db_manager

def check_user_details():
    """Check user details"""
    
    master_db = next(get_master_db())
    
    try:
        # Get all users
        users = master_db.query(MasterUser).all()
        print(f"\n=== User Details ===")
        
        for user in users:
            print(f"\nMaster User ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  First Name: {repr(user.first_name)}")
            print(f"  Last Name: {repr(user.last_name)}")
            print(f"  Primary Tenant: {user.tenant_id}")
            
            if user.tenant_id:
                try:
                    tenant_session = tenant_db_manager.get_tenant_session(user.tenant_id)
                    tenant_db = tenant_session()
                    
                    tenant_user = tenant_db.query(TenantUser).filter(
                        TenantUser.id == user.id
                    ).first()
                    
                    if tenant_user:
                        print(f"\n  Tenant User ID: {tenant_user.id}")
                        print(f"    Email: {tenant_user.email}")
                        print(f"    First Name: {repr(tenant_user.first_name)}")
                        print(f"    Last Name: {repr(tenant_user.last_name)}")
                    else:
                        print(f"  ✗ User not found in tenant database")
                    
                    tenant_db.close()
                    
                except Exception as e:
                    print(f"  Error: {e}")
        
    finally:
        master_db.close()

if __name__ == "__main__":
    check_user_details()
