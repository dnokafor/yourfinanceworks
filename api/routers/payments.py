from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.models.database import get_db
from api.models.models import Payment, Invoice, Client, User
from api.schemas.payment import (
    PaymentCreate, PaymentUpdate, Payment as PaymentSchema,
    PaymentWithInvoice
)
from api.routers.auth import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("/", response_model=List[PaymentSchema])
def read_payments(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payments = db.query(Payment).filter(
        Payment.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()
    return payments

@router.get("/{payment_id}", response_model=PaymentSchema)
def read_payment(
    payment_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.tenant_id == current_user.tenant_id
    ).first()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.post("/", response_model=PaymentSchema)
def create_payment(
    payment: PaymentCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify invoice belongs to the same tenant
    if payment.invoice_id:
        invoice = db.query(Invoice).filter(
            Invoice.id == payment.invoice_id,
            Invoice.tenant_id == current_user.tenant_id
        ).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
    
    db_payment = Payment(**payment.dict(), tenant_id=current_user.tenant_id)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.put("/{payment_id}", response_model=PaymentSchema)
def update_payment(
    payment_id: int, 
    payment: PaymentUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.tenant_id == current_user.tenant_id
    ).first()
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # If updating invoice_id, verify invoice belongs to the same tenant
    if payment.invoice_id and payment.invoice_id != db_payment.invoice_id:
        invoice = db.query(Invoice).filter(
            Invoice.id == payment.invoice_id,
            Invoice.tenant_id == current_user.tenant_id
        ).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
    
    payment_data = payment.dict(exclude_unset=True)
    for key, value in payment_data.items():
        setattr(db_payment, key, value)
    
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.delete("/{payment_id}")
def delete_payment(
    payment_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.tenant_id == current_user.tenant_id
    ).first()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted successfully"} 