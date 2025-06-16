from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from models.database import get_db
from models.models import Tenant, User
from routers.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tenant settings (using tenant info as settings)"""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Return tenant info formatted as settings
    return {
        "company_info": {
            "name": tenant.name,
            "email": tenant.email or "",
            "phone": tenant.phone or "",
            "address": tenant.address or "",
            "tax_id": tenant.tax_id or "",
            "logo": tenant.logo_url or ""
        },
        "invoice_settings": {
            "prefix": "INV-",
            "next_number": "0001",
            "terms": "Payment due within 30 days from the date of invoice.\nLate payments are subject to a 1.5% monthly finance charge.",
            "notes": "Thank you for your business!",
            "send_copy": True,
            "auto_reminders": True
        }
    }

@router.put("/")
def update_settings(
    settings: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update tenant settings"""
    # Only tenant admins can update settings
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Only tenant admins can update settings"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update tenant info from company_info
    if "company_info" in settings:
        company_info = settings["company_info"]
        if "name" in company_info:
            tenant.name = company_info["name"]
        if "email" in company_info:
            tenant.email = company_info["email"]
        if "phone" in company_info:
            tenant.phone = company_info["phone"]
        if "address" in company_info:
            tenant.address = company_info["address"]
        if "tax_id" in company_info:
            tenant.tax_id = company_info["tax_id"]
        if "logo" in company_info:
            tenant.logo_url = company_info["logo"]
    
    # Note: invoice_settings are currently stored as defaults
    # In a full implementation, you might want to store these in a separate settings table
    
    db.commit()
    db.refresh(tenant)
    
    # Return updated settings
    return {
        "company_info": {
            "name": tenant.name,
            "email": tenant.email or "",
            "phone": tenant.phone or "",
            "address": tenant.address or "",
            "tax_id": tenant.tax_id or "",
            "logo": tenant.logo_url or ""
        },
        "invoice_settings": {
            "prefix": "INV-",
            "next_number": "0001",
            "terms": "Payment due within 30 days from the date of invoice.\nLate payments are subject to a 1.5% monthly finance charge.",
            "notes": "Thank you for your business!",
            "send_copy": True,
            "auto_reminders": True
        }
    } 