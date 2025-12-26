#!/usr/bin/env python3
"""
Initialize challenges script for the invoice application.

This script initializes default challenge templates for the gamification system.
It can be run independently or as part of the database initialization process.
"""

import asyncio
import logging
import os
import sys

# Add the api directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from core.models.database import get_master_db
from core.services.tenant_database_manager import tenant_db_manager
from core.models.models import Tenant
from core.services.challenge_manager import ChallengeManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def initialize_challenges_for_tenant(tenant_id: int) -> bool:
    """Initialize challenges for a specific tenant"""
    try:
        logger.info(f"Initializing challenges for tenant {tenant_id}...")
        
        # Get tenant database session
        tenant_session = tenant_db_manager.get_tenant_session(tenant_id)
        tenant_db = tenant_session()
        
        try:
            # Create challenge manager
            challenge_manager = ChallengeManager(tenant_db)
            
            # Initialize default challenges
            success = await challenge_manager.initialize_default_challenges()
            
            if success:
                logger.info(f"Successfully initialized challenges for tenant {tenant_id}")
            else:
                logger.error(f"Failed to initialize challenges for tenant {tenant_id}")
            
            return success
            
        finally:
            tenant_db.close()
            
    except Exception as e:
        logger.error(f"Error initializing challenges for tenant {tenant_id}: {str(e)}")
        return False


async def initialize_challenges_for_all_tenants() -> bool:
    """Initialize challenges for all tenants"""
    try:
        logger.info("Starting challenge initialization for all tenants...")
        
        # Get master database session
        master_db = next(get_master_db())
        
        try:
            # Get all tenants
            tenants = master_db.query(Tenant).all()
            
            if not tenants:
                logger.warning("No tenants found")
                return True
            
            logger.info(f"Found {len(tenants)} tenants")
            
            # Initialize challenges for each tenant
            success_count = 0
            for tenant in tenants:
                if await initialize_challenges_for_tenant(tenant.id):
                    success_count += 1
            
            logger.info(f"Challenge initialization completed: {success_count}/{len(tenants)} tenants successful")
            return success_count == len(tenants)
            
        finally:
            master_db.close()
            
    except Exception as e:
        logger.error(f"Error initializing challenges for all tenants: {str(e)}")
        return False


async def main():
    """Main function"""
    logger.info("Starting challenge initialization script...")
    
    # Check if we're in a specific tenant mode
    tenant_id = os.environ.get("TENANT_ID")
    
    if tenant_id:
        # Initialize for specific tenant
        try:
            tenant_id = int(tenant_id)
            success = await initialize_challenges_for_tenant(tenant_id)
        except ValueError:
            logger.error(f"Invalid tenant ID: {tenant_id}")
            sys.exit(1)
    else:
        # Initialize for all tenants
        success = await initialize_challenges_for_all_tenants()
    
    if success:
        logger.info("Challenge initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("Challenge initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())