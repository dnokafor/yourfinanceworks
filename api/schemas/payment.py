from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class PaymentBase(BaseModel):
    invoice_id: int
    amount: float
    date: date
    method: str

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    invoice_id: Optional[int] = None
    amount: Optional[float] = None
    date: Optional[date] = None
    method: Optional[str] = None

class Payment(PaymentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaymentWithInvoice(Payment):
    invoice_number: str
    client_name: str

    class Config:
        from_attributes = True 