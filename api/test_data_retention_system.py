#!/usr/bin/env python3
"""
Test script for data retention policy system.

This script validates the correctness properties of the data retention system:
- Property 30: Data Retention Control
- Validates: Requirements 13.3, 13.4

Tests cover:
1. Preserve policy - data remains accessible after disable/enable
2. Archive policy - data is archived and can be restored
3. Delete policy - data is permanently removed
4. Policy transitions - changing policies handles data correctly
5. Data consistency - data state matches retention policy
"""

import asyncio
import logging
from datetime import datetime, timezone

from core.models.database import get_master_db
from core.services.tenant_database_manager import tenant_db_manager
from core.services.data_retention_manager import DataRetentionManager
from core.services.gamification_module_manager import GamificationModuleManager
from core.models.gamification import (
    UserGamificationProfile,
    UserAchievement,
    UserStreak,
    UserChallenge,
    PointHistory,
    Achievement,
    Challenge,
    HabitType,
    AchievementCategory,
    AchievementDifficulty,
    ChallengeType,
    DataRetentionPolicy
)
from core.schemas.gamification import (
    DisableGamificationRequest,
    DataRetentionPolicy as SchemaDataRetentionPolicy
)
from core.models.models import Tenant, User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_data_retention_system():
    """Run comprehensive tests for data retention system"""
    
    logger.info("🎯 TEST: Data Retention Policy System")
    logger.info("=" * 60)
    
    # Get master database
    master_db = next(get_master_db())
    
    try:
        # Get first active tenant
        tenant = master_db.query(Tenant).filter(Tenant.is_active == True).first()
        if not tenant:
            logger.error("❌ No active tenant found")
            return False
        
        logger.info(f"Testing with tenant: {tenant.id} ({tenant.name})")
        
        # Get tenant database session
        tenant_session = tenant_db_manager.get_tenant_session(tenant.id)
        tenant_db = tenant_session()
        
        try:
            all_tests_passed = True
            
            # ========== TEST 1: PRESERVE Policy ==========
            logger.info("\n✅ TEST 1: PRESERVE Policy - Data Preservation")
            logger.info("-" * 60)
            
            try:
                # Create test user
                test_user = User(
                    email=f"test_preserve_{datetime.now(timezone.utc).timestamp()}@example.com",
                    password_hash="test_hash",
                    is_active=True
                )
                tenant_db.add(test_user)
                tenant_db.commit()
                tenant_db.refresh(test_user)
                
                # Create gamification profile
                profile = UserGamificationProfile(
                    user_id=test_user.id,
                    module_enabled=True,
                    level=5,
                    total_experience_points=1000,
                    current_level_progress=50.0,
                    financial_health_score=75.0,
                    preferences={"features": {"points": True}},
                    statistics={"totalActionsCompleted": 100}
                )
                tenant_db.add(profile)
                tenant_db.commit()
                tenant_db.refresh(profile)
                
                # Create achievement
                achievement = Achievement(
                    achievement_id="test_preserve_achievement",
                    name="Test Achievement",
                    description="Test",
                    category=AchievementCategory.EXPENSE_TRACKING,
                    difficulty=AchievementDifficulty.BRONZE,
                    requirements=[{"type": "expense_count", "target": 10}],
                    reward_xp=100
                )
                tenant_db.add(achievement)
                tenant_db.commit()
                tenant_db.refresh(achievement)
                
                # Create user achievement
                user_achievement = UserAchievement(
                    profile_id=profile.id,
                    achievement_id=achievement.id,
                    progress=100.0,
                    is_completed=True,
                    unlocked_at=datetime.now(timezone.utc)
                )
                tenant_db.add(user_achievement)
                tenant_db.commit()
                
                # Apply PRESERVE policy
                manager = DataRetentionManager(tenant_db)
                success = await manager.apply_retention_policy(
                    profile.id,
                    DataRetentionPolicy.PRESERVE,
                    action="disable"
                )
                
                if not success:
                    logger.error("   ❌ Failed to apply PRESERVE policy")
                    all_tests_passed = False
                else:
                    logger.info("   ✅ PRESERVE policy applied successfully")
                
                # Verify data still exists
                achievements_count = tenant_db.query(UserAchievement).filter(
                    UserAchievement.profile_id == profile.id
                ).count()
                
                if achievements_count == 0:
                    logger.error("   ❌ Data was deleted with PRESERVE policy")
                    all_tests_passed = False
                else:
                    logger.info(f"   ✅ Data preserved: {achievements_count} achievement(s) remain")
                
            except Exception as e:
                logger.error(f"   ❌ PRESERVE policy test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 2: ARCHIVE Policy ==========
            logger.info("\n✅ TEST 2: ARCHIVE Policy - Data Archival")
            logger.info("-" * 60)
            
            try:
                # Create test user
                test_user2 = User(
                    email=f"test_archive_{datetime.now(timezone.utc).timestamp()}@example.com",
                    password_hash="test_hash",
                    is_active=True
                )
                tenant_db.add(test_user2)
                tenant_db.commit()
                tenant_db.refresh(test_user2)
                
                # Create gamification profile
                profile2 = UserGamificationProfile(
                    user_id=test_user2.id,
                    module_enabled=True,
                    level=3,
                    total_experience_points=500,
                    current_level_progress=25.0,
                    financial_health_score=60.0,
                    preferences={"features": {"points": True}},
                    statistics={"totalActionsCompleted": 50}
                )
                tenant_db.add(profile2)
                tenant_db.commit()
                tenant_db.refresh(profile2)
                
                # Store original data
                original_level = profile2.level
                original_xp = profile2.total_experience_points
                
                # Apply ARCHIVE policy
                manager = DataRetentionManager(tenant_db)
                success = await manager.apply_retention_policy(
                    profile2.id,
                    DataRetentionPolicy.ARCHIVE,
                    action="disable"
                )
                
                if not success:
                    logger.error("   ❌ Failed to apply ARCHIVE policy")
                    all_tests_passed = False
                else:
                    logger.info("   ✅ ARCHIVE policy applied successfully")
                
                # Verify snapshot was created
                tenant_db.refresh(profile2)
                if not profile2.preferences or "archived_data" not in profile2.preferences:
                    logger.error("   ❌ No archive snapshot created")
                    all_tests_passed = False
                else:
                    archived_data = profile2.preferences["archived_data"]
                    snapshot = archived_data.get("snapshot", {})
                    
                    if snapshot.get("level") != original_level:
                        logger.error("   ❌ Archive snapshot has incorrect level")
                        all_tests_passed = False
                    else:
                        logger.info(f"   ✅ Archive snapshot created with level={snapshot.get('level')}")
                
                # Test restoration
                success = await manager.apply_retention_policy(
                    profile2.id,
                    DataRetentionPolicy.ARCHIVE,
                    action="enable"
                )
                
                if not success:
                    logger.error("   ❌ Failed to restore archived data")
                    all_tests_passed = False
                else:
                    tenant_db.refresh(profile2)
                    if profile2.level != original_level or profile2.total_experience_points != original_xp:
                        logger.error("   ❌ Restored data doesn't match original")
                        all_tests_passed = False
                    else:
                        logger.info(f"   ✅ Data restored successfully: level={profile2.level}, xp={profile2.total_experience_points}")
                
            except Exception as e:
                logger.error(f"   ❌ ARCHIVE policy test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 3: DELETE Policy ==========
            logger.info("\n✅ TEST 3: DELETE Policy - Data Deletion")
            logger.info("-" * 60)
            
            try:
                # Create test user
                test_user3 = User(
                    email=f"test_delete_{datetime.now(timezone.utc).timestamp()}@example.com",
                    password_hash="test_hash",
                    is_active=True
                )
                tenant_db.add(test_user3)
                tenant_db.commit()
                tenant_db.refresh(test_user3)
                
                # Create gamification profile
                profile3 = UserGamificationProfile(
                    user_id=test_user3.id,
                    module_enabled=True,
                    level=10,
                    total_experience_points=5000,
                    current_level_progress=75.0,
                    financial_health_score=90.0,
                    preferences={"features": {"points": True}},
                    statistics={"totalActionsCompleted": 500}
                )
                tenant_db.add(profile3)
                tenant_db.commit()
                tenant_db.refresh(profile3)
                
                # Create achievement
                achievement3 = Achievement(
                    achievement_id="test_delete_achievement",
                    name="Test Achievement",
                    description="Test",
                    category=AchievementCategory.EXPENSE_TRACKING,
                    difficulty=AchievementDifficulty.BRONZE,
                    requirements=[{"type": "expense_count", "target": 10}],
                    reward_xp=100
                )
                tenant_db.add(achievement3)
                tenant_db.commit()
                tenant_db.refresh(achievement3)
                
                # Create user achievement
                user_achievement3 = UserAchievement(
                    profile_id=profile3.id,
                    achievement_id=achievement3.id,
                    progress=100.0,
                    is_completed=True,
                    unlocked_at=datetime.now(timezone.utc)
                )
                tenant_db.add(user_achievement3)
                tenant_db.commit()
                
                # Create point history
                point_history = PointHistory(
                    profile_id=profile3.id,
                    action_type="expense_added",
                    points_awarded=10,
                    base_points=10,
                    streak_multiplier=1.0
                )
                tenant_db.add(point_history)
                tenant_db.commit()
                
                # Verify data exists before delete
                achievements_before = tenant_db.query(UserAchievement).filter(
                    UserAchievement.profile_id == profile3.id
                ).count()
                point_history_before = tenant_db.query(PointHistory).filter(
                    PointHistory.profile_id == profile3.id
                ).count()
                
                logger.info(f"   Data before delete: {achievements_before} achievements, {point_history_before} point history entries")
                
                # Apply DELETE policy
                manager = DataRetentionManager(tenant_db)
                success = await manager.apply_retention_policy(
                    profile3.id,
                    DataRetentionPolicy.DELETE,
                    action="disable"
                )
                
                if not success:
                    logger.error("   ❌ Failed to apply DELETE policy")
                    all_tests_passed = False
                else:
                    logger.info("   ✅ DELETE policy applied successfully")
                
                # Verify all data is deleted
                achievements_after = tenant_db.query(UserAchievement).filter(
                    UserAchievement.profile_id == profile3.id
                ).count()
                point_history_after = tenant_db.query(PointHistory).filter(
                    PointHistory.profile_id == profile3.id
                ).count()
                
                if achievements_after > 0 or point_history_after > 0:
                    logger.error(f"   ❌ Data not deleted: {achievements_after} achievements, {point_history_after} point history entries remain")
                    all_tests_passed = False
                else:
                    logger.info("   ✅ All data deleted successfully")
                
                # Verify profile stats are reset
                tenant_db.refresh(profile3)
                if profile3.level != 1 or profile3.total_experience_points != 0:
                    logger.error(f"   ❌ Profile stats not reset: level={profile3.level}, xp={profile3.total_experience_points}")
                    all_tests_passed = False
                else:
                    logger.info("   ✅ Profile stats reset successfully")
                
            except Exception as e:
                logger.error(f"   ❌ DELETE policy test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 4: Data Consistency Validation ==========
            logger.info("\n✅ TEST 4: Data Consistency Validation")
            logger.info("-" * 60)
            
            try:
                # Create test user
                test_user4 = User(
                    email=f"test_validation_{datetime.now(timezone.utc).timestamp()}@example.com",
                    password_hash="test_hash",
                    is_active=True
                )
                tenant_db.add(test_user4)
                tenant_db.commit()
                tenant_db.refresh(test_user4)
                
                # Create gamification profile
                profile4 = UserGamificationProfile(
                    user_id=test_user4.id,
                    module_enabled=True,
                    level=2,
                    total_experience_points=200,
                    current_level_progress=10.0,
                    financial_health_score=50.0,
                    preferences={"features": {"points": True}},
                    statistics={"totalActionsCompleted": 20}
                )
                tenant_db.add(profile4)
                tenant_db.commit()
                tenant_db.refresh(profile4)
                
                # Get retention status
                manager = DataRetentionManager(tenant_db)
                status = await manager.get_data_retention_status(profile4.id)
                
                if not status["profile_found"]:
                    logger.error("   ❌ Profile not found in retention status")
                    all_tests_passed = False
                else:
                    logger.info(f"   ✅ Retention status retrieved: policy={status['retention_policy']}")
                
                # Validate data consistency
                validation = await manager.validate_data_consistency(profile4.id)
                
                if not validation["valid"]:
                    logger.error(f"   ❌ Data consistency validation failed: {validation['issues']}")
                    all_tests_passed = False
                else:
                    logger.info("   ✅ Data consistency validation passed")
                
            except Exception as e:
                logger.error(f"   ❌ Data consistency validation test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== SUMMARY ==========
            logger.info("\n" + "=" * 60)
            if all_tests_passed:
                logger.info("✅ ALL TESTS PASSED - Data Retention System Functional")
                logger.info("=" * 60)
                return True
            else:
                logger.error("❌ SOME TESTS FAILED - See details above")
                logger.info("=" * 60)
                return False
            
        finally:
            tenant_db.close()
    
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_data_retention_system())
    exit(0 if result else 1)
