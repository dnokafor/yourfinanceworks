from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import json

from models.database import get_db
from models.models import Settings
from schemas.settings import Settings as SettingsSchema, SettingsUpdate

router = APIRouter()

DEFAULT_COMPANY_INFO = {
    "name": "Your Company",
    "email": "contact@yourcompany.com",
    "phone": "(555) 123-4567",
    "address": "123 Business Avenue, Suite 100, New York, NY 10001",
    "tax_id": "12-3456789",
    "logo": ""
}

DEFAULT_INVOICE_SETTINGS = {
    "prefix": "INV-",
    "next_number": "0001",
    "terms": "Payment due within 30 days from the date of invoice.\nLate payments are subject to a 1.5% monthly finance charge.",
    "notes": "Thank you for your business!",
    "send_copy": True,
    "auto_reminders": True
}

DEFAULT_SETTINGS = {
    "company_info": DEFAULT_COMPANY_INFO,
    "invoice_settings": DEFAULT_INVOICE_SETTINGS
}

@router.get("/settings/", response_model=SettingsSchema)
def get_settings(db: Session = Depends(get_db)):
    # Try to get company info and invoice settings from database
    company_info = db.query(Settings).filter(Settings.key == "company_info").first()
    invoice_settings = db.query(Settings).filter(Settings.key == "invoice_settings").first()

    # Use defaults if not found
    company_info_data = company_info.value if company_info else DEFAULT_COMPANY_INFO
    invoice_settings_data = invoice_settings.value if invoice_settings else DEFAULT_INVOICE_SETTINGS

    return {
        "company_info": company_info_data,
        "invoice_settings": invoice_settings_data
    }

@router.put("/settings/", response_model=SettingsSchema)
def update_settings(settings_update: SettingsUpdate, db: Session = Depends(get_db)):
    # Get current settings first
    current_settings = get_settings(db=db)
    
    # Update company info if provided
    if settings_update.company_info:
        company_info = db.query(Settings).filter(Settings.key == "company_info").first()
        
        if company_info:
            # Update existing
            company_info.value = settings_update.company_info.model_dump()
        else:
            # Create new
            company_info = Settings(
                key="company_info",
                value=settings_update.company_info.model_dump()
            )
            db.add(company_info)
    
    # Update invoice settings if provided
    if settings_update.invoice_settings:
        invoice_settings = db.query(Settings).filter(Settings.key == "invoice_settings").first()
        
        if invoice_settings:
            # Update existing
            invoice_settings.value = settings_update.invoice_settings.model_dump()
        else:
            # Create new
            invoice_settings = Settings(
                key="invoice_settings",
                value=settings_update.invoice_settings.model_dump()
            )
            db.add(invoice_settings)
    
    try:
        db.commit()
        # Return updated settings
        return get_settings(db=db)
    except Exception as e:
        db.rollback()
        print(f"Error updating settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        ) 