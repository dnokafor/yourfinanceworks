from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InvoiceBase(BaseModel):
    amount: float = Field(..., description="Total amount of the invoice")
    due_date: datetime = Field(..., description="Due date of the invoice")
    status: str = Field(..., description="Status of the invoice (draft, sent, paid, etc.)")
    notes: Optional[str] = Field(None, description="Additional notes for the invoice")
    client_id: int = Field(..., description="ID of the client this invoice belongs to")

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    amount: Optional[float] = Field(None, description="Total amount of the invoice")
    due_date: Optional[datetime] = Field(None, description="Due date of the invoice")
    status: Optional[str] = Field(None, description="Status of the invoice (draft, sent, paid, etc.)")
    notes: Optional[str] = Field(None, description="Additional notes for the invoice")
    client_id: Optional[int] = Field(None, description="ID of the client this invoice belongs to")

class Invoice(InvoiceBase):
    id: int
    number: str
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class InvoiceWithClient(Invoice):
    client_name: str
    total_paid: float = 0.0 