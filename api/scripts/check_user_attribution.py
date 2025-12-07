#!/usr/bin/env python3
"""
Script to check if user attribution is working correctly for invoices.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import select
from core.models.database import get_master_db
from core.models.models import MasterUser, user_tenant_association
from core.models.models_per_tenant import Invoice, User as TenantUser
from core.services.tenant_database_manager import tenant_db_manager

def check_attribution():
    """Check user attribution for invoices"""
    
    # Get master database session
    master_db = next(get_master_db())
    
    try:
        # Get all users
        users = master_db.query(MasterUser).all()
        print(f"\n=== Master Users ===")
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Primary Tenant: {user.tenant_id}")
            
            # Check primary tenant
            tenants_to_check = []
            if user.tenant_id:
                tenants_to_check.append(user.tenant_id)
            
            # Also check association table for additional tenants
            stmt = select(user_tenant_association).where(
                user_tenant_association.c.user_id == user.id
            )
            memberships = master_db.execute(stmt).fetchall()
            for membership in memberships:
                if membership.tenant_id not in tenants_to_check:
                    tenants_to_check.append(membership.tenant_id)
            
            for tenant_id in tenants_to_check:
                print(f"\n  Tenant ID: {tenant_id}")
                
                # Check if user exists in tenant database
                try:
                    tenant_session = tenant_db_manager.get_tenant_session(tenant_id)
                    tenant_db = tenant_session()
                    
                    tenant_user = tenant_db.query(TenantUser).filter(
                        TenantUser.id == user.id
                    ).first()
                    
                    if tenant_user:
                        print(f"    ✓ User exists in tenant database (ID: {tenant_user.id})")
                        
                        # Check invoices created by this user
                        invoices = tenant_db.query(Invoice).filter(
                            Invoice.created_by_user_id == user.id
                        ).all()
                        
                        print(f"    Invoices created by this user: {len(invoices)}")
                        for inv in invoices[:5]:  # Show first 5
                            print(f"      - Invoice #{inv.number}, created_by_user_id: {inv.created_by_user_id}")
                        
                        # Check invoices without attribution
                        unattributed = tenant_db.query(Invoice).filter(
                            Invoice.created_by_user_id == None
                        ).count()
                        print(f"    Invoices without attribution: {unattributed}")
                        
                    else:
                        print(f"    ✗ User NOT found in tenant database!")
                        print(f"      This will cause attribution to fail.")
                        print(f"      Run: from core.utils.user_sync import sync_user_to_tenant_database")
                        print(f"           sync_user_to_tenant_database(master_user, {tenant_id})")
                    
                    tenant_db.close()
                    
                except Exception as e:
                    print(f"    Error checking tenant database: {e}")
                    
    finally:
        master_db.close()

if __name__ == "__main__":
    check_attribution()
