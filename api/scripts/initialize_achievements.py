#!/usr/bin/env python3
"""
Initialize achievement definitions in the database.

This script populates the achievements table with all predefined achievements
for the gamification system. It should be run after the gamification tables
are created via Alembic migration.

This script initializes achievements in ALL tenant databases.
"""

import sys
import os
import asyncio
import logging

# Add the parent directory to the path so we can import from the API
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.models.database import SessionLocal
from core.models.models import Tenant
from core.services.tenant_database_manager import tenant_db_manager
from core.services.achievement_engine import AchievementEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_achievements_for_tenant(tenant_id: int, tenant_name: str) -> bool:
    """Initialize achievements for a specific tenant."""
    try:
        logger.info(f"Initializing achievements for tenant {tenant_id} ({tenant_name})...")
        
        # Get tenant database session
        tenant_session = tenant_db_manager.get_tenant_session(tenant_id)
        if not tenant_session:
            logger.error(f"Could not get session for tenant {tenant_id}")
            return False
        
        db = tenant_session()
        
        try:
            # Create achievement engine
            achievement_engine = AchievementEngine(db)
            
            # Initialize achievements
            success = achievement_engine.initialize_achievements()
            
            if success:
                logger.info(f"✅ Achievements initialized for tenant {tenant_id}")
                return True
            else:
                logger.error(f"❌ Failed to initialize achievements for tenant {tenant_id}")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error initializing achievements for tenant {tenant_id}: {str(e)}")
        return False


async def initialize_achievements():
    """Initialize all achievement definitions in all tenant databases."""
    try:
        logger.info("Starting achievement initialization for all tenants...")
        
        # Get all tenants from master database
        master_db = SessionLocal()
        
        try:
            tenants = master_db.query(Tenant).filter(Tenant.is_active == True).all()
            
            if not tenants:
                logger.warning("No active tenants found")
                return True
            
            logger.info(f"Found {len(tenants)} active tenants")
            
            success_count = 0
            for tenant in tenants:
                success = await initialize_achievements_for_tenant(tenant.id, tenant.name)
                if success:
                    success_count += 1
            
            logger.info(f"✅ Achievement initialization completed for {success_count}/{len(tenants)} tenants")
            return success_count == len(tenants)
            
        finally:
            master_db.close()
            
    except Exception as e:
        logger.error(f"❌ Error during achievement initialization: {str(e)}")
        return False


async def verify_achievements():
    """Verify that achievements were created correctly in all tenant databases."""
    try:
        logger.info("Verifying achievement initialization for all tenants...")
        
        # Get all tenants from master database
        master_db = SessionLocal()
        
        try:
            tenants = master_db.query(Tenant).filter(Tenant.is_active == True).all()
            
            if not tenants:
                logger.warning("No active tenants found")
                return True
            
            total_verified = 0
            for tenant in tenants:
                success = await verify_achievements_for_tenant(tenant.id, tenant.name)
                if success:
                    total_verified += 1
            
            logger.info(f"✅ Achievement verification completed for {total_verified}/{len(tenants)} tenants")
            return total_verified == len(tenants)
            
        finally:
            master_db.close()
            
    except Exception as e:
        logger.error(f"❌ Error during achievement verification: {str(e)}")
        return False


async def verify_achievements_for_tenant(tenant_id: int, tenant_name: str) -> bool:
    """Verify achievements for a specific tenant."""
    try:
        logger.info(f"Verifying achievements for tenant {tenant_id} ({tenant_name})...")
        
        # Get tenant database session
        tenant_session = tenant_db_manager.get_tenant_session(tenant_id)
        if not tenant_session:
            logger.error(f"Could not get session for tenant {tenant_id}")
            return False
        
        db = tenant_session()
        
        try:
            from core.models.gamification import Achievement, AchievementCategory, AchievementDifficulty
            
            # Count total achievements
            total_count = db.query(Achievement).count()
            logger.info(f"  Tenant {tenant_id}: {total_count} total achievements")
            
            if total_count == 0:
                logger.error(f"  ❌ No achievements found for tenant {tenant_id}")
                return False
            
            # Count by category
            for category in AchievementCategory:
                count = db.query(Achievement).filter(
                    Achievement.category == category
                ).count()
                logger.info(f"    {category.value}: {count} achievements")
            
            logger.info(f"  ✅ Tenant {tenant_id} verification successful")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error verifying achievements for tenant {tenant_id}: {str(e)}")
        return False


async def main():
    """Main function to run the achievement initialization."""
    logger.info("🎯 Achievement Initialization Script")
    logger.info("=" * 50)
    
    # Initialize achievements
    init_success = await initialize_achievements()
    
    if init_success:
        # Verify achievements
        verify_success = await verify_achievements()
        
        if verify_success:
            logger.info("🎉 Achievement system is ready!")
            sys.exit(0)
        else:
            logger.error("💥 Achievement verification failed!")
            sys.exit(1)
    else:
        logger.error("💥 Achievement initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())