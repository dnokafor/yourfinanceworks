"""
Preference Hierarchy API Router

This module provides REST API endpoints for managing the preference hierarchy system
that respects: User Privacy > Organization Policy > System Defaults
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from core.models.database import get_db
from core.models.models_per_tenant import User
from core.routers.auth import get_current_user
from core.services.preference_hierarchy_resolver import PreferenceHierarchyResolver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification/preferences", tags=["preference-hierarchy"])


@router.get("/resolved/{user_id}")
async def get_resolved_preferences(
    user_id: int,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get resolved user preferences respecting the hierarchy:
    User Privacy > Organization Policy > System Defaults

    Users can only view their own preferences.
    Organization admins can view any user's preferences in their organization.
    """
    try:
        # Verify access
        if current_user.id != user_id:
            # Check if user is org admin
            if organization_id and current_user.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view these preferences"
                )

        resolver = PreferenceHierarchyResolver(db)
        result = await resolver.resolve_user_preferences(user_id, organization_id)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resolved preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get resolved preferences"
        )


@router.get("/point-values/{user_id}")
async def get_effective_point_values(
    user_id: int,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the effective point values for a user.
    """
    try:
        # Verify access
        if current_user.id != user_id and (not organization_id or current_user.organization_id != organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        resolver = PreferenceHierarchyResolver(db)
        point_values = await resolver.get_effective_point_values(user_id, organization_id)

        return {
            "user_id": user_id,
            "organization_id": organization_id,
            "point_values": point_values
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting effective point values: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get point values"
        )


@router.get("/achievement-thresholds/{user_id}")
async def get_effective_achievement_thresholds(
    user_id: int,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the effective achievement thresholds for a user.
    """
    try:
        # Verify access
        if current_user.id != user_id and (not organization_id or current_user.organization_id != organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        resolver = PreferenceHierarchyResolver(db)
        thresholds = await resolver.get_effective_achievement_thresholds(user_id, organization_id)

        return {
            "user_id": user_id,
            "organization_id": organization_id,
            "achievement_thresholds": thresholds
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting effective achievement thresholds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get achievement thresholds"
        )


@router.get("/enabled-features/{user_id}")
async def get_effective_enabled_features(
    user_id: int,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the effective enabled features for a user.
    """
    try:
        # Verify access
        if current_user.id != user_id and (not organization_id or current_user.organization_id != organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        resolver = PreferenceHierarchyResolver(db)
        features = await resolver.get_effective_enabled_features(user_id, organization_id)

        return {
            "user_id": user_id,
            "organization_id": organization_id,
            "enabled_features": features
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting effective enabled features: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get enabled features"
        )


@router.get("/privacy/{user_id}")
async def get_user_privacy_settings(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user privacy settings.
    These are ALWAYS user-controlled and never overridden by organization settings.
    Users can only view their own privacy settings.
    """
    try:
        # Verify access
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        resolver = PreferenceHierarchyResolver(db)
        privacy_settings = await resolver.get_user_privacy_settings(user_id)

        return {
            "user_id": user_id,
            "privacy_settings": privacy_settings,
            "note": "Privacy settings are always user-controlled and cannot be overridden by organization policies"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user privacy settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get privacy settings"
        )


@router.get("/feature-enabled/{user_id}/{feature}")
async def is_feature_enabled_for_user(
    user_id: int,
    feature: str,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if a specific feature is enabled for a user.
    """
    try:
        # Verify access
        if current_user.id != user_id and (not organization_id or current_user.organization_id != organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        resolver = PreferenceHierarchyResolver(db)
        is_enabled = await resolver.is_feature_enabled_for_user(user_id, feature, organization_id)

        return {
            "user_id": user_id,
            "feature": feature,
            "enabled": is_enabled
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking if feature is enabled: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check feature status"
        )


@router.get("/can-share-achievements/{user_id}")
async def can_user_share_achievements(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has opted in to share achievements.
    """
    try:
        # Verify access
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        resolver = PreferenceHierarchyResolver(db)
        can_share = await resolver.can_user_share_achievements(user_id)

        return {
            "user_id": user_id,
            "can_share_achievements": can_share
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking if user can share achievements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check achievement sharing setting"
        )


@router.get("/can-appear-on-leaderboard/{user_id}")
async def can_user_appear_on_leaderboard(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has opted in to appear on leaderboard.
    """
    try:
        # Verify access
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        resolver = PreferenceHierarchyResolver(db)
        can_appear = await resolver.can_user_appear_on_leaderboard(user_id)

        return {
            "user_id": user_id,
            "can_appear_on_leaderboard": can_appear
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking if user can appear on leaderboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check leaderboard setting"
        )


@router.get("/notification-frequency/{user_id}")
async def get_notification_frequency(
    user_id: int,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the notification frequency for a user.
    """
    try:
        # Verify access
        if current_user.id != user_id and (not organization_id or current_user.organization_id != organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        resolver = PreferenceHierarchyResolver(db)
        frequency = await resolver.get_notification_frequency(user_id, organization_id)

        return {
            "user_id": user_id,
            "notification_frequency": frequency
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification frequency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification frequency"
        )


@router.get("/preference-source/{user_id}/{setting_key}")
async def get_preference_source(
    user_id: int,
    setting_key: str,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Determine the source of a preference setting.
    Returns: "user", "organization", or "system"
    """
    try:
        # Verify access
        if current_user.id != user_id and (not organization_id or current_user.organization_id != organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these settings"
            )

        resolver = PreferenceHierarchyResolver(db)
        source = await resolver.get_preference_source(user_id, setting_key, organization_id)

        return {
            "user_id": user_id,
            "setting_key": setting_key,
            "source": source,
            "hierarchy": "User Privacy > Organization Policy > System Defaults"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preference source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get preference source"
        )
