from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from models.models_per_tenant import EmailNotificationSettings, User
from services.email_service import EmailService, EmailMessage
from jinja2 import Template
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling email notifications for user operations"""
    
    def __init__(self, db: Session, email_service: EmailService):
        self.db = db
        self.email_service = email_service
    
    def get_user_notification_settings(self, user_id: int) -> Optional[EmailNotificationSettings]:
        """Get notification settings for a user"""
        return self.db.query(EmailNotificationSettings).filter(
            EmailNotificationSettings.user_id == user_id
        ).first()
    
    def create_default_notification_settings(self, user_id: int) -> EmailNotificationSettings:
        """Create default notification settings for a new user"""
        settings = EmailNotificationSettings(user_id=user_id)
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings
    
    def should_send_notification(self, user_id: int, event_type: str) -> bool:
        """Check if notification should be sent for a specific event"""
        settings = self.get_user_notification_settings(user_id)
        if not settings:
            settings = self.create_default_notification_settings(user_id)
        
        return getattr(settings, event_type, False)
    
    def send_operation_notification(
        self,
        event_type: str,
        user_id: int,
        resource_type: str,
        resource_id: str,
        resource_name: str,
        details: Dict[str, Any],
        company_name: str = "Invoice Management System"
    ) -> bool:
        """Send notification for a user operation"""
        try:
            # Check if user wants this notification
            if not self.should_send_notification(user_id, event_type):
                return True  # Not an error, just not enabled
            
            # Get user info
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found for notification")
                return False
            
            # Get notification settings to check for custom email
            settings = self.get_user_notification_settings(user_id)
            notification_email = settings.notification_email if settings else None
            recipient_email = notification_email or user.email
            recipient_name = f"{user.first_name} {user.last_name}".strip() or user.email
            
            # Create email message
            message = self._create_notification_message(
                event_type=event_type,
                resource_type=resource_type,
                resource_name=resource_name,
                details=details,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                company_name=company_name
            )
            
            # Send email
            return self.email_service.send_email(message)
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    def _create_notification_message(
        self,
        event_type: str,
        resource_type: str,
        resource_name: str,
        details: Dict[str, Any],
        recipient_email: str,
        recipient_name: str,
        company_name: str
    ) -> EmailMessage:
        """Create email message for notification"""
        
        # Get event details
        event_info = self._get_event_info(event_type, resource_type)
        
        # Create subject
        subject = f"{company_name} - {event_info['title']}: {resource_name}"
        
        # Create HTML template
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ subject }}</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #f0f0f0;
                }
                .logo {
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }
                .title {
                    color: #333;
                    font-size: 20px;
                    margin-bottom: 10px;
                }
                .event-badge {
                    display: inline-block;
                    background-color: {{ event_color }};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 15px;
                    font-size: 12px;
                    font-weight: bold;
                    text-transform: uppercase;
                }
                .content {
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 30px;
                }
                .details {
                    background-color: #f8f9fa;
                    border-left: 4px solid {{ event_color }};
                    padding: 15px;
                    margin: 20px 0;
                }
                .details-title {
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }
                .detail-item {
                    margin: 5px 0;
                    font-size: 14px;
                }
                .footer {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #999;
                    font-size: 14px;
                    text-align: center;
                }
                .timestamp {
                    color: #999;
                    font-size: 12px;
                    margin-top: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">{{ company_name }}</div>
                    <h1 class="title">{{ event_title }}</h1>
                    <span class="event-badge">{{ event_type.replace('_', ' ').title() }}</span>
                </div>
                
                <div class="content">
                    <p>Hello {{ recipient_name }},</p>
                    <p>{{ event_description }}</p>
                </div>
                
                <div class="details">
                    <div class="details-title">Details:</div>
                    <div class="detail-item"><strong>{{ resource_type.title() }}:</strong> {{ resource_name }}</div>
                    {% for key, value in details.items() %}
                    <div class="detail-item"><strong>{{ key.replace('_', ' ').title() }}:</strong> {{ value }}</div>
                    {% endfor %}
                    <div class="timestamp">{{ timestamp }}</div>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from {{ company_name }}.</p>
                    <p>You can manage your notification preferences in your account settings.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        # Create text template
        text_template = Template("""
        {{ company_name }} - {{ event_title }}
        
        Hello {{ recipient_name }},
        
        {{ event_description }}
        
        Details:
        {{ resource_type.title() }}: {{ resource_name }}
        {% for key, value in details.items() %}
        {{ key.replace('_', ' ').title() }}: {{ value }}
        {% endfor %}
        
        Timestamp: {{ timestamp }}
        
        This is an automated notification from {{ company_name }}.
        You can manage your notification preferences in your account settings.
        """)
        
        # Render templates
        context = {
            'subject': subject,
            'company_name': company_name,
            'event_title': event_info['title'],
            'event_type': event_type,
            'event_description': event_info['description'],
            'event_color': event_info['color'],
            'resource_type': resource_type,
            'resource_name': resource_name,
            'details': details,
            'recipient_name': recipient_name,
            'timestamp': datetime.now(timezone.utc).strftime('%B %d, %Y at %I:%M %p UTC')
        }
        
        html_body = html_template.render(**context)
        text_body = text_template.render(**context)
        
        return EmailMessage(
            to_email=recipient_email,
            to_name=recipient_name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email="noreply@invoiceapp.com",
            from_name=company_name
        )
    
    def _get_event_info(self, event_type: str, resource_type: str) -> Dict[str, str]:
        """Get event information for notification"""
        event_map = {
            # User events
            'user_created': {
                'title': 'New User Created',
                'description': 'A new user has been added to your organization.',
                'color': '#28a745'
            },
            'user_updated': {
                'title': 'User Updated',
                'description': 'A user\'s information has been updated.',
                'color': '#ffc107'
            },
            'user_deleted': {
                'title': 'User Deleted',
                'description': 'A user has been removed from your organization.',
                'color': '#dc3545'
            },
            'user_login': {
                'title': 'User Login',
                'description': 'A user has logged into the system.',
                'color': '#17a2b8'
            },
            
            # Client events
            'client_created': {
                'title': 'New Client Added',
                'description': 'A new client has been added to your system.',
                'color': '#28a745'
            },
            'client_updated': {
                'title': 'Client Updated',
                'description': 'A client\'s information has been updated.',
                'color': '#ffc107'
            },
            'client_deleted': {
                'title': 'Client Deleted',
                'description': 'A client has been removed from your system.',
                'color': '#dc3545'
            },
            
            # Invoice events
            'invoice_created': {
                'title': 'New Invoice Created',
                'description': 'A new invoice has been created.',
                'color': '#28a745'
            },
            'invoice_updated': {
                'title': 'Invoice Updated',
                'description': 'An invoice has been updated.',
                'color': '#ffc107'
            },
            'invoice_deleted': {
                'title': 'Invoice Deleted',
                'description': 'An invoice has been deleted.',
                'color': '#dc3545'
            },
            'invoice_sent': {
                'title': 'Invoice Sent',
                'description': 'An invoice has been sent to a client.',
                'color': '#17a2b8'
            },
            'invoice_paid': {
                'title': 'Invoice Paid',
                'description': 'An invoice has been marked as paid.',
                'color': '#28a745'
            },
            'invoice_overdue': {
                'title': 'Invoice Overdue',
                'description': 'An invoice is now overdue.',
                'color': '#dc3545'
            },
            
            # Payment events
            'payment_created': {
                'title': 'Payment Recorded',
                'description': 'A new payment has been recorded.',
                'color': '#28a745'
            },
            'payment_updated': {
                'title': 'Payment Updated',
                'description': 'A payment has been updated.',
                'color': '#ffc107'
            },
            'payment_deleted': {
                'title': 'Payment Deleted',
                'description': 'A payment has been deleted.',
                'color': '#dc3545'
            },
            
            # Settings events
            'settings_updated': {
                'title': 'Settings Updated',
                'description': 'System settings have been updated.',
                'color': '#6f42c1'
            }
        }
        
        return event_map.get(event_type, {
            'title': f'{resource_type.title()} {event_type.replace("_", " ").title()}',
            'description': f'A {resource_type} operation has occurred.',
            'color': '#6c757d'
        })
    
    def send_daily_summary(self, user_id: int) -> bool:
        """Send daily summary notification"""
        # Implementation for daily summary
        pass
    
    def send_weekly_summary(self, user_id: int) -> bool:
        """Send weekly summary notification"""
        # Implementation for weekly summary
        pass