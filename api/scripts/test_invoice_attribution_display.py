#!/usr/bin/env python3
"""
Test script to verify invoice attribution display
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models.database import SessionLocal
from core.models.models import MasterUser
from core.services.tenant_database_manager import tenant_db_manager
from core.models.models_per_tenant import Invoice

def test_invoice_attribution():
    """Test that invoice attribution is working correctly"""
    
    # Get master DB session
    master_db = SessionLocal()
    
    try:
        # Get first user from master DB
        master_user = master_db.query(MasterUser).first()
        if not master_user:
            print("❌ No users found in master database")
            return
        
        print(f"✅ Found master user: {master_user.email}")
        print(f"   - ID: {master_user.id}")
        print(f"   - First name: {master_user.first_name}")
        print(f"   - Last name: {master_user.last_name}")
        print(f"   - Tenant ID: {master_user.tenant_id}")
        
        # Get tenant DB session
        tenant_id = master_user.tenant_id
        SessionLocal_tenant = tenant_db_manager.get_tenant_session(tenant_id)
        tenant_db = SessionLocal_tenant()
        
        try:
            # Get first invoice with created_by_user_id
            invoice = tenant_db.query(Invoice).filter(
                Invoice.created_by_user_id.isnot(None),
                Invoice.is_deleted == False
            ).first()
            
            if not invoice:
                print("\n❌ No invoices found with created_by_user_id")
                return
            
            print(f"\n✅ Found invoice: {invoice.number}")
            print(f"   - ID: {invoice.id}")
            print(f"   - Created by user ID: {invoice.created_by_user_id}")
            
            # Now test fetching the user from master DB
            creator = master_db.query(MasterUser).filter(
                MasterUser.id == invoice.created_by_user_id
            ).first()
            
            if creator:
                print(f"\n✅ Successfully fetched creator from master DB:")
                print(f"   - Email: {creator.email}")
                print(f"   - First name: {creator.first_name}")
                print(f"   - Last name: {creator.last_name}")
                
                # Format name
                if creator.first_name and creator.last_name:
                    display_name = f"{creator.first_name} {creator.last_name}"
                elif creator.first_name:
                    display_name = creator.first_name
                else:
                    display_name = creator.email
                
                print(f"   - Display name: {display_name}")
                print(f"\n✅ Attribution display should show: '{display_name}'")
            else:
                print(f"\n❌ Creator with ID {invoice.created_by_user_id} not found in master DB")
                
        finally:
            tenant_db.close()
            
    finally:
        master_db.close()

if __name__ == "__main__":
    test_invoice_attribution()
