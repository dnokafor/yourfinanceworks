#!/usr/bin/env python3
"""
Test script to simulate the API response for invoice attribution
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models.database import SessionLocal
from core.models.models import MasterUser
from core.services.tenant_database_manager import tenant_db_manager
from core.models.models_per_tenant import Invoice, Client
from sqlalchemy import func
from core.routers.payments import Payment

def test_api_response():
    """Simulate the read_invoice endpoint response"""
    
    # Get tenant DB session
    tenant_id = 1
    SessionLocal_tenant = tenant_db_manager.get_tenant_session(tenant_id)
    tenant_db = SessionLocal_tenant()
    
    try:
        # Get first invoice
        invoice_tuple = tenant_db.query(
            Invoice,
            Client.name.label('client_name'),
            Client.company.label('client_company'),
            func.coalesce(func.sum(Payment.amount), 0).label('total_paid')
        ).join(
            Client, Invoice.client_id == Client.id
        ).outerjoin(
            Payment, Invoice.id == Payment.invoice_id
        ).filter(
            Invoice.is_deleted == False
        ).group_by(
            Invoice.id, Client.name, Client.company
        ).first()
        
        if not invoice_tuple:
            print("❌ No invoices found")
            return
        
        invoice, client_name, client_company, total_paid = invoice_tuple
        
        print(f"✅ Found invoice: {invoice.number}")
        print(f"   - Created by user ID: {invoice.created_by_user_id}")
        
        # Get creator information from master database (unencrypted)
        created_by_username = None
        created_by_email = None
        
        if invoice.created_by_user_id:
            try:
                # Use direct master database session (bypass tenant context check)
                master_db = SessionLocal()
                try:
                    master_user = master_db.query(MasterUser).filter(
                        MasterUser.id == invoice.created_by_user_id
                    ).first()
                    
                    if master_user:
                        # Format name from master user (unencrypted)
                        if master_user.first_name and master_user.last_name:
                            created_by_username = f"{master_user.first_name} {master_user.last_name}"
                        elif master_user.first_name:
                            created_by_username = master_user.first_name
                        else:
                            created_by_username = master_user.email
                        created_by_email = master_user.email
                        
                        print(f"\n✅ Creator info from master DB:")
                        print(f"   - Username: {created_by_username}")
                        print(f"   - Email: {created_by_email}")
                    else:
                        print(f"\n❌ Master user {invoice.created_by_user_id} not found")
                finally:
                    master_db.close()
            except Exception as e:
                print(f"\n❌ Failed to load creator: {e}")
        
        # Build response dict (simplified)
        response = {
            "id": invoice.id,
            "number": invoice.number,
            "created_by_user_id": invoice.created_by_user_id,
            "created_by_username": created_by_username,
            "created_by_email": created_by_email
        }
        
        print(f"\n✅ API Response would include:")
        print(f"   created_by_user_id: {response['created_by_user_id']}")
        print(f"   created_by_username: {response['created_by_username']}")
        print(f"   created_by_email: {response['created_by_email']}")
        
        if created_by_username:
            print(f"\n✅ SUCCESS: Frontend should display '{created_by_username}'")
        else:
            print(f"\n❌ FAIL: Frontend will display 'Unknown'")
            
    finally:
        tenant_db.close()

if __name__ == "__main__":
    test_api_response()
