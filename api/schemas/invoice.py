from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class ItemBase(BaseModel):
    description: str
    quantity: int
    price: float

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    invoice_id: int

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    number: str
    client_id: int
    date: date
    due_date: date
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    items: List[ItemCreate]

class InvoiceUpdate(BaseModel):
    number: Optional[str] = None
    client_id: Optional[int] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class Invoice(InvoiceBase):
    id: int
    amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[Item] = []

    class Config:
        from_attributes = True

class InvoiceWithClient(Invoice):
    client_name: str

    class Config:
        from_attributes = True 