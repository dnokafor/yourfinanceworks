"""
Social features manager for gamification system.

This module handles leaderboards, achievement sharing, and group challenges.
All social features are opt-in and respect user privacy preferences.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import logging

from core.models.gamification import (
    UserGamificationProfile,
    Achievement,
    UserAchievement,
    AchievementShare,
    Leaderboard,
    GroupChallenge,
    GroupChallengeParticipant,
    UserChallenge,
    Challenge,
    OrganizationGamificationConfig
)
from core.models.models_per_tenant import User

logger = logging.getLogger(__name__)


class SocialFeaturesManager:
    """Manages social features including leaderboards, sharing, and group challenges."""

    def __init__(self, db: Session):
        self.db = db

    async def check_social_features_enabled(self, user_id: int) -> bool:
        """Check if social features are enabled for a user."""
        profile = self.db.query(UserGamificationProfile).filter(
            UserGamificationProfile.user_id == user_id
        ).first()
        
        if not profile or not profile.module_enabled:
            return False
        
        # Check if user has social features enabled in preferences
        preferences = profile.preferences or {}
        features = preferences.get("features", {})
        return features.get("social", False)

    async def share_achievement(
        self,
        user_id: int,
        user_achievement_id: int,
        share_message: Optional[str] = None,
        is_public: bool = False
    ) -> Optional[AchievementShare]:
        """
        Share an achievement with others.
        
        Args:
            user_id: ID of user sharing the achievement
            user_achievement_id: ID of the user achievement to share
            share_message: Optional message to include with share
            is_public: Whether the share is public or private
            
        Returns:
            AchievementShare object if successful, None otherwise
        """
        try:
            # Verify user has social features enabled
            if not await self.check_social_features_enabled(user_id):
                logger.warning(f"User {user_id} attempted to share achievement but social features disabled")
                return None
            
            # Verify the achievement belongs to the user
            user_achievement = self.db.query(UserAchievement).filter(
                UserAchievement.id == user_achievement_id
            ).first()
            
            if not user_achievement:
                logger.warning(f"Achievement {user_achievement_id} not found")
                return None
            
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.id == user_achievement.profile_id
            ).first()
            
            if not profile or profile.user_id != user_id:
                logger.warning(f"User {user_id} attempted to share achievement they don't own")
                return None
            
            # Create achievement share
            share = AchievementShare(
                user_achievement_id=user_achievement_id,
                shared_by_user_id=user_id,
                share_message=share_message,
                is_public=is_public,
                share_count=0
            )
            
            self.db.add(share)
            self.db.commit()
            self.db.refresh(share)
            
            logger.info(f"User {user_id} shared achievement {user_achievement_id}")
            return share
            
        except Exception as e:
            logger.error(f"Error sharing achievement: {str(e)}")
            self.db.rollback()
            return None

    async def get_leaderboard(
        self,
        leaderboard_type: str = "global",
        scope_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get leaderboard entries.
        
        Args:
            leaderboard_type: Type of leaderboard ("global", "organization", "team")
            scope_id: Scope ID for organization or team leaderboards
            limit: Maximum number of entries to return
            offset: Offset for pagination
            current_user_id: Current user ID to include their position
            
        Returns:
            Dictionary with leaderboard data
        """
        try:
            # Build query
            query = self.db.query(Leaderboard).filter(
                Leaderboard.leaderboard_type == leaderboard_type,
                Leaderboard.is_visible == True
            )
            
            if scope_id:
                query = query.filter(Leaderboard.scope_id == scope_id)
            
            # Get total count
            total_entries = query.count()
            
            # Get entries ordered by rank
            entries = query.order_by(Leaderboard.rank).limit(limit).offset(offset).all()
            
            # Get current user's position if provided
            user_rank = None
            user_entry = None
            if current_user_id:
                user_profile = self.db.query(UserGamificationProfile).filter(
                    UserGamificationProfile.user_id == current_user_id
                ).first()
                
                if user_profile:
                    user_leaderboard = self.db.query(Leaderboard).filter(
                        Leaderboard.profile_id == user_profile.id,
                        Leaderboard.leaderboard_type == leaderboard_type
                    )
                    
                    if scope_id:
                        user_leaderboard = user_leaderboard.filter(Leaderboard.scope_id == scope_id)
                    
                    user_leaderboard = user_leaderboard.first()
                    if user_leaderboard:
                        user_rank = user_leaderboard.rank
                        user_entry = user_leaderboard
            
            return {
                "leaderboard_type": leaderboard_type,
                "scope_id": scope_id,
                "entries": entries,
                "total_entries": total_entries,
                "user_rank": user_rank,
                "user_entry": user_entry,
                "last_updated": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}")
            return {
                "leaderboard_type": leaderboard_type,
                "scope_id": scope_id,
                "entries": [],
                "total_entries": 0,
                "user_rank": None,
                "user_entry": None,
                "last_updated": datetime.now(timezone.utc)
            }

    async def get_user_leaderboard_position(
        self,
        user_id: int,
        leaderboard_type: str = "global",
        scope_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a user's position on a leaderboard.
        
        Args:
            user_id: User ID
            leaderboard_type: Type of leaderboard
            scope_id: Scope ID if applicable
            
        Returns:
            Dictionary with user's leaderboard position
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                return None
            
            query = self.db.query(Leaderboard).filter(
                Leaderboard.profile_id == profile.id,
                Leaderboard.leaderboard_type == leaderboard_type
            )
            
            if scope_id:
                query = query.filter(Leaderboard.scope_id == scope_id)
            
            leaderboard_entry = query.first()
            
            if not leaderboard_entry:
                return None
            
            # Calculate percentile
            total_entries = self.db.query(Leaderboard).filter(
                Leaderboard.leaderboard_type == leaderboard_type
            )
            
            if scope_id:
                total_entries = total_entries.filter(Leaderboard.scope_id == scope_id)
            
            total_count = total_entries.count()
            percentile = ((total_count - leaderboard_entry.rank) / total_count * 100) if total_count > 0 else 0
            
            # Count entries ahead and behind
            entries_ahead = self.db.query(Leaderboard).filter(
                Leaderboard.leaderboard_type == leaderboard_type,
                Leaderboard.rank < leaderboard_entry.rank
            )
            
            if scope_id:
                entries_ahead = entries_ahead.filter(Leaderboard.scope_id == scope_id)
            
            entries_ahead_count = entries_ahead.count()
            entries_behind_count = total_count - leaderboard_entry.rank
            
            return {
                "rank": leaderboard_entry.rank,
                "experience_points": leaderboard_entry.experience_points,
                "level": leaderboard_entry.level,
                "rank_change": leaderboard_entry.rank_change,
                "percentile": percentile,
                "entries_ahead": entries_ahead_count,
                "entries_behind": entries_behind_count
            }
            
        except Exception as e:
            logger.error(f"Error getting user leaderboard position: {str(e)}")
            return None

    async def update_leaderboard_visibility(
        self,
        user_id: int,
        is_visible: bool,
        is_anonymous: bool = False
    ) -> bool:
        """
        Update user's leaderboard visibility settings.
        
        Args:
            user_id: User ID
            is_visible: Whether user should appear on leaderboard
            is_anonymous: Whether to show as anonymous
            
        Returns:
            True if successful, False otherwise
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                return False
            
            # Update all leaderboard entries for this user
            leaderboard_entries = self.db.query(Leaderboard).filter(
                Leaderboard.profile_id == profile.id
            ).all()
            
            for entry in leaderboard_entries:
                entry.is_visible = is_visible
                entry.is_anonymous = is_anonymous
                entry.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            logger.info(f"Updated leaderboard visibility for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating leaderboard visibility: {str(e)}")
            self.db.rollback()
            return False

    async def create_group_challenge(
        self,
        challenge_id: int,
        group_type: str,
        group_id: int,
        group_name: str,
        start_date: datetime,
        end_date: datetime,
        description: Optional[str] = None,
        max_participants: Optional[int] = None,
        group_reward_xp: int = 0,
        individual_reward_xp: int = 0
    ) -> Optional[GroupChallenge]:
        """
        Create a group challenge.
        
        Args:
            challenge_id: Base challenge ID
            group_type: Type of group ("organization", "team", "custom_group")
            group_id: ID of the group
            group_name: Name of the group
            start_date: Challenge start date
            end_date: Challenge end date
            description: Optional description
            max_participants: Maximum participants (None for unlimited)
            group_reward_xp: Bonus XP for group completion
            individual_reward_xp: Individual completion reward
            
        Returns:
            GroupChallenge object if successful, None otherwise
        """
        try:
            # Verify challenge exists
            challenge = self.db.query(Challenge).filter(
                Challenge.id == challenge_id
            ).first()
            
            if not challenge:
                logger.warning(f"Challenge {challenge_id} not found")
                return None
            
            # Create group challenge
            group_challenge = GroupChallenge(
                challenge_id=challenge_id,
                group_type=group_type,
                group_id=group_id,
                group_name=group_name,
                description=description,
                max_participants=max_participants,
                group_reward_xp=group_reward_xp,
                individual_reward_xp=individual_reward_xp,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                current_participants=0
            )
            
            self.db.add(group_challenge)
            self.db.commit()
            self.db.refresh(group_challenge)
            
            logger.info(f"Created group challenge {group_challenge.id} for {group_type} {group_id}")
            return group_challenge
            
        except Exception as e:
            logger.error(f"Error creating group challenge: {str(e)}")
            self.db.rollback()
            return None

    async def join_group_challenge(
        self,
        user_id: int,
        group_challenge_id: int
    ) -> Optional[GroupChallengeParticipant]:
        """
        Join a group challenge.
        
        Args:
            user_id: User ID
            group_challenge_id: Group challenge ID
            
        Returns:
            GroupChallengeParticipant object if successful, None otherwise
        """
        try:
            # Verify group challenge exists and is active
            group_challenge = self.db.query(GroupChallenge).filter(
                GroupChallenge.id == group_challenge_id,
                GroupChallenge.is_active == True
            ).first()
            
            if not group_challenge:
                logger.warning(f"Group challenge {group_challenge_id} not found or inactive")
                return None
            
            # Check max participants
            if group_challenge.max_participants:
                if group_challenge.current_participants >= group_challenge.max_participants:
                    logger.warning(f"Group challenge {group_challenge_id} is full")
                    return None
            
            # Get or create user challenge
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                logger.warning(f"Profile not found for user {user_id}")
                return None
            
            # Check if user already has this challenge
            existing_user_challenge = self.db.query(UserChallenge).filter(
                UserChallenge.profile_id == profile.id,
                UserChallenge.challenge_id == group_challenge.challenge_id
            ).first()
            
            if not existing_user_challenge:
                # Create new user challenge
                user_challenge = UserChallenge(
                    profile_id=profile.id,
                    challenge_id=group_challenge.challenge_id,
                    progress=0.0,
                    is_completed=False,
                    opted_in=True,
                    started_at=datetime.now(timezone.utc),
                    milestones=[]
                )
                self.db.add(user_challenge)
                self.db.flush()
            else:
                user_challenge = existing_user_challenge
            
            # Create group challenge participant
            participant = GroupChallengeParticipant(
                group_challenge_id=group_challenge_id,
                user_challenge_id=user_challenge.id,
                joined_at=datetime.now(timezone.utc),
                is_active=True,
                contribution_points=0
            )
            
            self.db.add(participant)
            
            # Update group challenge participant count
            group_challenge.current_participants += 1
            group_challenge.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(participant)
            
            logger.info(f"User {user_id} joined group challenge {group_challenge_id}")
            return participant
            
        except Exception as e:
            logger.error(f"Error joining group challenge: {str(e)}")
            self.db.rollback()
            return None

    async def leave_group_challenge(
        self,
        user_id: int,
        group_challenge_id: int
    ) -> bool:
        """
        Leave a group challenge.
        
        Args:
            user_id: User ID
            group_challenge_id: Group challenge ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find participant
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                return False
            
            participant = self.db.query(GroupChallengeParticipant).filter(
                GroupChallengeParticipant.group_challenge_id == group_challenge_id
            ).join(
                UserChallenge,
                GroupChallengeParticipant.user_challenge_id == UserChallenge.id
            ).filter(
                UserChallenge.profile_id == profile.id
            ).first()
            
            if not participant:
                logger.warning(f"Participant not found for user {user_id} in group challenge {group_challenge_id}")
                return False
            
            # Mark as inactive
            participant.is_active = False
            participant.left_at = datetime.now(timezone.utc)
            
            # Update group challenge participant count
            group_challenge = self.db.query(GroupChallenge).filter(
                GroupChallenge.id == group_challenge_id
            ).first()
            
            if group_challenge and group_challenge.current_participants > 0:
                group_challenge.current_participants -= 1
                group_challenge.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            logger.info(f"User {user_id} left group challenge {group_challenge_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error leaving group challenge: {str(e)}")
            self.db.rollback()
            return False

    async def get_group_challenge_details(
        self,
        group_challenge_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a group challenge.
        
        Args:
            group_challenge_id: Group challenge ID
            
        Returns:
            Dictionary with group challenge details
        """
        try:
            group_challenge = self.db.query(GroupChallenge).filter(
                GroupChallenge.id == group_challenge_id
            ).first()
            
            if not group_challenge:
                return None
            
            # Get participants
            participants = self.db.query(GroupChallengeParticipant).filter(
                GroupChallengeParticipant.group_challenge_id == group_challenge_id,
                GroupChallengeParticipant.is_active == True
            ).all()
            
            # Calculate group progress
            total_progress = 0
            if participants:
                for participant in participants:
                    user_challenge = self.db.query(UserChallenge).filter(
                        UserChallenge.id == participant.user_challenge_id
                    ).first()
                    if user_challenge:
                        total_progress += user_challenge.progress
                
                group_progress = total_progress / len(participants)
            else:
                group_progress = 0.0
            
            # Get top contributors
            top_contributors = sorted(
                [{"user_challenge_id": p.user_challenge_id, "contribution_points": p.contribution_points} 
                 for p in participants],
                key=lambda x: x["contribution_points"],
                reverse=True
            )[:5]
            
            return {
                "id": group_challenge.id,
                "challenge_id": group_challenge.challenge_id,
                "group_type": group_challenge.group_type,
                "group_id": group_challenge.group_id,
                "group_name": group_challenge.group_name,
                "description": group_challenge.description,
                "current_participants": group_challenge.current_participants,
                "max_participants": group_challenge.max_participants,
                "group_reward_xp": group_challenge.group_reward_xp,
                "individual_reward_xp": group_challenge.individual_reward_xp,
                "is_active": group_challenge.is_active,
                "start_date": group_challenge.start_date,
                "end_date": group_challenge.end_date,
                "group_progress": group_progress,
                "participants": participants,
                "top_contributors": top_contributors,
                "created_at": group_challenge.created_at,
                "updated_at": group_challenge.updated_at
            }
            
        except Exception as e:
            logger.error(f"Error getting group challenge details: {str(e)}")
            return None

    async def update_leaderboard_rankings(self) -> bool:
        """
        Update all leaderboard rankings based on current user progress.
        This should be called periodically or after significant user progress updates.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all profiles with gamification enabled
            profiles = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.module_enabled == True
            ).all()
            
            # Update global leaderboard
            for profile in profiles:
                # Get or create leaderboard entry
                leaderboard_entry = self.db.query(Leaderboard).filter(
                    Leaderboard.profile_id == profile.id,
                    Leaderboard.leaderboard_type == "global"
                ).first()
                
                if not leaderboard_entry:
                    leaderboard_entry = Leaderboard(
                        profile_id=profile.id,
                        leaderboard_type="global",
                        scope_id=None,
                        rank=0,
                        experience_points=profile.total_experience_points,
                        level=profile.level,
                        is_visible=True,
                        is_anonymous=False
                    )
                    self.db.add(leaderboard_entry)
                else:
                    old_rank = leaderboard_entry.rank
                    leaderboard_entry.experience_points = profile.total_experience_points
                    leaderboard_entry.level = profile.level
                    leaderboard_entry.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Recalculate ranks
            leaderboard_entries = self.db.query(Leaderboard).filter(
                Leaderboard.leaderboard_type == "global"
            ).order_by(desc(Leaderboard.experience_points)).all()
            
            for idx, entry in enumerate(leaderboard_entries, 1):
                old_rank = entry.rank
                entry.rank = idx
                entry.rank_change = old_rank - idx if old_rank > 0 else 0
                entry.last_rank_update = datetime.now(timezone.utc)
            
            self.db.commit()
            logger.info(f"Updated leaderboard rankings for {len(leaderboard_entries)} entries")
            return True
            
        except Exception as e:
            logger.error(f"Error updating leaderboard rankings: {str(e)}")
            self.db.rollback()
            return False
