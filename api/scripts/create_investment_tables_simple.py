#!/usr/bin/env python3
"""
Script to create investment tables using SQLAlchemy models
This bypasses the migration system issues and creates the tables needed for testing.
"""

import sys
import os
sys.path.append('/app')

from core.services.tenant_database_manager import TenantDatabaseManager
from plugins.investments.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_investment_tables():
    """Create investment tables using SQLAlchemy models"""

    try:
        # Get tenant database manager
        tenant_db_manager = TenantDatabaseManager()

        # Get list of tenant databases
        tenant_ids = [1, 2, 3]  # Known tenant IDs

        for tenant_id in tenant_ids:
            logger.info(f"Creating investment tables for tenant {tenant_id}")

            # Get database engine for tenant
            engine = tenant_db_manager.get_tenant_engine(tenant_id)

            # Create all investment tables
            Base.metadata.create_all(bind=engine)

            logger.info(f"Successfully created investment tables for tenant {tenant_id}")

    except Exception as e:
        logger.error(f"Error creating investment tables: {e}")
        raise

if __name__ == "__main__":
    create_investment_tables()
    print("Investment tables created successfully!")