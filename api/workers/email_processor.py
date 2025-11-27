import asyncio
import logging
import os
import time
import email
import imaplib
from email.header import decode_header
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

# Import models and services
from models.database import get_db, get_master_db, set_tenant_context
from models.models import Tenant, Settings as MasterSettings
from models.models_per_tenant import Settings, RawEmail, Expense, ExpenseAttachment
from services.tenant_database_manager import tenant_db_manager
from services.email_ingestion_service import EmailIngestionService
from constants.expense_status import ExpenseStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailProcessorWorker:
    def __init__(self):
        self.poll_interval = int(os.getenv("EMAIL_POLL_INTERVAL", "60"))
        self.batch_size = int(os.getenv("EMAIL_BATCH_SIZE", "10"))
        self.running = True

    async def start(self):
        logger.info("Starting Email Processor Worker...")
        while self.running:
            try:
                await self.process_all_tenants()
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
            
            logger.info(f"Sleeping for {self.poll_interval} seconds...")
            await asyncio.sleep(self.poll_interval)

    async def process_all_tenants(self):
        """Iterate through all active tenants and process their emails."""
        # Get all active tenants from master DB
        # Use get_master_db() to avoid tenant context check
        db = next(get_master_db())
        try:
            tenants = db.query(Tenant).filter(Tenant.is_active == True).all()
            logger.info(f"Found {len(tenants)} active tenants to process.")
            
            for tenant in tenants:
                try:
                    await self.process_tenant(tenant.id)
                except Exception as e:
                    logger.error(f"Error processing tenant {tenant.id}: {e}", exc_info=True)
        finally:
            db.close()

    async def process_tenant(self, tenant_id: int):
        """Process emails for a specific tenant."""
        logger.info(f"Processing tenant {tenant_id}...")
        
        # Set tenant context
        set_tenant_context(tenant_id)
        
        # Get tenant DB session
        SessionLocal = tenant_db_manager.get_tenant_session(tenant_id)
        if not SessionLocal:
            logger.warning(f"Could not get DB session for tenant {tenant_id}")
            return

        db = SessionLocal()
        try:
            # Check if email integration is enabled
            # We can use the service to check config and run logic
            # We need a user_id for the service. 
            # We'll try to find an admin user.
            from models.models_per_tenant import User
            admin_user = db.query(User).filter(User.role == "admin").first()
            user_id = admin_user.id if admin_user else 1 # Fallback
            
            service = EmailIngestionService(db, user_id, tenant_id)
            
            # Check if enabled
            if not service.settings or not service.settings.get("enabled", False):
                return

            config = service.settings
            
            # 1. Poll IMAP and save to RawEmail
            # Run in executor to avoid blocking the async loop with blocking I/O
            loop = asyncio.get_event_loop()
            downloaded = await loop.run_in_executor(None, service.poll_and_save, config)
            if downloaded > 0:
                logger.info(f"Tenant {tenant_id}: Downloaded {downloaded} new emails.")
            
            # 2. Process pending RawEmails
            # Process in batches
            processed = await loop.run_in_executor(None, service.process_pending_emails, self.batch_size)
            if processed > 0:
                logger.info(f"Tenant {tenant_id}: Processed {processed} emails.")
            
        except Exception as e:
            logger.error(f"Error processing tenant {tenant_id}: {e}", exc_info=True)
        finally:
            db.close()

if __name__ == "__main__":
    worker = EmailProcessorWorker()
    asyncio.run(worker.start())
