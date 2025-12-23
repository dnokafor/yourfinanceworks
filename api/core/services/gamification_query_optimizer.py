"""
Query optimization service for gamification system.

This module provides optimized database queries for frequently accessed data,
particularly for leaderboards and aggregated statistics. It includes:
- Optimized leaderboard queries with pagination
- Efficient streak aggregation
- Challenge progress aggregation
- Financial health score batch calculations
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, select, text
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)


class GamificationQueryOptimizer:
    """
    Provides optimized database queries for gamification data.
    
    Uses efficient SQL patterns, proper indexing, and pagination
    to minimize database load for frequently accessed data.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # Leaderboard Queries
    def get_global_leaderboard(
        self,
        limit: int = 100,
        offset: int = 0,
        include_stats: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get global leaderboard with optimized query.
        
        Args:
            limit: Number of results to return
            offset: Pagination offset
            include_stats: Whether to include detailed statistics
            
        Returns:
            List of leaderboard entries
        """
        try:
            from core.models.gamification import UserGamificationProfile
            from core.models.models import User
            
            # Base query with pagination
            query = self.db.query(
                UserGamificationProfile.user_id,
                UserGamificationProfile.level,
                UserGamificationProfile.total_experience_points,
                UserGamificationProfile.financial_health_score,
                User.email
            ).join(
                User, UserGamificationProfile.user_id == User.id
            ).filter(
                UserGamificationProfile.module_enabled == True
            ).order_by(
                desc(UserGamificationProfile.total_experience_points),
                desc(UserGamificationProfile.level)
            ).offset(offset).limit(limit)
            
            results = []
            for idx, (user_id, level, xp, health_score, email) in enumerate(query.all(), start=offset + 1):
                entry = {
                    "rank": idx,
                    "user_id": user_id,
                    "email": email,
                    "level": level,
                    "experience_points": xp,
                    "financial_health_score": health_score
                }
                
                if include_stats:
                    # Get additional stats
                    stats = self._get_user_stats(user_id)
                    entry.update(stats)
                
                results.append(entry)
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting global leaderboard: {str(e)}")
            return []
    
    def get_organization_leaderboard(
        self,
        org_id: int,
        limit: int = 100,
        offset: int = 0,
        include_stats: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get organization-specific leaderboard.
        
        Args:
            org_id: Organization ID
            limit: Number of results to return
            offset: Pagination offset
            include_stats: Whether to include detailed statistics
            
        Returns:
            List of leaderboard entries
        """
        try:
            from core.models.gamification import UserGamificationProfile
            from core.models.models import User, UserOrganization
            
            # Query with organization filter
            query = self.db.query(
                UserGamificationProfile.user_id,
                UserGamificationProfile.level,
                UserGamificationProfile.total_experience_points,
                UserGamificationProfile.financial_health_score,
                User.email
            ).join(
                User, UserGamificationProfile.user_id == User.id
            ).join(
                UserOrganization, User.id == UserOrganization.user_id
            ).filter(
                and_(
                    UserOrganization.organization_id == org_id,
                    UserGamificationProfile.module_enabled == True
                )
            ).order_by(
                desc(UserGamificationProfile.total_experience_points),
                desc(UserGamificationProfile.level)
            ).offset(offset).limit(limit)
            
            results = []
            for idx, (user_id, level, xp, health_score, email) in enumerate(query.all(), start=offset + 1):
                entry = {
                    "rank": idx,
                    "user_id": user_id,
                    "email": email,
                    "level": level,
                    "experience_points": xp,
                    "financial_health_score": health_score
                }
                
                if include_stats:
                    stats = self._get_user_stats(user_id)
                    entry.update(stats)
                
                results.append(entry)
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting organization leaderboard: {str(e)}")
            return []
    
    def get_user_leaderboard_rank(
        self,
        user_id: int,
        org_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a user's rank on the leaderboard.
        
        Args:
            user_id: User ID
            org_id: Organization ID (for org-specific rank)
            
        Returns:
            User's rank information or None
        """
        try:
            from core.models.gamification import UserGamificationProfile
            from core.models.models import User, UserOrganization
            
            # Get user's XP
            user_profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not user_profile or not user_profile.module_enabled:
                return None
            
            # Count users with higher XP
            if org_id:
                rank = self.db.query(func.count(UserGamificationProfile.id)).join(
                    User, UserGamificationProfile.user_id == User.id
                ).join(
                    UserOrganization, User.id == UserOrganization.user_id
                ).filter(
                    and_(
                        UserOrganization.organization_id == org_id,
                        UserGamificationProfile.module_enabled == True,
                        UserGamificationProfile.total_experience_points > user_profile.total_experience_points
                    )
                ).scalar() + 1
            else:
                rank = self.db.query(func.count(UserGamificationProfile.id)).filter(
                    and_(
                        UserGamificationProfile.module_enabled == True,
                        UserGamificationProfile.total_experience_points > user_profile.total_experience_points
                    )
                ).scalar() + 1
            
            return {
                "user_id": user_id,
                "rank": rank,
                "level": user_profile.level,
                "experience_points": user_profile.total_experience_points,
                "financial_health_score": user_profile.financial_health_score
            }
        
        except Exception as e:
            logger.error(f"Error getting user leaderboard rank: {str(e)}")
            return None
    
    # Streak Aggregation
    def get_active_streaks_summary(
        self,
        org_id: Optional[int] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Get summary of active streaks across users.
        
        Args:
            org_id: Organization ID (optional)
            limit: Maximum number of users to include
            
        Returns:
            Streak summary statistics
        """
        try:
            from core.models.gamification import UserStreak, UserGamificationProfile, HabitType
            from core.models.models import User, UserOrganization
            
            # Build base query
            query = self.db.query(
                UserStreak.habit_type,
                func.count(UserStreak.id).label("active_count"),
                func.avg(UserStreak.current_length).label("avg_length"),
                func.max(UserStreak.current_length).label("max_length"),
                func.max(UserStreak.longest_length).label("max_longest")
            ).join(
                UserGamificationProfile, UserStreak.profile_id == UserGamificationProfile.id
            ).filter(
                and_(
                    UserStreak.is_active == True,
                    UserStreak.current_length > 0,
                    UserGamificationProfile.module_enabled == True
                )
            )
            
            # Add organization filter if provided
            if org_id:
                query = query.join(
                    User, UserGamificationProfile.user_id == User.id
                ).join(
                    UserOrganization, User.id == UserOrganization.user_id
                ).filter(UserOrganization.organization_id == org_id)
            
            # Group by habit type
            query = query.group_by(UserStreak.habit_type)
            
            results = {}
            for habit_type, count, avg_len, max_len, max_longest in query.all():
                results[habit_type.value] = {
                    "active_users": count,
                    "average_length": float(avg_len) if avg_len else 0,
                    "max_current_length": max_len or 0,
                    "max_longest_length": max_longest or 0
                }
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting active streaks summary: {str(e)}")
            return {}
    
    # Challenge Progress Aggregation
    def get_challenge_completion_stats(
        self,
        challenge_id: int,
        org_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get completion statistics for a challenge.
        
        Args:
            challenge_id: Challenge ID
            org_id: Organization ID (optional)
            
        Returns:
            Challenge completion statistics
        """
        try:
            from core.models.gamification import UserChallenge, Challenge, UserGamificationProfile
            from core.models.models import User, UserOrganization
            
            # Get challenge info
            challenge = self.db.query(Challenge).filter(
                Challenge.id == challenge_id
            ).first()
            
            if not challenge:
                return {}
            
            # Build query for participants
            query = self.db.query(
                func.count(UserChallenge.id).label("total_participants"),
                func.sum(
                    func.cast(UserChallenge.is_completed, type_=int)
                ).label("completed_count"),
                func.avg(UserChallenge.progress).label("avg_progress")
            ).filter(
                and_(
                    UserChallenge.challenge_id == challenge_id,
                    UserChallenge.opted_in == True
                )
            )
            
            # Add organization filter if provided
            if org_id:
                query = query.join(
                    UserGamificationProfile, UserChallenge.profile_id == UserGamificationProfile.id
                ).join(
                    User, UserGamificationProfile.user_id == User.id
                ).join(
                    UserOrganization, User.id == UserOrganization.user_id
                ).filter(UserOrganization.organization_id == org_id)
            
            result = query.first()
            
            if result:
                total, completed, avg_progress = result
                completion_rate = (completed / total * 100) if total and completed else 0
                
                return {
                    "challenge_id": challenge_id,
                    "challenge_name": challenge.name,
                    "total_participants": total or 0,
                    "completed": completed or 0,
                    "completion_rate": completion_rate,
                    "average_progress": float(avg_progress) if avg_progress else 0
                }
            
            return {}
        
        except Exception as e:
            logger.error(f"Error getting challenge completion stats: {str(e)}")
            return {}
    
    # Financial Health Score Batch Calculation
    def get_health_score_distribution(
        self,
        org_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get distribution of financial health scores.
        
        Args:
            org_id: Organization ID (optional)
            
        Returns:
            Health score distribution statistics
        """
        try:
            from core.models.gamification import UserGamificationProfile
            from core.models.models import User, UserOrganization
            
            # Build query
            query = self.db.query(
                func.count(UserGamificationProfile.id).label("total_users"),
                func.avg(UserGamificationProfile.financial_health_score).label("avg_score"),
                func.min(UserGamificationProfile.financial_health_score).label("min_score"),
                func.max(UserGamificationProfile.financial_health_score).label("max_score"),
                func.stddev(UserGamificationProfile.financial_health_score).label("stddev_score")
            ).filter(
                UserGamificationProfile.module_enabled == True
            )
            
            # Add organization filter if provided
            if org_id:
                query = query.join(
                    User, UserGamificationProfile.user_id == User.id
                ).join(
                    UserOrganization, User.id == UserOrganization.user_id
                ).filter(UserOrganization.organization_id == org_id)
            
            result = query.first()
            
            if result:
                total, avg, min_score, max_score, stddev = result
                
                # Get score distribution buckets
                buckets = self._get_score_distribution_buckets(org_id)
                
                return {
                    "total_users": total or 0,
                    "average_score": float(avg) if avg else 0,
                    "min_score": float(min_score) if min_score else 0,
                    "max_score": float(max_score) if max_score else 0,
                    "stddev": float(stddev) if stddev else 0,
                    "distribution_buckets": buckets
                }
            
            return {}
        
        except Exception as e:
            logger.error(f"Error getting health score distribution: {str(e)}")
            return {}
    
    def _get_score_distribution_buckets(self, org_id: Optional[int] = None) -> Dict[str, int]:
        """Get distribution of users across score buckets"""
        try:
            from core.models.gamification import UserGamificationProfile
            from core.models.models import User, UserOrganization
            
            buckets = {
                "0-20": 0,
                "21-40": 0,
                "41-60": 0,
                "61-80": 0,
                "81-100": 0
            }
            
            # Query for each bucket
            for bucket_name, min_score, max_score in [
                ("0-20", 0, 20),
                ("21-40", 21, 40),
                ("41-60", 41, 60),
                ("61-80", 61, 80),
                ("81-100", 81, 100)
            ]:
                query = self.db.query(func.count(UserGamificationProfile.id)).filter(
                    and_(
                        UserGamificationProfile.module_enabled == True,
                        UserGamificationProfile.financial_health_score >= min_score,
                        UserGamificationProfile.financial_health_score <= max_score
                    )
                )
                
                if org_id:
                    query = query.join(
                        User, UserGamificationProfile.user_id == User.id
                    ).join(
                        UserOrganization, User.id == UserOrganization.user_id
                    ).filter(UserOrganization.organization_id == org_id)
                
                count = query.scalar() or 0
                buckets[bucket_name] = count
            
            return buckets
        
        except Exception as e:
            logger.error(f"Error getting score distribution buckets: {str(e)}")
            return {}
    
    # Helper Methods
    def _get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get additional statistics for a user"""
        try:
            from core.models.gamification import UserGamificationProfile, UserStreak, UserAchievement
            
            profile = self.db.query(UserGamificationProfile).filter(
                UserGamificationProfile.user_id == user_id
            ).first()
            
            if not profile:
                return {}
            
            # Get active streaks count
            active_streaks = self.db.query(func.count(UserStreak.id)).filter(
                and_(
                    UserStreak.profile_id == profile.id,
                    UserStreak.is_active == True,
                    UserStreak.current_length > 0
                )
            ).scalar() or 0
            
            # Get achievements count
            achievements = self.db.query(func.count(UserAchievement.id)).filter(
                and_(
                    UserAchievement.profile_id == profile.id,
                    UserAchievement.is_completed == True
                )
            ).scalar() or 0
            
            return {
                "active_streaks": active_streaks,
                "achievements_unlocked": achievements
            }
        
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {}
    
    def get_engagement_metrics(
        self,
        org_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get engagement metrics for the organization or globally.
        
        Args:
            org_id: Organization ID (optional)
            days: Number of days to look back
            
        Returns:
            Engagement metrics
        """
        try:
            from core.models.gamification import PointHistory, UserGamificationProfile
            from core.models.models import User, UserOrganization
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Count active users (those who earned points in the period)
            query = self.db.query(
                func.count(func.distinct(PointHistory.profile_id)).label("active_users"),
                func.count(PointHistory.id).label("total_actions"),
                func.sum(PointHistory.points_awarded).label("total_points")
            ).filter(
                PointHistory.created_at >= cutoff_date
            )
            
            if org_id:
                query = query.join(
                    UserGamificationProfile, PointHistory.profile_id == UserGamificationProfile.id
                ).join(
                    User, UserGamificationProfile.user_id == User.id
                ).join(
                    UserOrganization, User.id == UserOrganization.user_id
                ).filter(UserOrganization.organization_id == org_id)
            
            result = query.first()
            
            if result:
                active_users, total_actions, total_points = result
                
                return {
                    "period_days": days,
                    "active_users": active_users or 0,
                    "total_actions": total_actions or 0,
                    "total_points_awarded": total_points or 0,
                    "average_points_per_action": (total_points / total_actions) if total_actions else 0,
                    "average_actions_per_user": (total_actions / active_users) if active_users else 0
                }
            
            return {}
        
        except Exception as e:
            logger.error(f"Error getting engagement metrics: {str(e)}")
            return {}


def get_query_optimizer(db: Session) -> GamificationQueryOptimizer:
    """Get a query optimizer instance"""
    return GamificationQueryOptimizer(db)
