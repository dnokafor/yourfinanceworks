"""
Team Gamification Features Service

This service handles team-level gamification features including leaderboards,
group challenges, and team-based analytics.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, asc

from core.models.gamification import (
    UserGamificationProfile,
    UserChallenge,
    Challenge,
    ChallengeType,
    PointHistory,
    UserStreak,
    UserAchievement
)
from core.models.models_per_tenant import User

logger = logging.getLogger(__name__)


class TeamGamificationFeatures:
    """
    Service for managing team-level gamification features.
    """

    def __init__(self, db: Session):
        self.db = db

    # Leaderboard Features
    async def get_team_leaderboard(
        self,
        organization_id: int,
        limit: int = 100,
        metric: str = "xp"  # "xp", "level", "achievements", "streaks"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get team leaderboard ranked by specified metric.
        Respects user privacy settings.
        """
        try:
            # Get all users in the organization
            org_users = self.db.query(User).filter(
                User.organization_id == organization_id
            ).all()

            if not org_users:
                return []

            user_ids = [u.id for u in org_users]

            # Get gamification profiles for users who have opted in to leaderboards
            profiles = self.db.query(UserGamificationProfile).filter(
                and_(
                    UserGamificationProfile.user_id.in_(user_ids),
                    UserGamificationProfile.module_enabled == True
                )
            ).all()

            leaderboard_data = []

            for profile in profiles:
                # Check if user has opted in to leaderboard
                privacy_settings = profile.preferences.get("privacy", {})
                if not privacy_settings.get("showOnLeaderboard", False):
                    continue

                # Get user info
                user = self.db.query(User).filter(User.id == profile.user_id).first()
                if not user:
                    continue

                # Calculate metrics
                stats = profile.statistics or {}
                achievements_count = self.db.query(func.count(UserAchievement.id)).filter(
                    and_(
                        UserAchievement.profile_id == profile.id,
                        UserAchievement.is_completed == True
                    )
                ).scalar() or 0

                active_streaks = self.db.query(func.count(UserStreak.id)).filter(
                    and_(
                        UserStreak.profile_id == profile.id,
                        UserStreak.is_active == True,
                        UserStreak.current_length > 0
                    )
                ).scalar() or 0

                entry = {
                    "user_id": profile.user_id,
                    "user_name": user.name or f"User {user.id}",
                    "level": profile.level,
                    "total_xp": profile.total_experience_points,
                    "achievements_unlocked": achievements_count,
                    "active_streaks": active_streaks,
                    "financial_health_score": profile.financial_health_score,
                    "total_actions": stats.get("totalActionsCompleted", 0)
                }

                leaderboard_data.append(entry)

            # Sort by specified metric
            if metric == "xp":
                leaderboard_data.sort(key=lambda x: x["total_xp"], reverse=True)
            elif metric == "level":
                leaderboard_data.sort(key=lambda x: (x["level"], x["total_xp"]), reverse=True)
            elif metric == "achievements":
                leaderboard_data.sort(key=lambda x: x["achievements_unlocked"], reverse=True)
            elif metric == "streaks":
                leaderboard_data.sort(key=lambda x: x["active_streaks"], reverse=True)
            elif metric == "health":
                leaderboard_data.sort(key=lambda x: x["financial_health_score"], reverse=True)

            # Add rank
            for rank, entry in enumerate(leaderboard_data[:limit], 1):
                entry["rank"] = rank

            return leaderboard_data[:limit]

        except Exception as e:
            logger.error(f"Error getting team leaderboard for org {organization_id}: {str(e)}")
            return None

    async def get_user_leaderboard_position(
        self,
        user_id: int,
        organization_id: int,
        metric: str = "xp"
    ) -> Optional[Dict[str, Any]]:
        """Get a user's position on the team leaderboard"""
        try:
            leaderboard = await self.get_team_leaderboard(organization_id, limit=10000, metric=metric)

            if not leaderboard:
                return None

            for entry in leaderboard:
                if entry["user_id"] == user_id:
                    return entry

            return None

        except Exception as e:
            logger.error(f"Error getting leaderboard position for user {user_id}: {str(e)}")
            return None

    async def get_team_leaderboard_by_department(
        self,
        organization_id: int,
        department: str,
        limit: int = 50
    ) -> Optional[List[Dict[str, Any]]]:
        """Get leaderboard for a specific department within an organization"""
        try:
            # Get users in the department
            dept_users = self.db.query(User).filter(
                and_(
                    User.organization_id == organization_id,
                    User.department == department  # Assumes User model has department field
                )
            ).all()

            if not dept_users:
                return []

            user_ids = [u.id for u in dept_users]

            # Get gamification profiles
            profiles = self.db.query(UserGamificationProfile).filter(
                and_(
                    UserGamificationProfile.user_id.in_(user_ids),
                    UserGamificationProfile.module_enabled == True
                )
            ).all()

            leaderboard_data = []

            for profile in profiles:
                # Check privacy settings
                privacy_settings = profile.preferences.get("privacy", {})
                if not privacy_settings.get("showOnLeaderboard", False):
                    continue

                user = self.db.query(User).filter(User.id == profile.user_id).first()
                if not user:
                    continue

                achievements_count = self.db.query(func.count(UserAchievement.id)).filter(
                    and_(
                        UserAchievement.profile_id == profile.id,
                        UserAchievement.is_completed == True
                    )
                ).scalar() or 0

                entry = {
                    "user_id": profile.user_id,
                    "user_name": user.name or f"User {user.id}",
                    "level": profile.level,
                    "total_xp": profile.total_experience_points,
                    "achievements_unlocked": achievements_count,
                    "financial_health_score": profile.financial_health_score
                }

                leaderboard_data.append(entry)

            # Sort by XP
            leaderboard_data.sort(key=lambda x: x["total_xp"], reverse=True)

            # Add rank
            for rank, entry in enumerate(leaderboard_data[:limit], 1):
                entry["rank"] = rank

            return leaderboard_data[:limit]

        except Exception as e:
            logger.error(f"Error getting department leaderboard: {str(e)}")
            return None

    # Group Challenges
    async def create_group_challenge(
        self,
        organization_id: int,
        challenge_data: Dict[str, Any],
        created_by: int
    ) -> Optional[Dict[str, Any]]:
        """Create a group challenge for an organization"""
        try:
            # Validate required fields
            required_fields = ["name", "description", "duration_days", "requirements", "reward_xp"]
            if not all(field in challenge_data for field in required_fields):
                logger.error("Missing required fields for group challenge")
                return None

            # Create challenge
            challenge = Challenge(
                challenge_id=f"group_{organization_id}_{datetime.now(timezone.utc).timestamp()}",
                name=challenge_data["name"],
                description=challenge_data["description"],
                challenge_type=ChallengeType.COMMUNITY,
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
            logger.error(f"Error creating group challenge: {str(e)}")
            self.db.rollback()
            return None

    async def get_group_challenges(
        self,
        organization_id: int,
        active_only: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Get all group challenges for an organization"""
        try:
            query = self.db.query(Challenge).filter(
                and_(
                    Challenge.organization_id == organization_id,
                    Challenge.challenge_type == ChallengeType.COMMUNITY
                )
            )

            if active_only:
                query = query.filter(Challenge.is_active == True)

            challenges = query.all()

            return [
                {
                    "id": c.id,
                    "challenge_id": c.challenge_id,
                    "name": c.name,
                    "description": c.description,
                    "type": c.challenge_type.value,
                    "duration_days": c.duration_days,
                    "requirements": c.requirements,
                    "reward_xp": c.reward_xp,
                    "is_active": c.is_active,
                    "start_date": c.start_date.isoformat(),
                    "end_date": c.end_date.isoformat()
                }
                for c in challenges
            ]

        except Exception as e:
            logger.error(f"Error getting group challenges for org {organization_id}: {str(e)}")
            return None

    async def get_group_challenge_progress(
        self,
        challenge_id: int,
        organization_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get progress information for a group challenge"""
        try:
            challenge = self.db.query(Challenge).filter(
                and_(
                    Challenge.id == challenge_id,
                    Challenge.organization_id == organization_id
                )
            ).first()

            if not challenge:
                return None

            # Get all participants
            participants = self.db.query(UserChallenge).filter(
                UserChallenge.challenge_id == challenge_id
            ).all()

            total_participants = len(participants)
            completed_count = sum(1 for p in participants if p.is_completed)
            completion_rate = (completed_count / total_participants * 100) if total_participants > 0 else 0

            # Get top performers
            top_performers = sorted(
                [
                    {
                        "user_id": p.profile.user_id,
                        "progress": p.progress,
                        "completed": p.is_completed
                    }
                    for p in participants
                ],
                key=lambda x: x["progress"],
                reverse=True
            )[:10]

            return {
                "challenge_id": challenge.challenge_id,
                "name": challenge.name,
                "description": challenge.description,
                "total_participants": total_participants,
                "completed": completed_count,
                "completion_rate": completion_rate,
                "top_performers": top_performers,
                "start_date": challenge.start_date.isoformat(),
                "end_date": challenge.end_date.isoformat(),
                "time_remaining_days": max(0, (challenge.end_date - datetime.now(timezone.utc)).days)
            }

        except Exception as e:
            logger.error(f"Error getting group challenge progress: {str(e)}")
            return None

    # Team Analytics
    async def get_team_performance_summary(
        self,
        organization_id: int,
        time_range_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Get a summary of team performance metrics"""
        try:
            org_users = self.db.query(User).filter(
                User.organization_id == organization_id
            ).all()

            if not org_users:
                return {
                    "total_users": 0,
                    "active_users": 0,
                    "average_level": 0,
                    "average_xp": 0,
                    "total_achievements": 0,
                    "average_health_score": 0,
                    "engagement_trend": []
                }

            user_ids = [u.id for u in org_users]

            # Get active profiles
            profiles = self.db.query(UserGamificationProfile).filter(
                and_(
                    UserGamificationProfile.user_id.in_(user_ids),
                    UserGamificationProfile.module_enabled == True
                )
            ).all()

            total_users = len(org_users)
            active_users = len(profiles)

            if not profiles:
                return {
                    "total_users": total_users,
                    "active_users": 0,
                    "average_level": 0,
                    "average_xp": 0,
                    "total_achievements": 0,
                    "average_health_score": 0,
                    "engagement_trend": []
                }

            # Calculate averages
            avg_level = sum(p.level for p in profiles) / len(profiles)
            avg_xp = sum(p.total_experience_points for p in profiles) / len(profiles)
            avg_health_score = sum(p.financial_health_score for p in profiles) / len(profiles)

            # Total achievements
            total_achievements = self.db.query(func.count(UserAchievement.id)).filter(
                and_(
                    UserAchievement.profile_id.in_([p.id for p in profiles]),
                    UserAchievement.is_completed == True
                )
            ).scalar() or 0

            # Engagement trend (daily active users over time)
            start_date = datetime.now(timezone.utc) - timedelta(days=time_range_days)
            engagement_trend = []

            for i in range(0, time_range_days, 7):
                period_start = start_date + timedelta(days=i)
                period_end = period_start + timedelta(days=7)

                active_in_period = self.db.query(func.count(func.distinct(PointHistory.profile_id))).filter(
                    and_(
                        PointHistory.created_at >= period_start,
                        PointHistory.created_at < period_end,
                        PointHistory.profile_id.in_([p.id for p in profiles])
                    )
                ).scalar() or 0

                engagement_trend.append({
                    "date": period_start.isoformat(),
                    "active_users": active_in_period
                })

            return {
                "total_users": total_users,
                "active_users": active_users,
                "average_level": round(avg_level, 2),
                "average_xp": round(avg_xp, 2),
                "total_achievements": total_achievements,
                "average_health_score": round(avg_health_score, 2),
                "engagement_trend": engagement_trend
            }

        except Exception as e:
            logger.error(f"Error getting team performance summary: {str(e)}")
            return None

    async def get_team_habit_formation_report(
        self,
        organization_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get a report on team habit formation progress"""
        try:
            org_users = self.db.query(User).filter(
                User.organization_id == organization_id
            ).all()

            if not org_users:
                return {
                    "total_users": 0,
                    "habit_formation_stages": {},
                    "most_common_habits": [],
                    "habit_strength_distribution": {}
                }

            user_ids = [u.id for u in org_users]

            # Get active profiles
            profiles = self.db.query(UserGamificationProfile).filter(
                and_(
                    UserGamificationProfile.user_id.in_(user_ids),
                    UserGamificationProfile.module_enabled == True
                )
            ).all()

            # Categorize users by habit formation stage
            habit_stages = {
                "beginner": 0,      # Level 1-5
                "intermediate": 0,  # Level 6-15
                "advanced": 0,      # Level 16-30
                "expert": 0         # Level 31+
            }

            for profile in profiles:
                if profile.level <= 5:
                    habit_stages["beginner"] += 1
                elif profile.level <= 15:
                    habit_stages["intermediate"] += 1
                elif profile.level <= 30:
                    habit_stages["advanced"] += 1
                else:
                    habit_stages["expert"] += 1

            # Get most common habits (based on streak tracking)
            habit_counts = self.db.query(
                UserStreak.habit_type,
                func.count(UserStreak.id).label("count"),
                func.avg(UserStreak.current_length).label("avg_length")
            ).filter(
                UserStreak.profile_id.in_([p.id for p in profiles])
            ).group_by(UserStreak.habit_type).all()

            most_common_habits = [
                {
                    "habit": h.habit_type.value,
                    "users_tracking": h.count,
                    "average_streak_length": round(h.avg_length or 0, 1)
                }
                for h in habit_counts
            ]

            # Sort by count
            most_common_habits.sort(key=lambda x: x["users_tracking"], reverse=True)

            return {
                "total_users": len(org_users),
                "active_users": len(profiles),
                "habit_formation_stages": habit_stages,
                "most_common_habits": most_common_habits,
                "percentage_with_active_streaks": round(
                    (sum(1 for p in profiles if any(s.is_active for s in p.streaks)) / len(profiles) * 100)
                    if profiles else 0,
                    2
                )
            }

        except Exception as e:
            logger.error(f"Error getting team habit formation report: {str(e)}")
            return None
