"""
Plugin management router for handling plugin settings and configuration.
Commercial feature - requires plugin_management license.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timezone

from core.models.models import TenantPluginSettings, Tenant, MasterUser
from core.models.database import get_master_db
from core.routers.auth import get_current_user

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("/settings")
async def get_plugin_settings(
    db: Session = Depends(get_master_db),
    current_user: MasterUser = Depends(get_current_user)
):
    """
    Get enabled plugins for the current tenant.
    Returns list of enabled plugin IDs.
    """
    tenant_id = current_user.tenant_id

    settings = db.query(TenantPluginSettings).filter(
        TenantPluginSettings.tenant_id == tenant_id
    ).first()

    if not settings:
        # Create default settings if they don't exist
        settings = TenantPluginSettings(
            tenant_id=tenant_id,
            enabled_plugins=[]
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "tenant_id": tenant_id,
        "enabled_plugins": settings.enabled_plugins or [],
        "updated_at": settings.updated_at
    }


@router.post("/settings")
async def update_plugin_settings(
    payload: dict,
    db: Session = Depends(get_master_db),
    current_user: MasterUser = Depends(get_current_user)
):
    """
    Update enabled plugins for the current tenant.
    Requires admin role.

    Payload:
    {
        "enabled_plugins": ["investments", "reports"]
    }
    """
    tenant_id = current_user.tenant_id

    # Check if user is admin in the tenant
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage plugin settings"
        )

    enabled_plugins = payload.get("enabled_plugins", [])

    # Validate that enabled_plugins is a list
    if not isinstance(enabled_plugins, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="enabled_plugins must be a list of plugin IDs"
        )

    # Validate plugin IDs format
    valid_plugins = {"investments"}  # Add more plugins as they're created
    invalid_plugins = [p for p in enabled_plugins if p not in valid_plugins]

    if invalid_plugins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plugin IDs: {', '.join(invalid_plugins)}"
        )

    # Get or create settings
    settings = db.query(TenantPluginSettings).filter(
        TenantPluginSettings.tenant_id == tenant_id
    ).first()

    if not settings:
        settings = TenantPluginSettings(
            tenant_id=tenant_id,
            enabled_plugins=enabled_plugins
        )
        db.add(settings)
    else:
        settings.enabled_plugins = enabled_plugins
        settings.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(settings)

    return {
        "tenant_id": tenant_id,
        "enabled_plugins": settings.enabled_plugins,
        "updated_at": settings.updated_at,
        "message": "Plugin settings updated successfully"
    }


@router.post("/settings/{plugin_id}/enable")
async def enable_plugin(
    plugin_id: str,
    db: Session = Depends(get_master_db),
    current_user: MasterUser = Depends(get_current_user)
):
    """
    Enable a specific plugin for the current tenant.
    Requires admin role.
    """
    tenant_id = current_user.tenant_id

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage plugin settings"
        )

    # Validate plugin ID
    valid_plugins = {"investments"}
    if plugin_id not in valid_plugins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plugin ID: {plugin_id}"
        )

    settings = db.query(TenantPluginSettings).filter(
        TenantPluginSettings.tenant_id == tenant_id
    ).first()

    if not settings:
        settings = TenantPluginSettings(
            tenant_id=tenant_id,
            enabled_plugins=[plugin_id]
        )
        db.add(settings)
    else:
        if plugin_id not in settings.enabled_plugins:
            # Create a new list to ensure SQLAlchemy detects the change
            settings.enabled_plugins = list(settings.enabled_plugins) + [plugin_id]
            settings.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(settings)

    return {
        "tenant_id": tenant_id,
        "enabled_plugins": settings.enabled_plugins,
        "message": f"Plugin '{plugin_id}' enabled successfully"
    }


@router.post("/settings/{plugin_id}/disable")
async def disable_plugin(
    plugin_id: str,
    db: Session = Depends(get_master_db),
    current_user: MasterUser = Depends(get_current_user)
):
    """
    Disable a specific plugin for the current tenant.
    Requires admin role.
    """
    tenant_id = current_user.tenant_id

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage plugin settings"
        )

    settings = db.query(TenantPluginSettings).filter(
        TenantPluginSettings.tenant_id == tenant_id
    ).first()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin settings not found for this tenant"
        )

    if plugin_id in settings.enabled_plugins:
        # Create a new list to ensure SQLAlchemy detects the change
        settings.enabled_plugins = [p for p in settings.enabled_plugins if p != plugin_id]
        settings.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(settings)

    return {
        "tenant_id": tenant_id,
        "enabled_plugins": settings.enabled_plugins,
        "message": f"Plugin '{plugin_id}' disabled successfully"
    }
