"""
Test reminder attribution functionality.

This test verifies that reminders properly capture and display creator information.
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from core.models.models_per_tenant import Reminder, User, RecurrencePattern, ReminderStatus, ReminderPriority
from core.schemas.reminders import ReminderResponse, ReminderWithUsers


def test_reminder_creation_captures_creator(db_session: Session, test_user: User):
    """Test that reminder creation captures the creator's user ID"""
    # Create a reminder
    reminder = Reminder(
        title="Test Reminder",
        description="Test description",
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
        recurrence_pattern=RecurrencePattern.NONE,
        priority=ReminderPriority.MEDIUM,
        created_by_id=test_user.id,
        assigned_to_id=test_user.id
    )
    
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    
    # Verify creator is captured
    assert reminder.created_by_id == test_user.id
    assert reminder.created_by_id is not None


def test_reminder_response_includes_creator_info(db_session: Session, test_user: User):
    """Test that reminder responses include creator information"""
    # Create a reminder with creator
    reminder = Reminder(
        title="Test Reminder",
        description="Test description",
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
        recurrence_pattern=RecurrencePattern.NONE,
        priority=ReminderPriority.MEDIUM,
        created_by_id=test_user.id,
        assigned_to_id=test_user.id
    )
    
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    
    # Load with relationship
    from sqlalchemy.orm import joinedload
    reminder_with_user = db_session.query(Reminder).options(
        joinedload(Reminder.created_by)
    ).filter(Reminder.id == reminder.id).first()
    
    # Serialize to response schema
    response = ReminderResponse.model_validate(reminder_with_user)
    
    # Verify creator information is included
    assert response.created_by_user_id == test_user.id
    assert response.created_by_username is not None
    assert response.created_by_email == test_user.email


def test_reminder_with_users_includes_creator_relationship(db_session: Session, test_user: User):
    """Test that ReminderWithUsers includes the full creator relationship"""
    # Create a reminder
    reminder = Reminder(
        title="Test Reminder",
        description="Test description",
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
        recurrence_pattern=RecurrencePattern.NONE,
        priority=ReminderPriority.MEDIUM,
        created_by_id=test_user.id,
        assigned_to_id=test_user.id
    )
    
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    
    # Load with relationship
    from sqlalchemy.orm import joinedload
    reminder_with_user = db_session.query(Reminder).options(
        joinedload(Reminder.created_by),
        joinedload(Reminder.assigned_to)
    ).filter(Reminder.id == reminder.id).first()
    
    # Serialize to ReminderWithUsers schema
    response = ReminderWithUsers.model_validate(reminder_with_user)
    
    # Verify creator relationship is included
    assert response.created_by is not None
    assert response.created_by.id == test_user.id
    assert response.created_by.email == test_user.email


def test_reminder_handles_missing_creator_gracefully(db_session: Session, test_user: User):
    """Test that reminders handle missing creator information gracefully"""
    # Create a reminder
    reminder = Reminder(
        title="Test Reminder",
        description="Test description",
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
        recurrence_pattern=RecurrencePattern.NONE,
        priority=ReminderPriority.MEDIUM,
        created_by_id=test_user.id,
        assigned_to_id=test_user.id
    )
    
    db_session.add(reminder)
    db_session.commit()
    db_session.refresh(reminder)
    
    # Load WITHOUT the relationship (simulating missing user)
    reminder_no_user = db_session.query(Reminder).filter(Reminder.id == reminder.id).first()
    
    # Serialize to response schema
    response = ReminderResponse.model_validate(reminder_no_user)
    
    # Verify it handles missing creator gracefully
    assert response.created_by_user_id == test_user.id
    assert response.created_by_username == "Unknown"
    assert response.created_by_email is None


# Fixtures
@pytest.fixture
def test_user(db_session: Session):
    """Create a test user"""
    user = User(
        id=1,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        hashed_password="hashed",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def db_session():
    """Create a test database session"""
    from core.models.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
