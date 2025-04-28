from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from models.database import get_db
from models.models import Invoice, Item, Client
from schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, Invoice as InvoiceSchema,
    InvoiceWithClient, ItemCreate
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
    invoice_dict["items"] = []
    
    for item in items:
        item_dict = item.__dict__.copy()
        # Remove SQLAlchemy state attribute
        if "_sa_instance_state" in item_dict:
            del item_dict["_sa_instance_state"]
        invoice_dict["items"].append(item_dict)
    
    # Remove SQLAlchemy state attribute from invoice dictionary
    if "_sa_instance_state" in invoice_dict:
        del invoice_dict["_sa_instance_state"]
    
    return invoice_dict

@router.post("/invoices/", response_model=InvoiceSchema, status_code=status.HTTP_201_CREATED)
def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    # Check if client exists
    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Calculate total amount
    total_amount = sum(item.quantity * item.price for item in invoice.items)
    
    # Create invoice
    db_invoice = Invoice(
        number=invoice.number,
        client_id=invoice.client_id,
        date=invoice.date,
        due_date=invoice.due_date,
        amount=total_amount,
        status="pending",
        notes=invoice.notes
    )
    
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    # Create invoice items
    for item_data in invoice.items:
        db_item = Item(
            description=item_data.description,
            quantity=item_data.quantity,
            price=item_data.price,
            invoice_id=db_invoice.id
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_invoice)
    
    # Update client balance
    client.balance += total_amount
    db.commit()
    
    return db_invoice

@router.put("/invoices/{invoice_id}", response_model=InvoiceSchema)
def update_invoice(invoice_id: int, invoice: InvoiceUpdate, db: Session = Depends(get_db)):
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update invoice fields
    update_data = invoice.model_dump(exclude_unset=True)
    
    # Log what fields are being updated
    print(f"Updating invoice {invoice_id} with fields: {update_data}")
    
    # Only update attributes that exist on the model
    allowed_fields = ["number", "client_id", "date", "due_date", "notes", "status"]
    for key, value in update_data.items():
        if key in allowed_fields:
            setattr(db_invoice, key, value)
    
    try:
        db.commit()
        db.refresh(db_invoice)
        return db_invoice
    except Exception as e:
        db.rollback()
        print(f"Error updating invoice: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update invoice: {str(e)}"
        )

@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete related items first
    db.query(Item).filter(Item.invoice_id == invoice_id).delete()
    
    # Update client balance
    client = db.query(Client).filter(Client.id == db_invoice.client_id).first()
    if client:
        client.balance -= db_invoice.amount
        db.commit()
    
    # Delete invoice
    db.delete(db_invoice)
    db.commit()
    return None

@router.put("/invoices/{invoice_id}/items", response_model=InvoiceSchema)
def update_invoice_items(invoice_id: int, items: List[ItemCreate], db: Session = Depends(get_db)):
    """Update or replace items for an invoice"""
    # Check if invoice exists
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    try:
        # Delete existing items
        db.query(Item).filter(Item.invoice_id == invoice_id).delete()
        
        # Calculate new total
        total_amount = sum(item.quantity * item.price for item in items)
        
        # Update invoice amount
        db_invoice.amount = total_amount
        
        # Create new items
        for item_data in items:
            db_item = Item(
                description=item_data.description,
                quantity=item_data.quantity,
                price=item_data.price,
                invoice_id=invoice_id
            )
            db.add(db_item)
        
        db.commit()
        db.refresh(db_invoice)
        
        # Return updated invoice
        return db_invoice
    except Exception as e:
        db.rollback()
        print(f"Error updating invoice items: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update invoice items: {str(e)}"
        ) 