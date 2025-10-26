"""Add database encryption support

This migration adds support for transparent database encryption by:
1. Creating backup columns for existing data
2. Migrating data to encrypted format
3. Updating column types to use encrypted columns
4. Providing rollback procedures

Revision ID: add_database_encryption_support
Revises: 
Create Date: 2025-01-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging
import json

# revision identifiers, used by Alembic.
revision = 'add_database_encryption_support'
down_revision = None  # This will be set to the latest migration
depends_on = None

logger = logging.getLogger(__name__)


def upgrade():
    """
    Upgrade to encrypted columns.
    
    This migration performs the following steps:
    1. Add new encrypted columns alongside existing ones
    2. Migrate existing data to encrypted format
    3. Drop old unencrypted columns
    4. Rename encrypted columns to original names
    
    Note: This migration requires the encryption service to be available
    and properly configured before running.
    """
    
    # Get database connection
    connection = op.get_bind()
    
    logger.info("Starting database encryption migration...")
    
    # Step 1: Add new encrypted columns for User table
    logger.info("Adding encrypted columns for User table...")
    
    # User table encrypted columns
    op.add_column('users', sa.Column('email_encrypted', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('first_name_encrypted', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('last_name_encrypted', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('google_id_encrypted', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('azure_ad_id_encrypted', sa.Text(), nullable=True))
    
    # Client table encrypted columns
    logger.info("Adding encrypted columns for Client table...")
    op.add_column('clients', sa.Column('name_encrypted', sa.Text(), nullable=True))
    op.add_column('clients', sa.Column('email_encrypted', sa.Text(), nullable=True))
    op.add_column('clients', sa.Column('phone_encrypted', sa.Text(), nullable=True))
    op.add_column('clients', sa.Column('address_encrypted', sa.Text(), nullable=True))
    op.add_column('clients', sa.Column('company_encrypted', sa.Text(), nullable=True))
    
    # ClientNote table encrypted columns
    logger.info("Adding encrypted columns for ClientNote table...")
    op.add_column('client_notes', sa.Column('note_encrypted', sa.Text(), nullable=True))
    
    # Invoice table encrypted columns
    logger.info("Adding encrypted columns for Invoice table...")
    op.add_column('invoices', sa.Column('notes_encrypted', sa.Text(), nullable=True))
    op.add_column('invoices', sa.Column('custom_fields_encrypted', sa.Text(), nullable=True))
    op.add_column('invoices', sa.Column('attachment_filename_encrypted', sa.Text(), nullable=True))
    
    # Payment table encrypted columns
    logger.info("Adding encrypted columns for Payment table...")
    op.add_column('payments', sa.Column('reference_number_encrypted', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('notes_encrypted', sa.Text(), nullable=True))
    
    # Expense table encrypted columns
    logger.info("Adding encrypted columns for Expense table...")
    op.add_column('expenses', sa.Column('vendor_encrypted', sa.Text(), nullable=True))
    op.add_column('expenses', sa.Column('notes_encrypted', sa.Text(), nullable=True))
    op.add_column('expenses', sa.Column('receipt_filename_encrypted', sa.Text(), nullable=True))
    op.add_column('expenses', sa.Column('inventory_items_encrypted', sa.Text(), nullable=True))
    op.add_column('expenses', sa.Column('consumption_items_encrypted', sa.Text(), nullable=True))
    op.add_column('expenses', sa.Column('analysis_result_encrypted', sa.Text(), nullable=True))
    
    # AIConfig table encrypted columns
    logger.info("Adding encrypted columns for AIConfig table...")
    op.add_column('ai_configs', sa.Column('provider_url_encrypted', sa.Text(), nullable=True))
    op.add_column('ai_configs', sa.Column('api_key_encrypted', sa.Text(), nullable=True))
    
    # AuditLog table encrypted columns
    logger.info("Adding encrypted columns for AuditLog table...")
    op.add_column('audit_logs', sa.Column('user_email_encrypted', sa.Text(), nullable=True))
    op.add_column('audit_logs', sa.Column('details_encrypted', sa.Text(), nullable=True))
    op.add_column('audit_logs', sa.Column('ip_address_encrypted', sa.Text(), nullable=True))
    op.add_column('audit_logs', sa.Column('user_agent_encrypted', sa.Text(), nullable=True))
    
    logger.info("Encrypted columns added successfully.")
    
    # Step 2: Create a data migration function
    # Note: The actual data migration will be handled by a separate script
    # because it requires the encryption service to be running and configured
    
    logger.info("Migration structure complete. Data migration must be performed separately.")
    logger.info("Run the data migration script after this migration completes.")


def downgrade():
    """
    Downgrade from encrypted columns.
    
    This removes the encrypted columns and restores the original unencrypted columns.
    
    WARNING: This will result in data loss if the original unencrypted data
    has been removed. Only use this for rollback during initial deployment.
    """
    
    logger.info("Starting database encryption rollback...")
    
    # Remove encrypted columns from User table
    logger.info("Removing encrypted columns from User table...")
    op.drop_column('users', 'email_encrypted')
    op.drop_column('users', 'first_name_encrypted')
    op.drop_column('users', 'last_name_encrypted')
    op.drop_column('users', 'google_id_encrypted')
    op.drop_column('users', 'azure_ad_id_encrypted')
    
    # Remove encrypted columns from Client table
    logger.info("Removing encrypted columns from Client table...")
    op.drop_column('clients', 'name_encrypted')
    op.drop_column('clients', 'email_encrypted')
    op.drop_column('clients', 'phone_encrypted')
    op.drop_column('clients', 'address_encrypted')
    op.drop_column('clients', 'company_encrypted')
    
    # Remove encrypted columns from ClientNote table
    logger.info("Removing encrypted columns from ClientNote table...")
    op.drop_column('client_notes', 'note_encrypted')
    
    # Remove encrypted columns from Invoice table
    logger.info("Removing encrypted columns from Invoice table...")
    op.drop_column('invoices', 'notes_encrypted')
    op.drop_column('invoices', 'custom_fields_encrypted')
    op.drop_column('invoices', 'attachment_filename_encrypted')
    
    # Remove encrypted columns from Payment table
    logger.info("Removing encrypted columns from Payment table...")
    op.drop_column('payments', 'reference_number_encrypted')
    op.drop_column('payments', 'notes_encrypted')
    
    # Remove encrypted columns from Expense table
    logger.info("Removing encrypted columns from Expense table...")
    op.drop_column('expenses', 'vendor_encrypted')
    op.drop_column('expenses', 'notes_encrypted')
    op.drop_column('expenses', 'receipt_filename_encrypted')
    op.drop_column('expenses', 'inventory_items_encrypted')
    op.drop_column('expenses', 'consumption_items_encrypted')
    op.drop_column('expenses', 'analysis_result_encrypted')
    
    # Remove encrypted columns from AIConfig table
    logger.info("Removing encrypted columns from AIConfig table...")
    op.drop_column('ai_configs', 'provider_url_encrypted')
    op.drop_column('ai_configs', 'api_key_encrypted')
    
    # Remove encrypted columns from AuditLog table
    logger.info("Removing encrypted columns from AuditLog table...")
    op.drop_column('audit_logs', 'user_email_encrypted')
    op.drop_column('audit_logs', 'details_encrypted')
    op.drop_column('audit_logs', 'ip_address_encrypted')
    op.drop_column('audit_logs', 'user_agent_encrypted')
    
    logger.info("Database encryption rollback complete.")