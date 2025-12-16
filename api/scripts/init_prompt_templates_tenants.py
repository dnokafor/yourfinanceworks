#!/usr/bin/env python3
"""
Script to initialize prompt templates tables in all tenant databases.
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

def init_prompt_templates_tenants():
    """Initialize prompt templates tables in all tenant databases"""
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
                    # Check if prompt_templates table already exists
                    result = connection.execute(text("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'prompt_templates'
                    """))
                    
                    prompt_templates_exists = result.fetchone() is not None
                    
                    # Check if prompt_usage_logs table already exists
                    result = connection.execute(text("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = 'prompt_usage_logs'
                    """))
                    
                    prompt_usage_logs_exists = result.fetchone() is not None
                    
                    if prompt_templates_exists and prompt_usage_logs_exists:
                        logger.info(f"Prompt templates tables already exist in tenant_{tenant.id} database")
                    else:
                        # Create prompt_templates table
                        if not prompt_templates_exists:
                            logger.info(f"Creating prompt_templates table in tenant_{tenant.id} database")
                            connection.execute(text("""
                                CREATE TABLE prompt_templates (
                                    id SERIAL PRIMARY KEY,
                                    name VARCHAR(100) NOT NULL UNIQUE,
                                    category VARCHAR(50) NOT NULL,
                                    description TEXT,
                                    template_content TEXT NOT NULL,
                                    template_variables JSON,
                                    output_format VARCHAR(20) DEFAULT 'json',
                                    default_values JSON,
                                    version INTEGER DEFAULT 1,
                                    is_active BOOLEAN DEFAULT TRUE,
                                    provider_overrides JSON,
                                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                    created_by INTEGER,
                                    updated_by INTEGER
                                )
                            """))
                            
                            # Create indexes
                            connection.execute(text("""
                                CREATE INDEX ix_prompt_templates_category ON prompt_templates (category)
                            """))
                            connection.execute(text("""
                                CREATE INDEX ix_prompt_templates_name ON prompt_templates (name)
                            """))
                            
                            logger.info(f"Successfully created prompt_templates table in tenant_{tenant.id} database")
                        
                        # Create prompt_usage_logs table
                        if not prompt_usage_logs_exists:
                            logger.info(f"Creating prompt_usage_logs table in tenant_{tenant.id} database")
                            connection.execute(text("""
                                CREATE TABLE prompt_usage_logs (
                                    id SERIAL PRIMARY KEY,
                                    template_id INTEGER NOT NULL,
                                    tenant_id INTEGER,
                                    user_id INTEGER,
                                    provider_name VARCHAR(50) NOT NULL,
                                    model_name VARCHAR(100) NOT NULL,
                                    processing_time_ms INTEGER,
                                    token_count INTEGER,
                                    success BOOLEAN NOT NULL,
                                    error_message TEXT,
                                    input_preview TEXT,
                                    output_preview TEXT,
                                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                                )
                            """))
                            
                            # Create indexes
                            connection.execute(text("""
                                CREATE INDEX ix_prompt_usage_logs_template_id ON prompt_usage_logs (template_id)
                            """))
                            connection.execute(text("""
                                CREATE INDEX ix_prompt_usage_logs_tenant_id ON prompt_usage_logs (tenant_id)
                            """))
                            
                            logger.info(f"Successfully created prompt_usage_logs table in tenant_{tenant.id} database")
                    
                    connection.commit()
                    
            except Exception as e:
                logger.error(f"Error processing tenant {tenant.id}: {e}")
                continue
        
        logger.info("Prompt templates tables initialization completed for all tenant databases")
        
    except Exception as e:
        logger.error(f"Error initializing prompt templates tables: {e}")
        raise

if __name__ == "__main__":
    init_prompt_templates_tenants()
