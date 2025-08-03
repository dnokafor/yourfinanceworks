from sqlalchemy.orm import Session
from models.models_per_tenant import AuditLog
from models.models import AuditLog as MasterAuditLog
from typing import Optional, Dict, Any
from datetime import datetime, date

# Helper to convert all datetime objects in a dict/list to ISO strings
def convert_datetimes(obj):
    if isinstance(obj, dict):
        return {k: convert_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetimes(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    else:
        return obj


def log_audit_event(
    db: Session,
    user_id: int,
    user_email: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
):
    # Ensure details is JSON serializable
    if details is not None:
        details = convert_datetimes(details)
    audit_log = AuditLog(
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        error_message=error_message,
        created_at=datetime.utcnow(),
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def log_audit_event_master(
    db: Session,
    user_id: int,
    user_email: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    tenant_id: Optional[int] = None,
):
    """Log audit event in master database"""
    # Ensure details is JSON serializable
    if details is not None:
        details = convert_datetimes(details)
    audit_log = MasterAuditLog(
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        error_message=error_message,
        tenant_id=tenant_id,
        created_at=datetime.utcnow(),
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log 