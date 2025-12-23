"""
User Preference Controls API Router

This router provides REST API endpoints for managing user gamification preferences,
including feature toggles, personal goals, notification settings, and visual themes.

Implements Requirement 12: Customization and Preferences
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import logging

from core.models.database import get_db
from core.services.user_preference_controls import UserPreferenceControls
from core.routers.auth import get_current_user
from core.models.models_per_tenant import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification/preferences", tags=["gamification-preferences"])


@router.get("/", response_model=Dict[str, Any])
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all user preferences for gamification.
    
    Returns:
        Dictionary containing all user preferences including features, privacy,
        notifications, personal goals, achievement categories, and visual theme.
    """
    try:
        preference_controls = UserPreferenceControls(db)
        preferences = await preference_controls.get_user_preferences(current_user.id)
        
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User gamification profile not found"
            )
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user preferences for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user preferences"
        )


@router.put("/features", response_model=Dict[str, Any])
async def update_feature_preferences(
    features: Dict[str, bool],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update feature enable/disable preferences.
    
    Allows users to enable or disable specific game mechanics:
    - points: Experience point system
    - achievements: Achievement unlocking
    - streaks: Streak tracking
    - challenges: Challenge participation
    - social: Social features (leaderboards, sharing)
    - notifications: Gamification notifications
    
    Args:
        features: Dictionary of feature names to boolean values
        
    Returns:
        Updated feature preferences
    """
    try:
        preference_controls = UserPreferenceControls(db)
        result = await preference_controls.update_feature_preferences(current_user.id, features)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User gamification profile not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feature preferences for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feature preferences"
        )


@router.post("/personal-goals", response_model=Dict[str, Any])
async def set_personal_goals(
    goals: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set personal goals for the user.
    
    Allows users to define custom goals such as:
    - Daily expense tracking target
    - Weekly budget review frequency
    - Monthly invoice follow-up target
    - Habit formation milestones
    
    Args:
        goals: Dictionary of goal names to target values
        
    Returns:
        Updated personal goals
    """
    try:
        preference_controls = UserPreferenceControls(db)
        result = await preference_controls.set_personal_goals(current_user.id, goals)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User gamification profile not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting personal goals for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set personal goals"
        )


@router.get("/personal-goals", response_model=Dict[str, Any])
async def get_personal_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personal goals for the user.
    
    Returns:
        Dictionary of personal goals
    """
    try:
        preference_controls = UserPreferenceControls(db)
        result = await preference_controls.get_personal_goals(current_user.id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User gamification profile not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting personal goals for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personal goals"
        )


@router.put("/notification-frequency", response_model=Dict[str, Any])
async def update_notification_frequency(
    frequency: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update notification frequency preference.
    
    Allows users to choose how often they receive gamification notifications:
    - immediate: Real-time notifications
    - daily: Daily digest
    - weekly: Weekly digest
    - disabled: No notifications
    
    Args:
        frequency: Notification frequency (immediate, daily, weekly, disabled)
        
    Returns:
        Updated notification frequency setting
    """
    try:
        preference_controls = UserPreferenceControls(db)
        result = await preference_controls.update_notification_frequency(current_user.id, frequency)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid notification frequency or user profile not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification frequency for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification frequency"
        )


@router.put("/notification-types", response_model=Dict[str, Any])
async def update_notification_types(
    notification_types: Dict[str, bool],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update which types of notifications the user wants to receive.
    
    Allows users to enable/disable specific notification types:
    - streakReminders: Notifications when streaks are at risk
    - achievementCelebrations: Notifications when achievements are unlocked
    - challengeUpdates: Notifications about challenge progress
    
    Args:
        notification_types: Dictionary of notification type names to boolean values
        
    Returns:
        Updated notification types
    """
    try:
        preference_controls = UserPreferenceControls(db)
        result = await preference_controls.update_notification_types(current_user.id, notification_types)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User gamification profile not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification types for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification types"
        )


@router.put("/achievement-categories", response_model=Dict[str, Any])
async def set_achievement_category_preferences(
    categories: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set preferred achievement categories for the user.
    
    Allows users to select which achievement categories they want to focus on:
    - expense_tracking
    - invoice_management
    - habit_formation
    - financial_health
    - exploration
    
    Args:
        categories: List of achievement category names
        
    Returns:
        Updated achievement category preferences
    """
    try:
        preference_controls = UserPreferenceControls(db)
        result = await preference_controls.set_achievement_category_preferences(current_user.id, categories)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid achievement categories or user profile not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting achievement categories for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set achievement categories"
        )


@router.put("/visual-theme", response_model=Dict[str, Any])
async def set_visual_theme(
    theme: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set the visual theme for gamification interface.
    
    Available themes:
    - light: Light theme
    - dark: Dark theme
    - colorful: Colorful theme
    - minimal: Minimal theme
    - professional: Professional theme
    
    Args:
        theme: Theme name
        
    Returns:
        Updated visual theme preference
    """
    try:
        preference_controls = UserPreferenceControls(db)
        result = await preference_controls.set_visual_theme(current_user.id, theme)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid theme or user profile not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting visual theme for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set visual theme"
        )


@router.get("/available-themes", response_model=List[str])
async def get_available_themes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of available visual themes.
    
    Returns:
        List of available theme names
    """
    try:
        preference_controls = UserPreferenceControls(db)
        themes = await preference_controls.get_available_themes()
        return themes
        
    except Exception as e:
        logger.error(f"Error getting available themes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available themes"
        )


@router.get("/available-achievement-categories", response_model=List[str])
async def get_available_achievement_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of available achievement categories.
    
    Returns:
        List of available achievement category names
    """
    try:
        preference_controls = UserPreferenceControls(db)
        categories = await preference_controls.get_available_achievement_categories()
        return categories
        
    except Exception as e:
        logger.error(f"Error getting available achievement categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available achievement categories"
        )


@router.get("/available-notification-frequencies", response_model=List[str])
async def get_available_notification_frequencies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of available notification frequencies.
    
    Returns:
        List of available notification frequency options
    """
    try:
        preference_controls = UserPreferenceControls(db)
        frequencies = await preference_controls.get_available_notification_frequencies()
        return frequencies
        
    except Exception as e:
        logger.error(f"Error getting available notification frequencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available notification frequencies"
        )


@router.post("/reset-to-defaults", response_model=Dict[str, Any])
async def reset_preferences_to_defaults(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset all user preferences to system defaults.
    
    Returns:
        Reset preferences
    """
    try:
        preference_controls = UserPreferenceControls(db)
        result = await preference_controls.reset_preferences_to_defaults(current_user.id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User gamification profile not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting preferences for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset preferences"
        )


@router.post("/validate", response_model=Dict[str, Any])
async def validate_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate a preferences dictionary.
    
    Args:
        preferences: Dictionary of preferences to validate
        
    Returns:
        Validation results with any errors or warnings
    """
    try:
        preference_controls = UserPreferenceControls(db)
        result = await preference_controls.validate_preferences(preferences)
        return result
        
    except Exception as e:
        logger.error(f"Error validating preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate preferences"
        )
