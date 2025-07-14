#!/usr/bin/env python3
"""
Check and fix user role
"""
import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_master_db
from models.models import MasterUser

def check_and_fix_user_role():
    """Check and fix user role"""
    db = next(get_master_db())
    
    try:
        # Find the user
        user = db.query(MasterUser).filter(MasterUser.email == "admin@example.com").first()
        
        if user:
            print(f"Current user role: {user.role}")
            print(f"Email: {user.email}")
            print(f"Tenant ID: {user.tenant_id}")
            
            # Update the role to admin if it's not already
            if user.role != "admin":
                user.role = "admin"
                db.commit()
                print(f"✅ Updated user role to: {user.role}")
            else:
                print("✅ User already has admin role")
        else:
            print("❌ User not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_user_role() 