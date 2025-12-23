"""
Organization Gamification Administration Service

This service handles organization-level gamification configuration and administration,
including custom point values, achievement thresholds, team features, and analytics.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from core.models.gamification import (
    OrganizationGamificationConfig,
    UserGamificationProfile,
    PointHistory,
    UserAchievement,
    UserChallenge,
    Challenge,
    ChallengeType
)
from core.models.models_per_tenant import User

logger = logging.getLogger(__name__)


class OrganizationGamificationAdmin:
    """
    Service for managing organization-level gamification settings and analytics.
    """

    def __init__(self, db: Session):
        self.db = db

    # Configuration Management
    async def get_organization_config(self, organization_id: int) -> Optional[Dict[str, Any]]:
        """Get the gamification configuration for an organization"""
        try:
            config = self.db.query(OrganizationGamificationConfig).filter(
                OrganizationGamificationConfig.organization_id == organization_id
            ).first()

            if not config:
                # Return default configuration if none exists
                return await self._create_default_config(organization_id)

            return self._config_to_dict(config)

        except Exception as e:
            logger.error(f"Error getting organization config for org {organization_id}: {str(e)}")
            return None

    async def create_organization_config(
        self,
        organization_id: int,
        created_by: int,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new gamification configuration for an organization"""
        try:
            # Check if config already exists
            existing = self.db.query(OrganizationGamificationConfig).filter(
                OrganizationGamificationConfig.organization_id == organization_id
            ).first()

            if existing:
                logger.warning(f"Config already exists for organization {organization_id}")
                return self._config_to_dict(existing)

            # Create new config with defaults
            config = OrganizationGamificationConfig(
                organization_id=organization_id,
                enabled=True,
                created_by=created_by,
                updated_by=created_by
            )

            # Apply custom settings if provided
            if custom_settings:
                if "custom_point_values" in custom_settings:
                    config.custom_point_values = {
                        **config.custom_point_values,
                        **custom_settings["custom_point_values"]
                    }
                if "achievement_thresholds" in custom_settings:
                    config.achievement_thresholds = {
                        **config.achievement_thresholds,
                        **custom_settings["achievement_thresholds"]
                    }
                if "enabled_features" in custom_settings:
                    config.enabled_features = {
                        **config.enabled_features,
                        **custom_settings["enabled_features"]
                    }
                if "team_settings" in custom_settings:
                    config.team_settings = {
                        **config.team_settings,
                        **custom_settings["team_settings"]
                    }
                if "policy_alignment" in custom_settings:
                    config.policy_alignment = {
                        **config.policy_alignment,
                        **custom_settings["policy_alignment"]
                    }

            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)

            return self._config_to_dict(config)

        except Exception as e:
            logger.error(f"Error creating organization config for org {organization_id}: {str(e)}")
            self.db.rollback()
            return None

    async def update_point_values(
        self,
        organization_id: int,
        point_values: Dict[str, int],
        updated_by: int
    ) -> Optional[Dict[str, Any]]:
        """Update custom point values for an organization"""
        try:
            config = self.db.query(OrganizationGamificationConfig).filter(
                OrganizationGamificationConfig.organization_id == organization_id
            ).first()

            if not config:
                config = await self._create_default_config(organization_id)
                if not config:
                    return None
                config = self.db.query(OrganizationGamificationConfig).filter(
                    OrganizationGamificationConfig.organization_id == organization_id
                ).first()

            # Validate point values are within reasonable ranges
            validated_values = {}
            for key, value in point_values.items():
                if isinstance(value, int) and 1 <= value <= 1000:
                    validated_values[key] = value
                else:
                    logger.warning(f"Invalid point value for {key}: {value}")

            if validated_values:
                config.custom_point_values = {
                    **config.custom_point_values,
                    **validated_values
                }
                config.updated_by = updated_by
                config.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(config)

            return self._config_to_dict(config)

        except Exception as e:
            logger.error(f"Error updating point values for org {organization_id}: {str(e)}")
            self.db.rollback()
            return None

    async def set_achievement_thresholds(
        self,
        organization_id: int,
        thresholds: Dict[str, Any],
        updated_by: int
    ) -> Optional[Dict[str, Any]]:
        """Update achievement thresholds for an organization"""
        try:
            config = self.db.query(OrganizationGamificationConfig).filter(
                OrganizationGamificationConfig.organization_id == organization_id
            ).first()

            if not config:
                config = await self._create_default_config(organization_id)
                if not config:
                    return None
                config = self.db.query(OrganizationGamificationConfig).filter(
                    OrganizationGamificationConfig.organization_id == organization_id
                ).first()

            # Validate and update thresholds
            validated_thresholds = {}
            for key, value in thresholds.items():
                if key == "budgetAdherenceThreshold":
                    if isinstance(value, (int, float)) and 0 <= value <= 100:
                        validated_thresholds[key] = value
                elif key.endswith("Milestones"):
                    if isinstance(value, list) and all(isinstance(v, int) and v > 0 for v in value):
                        validated_thresholds[key] = sorted(value)
                else:
                    validated_thresholds[key] = value

            if validated_thresholds:
                config.achievement_thresholds = {
                    **config.achievement_thresholds,
                    **validated_thresholds
                }
                config.updated_by = updated_by
                config.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(config)

            return self._config_to_dict(config)

        except Exception as e:
            logger.error(f"Error setting achievement thresholds for org {organization_id}: {str(e)}")
            self.db.rollback()
            return None

    async def enable_feature_for_org(
        self,
        organization_id: int,
        feature: str,
        enabled: bool,
        updated_by: int
    ) -> Optional[Dict[str, Any]]:
        """Enable or disable a specific gamification feature for an organization"""
        try:
            config = self.db.query(OrganizationGamificationConfig).filter(
                OrganizationGamificationConfig.organization_id == organization_id
            ).first()

            if not config:
                config = await self._create_default_config(organization_id)
                if not config:
                    return None
                config = self.db.query(OrganizationGamificationConfig).filter(
                    OrganizationGamificationConfig.organization_id == organization_id
                ).first()

            # Update feature status
            if feature in config.enabled_features:
                config.enabled_features[feature] = enabled
                config.updated_by = updated_by
                config.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(config)

            return self._config_to_dict(config)

        except Exception as e:
            logger.error(f"Error enabling feature {feature} for org {organization_id}: {str(e)}")
            self.db.rollback()
            return None

    async def create_custom_challenge(
        self,
        organization_id: int,
        challenge_data: Dict[str, Any],
        created_by: int
    ) -> Optional[Dict[str, Any]]:
        """Create a custom challenge for an organization"""
        try:
            # Validate required fields
            required_fields = ["name", "description", "type", "duration_days", "requirements", "reward_xp"]
            if not all(field in challenge_data for field in required_fields):
                logger.error(f"Missing required fields for custom challenge")
                return None

            # Create challenge
            challenge = Challenge(
                challenge_id=f"org_{organization_id}_{datetime.now(timezone.utc).timestamp()}",
                name=challenge_data["name"],
                description=challenge_data["description"],
                challenge_type=ChallengeType[challenge_data["type"].upper()],
                duration_days=challenge_data["duration_days"],
                requirements=challenge_data["requirements"],
                reward_xp=challenge_data["reward_xp"],
                reward_badge_url=challenge_data.get("reward_badge_url"),
                organization_id=organization_id,
                is_active=True,
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc) + timedelta(days=challenge_data["duration_days"])
            )

            self.db.add(challenge)
            self.db.commit()
            self.db.refresh(challenge)

            return {
                "id": challenge.id,
                "challenge_id": challenge.challenge_id,
                "name": challenge.name,
                "description": challenge.description,
                "type": challenge.challenge_type.value,
                "duration_days": challenge.duration_days,
                "requirements": challenge.requirements,
                "reward_xp": challenge.reward_xp,
                "organization_id": challenge.organization_id,
                "is_active": challenge.is_active,
                "start_date": challenge.start_date.isoformat(),
                "end_date": challenge.end_date.isoformat()
            }

        except Exception as e:
            logger.error(f"Error creating custom challenge for org {organization_id}: {str(e)}")
            self.db.rollback()
            return None

    # Team Features and Analytics
    async def get_team_analytics(
        self,
        organization_id: int,
        time_range_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive team analytics for an organization"""
        try:
            # Get all users in the organization
            org_users = self.db.query(User).filter(
                User.organization_id == organization_id
            ).all()

            if not org_users:
                return {
                    "total_active_users": 0,
                    "average_engagement_score": 0,
                    "habit_formation_progress": [],
                    "top_performing_teams": [],
                    "challenge_completion_rates": [],
                    "financial_health_trends": []
                }

            user_ids = [u.id for u in org_users]

            # Calculate metrics
            start_date = datetime.now(timezone.utc) - timedelta(days=time_range_days)

            # Active users with gamification enabled
            active_users = self.db.query(UserGamificationProfile).filter(
                and_(
                    UserGamificationProfile.user_id.in_(user_ids),
                    UserGamificationProfile.module_enabled == True
                )
            ).all()

            total_active_users = len(active_users)

            # Average engagement score (based on points earned)
            point_stats = self.db.query(
                func.avg(UserGamificationProfile.total_experience_points).label("avg_xp"),
                func.avg(UserGamificationProfile.level).label("avg_level")
            ).filter(
                UserGamificationProfile.user_id.in_(user_ids)
            ).first()

            avg_xp = point_stats.avg_xp or 0
            avg_level = point_stats.avg_level or 1

            # Normalize engagement score (0-100)
            average_engagement_score = min(100, (avg_xp / 1000) * 100) if avg_xp else 0

            # Habit formation progress
            habit_progress = []
            for profile in active_users:
                if profile.statistics:
                    habit_progress.append({
                        "user_id": profile.user_id,
                        "level": profile.level,
                        "total_xp": profile.total_experience_points,
                        "achievements_unlocked": profile.statistics.get("achievementsUnlocked", 0),
                        "longest_streak": profile.statistics.get("longestStreak", 0)
                    })

            # Challenge completion rates
            challenge_stats = self.db.query(
                Challenge.challenge_id,
                Challenge.name,
                func.count(UserChallenge.id).label("total_participants"),
                func.sum(func.cast(UserChallenge.is_completed, type_=int)).label("completed_count")
            ).join(
                UserChallenge,
                Challenge.id == UserChallenge.challenge_id,
                isouter=True
            ).filter(
                Challenge.organization_id == organization_id,
                Challenge.created_at >= start_date
            ).group_by(Challenge.id, Challenge.challenge_id, Challenge.name).all()

            challenge_completion_rates = []
            for stat in challenge_stats:
                completion_rate = 0
                if stat.total_participants and stat.total_participants > 0:
                    completion_rate = (stat.completed_count or 0) / stat.total_participants * 100

                challenge_completion_rates.append({
                    "challenge_id": stat.challenge_id,
                    "challenge_name": stat.name,
                    "total_participants": stat.total_participants or 0,
                    "completed": stat.completed_count or 0,
                    "completion_rate": completion_rate
                })

            # Financial health trends
            health_scores = [p.financial_health_score for p in active_users if p.financial_health_score]
            avg_health_score = sum(health_scores) / len(health_scores) if health_scores else 0

            financial_health_trends = [
                {
                    "date": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(),
                    "average_score": avg_health_score
                }
                for i in range(0, time_range_days, 7)
            ]

            return {
                "total_active_users": total_active_users,
                "average_engagement_score": round(average_engagement_score, 2),
                "average_level": round(avg_level, 2),
                "habit_formation_progress": habit_progress,
                "challenge_completion_rates": challenge_completion_rates,
                "financial_health_trends": financial_health_trends,
                "time_range_days": time_range_days
            }

        except Exception as e:
            logger.error(f"Error getting team analytics for org {organization_id}: {str(e)}")
            return None

    async def get_engagement_metrics(self, organization_id: int) -> Optional[Dict[str, Any]]:
        """Get engagement metrics for an organization"""
        try:
            org_users = self.db.query(User).filter(
                User.organization_id == organization_id
            ).all()

            if not org_users:
                return {
                    "daily_active_users": 0,
                    "weekly_active_users": 0,
                    "average_session_duration": 0,
                    "feature_usage_stats": {},
                    "habit_consistency_scores": {}
                }

            user_ids = [u.id for u in org_users]

            # Daily active users (users with activity in last 24 hours)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            daily_active = self.db.query(func.count(func.distinct(PointHistory.profile_id))).filter(
                and_(
                    PointHistory.created_at >= yesterday,
                    PointHistory.profile_id.in_(
                        self.db.query(UserGamificationProfile.id).filter(
                            UserGamificationProfile.user_id.in_(user_ids)
                        )
                    )
                )
            ).scalar() or 0

            # Weekly active users (users with activity in last 7 days)
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            weekly_active = self.db.query(func.count(func.distinct(PointHistory.profile_id))).filter(
                and_(
                    PointHistory.created_at >= week_ago,
                    PointHistory.profile_id.in_(
                        self.db.query(UserGamificationProfile.id).filter(
                            UserGamificationProfile.user_id.in_(user_ids)
                        )
                    )
                )
            ).scalar() or 0

            # Feature usage stats
            feature_usage = self.db.query(
                PointHistory.action_type,
                func.count(PointHistory.id).label("count"),
                func.sum(PointHistory.points_awarded).label("total_points")
            ).filter(
                PointHistory.profile_id.in_(
                    self.db.query(UserGamificationProfile.id).filter(
                        UserGamificationProfile.user_id.in_(user_ids)
                    )
                )
            ).group_by(PointHistory.action_type).all()

            feature_usage_stats = {
                stat.action_type: {
                    "count": stat.count,
                    "total_points": stat.total_points
                }
                for stat in feature_usage
            }

            # Habit consistency scores
            profiles = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id.in_(user_ids)
            ).all()

            habit_consistency_scores = {}
            for profile in profiles:
                if profile.statistics:
                    total_actions = profile.statistics.get("totalActionsCompleted", 0)
                    if total_actions > 0:
                        consistency_score = min(100, (total_actions / 100) * 100)
                        habit_consistency_scores[f"user_{profile.user_id}"] = consistency_score

            return {
                "daily_active_users": daily_active,
                "weekly_active_users": weekly_active,
                "average_session_duration": 0,  # Would need session tracking
                "feature_usage_stats": feature_usage_stats,
                "habit_consistency_scores": habit_consistency_scores
            }

        except Exception as e:
            logger.error(f"Error getting engagement metrics for org {organization_id}: {str(e)}")
            return None

    # Preference Hierarchy
    async def resolve_user_preferences(
        self,
        user_id: int,
        organization_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve user preferences respecting the hierarchy:
        User Privacy > Organization Policy > System Defaults
        """
        try:
            # Get user profile
            user_profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not user_profile:
                return None

            # Get organization config
            org_config = self.db.query(OrganizationGamificationConfig).filter(
                OrganizationGamificationConfig.organization_id == organization_id
            ).first()

            # Start with system defaults
            resolved_preferences = {
                "point_values": {
                    "expenseTracking": 10,
                    "invoiceCreation": 15,
                    "budgetReview": 20,
                    "receiptUpload": 3,
                    "categoryAccuracy": 5,
                    "timelyReminders": 8,
                    "promptPaymentMarking": 12
                },
                "enabled_features": {
                    "points": True,
                    "achievements": True,
                    "streaks": True,
                    "challenges": True,
                    "leaderboards": False,
                    "teamChallenges": False,
                    "socialSharing": False,
                    "notifications": True
                },
                "privacy_settings": {
                    "shareAchievements": False,
                    "showOnLeaderboard": False,
                    "allowFriendRequests": False
                }
            }

            # Apply organization settings (if org config exists)
            if org_config:
                resolved_preferences["point_values"] = {
                    **resolved_preferences["point_values"],
                    **org_config.custom_point_values
                }
                resolved_preferences["enabled_features"] = {
                    **resolved_preferences["enabled_features"],
                    **org_config.enabled_features
                }

            # Apply user preferences (always override for privacy settings)
            if user_profile.preferences:
                user_prefs = user_profile.preferences
                if "features" in user_prefs:
                    resolved_preferences["enabled_features"] = {
                        **resolved_preferences["enabled_features"],
                        **user_prefs["features"]
                    }
                if "privacy" in user_prefs:
                    # Privacy settings are always user-controlled
                    resolved_preferences["privacy_settings"] = user_prefs["privacy"]

            return resolved_preferences

        except Exception as e:
            logger.error(f"Error resolving user preferences for user {user_id}: {str(e)}")
            return None

    async def get_effective_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the effective gamification settings for a user"""
        try:
            user_profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()

            if not user_profile:
                return None

            # Get user's organization (would need to be added to User model)
            # For now, return user's preferences
            return {
                "enabled": user_profile.module_enabled,
                "preferences": user_profile.preferences,
                "statistics": user_profile.statistics,
                "level": user_profile.level,
                "total_xp": user_profile.total_experience_points
            }

        except Exception as e:
            logger.error(f"Error getting effective settings for user {user_id}: {str(e)}")
            return None

    # Private Helper Methods
    async def _create_default_config(self, organization_id: int) -> Optional[Dict[str, Any]]:
        """Create a default configuration for an organization"""
        try:
            config = OrganizationGamificationConfig(
                organization_id=organization_id,
                enabled=True
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            return self._config_to_dict(config)
        except Exception as e:
            logger.error(f"Error creating default config for org {organization_id}: {str(e)}")
            self.db.rollback()
            return None

    def _config_to_dict(self, config: OrganizationGamificationConfig) -> Dict[str, Any]:
        """Convert OrganizationGamificationConfig to dictionary"""
        return {
            "id": config.id,
            "organization_id": config.organization_id,
            "enabled": config.enabled,
            "custom_point_values": config.custom_point_values,
            "achievement_thresholds": config.achievement_thresholds,
            "enabled_features": config.enabled_features,
            "team_settings": config.team_settings,
            "policy_alignment": config.policy_alignment,
            "created_by": config.created_by,
            "updated_by": config.updated_by,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
