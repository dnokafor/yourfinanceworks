from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from models.database import get_db
from models.models import Invoice, Item, Client
from schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, Invoice as InvoiceSchema,
    InvoiceWithClient
)

router = APIRouter()

@router.get("/invoices/", response_model=List[InvoiceWithClient])
def read_invoices(
    skip: int = 0, 
    limit: int = 100, 
    status: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Invoice,
        Client.name.label("client_name")
    ).join(Client)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    invoices = query.offset(skip).limit(limit).all()
    
    # Convert SQLAlchemy objects to Pydantic model
    result = []
    for invoice_tuple in invoices:
        invoice_dict = invoice_tuple[0].__dict__
        invoice_dict["client_name"] = invoice_tuple[1]
        result.append(invoice_dict)
    
    return result

@router.get("/invoices/{invoice_id}", response_model=InvoiceWithClient)
def read_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(
        Invoice,
        Client.name.label("client_name")
    ).join(Client).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice_dict = invoice[0].__dict__
    invoice_dict["client_name"] = invoice[1]
    
    # Add items to the invoice response
    items = db.query(Item).filter(Item.invoice_id == invoice_id).all()
    invoice_dict["items"] = [item.__dict__ for item in items]
    
    return invoice_dict 