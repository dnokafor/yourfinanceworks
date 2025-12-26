#!/usr/bin/env python3
"""
Unit test for achievement engine functionality.
Tests the achievement engine without requiring database connections.
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

# Add the parent directory to the path so we can import from the API
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.achievement_engine import AchievementEngine
from core.models.gamification import (
    AchievementCategory, 
    AchievementDifficulty,
    UserGamificationProfile,
    Achievement,
    UserAchievement,
    UserStreak,
    HabitType
)
from core.schemas.gamification import FinancialEvent, ActionType


class TestAchievementEngine(unittest.TestCase):
    """Test cases for the Achievement Engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.achievement_engine = AchievementEngine(self.mock_db)

    def test_achievement_definitions_completeness(self):
        """Test that all required achievement definitions are present"""
        definitions = self.achievement_engine._get_achievement_definitions()
        
        # Check that we have achievements
        self.assertGreater(len(definitions), 0, "Should have achievement definitions")
        
        # Check all required categories are present
        categories = set(defn["category"] for defn in definitions)
        expected_categories = {
            AchievementCategory.EXPENSE_TRACKING,
            AchievementCategory.INVOICE_MANAGEMENT,
            AchievementCategory.HABIT_FORMATION,
            AchievementCategory.FINANCIAL_HEALTH,
            AchievementCategory.EXPLORATION
        }
        self.assertEqual(categories, expected_categories, "All achievement categories should be present")
        
        # Check specific milestone achievements exist
        achievement_ids = [defn["achievement_id"] for defn in definitions]
        
        # Expense tracking milestones (Requirements 2.5)
        expected_expense_achievements = [
            "expense_tracker_first", "expense_tracker_10", "expense_tracker_50", 
            "expense_tracker_100", "expense_tracker_500"
        ]
        for achievement_id in expected_expense_achievements:
            self.assertIn(achievement_id, achievement_ids, f"Should have {achievement_id}")
        
        # Invoice management milestones (Requirements 3.5)
        expected_invoice_achievements = [
            "invoice_creator_first", "invoice_creator_10", "invoice_creator_100"
        ]
        for achievement_id in expected_invoice_achievements:
            self.assertIn(achievement_id, achievement_ids, f"Should have {achievement_id}")
        
        # Streak milestones (Requirements 4.5)
        expected_streak_achievements = [
            "streak_warrior_7", "streak_warrior_30", "streak_warrior_90", "streak_warrior_365"
        ]
        for achievement_id in expected_streak_achievements:
            self.assertIn(achievement_id, achievement_ids, f"Should have {achievement_id}")

    def test_achievement_difficulty_levels(self):
        """Test that achievements have proper difficulty levels (Requirements 5.7)"""
        definitions = self.achievement_engine._get_achievement_definitions()
        
        # Check that all difficulty levels are used
        difficulties = set(defn["difficulty"] for defn in definitions)
        expected_difficulties = {
            AchievementDifficulty.BRONZE,
            AchievementDifficulty.SILVER,
            AchievementDifficulty.GOLD,
            AchievementDifficulty.PLATINUM
        }
        self.assertEqual(difficulties, expected_difficulties, "All difficulty levels should be used")
        
        # Check that first achievements are Bronze
        first_achievements = [defn for defn in definitions if "first" in defn["achievement_id"]]
        for achievement in first_achievements:
            self.assertEqual(achievement["difficulty"], AchievementDifficulty.BRONZE, 
                           "First achievements should be Bronze difficulty")

    def test_achievement_requirements_structure(self):
        """Test that achievement requirements are properly structured"""
        definitions = self.achievement_engine._get_achievement_definitions()
        
        for defn in definitions:
            # Each achievement should have requirements
            self.assertIn("requirements", defn, f"Achievement {defn['achievement_id']} should have requirements")
            self.assertIsInstance(defn["requirements"], list, "Requirements should be a list")
            self.assertGreater(len(defn["requirements"]), 0, "Should have at least one requirement")
            
            # Each requirement should have type and target
            for req in defn["requirements"]:
                self.assertIn("type", req, "Requirement should have type")
                self.assertIn("target", req, "Requirement should have target")
                self.assertIsInstance(req["target"], (int, float), "Target should be numeric")

    def test_achievement_rewards(self):
        """Test that achievements have proper rewards"""
        definitions = self.achievement_engine._get_achievement_definitions()
        
        for defn in definitions:
            # Each achievement should have XP reward
            self.assertIn("reward_xp", defn, f"Achievement {defn['achievement_id']} should have XP reward")
            self.assertGreater(defn["reward_xp"], 0, "XP reward should be positive")
            
            # Higher difficulty should generally have higher rewards
            if defn["difficulty"] == AchievementDifficulty.PLATINUM:
                self.assertGreaterEqual(defn["reward_xp"], 500, "Platinum achievements should have high XP")

    @patch('core.services.achievement_engine.logger')
    def test_calculate_achievement_progress_expense_count(self, mock_logger):
        """Test progress calculation for expense count achievements"""
        # Create mock profile with statistics
        mock_profile = Mock()
        mock_profile.statistics = {"expensesTracked": 25}
        
        # Create mock achievement for 50 expenses
        mock_achievement = Mock()
        mock_achievement.requirements = [{"type": "expense_count", "target": 50}]
        
        # Test progress calculation
        import asyncio
        progress = asyncio.run(self.achievement_engine._calculate_achievement_progress(mock_profile, mock_achievement))
        
        # Should be 50% progress (25/50 * 100)
        self.assertEqual(progress, 50.0, "Progress should be 50% for 25/50 expenses")

    @patch('core.services.achievement_engine.logger')
    def test_calculate_achievement_progress_level_reached(self, mock_logger):
        """Test progress calculation for level-based achievements"""
        # Create mock profile at level 8
        mock_profile = Mock()
        mock_profile.level = 8
        
        # Create mock achievement for level 10
        mock_achievement = Mock()
        mock_achievement.requirements = [{"type": "level_reached", "target": 10}]
        
        # Test progress calculation
        import asyncio
        progress = asyncio.run(self.achievement_engine._calculate_achievement_progress(mock_profile, mock_achievement))
        
        # Should be 0% progress (not reached yet)
        self.assertEqual(progress, 0.0, "Progress should be 0% for level not yet reached")
        
        # Test when level is reached
        mock_profile.level = 10
        progress = asyncio.run(self.achievement_engine._calculate_achievement_progress(mock_profile, mock_achievement))
        self.assertEqual(progress, 100.0, "Progress should be 100% when level is reached")

    def test_achievement_categories_coverage(self):
        """Test that all required achievement categories are covered (Requirements 5.1-5.5)"""
        definitions = self.achievement_engine._get_achievement_definitions()
        
        # Group by category
        by_category = {}
        for defn in definitions:
            category = defn["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(defn)
        
        # Check expense tracking achievements (Requirements 5.1)
        expense_achievements = by_category.get(AchievementCategory.EXPENSE_TRACKING, [])
        self.assertGreater(len(expense_achievements), 0, "Should have expense tracking achievements")
        
        # Check invoice management achievements (Requirements 5.2)
        invoice_achievements = by_category.get(AchievementCategory.INVOICE_MANAGEMENT, [])
        self.assertGreater(len(invoice_achievements), 0, "Should have invoice management achievements")
        
        # Check habit formation achievements (Requirements 5.4)
        habit_achievements = by_category.get(AchievementCategory.HABIT_FORMATION, [])
        self.assertGreater(len(habit_achievements), 0, "Should have habit formation achievements")
        
        # Check financial health achievements (Requirements 5.3)
        health_achievements = by_category.get(AchievementCategory.FINANCIAL_HEALTH, [])
        self.assertGreater(len(health_achievements), 0, "Should have financial health achievements")
        
        # Check exploration achievements (Requirements 5.5)
        exploration_achievements = by_category.get(AchievementCategory.EXPLORATION, [])
        self.assertGreater(len(exploration_achievements), 0, "Should have exploration achievements")

    def test_milestone_detection_logic(self):
        """Test that milestone detection logic works correctly"""
        # This tests the core logic without database dependencies
        definitions = self.achievement_engine._get_achievement_definitions()
        
        # Find expense milestone achievements
        expense_milestones = [
            defn for defn in definitions 
            if defn["category"] == AchievementCategory.EXPENSE_TRACKING 
            and any(req["type"] == "expense_count" for req in defn["requirements"])
        ]
        
        # Should have the required milestones: 1, 10, 50, 100, 500
        targets = []
        for achievement in expense_milestones:
            for req in achievement["requirements"]:
                if req["type"] == "expense_count":
                    targets.append(req["target"])
        
        expected_targets = [1, 10, 50, 100, 500]
        for target in expected_targets:
            self.assertIn(target, targets, f"Should have expense milestone for {target} expenses")


if __name__ == "__main__":
    print("🧪 Running Achievement Engine Unit Tests")
    print("=" * 50)
    
    # Run the tests
    unittest.main(verbosity=2)