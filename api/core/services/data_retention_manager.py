"""
Data Retention Manager Service.

This service manages data retention policies for the gamification system,
handling preservation, archival, and deletion of user gamification data
when the module is disabled or re-enabled.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.models.gamification import (
    UserGamificationProfile,
    UserAchievement,
    UserStreak,
    UserChallenge,
    PointHistory,
    DataRetentionPolicy
)

logger = logging.getLogger(__name__)


class DataRetentionManager:
    """
    Manages data retention policies for gamification data.
    
    Supports three retention policies:
    - PRESERVE: Keep data when disabled, restore when re-enabled
    - ARCHIVE: Archive data when disabled, can be restored later
    - DELETE: Delete data when disabled (permanent)
    """

    def __init__(self, db: Session):
        self.db = db

    async def apply_retention_policy(
        self,
        profile_id: int,
        policy: DataRetentionPolicy,
        action: str = "disable"  # "disable" or "enable"
    ) -> bool:
        """
        Apply the specified retention policy to a user's gamification data.
        
        Args:
            profile_id: The ID of the user's gamification profile
            policy: The retention policy to apply
            action: Whether this is for disabling ("disable") or enabling ("enable")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.id == profile_id
            ).first()
            
            if not profile:
                logger.warning(f"Profile {profile_id} not found")
                return False
            
            logger.info(f"Applying {policy.value} retention policy for profile {profile_id} on {action}")
            
            if action == "disable":
                if policy == DataRetentionPolicy.DELETE:
                    return await self._delete_all_data(profile_id)
                elif policy == DataRetentionPolicy.ARCHIVE:
                    return await self._archive_all_data(profile_id)
                elif policy == DataRetentionPolicy.PRESERVE:
                    return await self._preserve_all_data(profile_id)
            elif action == "enable":
                if policy == DataRetentionPolicy.ARCHIVE:
                    return await self._restore_archived_data(profile_id)
                elif policy == DataRetentionPolicy.PRESERVE:
                    # Data should already be preserved, nothing to do
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying retention policy: {str(e)}")
            return False

    async def _preserve_all_data(self, profile_id: int) -> bool:
        """
        Preserve all gamification data when disabling.
        Data remains in the database and is restored when re-enabled.
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.id == profile_id
            ).first()
            
            if not profile:
                return False
            
            # Mark data as preserved in preferences
            if not profile.preferences:
                profile.preferences = {}
            
            profile.preferences["data_preserved_at"] = datetime.now(timezone.utc).isoformat()
            profile.preferences["retention_policy"] = DataRetentionPolicy.PRESERVE.value
            
            self.db.commit()
            logger.info(f"Data preserved for profile {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error preserving data for profile {profile_id}: {str(e)}")
            self.db.rollback()
            return False

    async def _archive_all_data(self, profile_id: int) -> bool:
        """
        Archive all gamification data when disabling.
        Data is moved to archive tables and can be restored later.
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.id == profile_id
            ).first()
            
            if not profile:
                return False
            
            # Create archive snapshot in preferences
            if not profile.preferences:
                profile.preferences = {}
            
            archive_data = {
                "archived_at": datetime.now(timezone.utc).isoformat(),
                "retention_policy": DataRetentionPolicy.ARCHIVE.value,
                "snapshot": {
                    "level": profile.level,
                    "total_experience_points": profile.total_experience_points,
                    "current_level_progress": profile.current_level_progress,
                    "financial_health_score": profile.financial_health_score,
                    "statistics": profile.statistics,
                    "achievements_count": len(profile.achievements),
                    "streaks_count": len(profile.streaks),
                    "challenges_count": len(profile.challenges),
                    "point_history_count": len(profile.point_history)
                }
            }
            
            profile.preferences["archived_data"] = archive_data
            
            self.db.commit()
            logger.info(f"Data archived for profile {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving data for profile {profile_id}: {str(e)}")
            self.db.rollback()
            return False

    async def _delete_all_data(self, profile_id: int) -> bool:
        """
        Delete all gamification data when disabling with DELETE policy.
        This is permanent and cannot be recovered.
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.id == profile_id
            ).first()
            
            if not profile:
                return False
            
            # Store deletion timestamp for audit purposes
            if not profile.preferences:
                profile.preferences = {}
            
            profile.preferences["data_deleted_at"] = datetime.now(timezone.utc).isoformat()
            profile.preferences["retention_policy"] = DataRetentionPolicy.DELETE.value
            
            # Delete all related data
            deleted_counts = {
                "achievements": 0,
                "streaks": 0,
                "challenges": 0,
                "point_history": 0
            }
            
            # Delete achievements
            achievements = self.db.query(UserAchievement).filter(
                UserAchievement.profile_id == profile_id
            ).all()
            deleted_counts["achievements"] = len(achievements)
            for achievement in achievements:
                self.db.delete(achievement)
            
            # Delete streaks
            streaks = self.db.query(UserStreak).filter(
                UserStreak.profile_id == profile_id
            ).all()
            deleted_counts["streaks"] = len(streaks)
            for streak in streaks:
                self.db.delete(streak)
            
            # Delete challenges
            challenges = self.db.query(UserChallenge).filter(
                UserChallenge.profile_id == profile_id
            ).all()
            deleted_counts["challenges"] = len(challenges)
            for challenge in challenges:
                self.db.delete(challenge)
            
            # Delete point history
            point_history = self.db.query(PointHistory).filter(
                PointHistory.profile_id == profile_id
            ).all()
            deleted_counts["point_history"] = len(point_history)
            for history in point_history:
                self.db.delete(history)
            
            # Reset profile statistics
            profile.level = 1
            profile.total_experience_points = 0
            profile.current_level_progress = 0.0
            profile.financial_health_score = 0.0
            profile.statistics = {
                "totalActionsCompleted": 0,
                "expensesTracked": 0,
                "invoicesCreated": 0,
                "receiptsUploaded": 0,
                "budgetReviews": 0,
                "longestStreak": 0,
                "achievementsUnlocked": 0,
                "challengesCompleted": 0
            }
            
            self.db.commit()
            logger.info(f"Data deleted for profile {profile_id}: {deleted_counts}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting data for profile {profile_id}: {str(e)}")
            self.db.rollback()
            return False

    async def _restore_archived_data(self, profile_id: int) -> bool:
        """
        Restore archived gamification data when re-enabling with ARCHIVE policy.
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.id == profile_id
            ).first()
            
            if not profile:
                return False
            
            if not profile.preferences or "archived_data" not in profile.preferences:
                logger.warning(f"No archived data found for profile {profile_id}")
                return True  # Not an error, just nothing to restore
            
            archived_data = profile.preferences.get("archived_data", {})
            snapshot = archived_data.get("snapshot", {})
            
            # Restore profile data from snapshot
            profile.level = snapshot.get("level", 1)
            profile.total_experience_points = snapshot.get("total_experience_points", 0)
            profile.current_level_progress = snapshot.get("current_level_progress", 0.0)
            profile.financial_health_score = snapshot.get("financial_health_score", 0.0)
            profile.statistics = snapshot.get("statistics", {})
            
            # Remove archived data marker
            if "archived_data" in profile.preferences:
                del profile.preferences["archived_data"]
            
            profile.preferences["data_restored_at"] = datetime.now(timezone.utc).isoformat()
            
            self.db.commit()
            logger.info(f"Data restored for profile {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring archived data for profile {profile_id}: {str(e)}")
            self.db.rollback()
            return False

    async def get_data_retention_status(self, profile_id: int) -> Dict[str, Any]:
        """
        Get the current data retention status for a profile.
        
        Returns:
            Dict containing retention policy, data counts, and status information
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.id == profile_id
            ).first()
            
            if not profile:
                return {
                    "profile_found": False,
                    "status": "not_found"
                }
            
            # Count data
            achievements_count = self.db.query(UserAchievement).filter(
                UserAchievement.profile_id == profile_id
            ).count()
            
            streaks_count = self.db.query(UserStreak).filter(
                UserStreak.profile_id == profile_id
            ).count()
            
            challenges_count = self.db.query(UserChallenge).filter(
                UserChallenge.profile_id == profile_id
            ).count()
            
            point_history_count = self.db.query(PointHistory).filter(
                PointHistory.profile_id == profile_id
            ).count()
            
            # Get retention policy info
            preferences = profile.preferences or {}
            retention_policy = profile.data_retention_policy.value if profile.data_retention_policy else "unknown"
            
            status = {
                "profile_found": True,
                "profile_id": profile_id,
                "module_enabled": profile.module_enabled,
                "retention_policy": retention_policy,
                "data_counts": {
                    "achievements": achievements_count,
                    "streaks": streaks_count,
                    "challenges": challenges_count,
                    "point_history": point_history_count,
                    "total": achievements_count + streaks_count + challenges_count + point_history_count
                },
                "profile_state": {
                    "level": profile.level,
                    "total_experience_points": profile.total_experience_points,
                    "financial_health_score": profile.financial_health_score
                },
                "timestamps": {
                    "enabled_at": profile.enabled_at.isoformat() if profile.enabled_at else None,
                    "disabled_at": profile.disabled_at.isoformat() if profile.disabled_at else None,
                    "created_at": profile.created_at.isoformat() if profile.created_at else None,
                    "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
                },
                "retention_info": {
                    "data_preserved_at": preferences.get("data_preserved_at"),
                    "data_archived_at": preferences.get("archived_data", {}).get("archived_at"),
                    "data_deleted_at": preferences.get("data_deleted_at"),
                    "data_restored_at": preferences.get("data_restored_at")
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting retention status for profile {profile_id}: {str(e)}")
            return {
                "profile_found": False,
                "error": str(e)
            }

    async def validate_data_consistency(self, profile_id: int) -> Dict[str, Any]:
        """
        Validate data consistency for a profile based on its retention policy.
        
        Returns:
            Dict containing validation results and any issues found
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.id == profile_id
            ).first()
            
            if not profile:
                return {
                    "valid": False,
                    "issues": ["Profile not found"]
                }
            
            issues = []
            
            # Check consistency based on retention policy
            if profile.data_retention_policy == DataRetentionPolicy.DELETE and not profile.module_enabled:
                # If deleted and disabled, should have minimal data
                achievements_count = self.db.query(UserAchievement).filter(
                    UserAchievement.profile_id == profile_id
                ).count()
                
                streaks_count = self.db.query(UserStreak).filter(
                    UserStreak.profile_id == profile_id
                ).count()
                
                challenges_count = self.db.query(UserChallenge).filter(
                    UserChallenge.profile_id == profile_id
                ).count()
                
                point_history_count = self.db.query(PointHistory).filter(
                    PointHistory.profile_id == profile_id
                ).count()
                
                if achievements_count > 0:
                    issues.append(f"DELETE policy but {achievements_count} achievements remain")
                if streaks_count > 0:
                    issues.append(f"DELETE policy but {streaks_count} streaks remain")
                if challenges_count > 0:
                    issues.append(f"DELETE policy but {challenges_count} challenges remain")
                if point_history_count > 0:
                    issues.append(f"DELETE policy but {point_history_count} point history records remain")
            
            # Check timestamp consistency
            if profile.module_enabled and profile.disabled_at:
                issues.append("Module enabled but disabled_at timestamp is set")
            
            if not profile.module_enabled and not profile.disabled_at:
                issues.append("Module disabled but disabled_at timestamp is not set")
            
            # Check profile state consistency
            if profile.level < 1:
                issues.append(f"Invalid level: {profile.level}")
            
            if profile.total_experience_points < 0:
                issues.append(f"Negative experience points: {profile.total_experience_points}")
            
            if not (0 <= profile.current_level_progress <= 100):
                issues.append(f"Invalid level progress: {profile.current_level_progress}")
            
            if not (0 <= profile.financial_health_score <= 100):
                issues.append(f"Invalid financial health score: {profile.financial_health_score}")
            
            return {
                "valid": len(issues) == 0,
                "profile_id": profile_id,
                "module_enabled": profile.module_enabled,
                "retention_policy": profile.data_retention_policy.value if profile.data_retention_policy else "unknown",
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Error validating data consistency for profile {profile_id}: {str(e)}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"]
            }

    async def migrate_data_on_policy_change(
        self,
        profile_id: int,
        old_policy: DataRetentionPolicy,
        new_policy: DataRetentionPolicy
    ) -> bool:
        """
        Migrate data when retention policy is changed.
        
        Args:
            profile_id: The ID of the user's gamification profile
            old_policy: The previous retention policy
            new_policy: The new retention policy
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.id == profile_id
            ).first()
            
            if not profile:
                return False
            
            logger.info(f"Migrating data for profile {profile_id} from {old_policy.value} to {new_policy.value}")
            
            # If changing from DELETE to something else, we can't recover deleted data
            if old_policy == DataRetentionPolicy.DELETE and new_policy != DataRetentionPolicy.DELETE:
                logger.warning(f"Cannot recover deleted data for profile {profile_id}")
                return True  # Not an error, just can't recover
            
            # If changing from ARCHIVE to PRESERVE, restore archived data
            if old_policy == DataRetentionPolicy.ARCHIVE and new_policy == DataRetentionPolicy.PRESERVE:
                return await self._restore_archived_data(profile_id)
            
            # If changing to ARCHIVE, archive current data
            if new_policy == DataRetentionPolicy.ARCHIVE:
                return await self._archive_all_data(profile_id)
            
            # Update policy in profile
            profile.data_retention_policy = new_policy
            self.db.commit()
            
            logger.info(f"Successfully migrated data for profile {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating data for profile {profile_id}: {str(e)}")
            self.db.rollback()
            return False
