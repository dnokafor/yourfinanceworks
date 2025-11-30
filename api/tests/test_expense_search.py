"""Test expense search functionality"""
import pytest
from sqlalchemy.orm import Session
from core.models.models_per_tenant import Expense, User
from core.models.models import MasterUser
from datetime import datetime


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user"""
    user = MasterUser(
        email="test@example.com",
        hashed_password="hashed",
        tenant_id=1,
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_expenses(db_session: Session, test_user):
    """Create test expenses with different vendors and notes"""
    expenses = [
        Expense(
            user_id=test_user.id,
            amount=100.00,
            currency="USD",
            expense_date="2024-01-01",
            category="Office Supplies",
            vendor="Walmart",
            notes="Office supplies from Walmart",
            status="recorded"
        ),
        Expense(
            user_id=test_user.id,
            amount=50.00,
            currency="USD",
            expense_date="2024-01-02",
            category="Groceries",
            vendor="Target",
            notes="Groceries",
            status="recorded"
        ),
        Expense(
            user_id=test_user.id,
            amount=75.00,
            currency="USD",
            expense_date="2024-01-03",
            category="Office Supplies",
            vendor="Amazon",
            notes="Walmart gift card purchase",
            status="recorded"
        ),
    ]
    for expense in expenses:
        db_session.add(expense)
    db_session.commit()
    return expenses


def test_search_by_vendor(db_session: Session, test_user, test_expenses):
    """Test searching expenses by vendor name"""
    # Search for Walmart vendor
    query = db_session.query(Expense).filter(Expense.user_id == test_user.id)
    query = query.filter(Expense.vendor.ilike("%Walmart%"))
    results = query.all()
    
    assert len(results) == 1
    assert results[0].vendor == "Walmart"


def test_search_by_notes(db_session: Session, test_user, test_expenses):
    """Test searching expenses by notes"""
    # Search for Walmart in notes
    import sqlalchemy as sa
    query = db_session.query(Expense).filter(Expense.user_id == test_user.id)
    query = query.filter(Expense.notes.ilike("%Walmart%"))
    results = query.all()
    
    assert len(results) == 2
    assert any(e.vendor == "Walmart" for e in results)
    assert any(e.vendor == "Amazon" for e in results)


def test_search_combined_vendor_and_notes(db_session: Session, test_user, test_expenses):
    """Test searching across vendor and notes fields"""
    import sqlalchemy as sa
    query = db_session.query(Expense).filter(Expense.user_id == test_user.id)
    search_term = "%Walmart%"
    query = query.filter(
        (Expense.vendor.ilike(search_term)) |
        (Expense.notes.ilike(search_term))
    )
    results = query.all()
    
    assert len(results) == 2
    vendors = [e.vendor for e in results]
    assert "Walmart" in vendors
    assert "Amazon" in vendors


def test_search_case_insensitive(db_session: Session, test_user, test_expenses):
    """Test that search is case insensitive"""
    query = db_session.query(Expense).filter(Expense.user_id == test_user.id)
    query = query.filter(Expense.vendor.ilike("%walmart%"))
    results = query.all()
    
    assert len(results) == 1
    assert results[0].vendor == "Walmart"


def test_search_no_results(db_session: Session, test_user, test_expenses):
    """Test search with no matching results"""
    query = db_session.query(Expense).filter(Expense.user_id == test_user.id)
    query = query.filter(Expense.vendor.ilike("%Costco%"))
    results = query.all()
    
    assert len(results) == 0
