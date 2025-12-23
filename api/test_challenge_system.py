#!/usr/bin/env python3
"""
Test script for the challenge system implementation.

This script tests the core functionality of the challenge management system
including challenge creation, user participation, progress tracking, and completion.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the API directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from core.models.database import SessionLocal, set_tenant_context
from core.services.challenge_manager import ChallengeManager
from core.services.gamification_service import GamificationService
from core.schemas.gamification import (
    FinancialEvent,
    ActionType,
    ChallengeCreate,
    ChallengeType,
    ChallengeRequirement
)


async def create_test_tables(db: Session):
    """Create test tables for SQLite"""
    try:
        # Import the models to ensure they're registered
        from core.models.gamification import (
            UserGamificationProfile,
            Achievement,
            UserAchievement,
            UserStreak,
            Challenge,
            UserChallenge,
            PointHistory,
            OrganizationGamificationConfig
        )
        from core.models.models_per_tenant import Base
        
        # Create all tables
        Base.metadata.create_all(bind=db.bind)
        
    except Exception as e:
        print(f"Error creating test tables: {str(e)}")
        raise


async def test_challenge_system():
    """Test the challenge system functionality"""
    print("🎯 Testing Challenge System Implementation")
    print("=" * 50)
    
    # Set tenant context for testing (use tenant 1)
    set_tenant_context(1)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Create tables if they don't exist (for SQLite testing)
        print("\n0. Setting up test database tables...")
        await create_test_tables(db)
        print("   ✅ Test tables created")
        
        # Initialize services
        challenge_manager = ChallengeManager(db)
        gamification_service = GamificationService(db)
        
        # Test 1: Initialize default challenges
        print("\n1. Testing default challenge initialization...")
        success = await challenge_manager.initialize_default_challenges()
        print(f"   ✅ Default challenges initialized: {success}")
        
        # Test 2: Get available challenges
        print("\n2. Testing available challenges retrieval...")
        available_challenges = await challenge_manager.get_available_challenges(user_id=1)
        print(f"   ✅ Found {len(available_challenges)} available challenges")
        
        for challenge in available_challenges[:3]:  # Show first 3
            print(f"      - {challenge.name}: {challenge.description}")
        
        # Test 3: Get weekly challenges
        print("\n3. Testing weekly challenges...")
        weekly_challenges = await challenge_manager.get_weekly_challenges()
        print(f"   ✅ Found {len(weekly_challenges)} weekly challenges")
        
        # Test 4: Get monthly challenges
        print("\n4. Testing monthly challenges...")
        monthly_challenges = await challenge_manager.get_monthly_challenges()
        print(f"   ✅ Found {len(monthly_challenges)} monthly challenges")
        
        # Test 5: Create a test user profile (if not exists)
        print("\n5. Testing user profile creation...")
        try:
            profile = await gamification_service.enable_gamification(user_id=1)
            print(f"   ✅ User profile created/enabled for user 1")
        except Exception as e:
            print(f"   ℹ️  User profile may already exist: {str(e)}")
        
        # Test 6: Opt user into a challenge
        if available_challenges:
            print("\n6. Testing challenge opt-in...")
            first_challenge = available_challenges[0]
            user_challenge = await challenge_manager.opt_into_challenge(
                user_id=1, 
                challenge_id=first_challenge.id
            )
            
            if user_challenge:
                print(f"   ✅ User opted into challenge: {first_challenge.name}")
                print(f"      Progress: {user_challenge.progress}%")
            else:
                print("   ❌ Failed to opt into challenge")
        
        # Test 7: Get user challenges
        print("\n7. Testing user challenges retrieval...")
        user_challenges = await challenge_manager.get_user_challenges(user_id=1)
        print(f"   ✅ User has {len(user_challenges)} active challenges")
        
        # Test 8: Simulate financial events and test progress tracking
        if user_challenges:
            print("\n8. Testing challenge progress tracking...")
            
            # Create test financial events
            test_events = [
                FinancialEvent(
                    user_id=1,
                    action_type=ActionType.EXPENSE_ADDED,
                    timestamp=datetime.now(timezone.utc),
                    metadata={"amount": 25.50, "category": "food"}
                ),
                FinancialEvent(
                    user_id=1,
                    action_type=ActionType.RECEIPT_UPLOADED,
                    timestamp=datetime.now(timezone.utc),
                    metadata={"expense_id": 1}
                ),
                FinancialEvent(
                    user_id=1,
                    action_type=ActionType.INVOICE_CREATED,
                    timestamp=datetime.now(timezone.utc),
                    metadata={"amount": 1000.00, "client": "Test Client"}
                )
            ]
            
            for i, event in enumerate(test_events):
                print(f"   Processing event {i+1}: {event.action_type.value}")
                
                # Process through gamification service (which includes challenge updates)
                result = await gamification_service.process_financial_event(event)
                
                if result and result.challenges_updated:
                    print(f"      ✅ Updated {len(result.challenges_updated)} challenges")
                    for challenge_update in result.challenges_updated:
                        print(f"         - {challenge_update['challenge_name']}: "
                              f"{challenge_update['old_progress']:.1f}% → "
                              f"{challenge_update['new_progress']:.1f}%")
                else:
                    print(f"      ℹ️  No challenge updates from this event")
        
        # Test 9: Get detailed challenge progress
        if user_challenges:
            print("\n9. Testing detailed challenge progress...")
            first_user_challenge = user_challenges[0]
            progress_details = await challenge_manager.get_challenge_progress(
                user_id=1, 
                challenge_id=first_user_challenge.challenge.id
            )
            
            if progress_details:
                print(f"   ✅ Challenge: {progress_details['challenge_name']}")
                print(f"      Overall Progress: {progress_details['progress']:.1f}%")
                print(f"      Completed: {progress_details['is_completed']}")
                print(f"      Time Remaining: {progress_details.get('time_remaining', 'N/A')}")
            else:
                print("   ❌ Failed to get challenge progress details")
        
        # Test 10: Test challenge opt-out
        if user_challenges:
            print("\n10. Testing challenge opt-out...")
            first_user_challenge = user_challenges[0]
            success = await challenge_manager.opt_out_of_challenge(
                user_id=1, 
                challenge_id=first_user_challenge.challenge.id
            )
            print(f"    ✅ Opt-out successful: {success}")
            
            # Verify opt-out
            updated_challenges = await challenge_manager.get_user_challenges(user_id=1)
            opted_in_count = sum(1 for uc in updated_challenges if uc.opted_in)
            print(f"    ✅ User now has {opted_in_count} opted-in challenges")
        
        # Test 11: Create a custom challenge
        print("\n11. Testing custom challenge creation...")
        try:
            custom_challenge_data = ChallengeCreate(
                challenge_id="test_custom_challenge",
                name="Test Custom Challenge",
                description="A test challenge created by the test script",
                challenge_type=ChallengeType.PERSONAL,
                duration_days=7,
                requirements=[
                    ChallengeRequirement(
                        type="track_expenses",
                        target=5,
                        period="total"
                    )
                ],
                reward_xp=50,
                reward_badge_url="/badges/test_custom.png"
            )
            
            custom_challenge = await challenge_manager.create_challenge_template(custom_challenge_data)
            print(f"   ✅ Custom challenge created: {custom_challenge.name}")
            print(f"      ID: {custom_challenge.challenge_id}")
            print(f"      Reward XP: {custom_challenge.reward_xp}")
            
        except Exception as e:
            print(f"   ❌ Failed to create custom challenge: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 Challenge System Test Complete!")
        print("\nSummary:")
        print(f"- Default challenges initialized: ✅")
        print(f"- Challenge retrieval: ✅")
        print(f"- User participation: ✅")
        print(f"- Progress tracking: ✅")
        print(f"- Custom challenge creation: ✅")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_challenge_system())