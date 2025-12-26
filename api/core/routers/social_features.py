"""
Social features API router for gamification.

This module provides REST API endpoints for social features including
leaderboards, achievement sharing, and group challenges.
All features are opt-in and respect user privacy preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from core.models.database import get_db
from core.services.social_features_manager import SocialFeaturesManager
from core.schemas.gamification import (
    AchievementShareResponse,
    LeaderboardResponse,
    UserLeaderboardPosition,
    GroupChallengeResponse,
    GroupChallengeDetailResponse,
    GroupChallengeParticipantResponse,
    SocialFeaturesStatusResponse,
    ShareAchievementRequest,
    ShareAchievementResponse,
    JoinGroupChallengeRequest,
    JoinGroupChallengeResponse,
    LeaveGroupChallengeRequest,
    LeaveGroupChallengeResponse,
    UpdateLeaderboardVisibilityRequest,
    UpdateLeaderboardVisibilityResponse
)
from core.routers.auth import get_current_user
from core.models.models_per_tenant import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification/social", tags=["gamification-social"])


@router.get("/status", response_model=SocialFeaturesStatusResponse)
async def get_social_features_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current social features status for the authenticated user.
    """
    try:
        social_manager = SocialFeaturesManager(db)
        social_enabled = await social_manager.check_social_features_enabled(current_user.id)
        
        return SocialFeaturesStatusResponse(
            social_features_enabled=social_enabled,
            leaderboards_enabled=social_enabled,
            achievement_sharing_enabled=social_enabled,
            group_challenges_enabled=social_enabled,
            user_social_preferences={
                "shareAchievements": False,
                "showOnLeaderboard": False,
                "allowFriendRequests": False
            }
        )
    except Exception as e:
        logger.error(f"Error getting social features status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get social features status"
        )


@router.post("/achievements/share", response_model=ShareAchievementResponse)
async def share_achievement(
    request: ShareAchievementRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share an achievement with others.
    """
    try:
        social_manager = SocialFeaturesManager(db)
        
        # Check if social features are enabled
        if not await social_manager.check_social_features_enabled(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Social features are not enabled for this user"
            )
        
        share = await social_manager.share_achievement(
            user_id=current_user.id,
            user_achievement_id=request.user_achievement_id,
            share_message=request.share_message,
            is_public=request.is_public
        )
        
        if not share:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to share achievement"
            )
        
        return ShareAchievementResponse(
            success=True,
            share_id=share.id,
            message="Achievement shared successfully",
            share_url=f"/achievements/shared/{share.id}" if share.is_public else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing achievement for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share achievement"
        )


@router.get("/leaderboard/global", response_model=LeaderboardResponse)
async def get_global_leaderboard(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the global leaderboard.
    """
    try:
        social_manager = SocialFeaturesManager(db)
        
        leaderboard_data = await social_manager.get_leaderboard(
            leaderboard_type="global",
            scope_id=None,
            limit=limit,
            offset=offset,
            current_user_id=current_user.id
        )
        
        return LeaderboardResponse(
            leaderboard_type=leaderboard_data["leaderboard_type"],
            scope_id=leaderboard_data["scope_id"],
            entries=leaderboard_data["entries"],
            total_entries=leaderboard_data["total_entries"],
            user_rank=leaderboard_data["user_rank"],
            user_entry=leaderboard_data["user_entry"],
            last_updated=leaderboard_data["last_updated"]
        )
    except Exception as e:
        logger.error(f"Error getting global leaderboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard"
        )


@router.get("/leaderboard/organization/{organization_id}", response_model=LeaderboardResponse)
async def get_organization_leaderboard(
    organization_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the organization leaderboard.
    """
    try:
        social_manager = SocialFeaturesManager(db)
        
        leaderboard_data = await social_manager.get_leaderboard(
            leaderboard_type="organization",
            scope_id=organization_id,
            limit=limit,
            offset=offset,
            current_user_id=current_user.id
        )
        
        return LeaderboardResponse(
            leaderboard_type=leaderboard_data["leaderboard_type"],
            scope_id=leaderboard_data["scope_id"],
            entries=leaderboard_data["entries"],
            total_entries=leaderboard_data["total_entries"],
            user_rank=leaderboard_data["user_rank"],
            user_entry=leaderboard_data["user_entry"],
            last_updated=leaderboard_data["last_updated"]
        )
    except Exception as e:
        logger.error(f"Error getting organization leaderboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard"
        )


@router.get("/leaderboard/position", response_model=UserLeaderboardPosition)
async def get_user_leaderboard_position(
    leaderboard_type: str = Query("global"),
    scope_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's position on a leaderboard.
    """
    try:
        social_manager = SocialFeaturesManager(db)
        
        position = await social_manager.get_user_leaderboard_position(
            user_id=current_user.id,
            leaderboard_type=leaderboard_type,
            scope_id=scope_id
        )
        
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found on leaderboard"
            )
        
        return UserLeaderboardPosition(**position)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user leaderboard position: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard position"
        )


@router.put("/leaderboard/visibility", response_model=UpdateLeaderboardVisibilityResponse)
async def update_leaderboard_visibility(
    request: UpdateLeaderboardVisibilityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's leaderboard visibility settings.
    """
    try:
        social_manager = SocialFeaturesManager(db)
        
        success = await social_manager.update_leaderboard_visibility(
            user_id=current_user.id,
            is_visible=request.is_visible,
            is_anonymous=request.is_anonymous
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update leaderboard visibility"
            )
        
        return UpdateLeaderboardVisibilityResponse(
            success=True,
            message="Leaderboard visibility updated successfully",
            new_visibility={
                "is_visible": request.is_visible,
                "is_anonymous": request.is_anonymous
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating leaderboard visibility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update leaderboard visibility"
        )


@router.post("/group-challenges/join", response_model=JoinGroupChallengeResponse)
async def join_group_challenge(
    request: JoinGroupChallengeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join a group challenge.
    """
    try:
        social_manager = SocialFeaturesManager(db)
        
        # Check if social features are enabled
        if not await social_manager.check_social_features_enabled(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Social features are not enabled for this user"
            )
        
        participant = await social_manager.join_group_challenge(
            user_id=current_user.id,
            group_challenge_id=request.group_challenge_id
        )
        
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to join group challenge"
            )
        
        # Get group challenge details
        group_challenge_details = await social_manager.get_group_challenge_details(
            request.group_challenge_id
        )
        
        return JoinGroupChallengeResponse(
            success=True,
            participant_id=participant.id,
            message="Successfully joined group challenge",
            group_challenge=GroupChallengeResponse(**{
                k: v for k, v in group_challenge_details.items()
                if k in GroupChallengeResponse.__fields__
            })
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining group challenge for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join group challenge"
        )


@router.post("/group-challenges/leave", response_model=LeaveGroupChallengeResponse)
async def leave_group_challenge(
    request: LeaveGroupChallengeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Leave a group challenge.
    """
    try:
        social_manager = SocialFeaturesManager(db)
        
        success = await social_manager.leave_group_challenge(
            user_id=current_user.id,
            group_challenge_id=request.group_challenge_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to leave group challenge"
            )
        
        return LeaveGroupChallengeResponse(
            success=True,
            message="Successfully left group challenge"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leaving group challenge for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave group challenge"
        )


@router.get("/group-challenges/{group_challenge_id}", response_model=GroupChallengeDetailResponse)
async def get_group_challenge_details(
    group_challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a group challenge.
    """
    try:
        social_manager = SocialFeaturesManager(db)
        
        details = await social_manager.get_group_challenge_details(group_challenge_id)
        
        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group challenge not found"
            )
        
        return GroupChallengeDetailResponse(**details)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group challenge details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get group challenge details"
        )
