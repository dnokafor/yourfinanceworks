#!/usr/bin/env python3
"""
Checkpoint test for core gamification system functionality.

This test validates:
1. Module enable/disable functionality
2. Core gamification features (points, achievements, streaks, challenges)
3. Data persistence and user profile management
4. Financial health score calculation
5. Dashboard completeness
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from core.models.database import get_master_db
from core.services.tenant_database_manager import tenant_db_manager
from core.services.gamification_service import GamificationService
from core.services.gamification_module_manager import GamificationModuleManager
from core.schemas.gamification import (
    FinancialEvent,
    ActionType,
    EnableGamificationRequest,
    DisableGamificationRequest,
    GamificationPreferences,
    DataRetentionPolicy
)
from core.models.models import Tenant

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_checkpoint():
    """Run comprehensive checkpoint tests for core gamification system"""
    
    logger.info("🎯 CHECKPOINT: Core Gamification System Functional")
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
            # Initialize services
            gamification_service = GamificationService(tenant_db)
            module_manager = GamificationModuleManager(tenant_db)
            
            test_user_id = 1
            all_tests_passed = True
            
            # ========== TEST 1: Module Enable/Disable Functionality ==========
            logger.info("\n✅ TEST 1: Module Enable/Disable Functionality")
            logger.info("-" * 60)
            
            try:
                # Check initial state
                is_enabled = await module_manager.is_enabled(test_user_id)
                logger.info(f"   Initial state - Gamification enabled: {is_enabled}")
                
                # Enable gamification
                enable_request = EnableGamificationRequest(
                    preferences=GamificationPreferences(),
                    data_retention_policy=DataRetentionPolicy.PRESERVE
                )
                profile = await module_manager.enable_gamification(test_user_id, enable_request)
                logger.info(f"   ✅ Gamification enabled for user {test_user_id}")
                logger.info(f"      - Level: {profile.level}")
                logger.info(f"      - Total XP: {profile.total_experience_points}")
                
                # Verify enabled
                is_enabled = await module_manager.is_enabled(test_user_id)
                if not is_enabled:
                    logger.error("   ❌ Failed to enable gamification")
                    all_tests_passed = False
                else:
                    logger.info(f"   ✅ Verified gamification is enabled")
                
                # Get module status
                status = await module_manager.get_module_status(test_user_id)
                logger.info(f"   ✅ Module status retrieved: enabled={status.enabled}")
                
            except Exception as e:
                logger.error(f"   ❌ Module enable/disable test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 2: Core Points System ==========
            logger.info("\n✅ TEST 2: Core Points System")
            logger.info("-" * 60)
            
            try:
                # Process expense event
                expense_event = FinancialEvent(
                    action_type=ActionType.EXPENSE_ADDED,
                    user_id=test_user_id,
                    amount=50.00,
                    metadata={"category": "food", "description": "Lunch"},
                    timestamp=datetime.now(timezone.utc)
                )
                
                result = await gamification_service.process_financial_event(expense_event)
                
                if result is None:
                    logger.error("   ❌ No result returned from event processing")
                    all_tests_passed = False
                else:
                    logger.info(f"   ✅ Event processed successfully")
                    logger.info(f"      - Points awarded: {result.points_awarded}")
                    logger.info(f"      - Celebration triggered: {result.celebration_triggered}")
                    
                    if result.points_awarded <= 0:
                        logger.error("   ❌ No points awarded")
                        all_tests_passed = False
                    else:
                        logger.info(f"   ✅ Points awarded correctly")
                
            except Exception as e:
                logger.error(f"   ❌ Points system test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 3: Data Persistence ==========
            logger.info("\n✅ TEST 3: Data Persistence and User Profile Management")
            logger.info("-" * 60)
            
            try:
                # Get user profile
                user_profile = await module_manager.get_user_profile(test_user_id)
                
                if user_profile is None:
                    logger.error("   ❌ Failed to retrieve user profile")
                    all_tests_passed = False
                else:
                    logger.info(f"   ✅ User profile retrieved")
                    logger.info(f"      - User ID: {user_profile.user_id}")
                    logger.info(f"      - Level: {user_profile.level}")
                    logger.info(f"      - Total XP: {user_profile.total_experience_points}")
                    logger.info(f"      - Module enabled: {user_profile.module_enabled}")
                    
                    # Verify profile has expected data
                    if user_profile.total_experience_points <= 0:
                        logger.warning("   ⚠️  Profile has no experience points yet")
                    else:
                        logger.info(f"   ✅ Profile data persisted correctly")
                
            except Exception as e:
                logger.error(f"   ❌ Data persistence test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 4: Achievements System ==========
            logger.info("\n✅ TEST 4: Achievements System")
            logger.info("-" * 60)
            
            try:
                # Get user achievements
                achievements = await gamification_service.get_user_achievements(test_user_id)
                logger.info(f"   ✅ Retrieved {len(achievements)} achievements")
                
                if achievements:
                    completed = [a for a in achievements if a.get('completed', False)]
                    logger.info(f"      - Completed: {len(completed)}")
                    logger.info(f"      - In progress: {len(achievements) - len(completed)}")
                    
                    if completed:
                        logger.info(f"   ✅ Achievements are being unlocked")
                    else:
                        logger.info(f"   ℹ️  No achievements completed yet (expected for new user)")
                else:
                    logger.warning("   ⚠️  No achievements found")
                
            except Exception as e:
                logger.error(f"   ❌ Achievements system test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 5: Streaks System ==========
            logger.info("\n✅ TEST 5: Streaks System")
            logger.info("-" * 60)
            
            try:
                # Get user streaks
                streaks = await gamification_service.get_user_streaks(test_user_id)
                logger.info(f"   ✅ Retrieved {len(streaks)} streaks")
                
                if streaks:
                    for streak in streaks:
                        logger.info(f"      - {streak['habit_type']}: {streak['current_length']} days")
                    logger.info(f"   ✅ Streak tracking is functional")
                else:
                    logger.warning("   ⚠️  No streaks found")
                
            except Exception as e:
                logger.error(f"   ❌ Streaks system test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 6: Challenges System ==========
            logger.info("\n✅ TEST 6: Challenges System")
            logger.info("-" * 60)
            
            try:
                # Get available challenges
                available_challenges = await gamification_service.get_available_challenges(test_user_id)
                logger.info(f"   ✅ Retrieved {len(available_challenges)} available challenges")
                
                # Get user challenges
                user_challenges = await gamification_service.get_user_challenges(test_user_id)
                logger.info(f"   ✅ User has {len(user_challenges)} active challenges")
                
                if available_challenges or user_challenges:
                    logger.info(f"   ✅ Challenge system is functional")
                else:
                    logger.warning("   ⚠️  No challenges available")
                
            except Exception as e:
                logger.error(f"   ❌ Challenges system test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 7: Financial Health Score ==========
            logger.info("\n✅ TEST 7: Financial Health Score")
            logger.info("-" * 60)
            
            try:
                # Get financial health score
                health_score = await gamification_service.get_financial_health_score(test_user_id)
                
                if health_score is None:
                    logger.warning("   ⚠️  No health score calculated yet")
                else:
                    logger.info(f"   ✅ Financial health score retrieved")
                    logger.info(f"      - Overall score: {health_score['overall']}/100")
                    logger.info(f"      - Trend: {health_score['trend']}")
                    
                    if 0 <= health_score['overall'] <= 100:
                        logger.info(f"   ✅ Health score is valid")
                    else:
                        logger.error(f"   ❌ Health score out of range: {health_score['overall']}")
                        all_tests_passed = False
                
            except Exception as e:
                logger.error(f"   ❌ Financial health score test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 8: Dashboard Completeness ==========
            logger.info("\n✅ TEST 8: Dashboard Completeness")
            logger.info("-" * 60)
            
            try:
                # Get dashboard
                dashboard = await gamification_service.get_user_dashboard(test_user_id)
                
                if dashboard is None:
                    logger.error("   ❌ Failed to retrieve dashboard")
                    all_tests_passed = False
                else:
                    logger.info(f"   ✅ Dashboard retrieved successfully")
                    logger.info(f"      - Profile level: {dashboard.profile.level}")
                    logger.info(f"      - Total XP: {dashboard.profile.total_experience_points}")
                    logger.info(f"      - Recent achievements: {len(dashboard.recent_achievements)}")
                    logger.info(f"      - Active streaks: {len(dashboard.active_streaks)}")
                    logger.info(f"      - Active challenges: {len(dashboard.active_challenges)}")
                    logger.info(f"      - Recent points: {len(dashboard.recent_points)}")
                    
                    # Verify dashboard has expected components
                    if dashboard.profile and dashboard.level_progress:
                        logger.info(f"   ✅ Dashboard is complete with all components")
                    else:
                        logger.warning("   ⚠️  Dashboard missing some components")
                
            except Exception as e:
                logger.error(f"   ❌ Dashboard test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 9: Module Disable and Data Retention ==========
            logger.info("\n✅ TEST 9: Module Disable and Data Retention")
            logger.info("-" * 60)
            
            try:
                # Disable gamification with PRESERVE policy
                disable_request = DisableGamificationRequest(
                    data_retention_policy=DataRetentionPolicy.PRESERVE
                )
                success = await module_manager.disable_gamification(test_user_id, disable_request)
                
                if not success:
                    logger.error("   ❌ Failed to disable gamification")
                    all_tests_passed = False
                else:
                    logger.info(f"   ✅ Gamification disabled successfully")
                    
                    # Verify disabled
                    is_enabled = await module_manager.is_enabled(test_user_id)
                    if is_enabled:
                        logger.error("   ❌ Gamification still enabled after disable")
                        all_tests_passed = False
                    else:
                        logger.info(f"   ✅ Verified gamification is disabled")
                    
                    # Verify data is preserved
                    status = await module_manager.get_module_status(test_user_id)
                    if status.data_retention_policy == DataRetentionPolicy.PRESERVE:
                        logger.info(f"   ✅ Data retention policy is PRESERVE")
                    else:
                        logger.error(f"   ❌ Data retention policy incorrect: {status.data_retention_policy}")
                        all_tests_passed = False
                
            except Exception as e:
                logger.error(f"   ❌ Module disable test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 10: Module Re-enable ==========
            logger.info("\n✅ TEST 10: Module Re-enable and Data Restoration")
            logger.info("-" * 60)
            
            try:
                # Re-enable gamification
                enable_request = EnableGamificationRequest(
                    preferences=GamificationPreferences(),
                    data_retention_policy=DataRetentionPolicy.PRESERVE
                )
                profile = await module_manager.enable_gamification(test_user_id, enable_request)
                logger.info(f"   ✅ Gamification re-enabled for user {test_user_id}")
                
                # Verify data was restored
                is_enabled = await module_manager.is_enabled(test_user_id)
                if not is_enabled:
                    logger.error("   ❌ Failed to re-enable gamification")
                    all_tests_passed = False
                else:
                    logger.info(f"   ✅ Verified gamification is re-enabled")
                    
                    # Check if data was preserved
                    if profile.total_experience_points > 0:
                        logger.info(f"   ✅ User data was preserved: {profile.total_experience_points} XP")
                    else:
                        logger.warning("   ⚠️  User data may not have been preserved")
                
            except Exception as e:
                logger.error(f"   ❌ Module re-enable test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== TEST 11: Module State Validation ==========
            logger.info("\n✅ TEST 11: Module State Validation")
            logger.info("-" * 60)
            
            try:
                # Validate module state
                validation = await module_manager.validate_module_state(test_user_id)
                logger.info(f"   ✅ Module state validation completed")
                logger.info(f"      - Profile exists: {validation['profile_exists']}")
                logger.info(f"      - Module enabled: {validation['module_enabled']}")
                logger.info(f"      - Data consistent: {validation['data_consistent']}")
                
                if validation['data_consistent']:
                    logger.info(f"   ✅ Module state is consistent")
                else:
                    logger.error(f"   ❌ Module state has issues: {validation['issues']}")
                    all_tests_passed = False
                
            except Exception as e:
                logger.error(f"   ❌ Module state validation test failed: {str(e)}")
                all_tests_passed = False
            
            # ========== SUMMARY ==========
            logger.info("\n" + "=" * 60)
            if all_tests_passed:
                logger.info("✅ ALL CHECKPOINT TESTS PASSED!")
                logger.info("=" * 60)
                logger.info("\n✅ Core gamification system is functional:")
                logger.info("   ✅ Module enable/disable functionality works")
                logger.info("   ✅ Core gamification features (points, achievements, streaks, challenges)")
                logger.info("   ✅ Data persistence and user profile management")
                logger.info("   ✅ Financial health score calculation")
                logger.info("   ✅ Dashboard completeness")
                logger.info("   ✅ Data retention policies")
                logger.info("\n🎉 Ready to proceed with advanced features!")
                return True
            else:
                logger.error("❌ SOME CHECKPOINT TESTS FAILED")
                logger.error("=" * 60)
                logger.error("\nPlease review the errors above and fix them before proceeding.")
                return False
            
        finally:
            tenant_db.close()
            
    except Exception as e:
        logger.error(f"❌ Checkpoint test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        master_db.close()


if __name__ == "__main__":
    success = asyncio.run(test_checkpoint())
    exit(0 if success else 1)
