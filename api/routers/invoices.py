from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from api.models.database import get_db
from api.models.models import Invoice, Item, Client, User
from api.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, Invoice as InvoiceSchema,
    InvoiceWithClient, ItemCreate
)
from api.routers.auth import get_current_user

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.get("/", response_model=List[InvoiceSchema])
def read_invoices(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoices = db.query(Invoice).filter(
        Invoice.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()
    return invoices

@router.get("/{invoice_id}", response_model=InvoiceSchema)
def read_invoice(
    invoice_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == current_user.tenant_id
    ).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/", response_model=InvoiceSchema, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice: InvoiceCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify client belongs to the same tenant
    if invoice.client_id:
        client = db.query(Client).filter(
            Client.id == invoice.client_id,
            Client.tenant_id == current_user.tenant_id
        ).first()
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
        notes=invoice.notes,
        tenant_id=current_user.tenant_id
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

@router.put("/{invoice_id}", response_model=InvoiceSchema)
def update_invoice(
    invoice_id: int, 
    invoice: InvoiceUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == current_user.tenant_id
    ).first()
    if db_invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # If updating client_id, verify client belongs to the same tenant
    if invoice.client_id and invoice.client_id != db_invoice.client_id:
        client = db.query(Client).filter(
            Client.id == invoice.client_id,
            Client.tenant_id == current_user.tenant_id
        ).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    
    # Update invoice fields
    update_data = invoice.dict(exclude_unset=True)
    
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

@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == current_user.tenant_id
    ).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete related items first
    db.query(Item).filter(Item.invoice_id == invoice_id).delete()
    
    # Update client balance
    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    if client:
        client.balance -= invoice.amount
        db.commit()
    
    # Delete invoice
    db.delete(invoice)
    db.commit()
    return None

@router.put("/{invoice_id}/items", response_model=InvoiceSchema)
def update_invoice_items(
    invoice_id: int, 
    items: List[ItemCreate], 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update or replace items for an invoice"""
    # Check if invoice exists and belongs to current user's tenant
    db_invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == current_user.tenant_id
    ).first()
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