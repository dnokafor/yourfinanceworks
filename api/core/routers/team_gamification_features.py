"""
Team Gamification Features API Router

This module provides REST API endpoints for team-level gamification features
including leaderboards, group challenges, and team analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import logging

from core.models.database import get_db
from core.models.models_per_tenant import User
from core.routers.auth import get_current_user
from core.services.team_gamification_features import TeamGamificationFeatures

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification/team", tags=["team-gamification"])


# Helper function to verify organization access
async def verify_org_access(current_user: User, organization_id: int) -> bool:
    """Verify that the current user belongs to the organization"""
    return current_user.organization_id == organization_id


@router.get("/leaderboard/{organization_id}")
async def get_team_leaderboard(
    organization_id: int,
    limit: int = 100,
    metric: str = "xp",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get team leaderboard ranked by specified metric.
    Respects user privacy settings - only shows users who opted in.
    """
    try:
        # Verify user belongs to organization
        if not await verify_org_access(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this organization's leaderboard"
            )

        team_service = TeamGamificationFeatures(db)
        leaderboard = await team_service.get_team_leaderboard(
            organization_id,
            limit=min(limit, 1000),  # Cap at 1000
            metric=metric
        )

        if leaderboard is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get team leaderboard"
            )

        return {
            "organization_id": organization_id,
            "metric": metric,
            "leaderboard": leaderboard
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team leaderboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get team leaderboard"
        )


@router.get("/leaderboard/{organization_id}/position")
async def get_user_leaderboard_position(
    organization_id: int,
    metric: str = "xp",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's position on the team leaderboard.
    """
    try:
        # Verify user belongs to organization
        if not await verify_org_access(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this organization's leaderboard"
            )

        team_service = TeamGamificationFeatures(db)
        position = await team_service.get_user_leaderboard_position(
            current_user.id,
            organization_id,
            metric
        )

        if position is None:
            return {
                "message": "User not on leaderboard (may have opted out or disabled gamification)"
            }

        return position

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user leaderboard position: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard position"
        )


@router.get("/leaderboard/{organization_id}/department/{department}")
async def get_department_leaderboard(
    organization_id: int,
    department: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard for a specific department within an organization.
    """
    try:
        # Verify user belongs to organization
        if not await verify_org_access(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this organization's leaderboard"
            )

        team_service = TeamGamificationFeatures(db)
        leaderboard = await team_service.get_team_leaderboard_by_department(
            organization_id,
            department,
            limit=min(limit, 500)
        )

        if leaderboard is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get department leaderboard"
            )

        return {
            "organization_id": organization_id,
            "department": department,
            "leaderboard": leaderboard
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting department leaderboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get department leaderboard"
        )


@router.post("/challenges/{organization_id}")
async def create_group_challenge(
    organization_id: int,
    challenge_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a group challenge for an organization.
    Requires organization admin privileges.
    """
    try:
        # Verify user is org admin
        if not await verify_org_access(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create challenges for this organization"
            )

        # TODO: Add proper admin role checking

        team_service = TeamGamificationFeatures(db)
        challenge = await team_service.create_group_challenge(
            organization_id,
            challenge_data,
            current_user.id
        )

        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create group challenge"
            )

        return challenge

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating group challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group challenge"
        )


@router.get("/challenges/{organization_id}")
async def get_group_challenges(
    organization_id: int,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all group challenges for an organization.
    """
    try:
        # Verify user belongs to organization
        if not await verify_org_access(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this organization's challenges"
            )

        team_service = TeamGamificationFeatures(db)
        challenges = await team_service.get_group_challenges(
            organization_id,
            active_only
        )

        if challenges is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get group challenges"
            )

        return {
            "organization_id": organization_id,
            "challenges": challenges
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group challenges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get group challenges"
        )


@router.get("/challenges/{organization_id}/{challenge_id}/progress")
async def get_group_challenge_progress(
    organization_id: int,
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get progress information for a group challenge.
    """
    try:
        # Verify user belongs to organization
        if not await verify_org_access(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this organization's challenges"
            )

        team_service = TeamGamificationFeatures(db)
        progress = await team_service.get_group_challenge_progress(
            challenge_id,
            organization_id
        )

        if progress is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Challenge not found"
            )

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group challenge progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get challenge progress"
        )


@router.get("/analytics/{organization_id}/performance")
async def get_team_performance_summary(
    organization_id: int,
    time_range_days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a summary of team performance metrics.
    Requires organization admin privileges.
    """
    try:
        # Verify user is org admin
        if not await verify_org_access(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this organization's analytics"
            )

        # TODO: Add proper admin role checking

        team_service = TeamGamificationFeatures(db)
        summary = await team_service.get_team_performance_summary(
            organization_id,
            time_range_days
        )

        if summary is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get team performance summary"
            )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team performance summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get team performance summary"
        )


@router.get("/analytics/{organization_id}/habit-formation")
async def get_team_habit_formation_report(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a report on team habit formation progress.
    Requires organization admin privileges.
    """
    try:
        # Verify user is org admin
        if not await verify_org_access(current_user, organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this organization's analytics"
            )

        # TODO: Add proper admin role checking

        team_service = TeamGamificationFeatures(db)
        report = await team_service.get_team_habit_formation_report(organization_id)

        if report is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get habit formation report"
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting habit formation report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get habit formation report"
        )
