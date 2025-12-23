#!/usr/bin/env python3
"""
Test script to verify achievement engine functionality.
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from core.models.database import get_master_db
from core.services.tenant_database_manager import tenant_db_manager
from core.services.gamification_service import GamificationService
from core.schemas.gamification import FinancialEvent, ActionType
from core.models.models import Tenant

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_achievement_engine():
    """Test the achievement engine with sample financial events."""
    
    logger.info("🧪 Testing Achievement Engine Functionality")
    logger.info("=" * 50)
    
    # Get master database
    master_db = next(get_master_db())
    
    try:
        # Get first tenant
        tenant = master_db.query(Tenant).filter(Tenant.is_active == True).first()
        if not tenant:
            logger.error("No active tenant found")
            return
        
        logger.info(f"Testing with tenant: {tenant.id} ({tenant.name})")
        
        # Get tenant database session
        tenant_session = tenant_db_manager.get_tenant_session(tenant.id)
        tenant_db = tenant_session()
        
        try:
            # Initialize gamification service
            gamification_service = GamificationService(tenant_db)
            
            # Test user ID (assuming user 1 exists)
            test_user_id = 1
            
            # Check if gamification is enabled for user
            is_enabled = await gamification_service.is_enabled_for_user(test_user_id)
            logger.info(f"Gamification enabled for user {test_user_id}: {is_enabled}")
            
            if not is_enabled:
                logger.info("Enabling gamification for test user...")
                from core.services.gamification_module_manager import GamificationModuleManager
                from core.schemas.gamification import EnableGamificationRequest
                
                module_manager = GamificationModuleManager(tenant_db)
                enable_request = EnableGamificationRequest(
                    preferences={
                        "features": {
                            "points": True,
                            "achievements": True,
                            "streaks": True,
                            "challenges": True,
                            "social": False,
                            "notifications": True
                        }
                    }
                )
                
                profile = await module_manager.enable_gamification(test_user_id, enable_request)
                logger.info(f"✅ Gamification enabled for user {test_user_id}")
                logger.info(f"   Profile created with level {profile.level} and {profile.total_experience_points} points")
            
            # Test 1: Process expense creation event
            logger.info("\n📝 Test 1: Processing expense creation event...")
            expense_event = FinancialEvent(
                action_type=ActionType.EXPENSE_ADDED,
                user_id=test_user_id,
                amount=25.50,
                metadata={
                    "expense_id": 1,
                    "category": "food",
                    "description": "Lunch at restaurant"
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            result = await gamification_service.process_financial_event(expense_event)
            if result:
                logger.info(f"✅ Event processed successfully!")
                logger.info(f"   Points awarded: {result.points_awarded}")
                logger.info(f"   Level up: {result.level_up}")
                logger.info(f"   Achievements unlocked: {len(result.achievements_unlocked)}")
                for achievement in result.achievements_unlocked:
                    logger.info(f"     🏆 {achievement.title}: {achievement.description}")
            else:
                logger.info("❌ No result returned from event processing")
            
            # Test 2: Process multiple expenses to trigger milestone achievements
            logger.info("\n📝 Test 2: Processing multiple expenses for milestones...")
            for i in range(2, 6):  # Create 4 more expenses
                expense_event = FinancialEvent(
                    action_type=ActionType.EXPENSE_ADDED,
                    user_id=test_user_id,
                    amount=float(15 + i * 5),
                    metadata={
                        "expense_id": i,
                        "category": "business",
                        "description": f"Business expense #{i}"
                    },
                    timestamp=datetime.now(timezone.utc)
                )
                
                result = await gamification_service.process_financial_event(expense_event)
                if result and result.achievements_unlocked:
                    logger.info(f"   Expense #{i}: {len(result.achievements_unlocked)} achievements unlocked")
                    for achievement in result.achievements_unlocked:
                        logger.info(f"     🏆 {achievement.title}")
            
            # Test 3: Get user dashboard
            logger.info("\n📊 Test 3: Getting user dashboard...")
            dashboard = await gamification_service.get_user_dashboard(test_user_id)
            if dashboard:
                logger.info(f"✅ Dashboard retrieved successfully!")
                logger.info(f"   Current level: {dashboard.profile.level}")
                logger.info(f"   Total points: {dashboard.profile.total_experience_points}")
                logger.info(f"   Recent achievements: {len(dashboard.recent_achievements)}")
                logger.info(f"   Active streaks: {len(dashboard.active_streaks)}")
            else:
                logger.info("❌ No dashboard data returned")
            
            # Test 4: Get user achievements
            logger.info("\n🏆 Test 4: Getting user achievements...")
            achievements = await gamification_service.get_user_achievements(test_user_id)
            if achievements:
                completed = [a for a in achievements if a.get('completed', False)]
                logger.info(f"✅ Retrieved {len(achievements)} achievements")
                logger.info(f"   Completed: {len(completed)}")
                logger.info(f"   In progress: {len(achievements) - len(completed)}")
                
                # Show completed achievements
                if completed:
                    logger.info("   Completed achievements:")
                    for achievement in completed[:3]:  # Show first 3
                        logger.info(f"     🏆 {achievement.get('title', 'Unknown')}")
            else:
                logger.info("❌ No achievements returned")
            
            logger.info("\n✅ Achievement engine testing completed successfully!")
            
        finally:
            tenant_db.close()
            
    except Exception as e:
        logger.error(f"❌ Error during testing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        master_db.close()

if __name__ == "__main__":
    asyncio.run(test_achievement_engine())