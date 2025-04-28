from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models.models import Payment, Invoice, Client
from schemas.payment import (
    PaymentCreate, PaymentUpdate, Payment as PaymentSchema,
    PaymentWithInvoice
)

router = APIRouter()

@router.get("/payments/", response_model=List[PaymentWithInvoice])
def read_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    payments = db.query(
        Payment,
        Invoice.number.label("invoice_number"),
        Client.name.label("client_name")
    ).select_from(Payment).join(
        Invoice, Payment.invoice_id == Invoice.id
    ).join(
        Client, Invoice.client_id == Client.id
    ).offset(skip).limit(limit).all()
    
    # Convert SQLAlchemy objects to Pydantic model
    result = []
    for payment_tuple in payments:
        payment = payment_tuple[0]
        payment_dict = {
            "id": payment.id,
            "invoice_id": payment.invoice_id,
            "amount": payment.amount,
            "date": payment.date,
            "method": payment.method,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
            "invoice_number": payment_tuple[1],
            "client_name": payment_tuple[2]
        }
        result.append(payment_dict)
    
    return result

@router.get("/payments/{payment_id}", response_model=PaymentWithInvoice)
def read_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(
        Payment,
        Invoice.number.label("invoice_number"),
        Client.name.label("client_name")
    ).select_from(Payment).join(
        Invoice, Payment.invoice_id == Invoice.id
    ).join(
        Client, Invoice.client_id == Client.id
    ).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment_obj = payment[0]
    payment_dict = {
        "id": payment_obj.id,
        "invoice_id": payment_obj.invoice_id,
        "amount": payment_obj.amount,
        "date": payment_obj.date,
        "method": payment_obj.method,
        "created_at": payment_obj.created_at,
        "updated_at": payment_obj.updated_at,
        "invoice_number": payment[1],
        "client_name": payment[2]
    }
    
    return payment_dict

@router.post("/payments/", response_model=PaymentSchema, status_code=status.HTTP_201_CREATED)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    # Check if invoice exists
    invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Create payment
    db_payment = Payment(
        invoice_id=payment.invoice_id,
        amount=payment.amount,
        date=payment.date,
        method=payment.method
    )
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # Update invoice status if paid in full
    total_paid = db.query(Payment).filter(Payment.invoice_id == payment.invoice_id).all()
    total_amount_paid = sum(p.amount for p in total_paid)
    
    if total_amount_paid >= invoice.amount:
        invoice.status = "paid"
        
        # Update client balance
        client = db.query(Client).filter(Client.id == invoice.client_id).first()
        if client:
            client.balance -= payment.amount
            
    elif invoice.status == "overdue":
        invoice.status = "pending"
    
    db.commit()
    
    return db_payment

@router.put("/payments/{payment_id}", response_model=PaymentSchema)
def update_payment(payment_id: int, payment: PaymentUpdate, db: Session = Depends(get_db)):
    db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Update payment fields
    update_data = payment.model_dump(exclude_unset=True)
    
    # Store old amount for balance adjustment
    old_amount = db_payment.amount
    
    for key, value in update_data.items():
        setattr(db_payment, key, value)
    
    db.commit()
    db.refresh(db_payment)
    
    # If amount changed, update invoice status and client balance
    if "amount" in update_data and old_amount != db_payment.amount:
        invoice = db.query(Invoice).filter(Invoice.id == db_payment.invoice_id).first()
        if invoice:
            total_paid = db.query(Payment).filter(Payment.invoice_id == db_payment.invoice_id).all()
            total_amount_paid = sum(p.amount for p in total_paid)
            
            # Update invoice status
            if total_amount_paid >= invoice.amount:
                invoice.status = "paid"
            else:
                invoice.status = "pending"
            
            # Update client balance
            client = db.query(Client).filter(Client.id == invoice.client_id).first()
            if client:
                amount_diff = db_payment.amount - old_amount
                client.balance -= amount_diff
            
            db.commit()
    
    return db_payment

@router.delete("/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Get invoice and update status
    invoice = db.query(Invoice).filter(Invoice.id == db_payment.invoice_id).first()
    if invoice:
        # Update client balance
        client = db.query(Client).filter(Client.id == invoice.client_id).first()
        if client:
            client.balance += db_payment.amount
            db.commit()
        
        # Delete payment
        db.delete(db_payment)
        db.commit()
        
        # Update invoice status after payment deletion
        remaining_payments = db.query(Payment).filter(Payment.invoice_id == invoice.id).all()
        if not remaining_payments:
            invoice.status = "pending"
        else:
            total_amount_paid = sum(p.amount for p in remaining_payments)
            if total_amount_paid < invoice.amount:
                invoice.status = "pending"
        
        db.commit()
    else:
        # Just delete the payment if no invoice found
        db.delete(db_payment)
        db.commit()
    
    return None 