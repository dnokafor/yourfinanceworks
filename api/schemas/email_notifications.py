from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class EmailNotificationSettingsBase(BaseModel):
    # User operation notifications
    user_created: bool = False
    user_updated: bool = False
    user_deleted: bool = False
    user_login: bool = False
    
    # Client operation notifications
    client_created: bool = True
    client_updated: bool = False
    client_deleted: bool = True
    
    # Invoice operation notifications
    invoice_created: bool = True
    invoice_updated: bool = False
    invoice_deleted: bool = True
    invoice_sent: bool = True
    invoice_paid: bool = True
    invoice_overdue: bool = True
    
    # Payment operation notifications
    payment_created: bool = True
    payment_updated: bool = False
    payment_deleted: bool = True
    
    # Settings operation notifications
    settings_updated: bool = False
    
    # Additional notification preferences
    notification_email: Optional[str] = None
    daily_summary: bool = False
    weekly_summary: bool = False

class EmailNotificationSettingsCreate(EmailNotificationSettingsBase):
    pass

class EmailNotificationSettingsUpdate(EmailNotificationSettingsBase):
    pass

class EmailNotificationSettings(EmailNotificationSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class NotificationEvent(BaseModel):
    event_type: str
    user_id: int
    resource_type: str
    resource_id: str
    resource_name: str
    details: dict
    timestamp: datetime