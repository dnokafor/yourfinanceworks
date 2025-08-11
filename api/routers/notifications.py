from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from models.database import get_db, get_master_db
from models.models_per_tenant import EmailNotificationSettings, User
from models.models import MasterUser
from schemas.email_notifications import (
    EmailNotificationSettings as EmailNotificationSettingsSchema,
    EmailNotificationSettingsCreate,
    EmailNotificationSettingsUpdate
)
from routers.auth import get_current_user
from services.tenant_database_manager import tenant_db_manager
from utils.audit import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/settings", response_model=EmailNotificationSettingsSchema)
async def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: MasterUser = Depends(get_current_user)
):
    """Get current user's notification settings"""
    # Manually set tenant context and get tenant database
    try:
        # Find or create the tenant user by email
        tenant_user = db.query(User).filter(User.email == current_user.email).first()
        if not tenant_user:
            # Create user in tenant database
            tenant_user = User(
                email=current_user.email,
                hashed_password=current_user.hashed_password,
                is_active=current_user.is_active,
                is_superuser=current_user.is_superuser,
                role=current_user.role,
                first_name=current_user.first_name,
                last_name=current_user.last_name
            )
            db.add(tenant_user)
            db.commit()
            db.refresh(tenant_user)
        
        settings = db.query(EmailNotificationSettings).filter(
            EmailNotificationSettings.user_id == tenant_user.id
        ).first()
        
        if not settings:
            # Create default settings
            settings = EmailNotificationSettings(user_id=tenant_user.id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return settings
    except Exception as e:
        logger.error(f"Error getting notification settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification settings"
        )
    
@router.put("/settings", response_model=EmailNotificationSettingsSchema)
async def update_notification_settings(
    settings_update: EmailNotificationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's notification settings"""
    try:
        settings = db.query(EmailNotificationSettings).filter(
            EmailNotificationSettings.user_id == current_user.id
        ).first()
        
        if not settings:
            # Create new settings
            settings = EmailNotificationSettings(
                user_id=current_user.id,
                **settings_update.model_dump()
            )
            db.add(settings)
        else:
            # Update existing settings
            for field, value in settings_update.model_dump().items():
                setattr(settings, field, value)
        
        db.commit()
        db.refresh(settings)
        
        # Log audit event
        log_audit_event(
            db=db,
            user_id=current_user.id,
            user_email=current_user.email,
            action="UPDATE",
            resource_type="notification_settings",
            resource_id=str(settings.id),
            resource_name="Email Notification Settings",
            details=settings_update.model_dump(),
            status="success"
        )
        
        return settings
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating notification settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings"
        )

@router.post("/test")
async def test_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a test notification to verify settings"""
    try:
        from services.notification_service import NotificationService
        from services.email_service import EmailService, EmailProviderConfig, EmailProvider
        from models.models_per_tenant import Settings
        
        # Get email configuration
        email_settings = db.query(Settings).filter(
            Settings.key == "email_config"
        ).first()
        
        if not email_settings or not email_settings.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email service not configured"
            )
        
        # Create email service
        email_config_data = email_settings.value
        config = EmailProviderConfig(
            provider=EmailProvider(email_config_data['provider']),
            aws_access_key_id=email_config_data.get('aws_access_key_id'),
            aws_secret_access_key=email_config_data.get('aws_secret_access_key'),
            aws_region=email_config_data.get('aws_region'),
            azure_connection_string=email_config_data.get('azure_connection_string'),
            mailgun_api_key=email_config_data.get('mailgun_api_key'),
            mailgun_domain=email_config_data.get('mailgun_domain')
        )
        email_service = EmailService(config)
        
        # Create notification service
        notification_service = NotificationService(db, email_service)
        
        # Send test notification
        success = notification_service.send_operation_notification(
            event_type="settings_updated",
            user_id=current_user.id,
            resource_type="notification",
            resource_id="test",
            resource_name="Test Notification",
            details={
                "message": "This is a test notification to verify your email notification settings.",
                "test_time": "now"
            }
        )
        
        if success:
            return {"message": "Test notification sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test notification"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )