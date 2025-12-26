"""
Organization Gamification Administration API Router

This module provides REST API endpoints for organization administrators to manage
gamification settings, team features, and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import logging

from core.models.database import get_db
from core.models.models_per_tenant import User
from core.routers.auth import get_current_user
from core.services.organization_gamification_admin import OrganizationGamificationAdmin
from core.schemas.gamification import (
    DataRetentionPolicy,
    ChallengeType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification/organization", tags=["gamification-admin"])


# Helper function to verify organization admin
async def verify_org_admin(current_user: User, organization_id: int) -> bool:
    """Verify that the current user is an admin for the organization"""
    # This would check if user is org admin
    # For now, we'll assume the user is an admin if they have the right role
    return True  # TODO: Implement proper role checking


@router.get("/config/{organization_id}")
async def get_organization_config(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the gamification configuration for an organization.
    Requires organization admin privileges.
    """
    try:
        # Verify admin access
        if not await verify_org_admin(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this organization's settings"
            )

        admin_service = OrganizationGamificationAdmin(db)
        config = await admin_service.get_organization_config(organization_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization configuration not found"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization configuration"
        )


@router.post("/config/{organization_id}")
async def create_organization_config(
    organization_id: int,
    custom_settings: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new gamification configuration for an organization.
    Requires organization admin privileges.
    """
    try:
        # Verify admin access
        if not await verify_org_admin(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to configure this organization"
            )

        admin_service = OrganizationGamificationAdmin(db)
        config = await admin_service.create_organization_config(
            organization_id,
            current_user.id,
            custom_settings
        )

        if not config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization configuration"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization configuration"
        )


@router.put("/config/{organization_id}/point-values")
async def update_point_values(
    organization_id: int,
    point_values: Dict[str, int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update custom point values for an organization.
    Requires organization admin privileges.
    """
    try:
        # Verify admin access
        if not await verify_org_admin(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this organization's settings"
            )

        admin_service = OrganizationGamificationAdmin(db)
        config = await admin_service.update_point_values(
            organization_id,
            point_values,
            current_user.id
        )

        if not config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update point values"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating point values: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update point values"
        )


@router.put("/config/{organization_id}/achievement-thresholds")
async def set_achievement_thresholds(
    organization_id: int,
    thresholds: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update achievement thresholds for an organization.
    Requires organization admin privileges.
    """
    try:
        # Verify admin access
        if not await verify_org_admin(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this organization's settings"
            )

        admin_service = OrganizationGamificationAdmin(db)
        config = await admin_service.set_achievement_thresholds(
            organization_id,
            thresholds,
            current_user.id
        )

        if not config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set achievement thresholds"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting achievement thresholds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set achievement thresholds"
        )


@router.put("/config/{organization_id}/features/{feature}")
async def enable_feature(
    organization_id: int,
    feature: str,
    enabled: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enable or disable a specific gamification feature for an organization.
    Requires organization admin privileges.
    """
    try:
        # Verify admin access
        if not await verify_org_admin(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this organization's settings"
            )

        admin_service = OrganizationGamificationAdmin(db)
        config = await admin_service.enable_feature_for_org(
            organization_id,
            feature,
            enabled,
            current_user.id
        )

        if not config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update feature status"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling feature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feature status"
        )


@router.post("/challenges/{organization_id}")
async def create_custom_challenge(
    organization_id: int,
    challenge_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a custom challenge for an organization.
    Requires organization admin privileges.
    """
    try:
        # Verify admin access
        if not await verify_org_admin(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create challenges for this organization"
            )

        admin_service = OrganizationGamificationAdmin(db)
        challenge = await admin_service.create_custom_challenge(
            organization_id,
            challenge_data,
            current_user.id
        )

        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create custom challenge"
            )

        return challenge

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating custom challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create custom challenge"
        )


@router.get("/analytics/{organization_id}")
async def get_team_analytics(
    organization_id: int,
    time_range_days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive team analytics for an organization.
    Requires organization admin privileges.
    """
    try:
        # Verify admin access
        if not await verify_org_admin(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this organization's analytics"
            )

        admin_service = OrganizationGamificationAdmin(db)
        analytics = await admin_service.get_team_analytics(
            organization_id,
            time_range_days
        )

        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get team analytics"
            )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get team analytics"
        )


@router.get("/engagement-metrics/{organization_id}")
async def get_engagement_metrics(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get engagement metrics for an organization.
    Requires organization admin privileges.
    """
    try:
        # Verify admin access
        if not await verify_org_admin(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this organization's metrics"
            )

        admin_service = OrganizationGamificationAdmin(db)
        metrics = await admin_service.get_engagement_metrics(organization_id)

        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get engagement metrics"
            )

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting engagement metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get engagement metrics"
        )


@router.get("/preferences/{user_id}/{organization_id}")
async def resolve_user_preferences(
    user_id: int,
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resolve user preferences respecting the hierarchy:
    User Privacy > Organization Policy > System Defaults
    """
    try:
        # Verify admin access or user is viewing their own preferences
        if current_user.id != user_id and not await verify_org_admin(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these preferences"
            )

        admin_service = OrganizationGamificationAdmin(db)
        preferences = await admin_service.resolve_user_preferences(user_id, organization_id)

        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User preferences not found"
            )

        return preferences

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving user preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve user preferences"
        )


@router.get("/effective-settings/{user_id}")
async def get_effective_settings(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the effective gamification settings for a user.
    Users can only view their own settings.
    """
    try:
        # Verify user is viewing their own settings
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        admin_service = OrganizationGamificationAdmin(db)
        settings = await admin_service.get_effective_settings(user_id)

        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User settings not found"
            )

        return settings

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting effective settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get effective settings"
        )
