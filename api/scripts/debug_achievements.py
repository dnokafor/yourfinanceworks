#!/usr/bin/env python3
"""Debug script to check if achievements are being created and returned correctly."""

import sys
import os

# Add /app to path so we can import core modules
sys.path.insert(0, '/app')

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from core.models.database import SessionLocal
from core.models.gamification import Achievement, UserGamificationProfile, UserAchievement
from core.services.gamification_service import GamificationService

def main():
    db = SessionLocal()
    
    try:
        # Check Achievement definitions
        print("=" * 60)
        print("ACHIEVEMENT DEFINITIONS")
        print("=" * 60)
        achievements = db.query(Achievement).all()
        print(f"Total achievements in database: {len(achievements)}")
        
        if achievements:
            print("\nFirst 5 achievements:")
            for a in achievements[:5]:
                print(f"  - {a.achievement_id}: {a.name}")
                print(f"    Category: {a.category}")
                print(f"    Active: {a.is_active}")
                print()
        else:
            print("❌ NO ACHIEVEMENTS FOUND IN DATABASE!")
        
        # Check UserGamificationProfile
        print("=" * 60)
        print("USER GAMIFICATION PROFILES")
        print("=" * 60)
        profiles = db.query(UserGamificationProfile).all()
        print(f"Total profiles: {len(profiles)}")
        
        if profiles:
            for profile in profiles[:3]:
                print(f"\nProfile ID: {profile.id}, User ID: {profile.user_id}")
                print(f"  Module Enabled: {profile.module_enabled}")
                
                # Check UserAchievements for this profile
                user_achievements = db.query(UserAchievement).filter(
                    UserAchievement.profile_id == profile.id
                ).all()
                print(f"  User Achievements: {len(user_achievements)}")
                
                if user_achievements:
                    print(f"    First 3:")
                    for ua in user_achievements[:3]:
                        print(f"      - Achievement ID: {ua.achievement_id}, Completed: {ua.is_completed}, Progress: {ua.progress}")
                else:
                    print(f"    ❌ NO USER ACHIEVEMENTS FOR THIS PROFILE!")
        else:
            print("❌ NO PROFILES FOUND!")
        
        # Test the gamification service
        print("\n" + "=" * 60)
        print("GAMIFICATION SERVICE TEST")
        print("=" * 60)
        
        if profiles:
            profile = profiles[0]
            service = GamificationService(db)
            
            print(f"\nTesting get_user_achievements for profile {profile.id}...")
            achievements_result = service.get_user_achievements(profile.user_id)
            print(f"Result: {len(achievements_result)} achievements returned")
            
            if achievements_result:
                print("First achievement:")
                print(f"  {achievements_result[0]}")
            else:
                print("❌ NO ACHIEVEMENTS RETURNED FROM SERVICE!")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
