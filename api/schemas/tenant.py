from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class TenantBase(BaseModel):
    name: str
    subdomain: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    logo_url: Optional[str] = None
    default_currency: str = "USD"
    is_active: bool = True
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Organization name must be at least 2 characters long')
        return v.strip()

class TenantCreate(TenantBase):
    pass

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    subdomain: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    logo_url: Optional[str] = None
    default_currency: Optional[str] = None
    is_active: Optional[bool] = None

class Tenant(TenantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 