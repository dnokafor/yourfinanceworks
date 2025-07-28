from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import requests
import json
import os
import logging

from models.database import get_master_db, set_tenant_context
from models.models import MasterUser
from models.models_per_tenant import SupportedCurrency, CurrencyRate
from schemas.currency import SupportedCurrency as SupportedCurrencySchema, CurrencyRate as CurrencyRateSchema, CurrencyConversion
from routers.auth import get_current_user
from services.tenant_database_manager import tenant_db_manager
from utils.rbac import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/currencies", tags=["currencies"])

# Exchange rate API configuration
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")
EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/"
BACKUP_API_URL = "https://api.fixer.io/latest"
FIXER_API_KEY = os.getenv("FIXER_API_KEY")

@router.get("/supported", response_model=List[SupportedCurrencySchema])
async def get_supported_currencies(
    active_only: bool = True,
    current_user: MasterUser = Depends(get_current_user)
):
    """Get list of supported currencies"""
    # Manually set tenant context and get tenant database
    set_tenant_context(current_user.tenant_id)
    tenant_session = tenant_db_manager.get_tenant_session(current_user.tenant_id)
    db = tenant_session()
    
    try:
        query = db.query(SupportedCurrency)
        
        if active_only:
            query = query.filter(SupportedCurrency.is_active == True)
        
        currencies = query.order_by(SupportedCurrency.code).all()
        return currencies
    finally:
        db.close()

@router.get("/rates", response_model=List[CurrencyRateSchema])
async def get_currency_rates(
    from_currency: Optional[str] = None,
    to_currency: Optional[str] = None,
    current_user: MasterUser = Depends(get_current_user)
):
    """Get currency exchange rates"""
    # Manually set tenant context and get tenant database
    set_tenant_context(current_user.tenant_id)
    tenant_session = tenant_db_manager.get_tenant_session(current_user.tenant_id)
    db = tenant_session()
    
    try:
        query = db.query(CurrencyRate)
        
        # Apply filters if provided
        filters = []
        if from_currency:
            filters.append(CurrencyRate.from_currency == from_currency.upper())
        if to_currency:
            filters.append(CurrencyRate.to_currency == to_currency.upper())
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get the most recent rates (within last 24 hours)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        rates = query.filter(
            CurrencyRate.effective_date >= cutoff_time
        ).order_by(
            CurrencyRate.from_currency,
            CurrencyRate.to_currency,
            CurrencyRate.effective_date.desc()
        ).all()
        
        # Remove duplicates (keep only the most recent rate for each currency pair)
        unique_rates = {}
        for rate in rates:
            pair_key = f"{rate.from_currency}_{rate.to_currency}"
            if pair_key not in unique_rates:
                unique_rates[pair_key] = rate
        
        return list(unique_rates.values())
    finally:
        db.close()

@router.post("/rates", response_model=CurrencyRateSchema)
async def create_or_update_exchange_rate(
    rate_data: CurrencyRateSchema,
    current_user: MasterUser = Depends(get_current_user)
):
    """Create or update an exchange rate"""
    # Manually set tenant context and get tenant database
    set_tenant_context(current_user.tenant_id)
    tenant_session = tenant_db_manager.get_tenant_session(current_user.tenant_id)
    db = tenant_session()
    
    try:
        # Validate currency codes
        if not db.query(SupportedCurrency).filter(SupportedCurrency.code == rate_data.from_currency.upper()).first():
            raise HTTPException(
                status_code=400,
                detail="Invalid 'from_currency' code"
            )
        
        if not db.query(SupportedCurrency).filter(SupportedCurrency.code == rate_data.to_currency.upper()).first():
            raise HTTPException(
                status_code=400,
                detail="Invalid 'to_currency' code"
            )
        
        if rate_data.from_currency == rate_data.to_currency:
            raise HTTPException(
                status_code=400,
                detail="From and to currencies cannot be the same"
            )
        
        if rate_data.rate <= 0:
            raise HTTPException(
                status_code=400,
                detail="Exchange rate must be positive"
            )
        
        # Check if rate already exists for the same date
        existing_rate = db.query(CurrencyRate).filter(
            CurrencyRate.from_currency == rate_data.from_currency.upper(),
            CurrencyRate.to_currency == rate_data.to_currency.upper(),
            CurrencyRate.effective_date == rate_data.effective_date
        ).first()
        
        if existing_rate:
            existing_rate.rate = rate_data.rate
            existing_rate.updated_at = datetime.now(timezone.utc)
        else:
            new_rate = CurrencyRate(
                from_currency=rate_data.from_currency.upper(),
                to_currency=rate_data.to_currency.upper(),
                rate=rate_data.rate,
                effective_date=rate_data.effective_date
            )
            db.add(new_rate)
        
        db.commit()
        db.refresh(existing_rate if existing_rate else new_rate)
        
        return existing_rate if existing_rate else new_rate
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating exchange rate: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create/update exchange rate"
        )
    finally:
        db.close()

@router.put("/rates/{rate_id}", response_model=CurrencyRateSchema)
async def update_exchange_rate(
    rate_id: int,
    rate_update: CurrencyRateSchema,
    current_user: MasterUser = Depends(get_current_user)
):
    """Update a specific exchange rate"""
    # Manually set tenant context and get tenant database
    set_tenant_context(current_user.tenant_id)
    tenant_session = tenant_db_manager.get_tenant_session(current_user.tenant_id)
    db = tenant_session()
    
    try:
        from models.models_per_tenant import CurrencyRate as CurrencyRateModel
        
        # Get existing rate
        existing_rate = db.query(CurrencyRateModel).filter(
            CurrencyRateModel.id == rate_id
        ).first()
        
        if not existing_rate:
            raise HTTPException(
                status_code=404,
                detail="Exchange rate not found"
            )
        
        # Update fields
        if rate_update.rate is not None:
            if rate_update.rate <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Exchange rate must be positive"
                )
            existing_rate.rate = rate_update.rate
        
        if rate_update.effective_date is not None:
            existing_rate.effective_date = rate_update.effective_date
        
        existing_rate.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(existing_rate)
        
        return existing_rate
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating exchange rate: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update exchange rate"
        )
    finally:
        db.close()

@router.post("/convert", response_model=CurrencyConversion)
async def convert_currency(
    amount: float = 1.0, # Default to 1.0 for conversion
    from_currency: str = "USD",
    to_currency: str = "USD",
    conversion_date: Optional[datetime] = None, # Use datetime for date comparison
    current_user: MasterUser = Depends(get_current_user)
):
    """Convert amount from one currency to another"""
    # Manually set tenant context and get tenant database
    set_tenant_context(current_user.tenant_id)
    tenant_session = tenant_db_manager.get_tenant_session(current_user.tenant_id)
    db = tenant_session()
    
    try:
        if amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Amount must be positive"
            )
        
        # Validate currency codes
        if not db.query(SupportedCurrency).filter(SupportedCurrency.code == from_currency.upper()).first():
            raise HTTPException(
                status_code=400,
                detail="Invalid 'from_currency' code"
            )
        
        if not db.query(SupportedCurrency).filter(SupportedCurrency.code == to_currency.upper()).first():
            raise HTTPException(
                status_code=400,
                detail="Invalid 'to_currency' code"
            )
        
        if from_currency == to_currency:
            return CurrencyConversion(
                from_currency=from_currency,
                to_currency=to_currency,
                amount=amount,
                converted_amount=amount,
                exchange_rate=1.0,
                conversion_date=datetime.now(timezone.utc)
            )
        
        # Determine the effective date for the conversion
        if conversion_date:
            effective_date = conversion_date.date()
        else:
            effective_date = datetime.now(timezone.utc).date()
        
        # Get the exchange rate for the specified date
        rate = db.query(CurrencyRate).filter(
            CurrencyRate.from_currency == from_currency.upper(),
            CurrencyRate.to_currency == to_currency.upper(),
            CurrencyRate.effective_date == effective_date
        ).first()
        
        if not rate:
            raise HTTPException(
                status_code=404,
                detail="No exchange rate found for the specified date"
            )
        
        converted_amount = amount * rate.rate
        
        return CurrencyConversion(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            converted_amount=converted_amount,
            exchange_rate=rate.rate,
            conversion_date=datetime.combine(effective_date, datetime.min.time().replace(tzinfo=timezone.utc))
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting currency: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to convert currency"
        )
    finally:
        db.close()

@router.delete("/rates/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange_rate(
    rate_id: int,
    current_user: MasterUser = Depends(get_current_user)
):
    """Delete an exchange rate"""
    # Manually set tenant context and get tenant database
    set_tenant_context(current_user.tenant_id)
    tenant_session = tenant_db_manager.get_tenant_session(current_user.tenant_id)
    db = tenant_session()
    
    try:
        from models.models_per_tenant import CurrencyRate as CurrencyRateModel
        
        existing_rate = db.query(CurrencyRateModel).filter(
            CurrencyRateModel.id == rate_id
        ).first()
        
        if not existing_rate:
            raise HTTPException(
                status_code=404,
                detail="Exchange rate not found"
            )
        
        db.delete(existing_rate)
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting exchange rate: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete exchange rate"
        ) 
    finally:
        db.close()

@router.post("/custom", response_model=SupportedCurrencySchema)
async def create_custom_currency(
    currency_data: SupportedCurrencySchema,
    current_user: MasterUser = Depends(get_current_user)
):
    """Create a custom currency"""
    # Manually set tenant context and get tenant database
    set_tenant_context(current_user.tenant_id)
    tenant_session = tenant_db_manager.get_tenant_session(current_user.tenant_id)
    db = tenant_session()
    
    try:
        from models.models_per_tenant import SupportedCurrency as SupportedCurrencyModel
        
        # Check if currency code already exists
        existing_currency = db.query(SupportedCurrencyModel).filter(
            SupportedCurrencyModel.code == currency_data.code.upper()
        ).first()
        
        if existing_currency:
            raise HTTPException(
                status_code=400,
                detail=f"Currency with code {currency_data.code.upper()} already exists"
            )
        
        # Create new currency
        new_currency = SupportedCurrencyModel(
            code=currency_data.code.upper(),
            name=currency_data.name,
            symbol=currency_data.symbol,
            decimal_places=currency_data.decimal_places,
            is_active=currency_data.is_active
        )
        
        # Set updated_at if the column exists
        try:
            new_currency.updated_at = datetime.now(timezone.utc)
        except AttributeError:
            # updated_at column might not exist yet
            pass
        
        db.add(new_currency)
        db.commit()
        db.refresh(new_currency)
        
        return new_currency
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating custom currency: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create custom currency"
        )
    finally:
        db.close()

@router.put("/custom/{currency_id}", response_model=SupportedCurrencySchema)
async def update_custom_currency(
    currency_id: int,
    currency_update: SupportedCurrencySchema,
    current_user: MasterUser = Depends(get_current_user)
):
    """Update a custom currency"""
    # Manually set tenant context and get tenant database
    set_tenant_context(current_user.tenant_id)
    tenant_session = tenant_db_manager.get_tenant_session(current_user.tenant_id)
    db = tenant_session()
    
    try:
        from models.models_per_tenant import SupportedCurrency as SupportedCurrencyModel
        
        # Get existing currency
        existing_currency = db.query(SupportedCurrencyModel).filter(
            SupportedCurrencyModel.id == currency_id
        ).first()
        
        if not existing_currency:
            raise HTTPException(
                status_code=404,
                detail="Currency not found"
            )
        
        # Update fields
        if currency_update.name is not None:
            existing_currency.name = currency_update.name
        
        if currency_update.symbol is not None:
            existing_currency.symbol = currency_update.symbol
        
        if currency_update.decimal_places is not None:
            existing_currency.decimal_places = currency_update.decimal_places
        
        if currency_update.is_active is not None:
            existing_currency.is_active = currency_update.is_active
        
        from datetime import datetime
        try:
            existing_currency.updated_at = datetime.now(timezone.utc)
        except AttributeError:
            # updated_at column might not exist yet
            pass
        
        db.commit()
        db.refresh(existing_currency)
        
        return existing_currency
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating custom currency: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update custom currency"
        )
    finally:
        db.close()

@router.delete("/custom/{currency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_currency(
    currency_id: int,
    current_user: MasterUser = Depends(get_current_user)
):
    """Delete a custom currency"""
    # Manually set tenant context and get tenant database
    set_tenant_context(current_user.tenant_id)
    tenant_session = tenant_db_manager.get_tenant_session(current_user.tenant_id)
    db = tenant_session()
    
    try:
        from models.models_per_tenant import SupportedCurrency as SupportedCurrencyModel
        
        # Get existing currency
        existing_currency = db.query(SupportedCurrencyModel).filter(
            SupportedCurrencyModel.id == currency_id
        ).first()
        
        if not existing_currency:
            raise HTTPException(
                status_code=404,
                detail="Currency not found"
            )
        
        # Check if currency is being used in invoices or payments
        from models.models_per_tenant import Invoice
        from routers.payments import Payment
        invoice_count = db.query(Invoice).filter(Invoice.currency == existing_currency.code).count()
        payment_count = db.query(Payment).filter(Payment.currency == existing_currency.code).count()
        
        if invoice_count > 0 or payment_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete currency {existing_currency.code} as it is being used in {invoice_count} invoices and {payment_count} payments"
            )
        
        db.delete(existing_currency)
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting custom currency: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete custom currency"
        ) 
    finally:
        db.close() 