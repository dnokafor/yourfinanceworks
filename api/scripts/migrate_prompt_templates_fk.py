#!/usr/bin/env python3
"""
Migration script to fix foreign key constraints in prompt_templates tables.
Removes foreign key references to master_users table which doesn't exist in tenant databases.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.models.database import get_master_db
from core.models.models import Tenant
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_prompt_templates_fk():
    """Remove foreign key constraints from prompt_templates tables in all tenant databases"""
    try:
        # Get master database session
        master_db = next(get_master_db())
        
        # Get all active tenants
        tenants = master_db.query(Tenant).filter(Tenant.is_active == True).all()
        
        logger.info(f"Found {len(tenants)} active tenants")

        for tenant in tenants:
            try:
                # Construct tenant database URL
                tenant_db_url = f"postgresql://postgres:password@postgres-master:5432/tenant_{tenant.id}"
                tenant_engine = create_engine(tenant_db_url)
                
                with tenant_engine.connect() as connection:
                    # Check if prompt_templates table exists
                    result = connection.execute(text("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'prompt_templates'
                    """))
                    
                    if not result.fetchone():
                        logger.info(f"prompt_templates table does not exist for tenant_{tenant.id}, skipping")
                        continue
                    
                    logger.info(f"Migrating prompt_templates table for tenant_{tenant.id}")
                    
                    # Drop foreign key constraints if they exist
                    try:
                        # Check for existing constraints
                        constraints = connection.execute(text("""
                            SELECT constraint_name 
                            FROM information_schema.table_constraints 
                            WHERE table_name = 'prompt_templates' 
                            AND constraint_type = 'FOREIGN KEY'
                        """)).fetchall()
                        
                        for constraint in constraints:
                            constraint_name = constraint[0]
                            if 'created_by' in constraint_name or 'updated_by' in constraint_name:
                                logger.info(f"Dropping constraint {constraint_name} from prompt_templates")
                                connection.execute(text(f"""
                                    ALTER TABLE prompt_templates DROP CONSTRAINT {constraint_name}
                                """))
                    
                    except Exception as e:
                        logger.warning(f"Error dropping constraints from prompt_templates: {e}")
                    
                    # Check if prompt_usage_logs table exists
                    result = connection.execute(text("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'prompt_usage_logs'
                    """))
                    
                    if result.fetchone():
                        logger.info(f"Migrating prompt_usage_logs table for tenant_{tenant.id}")
                        
                        try:
                            # Check for existing constraints
                            constraints = connection.execute(text("""
                                SELECT constraint_name 
                                FROM information_schema.table_constraints 
                                WHERE table_name = 'prompt_usage_logs' 
                                AND constraint_type = 'FOREIGN KEY'
                            """)).fetchall()
                            
                            for constraint in constraints:
                                constraint_name = constraint[0]
                                if 'user_id' in constraint_name:
                                    logger.info(f"Dropping constraint {constraint_name} from prompt_usage_logs")
                                    connection.execute(text(f"""
                                        ALTER TABLE prompt_usage_logs DROP CONSTRAINT {constraint_name}
                                    """))
                        
                        except Exception as e:
                            logger.warning(f"Error dropping constraints from prompt_usage_logs: {e}")
                    
                    connection.commit()
                    logger.info(f"Successfully migrated tenant_{tenant.id}")
                    
            except Exception as e:
                logger.error(f"Error processing tenant {tenant.id}: {e}")
                continue
        
        logger.info("Foreign key migration completed for all tenant databases")
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    migrate_prompt_templates_fk()
