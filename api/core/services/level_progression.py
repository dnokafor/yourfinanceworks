"""
Level progression system for the gamification module.

This module handles level calculations, level-up detection, celebration triggers,
and progress tracking to the next level.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from core.models.gamification import UserGamificationProfile
from core.schemas.gamification import UserGamificationProfileResponse

logger = logging.getLogger(__name__)


class LevelProgressionSystem:
    """
    Handles all level progression logic for the gamification system.
    
    Features:
    - Dynamic level calculation based on accumulated XP
    - Level-up detection and celebration triggers
    - Progress tracking to next level
    - Customizable level curves
    - Level milestone rewards
    """

    # Level progression configuration
    BASE_XP_PER_LEVEL = 1000  # XP required for level 1 to 2
    LEVEL_CURVE_MULTIPLIER = 1.2  # Each level requires 20% more XP than previous
    MAX_LEVEL = 100  # Maximum achievable level
    
    # Level milestone rewards (bonus XP for reaching certain levels)
    LEVEL_MILESTONES = {
        5: 100,    # Bonus XP for reaching level 5
        10: 250,   # Bonus XP for reaching level 10
        25: 500,   # Bonus XP for reaching level 25
        50: 1000,  # Bonus XP for reaching level 50
        75: 2000,  # Bonus XP for reaching level 75
        100: 5000  # Bonus XP for reaching level 100
    }
    
    # Celebration types for different level achievements
    CELEBRATION_TYPES = {
        "level_up": "standard",
        "milestone": "special",
        "major_milestone": "epic"
    }

    def __init__(self, db: Session):
        self.db = db

    async def calculate_level_from_xp(self, total_xp: int) -> int:
        """
        Calculate user level based on total experience points.
        
        Uses a progressive curve where each level requires more XP than the previous.
        Formula: level = floor(log(total_xp / base_xp + 1) / log(multiplier)) + 1
        """
        try:
            if total_xp <= 0:
                return 1
            
            # Use iterative approach for more predictable results
            level = 1
            xp_required = 0
            
            while level < self.MAX_LEVEL:
                xp_for_next_level = self._calculate_xp_for_level(level + 1)
                if total_xp < xp_for_next_level:
                    break
                level += 1
            
            return min(level, self.MAX_LEVEL)
            
        except Exception as e:
            logger.error(f"Error calculating level from XP {total_xp}: {str(e)}")
            return 1

    def _calculate_xp_for_level(self, target_level: int) -> int:
        """Calculate total XP required to reach a specific level"""
        if target_level <= 1:
            return 0
        
        total_xp = 0
        for level in range(2, target_level + 1):
            # Each level requires base_xp * (multiplier ^ (level - 2))
            xp_for_this_level = int(self.BASE_XP_PER_LEVEL * (self.LEVEL_CURVE_MULTIPLIER ** (level - 2)))
            total_xp += xp_for_this_level
        
        return total_xp

    async def calculate_level_progress(self, profile: UserGamificationProfile) -> Dict[str, Any]:
        """
        Calculate detailed level progress information for a user.
        
        Returns progress to next level, XP needed, and percentage complete.
        """
        try:
            current_level = profile.level
            total_xp = profile.total_experience_points
            
            # Calculate XP thresholds
            xp_for_current_level = self._calculate_xp_for_level(current_level)
            xp_for_next_level = self._calculate_xp_for_level(current_level + 1)
            
            # Calculate progress within current level
            xp_progress_in_level = total_xp - xp_for_current_level
            xp_needed_for_next = xp_for_next_level - total_xp
            xp_required_for_level = xp_for_next_level - xp_for_current_level
            
            # Calculate percentage progress
            if xp_required_for_level > 0:
                progress_percentage = (xp_progress_in_level / xp_required_for_level) * 100
            else:
                progress_percentage = 100.0
            
            # Ensure we don't exceed 100% or go below 0%
            progress_percentage = max(0.0, min(100.0, progress_percentage))
            
            return {
                "current_level": current_level,
                "total_xp": total_xp,
                "xp_for_current_level": xp_for_current_level,
                "xp_for_next_level": xp_for_next_level,
                "xp_progress_in_level": xp_progress_in_level,
                "xp_needed_for_next": max(0, xp_needed_for_next),
                "xp_required_for_level": xp_required_for_level,
                "progress_percentage": progress_percentage,
                "is_max_level": current_level >= self.MAX_LEVEL
            }
            
        except Exception as e:
            logger.error(f"Error calculating level progress for profile {profile.id}: {str(e)}")
            return {
                "current_level": profile.level,
                "total_xp": profile.total_experience_points,
                "xp_for_current_level": 0,
                "xp_for_next_level": 1000,
                "xp_progress_in_level": 0,
                "xp_needed_for_next": 1000,
                "xp_required_for_level": 1000,
                "progress_percentage": 0.0,
                "is_max_level": False
            }

    async def check_level_up(
        self, 
        profile: UserGamificationProfile, 
        points_awarded: int
    ) -> Optional[Dict[str, Any]]:
        """
        Check if user should level up after receiving points.
        
        Returns level-up information if a level up occurred, None otherwise.
        """
        try:
            old_level = profile.level
            old_total_xp = profile.total_experience_points
            new_total_xp = old_total_xp + points_awarded
            
            # Calculate new level
            new_level = await self.calculate_level_from_xp(new_total_xp)
            
            if new_level > old_level:
                # Level up occurred!
                profile.level = new_level
                profile.total_experience_points = new_total_xp
                
                # Update level progress
                level_progress = await self.calculate_level_progress(profile)
                profile.current_level_progress = level_progress["progress_percentage"]
                
                # Check for milestone rewards
                milestone_bonus = 0
                celebration_type = "level_up"
                
                for milestone_level, bonus_xp in self.LEVEL_MILESTONES.items():
                    if old_level < milestone_level <= new_level:
                        milestone_bonus += bonus_xp
                        if milestone_level in [10, 25, 50, 75, 100]:
                            celebration_type = "major_milestone"
                        else:
                            celebration_type = "milestone"
                
                # Apply milestone bonus
                if milestone_bonus > 0:
                    profile.total_experience_points += milestone_bonus
                    new_total_xp += milestone_bonus
                    logger.info(f"Milestone bonus: +{milestone_bonus} XP for reaching level {new_level}")
                
                # Prepare level-up result
                level_up_result = {
                    "old_level": old_level,
                    "new_level": new_level,
                    "levels_gained": new_level - old_level,
                    "milestone_bonus": milestone_bonus,
                    "celebration_type": celebration_type,
                    "xp_before": old_total_xp,
                    "xp_after": new_total_xp,
                    "xp_gained": points_awarded,
                    "level_progress": level_progress,
                    "is_milestone": new_level in self.LEVEL_MILESTONES,
                    "milestone_levels": [level for level in self.LEVEL_MILESTONES.keys() 
                                       if old_level < level <= new_level]
                }
                
                logger.info(f"Level up! User profile {profile.id}: {old_level} → {new_level}")
                return level_up_result
            
            else:
                # No level up, just update progress
                profile.total_experience_points = new_total_xp
                level_progress = await self.calculate_level_progress(profile)
                profile.current_level_progress = level_progress["progress_percentage"]
                return None
                
        except Exception as e:
            logger.error(f"Error checking level up for profile {profile.id}: {str(e)}")
            # Ensure XP is still updated even on error
            profile.total_experience_points = profile.total_experience_points + points_awarded
            return None

    async def get_level_rewards_info(self, level: int) -> Dict[str, Any]:
        """Get information about rewards and benefits for a specific level"""
        try:
            rewards = {
                "level": level,
                "milestone_bonus": self.LEVEL_MILESTONES.get(level, 0),
                "is_milestone": level in self.LEVEL_MILESTONES,
                "benefits": []
            }
            
            # Add level-specific benefits
            if level >= 5:
                rewards["benefits"].append("Unlocked achievement categories")
            if level >= 10:
                rewards["benefits"].append("Access to weekly challenges")
            if level >= 25:
                rewards["benefits"].append("Social features available")
            if level >= 50:
                rewards["benefits"].append("Custom challenge creation")
            if level >= 75:
                rewards["benefits"].append("Advanced analytics dashboard")
            if level >= 100:
                rewards["benefits"].append("Master level status")
            
            return rewards
            
        except Exception as e:
            logger.error(f"Error getting level rewards info for level {level}: {str(e)}")
            return {
                "level": level,
                "milestone_bonus": 0,
                "is_milestone": False,
                "benefits": []
            }

    async def get_celebration_config(self, level_up_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get celebration configuration based on level-up result.
        
        Returns configuration for UI celebration animations and messages.
        """
        try:
            celebration_type = level_up_result.get("celebration_type", "level_up")
            new_level = level_up_result.get("new_level", 1)
            levels_gained = level_up_result.get("levels_gained", 1)
            milestone_bonus = level_up_result.get("milestone_bonus", 0)
            
            config = {
                "type": celebration_type,
                "duration": 3000,  # milliseconds
                "animation": "level_up",
                "sound": "level_up_sound",
                "message": f"Level Up! You reached level {new_level}!",
                "show_confetti": True,
                "show_badge": True,
                "auto_dismiss": True
            }
            
            # Customize based on celebration type
            if celebration_type == "milestone":
                config.update({
                    "duration": 5000,
                    "animation": "milestone_celebration",
                    "sound": "milestone_sound",
                    "message": f"Milestone Achieved! Level {new_level} reached!",
                    "show_fireworks": True
                })
                
                if milestone_bonus > 0:
                    config["message"] += f" Bonus: +{milestone_bonus} XP!"
            
            elif celebration_type == "major_milestone":
                config.update({
                    "duration": 8000,
                    "animation": "epic_celebration",
                    "sound": "epic_sound",
                    "message": f"Epic Achievement! Level {new_level} conquered!",
                    "show_fireworks": True,
                    "show_special_effects": True,
                    "auto_dismiss": False  # Let user dismiss manually
                })
                
                if milestone_bonus > 0:
                    config["message"] += f" Epic Bonus: +{milestone_bonus} XP!"
            
            # Multi-level ups
            if levels_gained > 1:
                config["message"] = f"Amazing! {levels_gained} levels gained! Now level {new_level}!"
                config["duration"] = min(config["duration"] * levels_gained, 10000)
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting celebration config: {str(e)}")
            return {
                "type": "level_up",
                "duration": 3000,
                "animation": "level_up",
                "sound": "level_up_sound",
                "message": "Level Up!",
                "show_confetti": True,
                "show_badge": True,
                "auto_dismiss": True
            }

    async def get_leaderboard_level_distribution(self) -> Dict[str, Any]:
        """Get distribution of users across different levels for analytics"""
        try:
            # This would query the database for level distribution
            # For now, return a placeholder structure
            return {
                "total_users": 0,
                "level_distribution": {},
                "average_level": 0.0,
                "max_level_achieved": 1
            }
            
        except Exception as e:
            logger.error(f"Error getting level distribution: {str(e)}")
            return {
                "total_users": 0,
                "level_distribution": {},
                "average_level": 0.0,
                "max_level_achieved": 1
            }

    def get_level_curve_info(self) -> Dict[str, Any]:
        """Get information about the level progression curve"""
        return {
            "base_xp_per_level": self.BASE_XP_PER_LEVEL,
            "curve_multiplier": self.LEVEL_CURVE_MULTIPLIER,
            "max_level": self.MAX_LEVEL,
            "milestones": self.LEVEL_MILESTONES,
            "sample_xp_requirements": {
                level: self._calculate_xp_for_level(level) 
                for level in [1, 5, 10, 25, 50, 75, 100]
            }
        }