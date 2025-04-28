from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class ClientBase(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    balance: float = 0.0

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    balance: Optional[float] = None

class Client(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 