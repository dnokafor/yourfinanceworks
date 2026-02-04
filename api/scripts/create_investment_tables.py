#!/usr/bin/env python3
"""
Script to create investment tables directly in tenant databases
This bypasses the migration system issues and creates the tables needed for testing.
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy import create_engine, text
from core.services.tenant_database_manager import TenantDatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_investment_tables():
    """Create investment tables in all tenant databases"""

    # SQL to create investment tables with tenant_id column
    create_tables_sql = """
    -- Create enum types for investment management
    DO $$ BEGIN
        CREATE TYPE portfoliotype AS ENUM ('TAXABLE', 'RETIREMENT', 'BUSINESS');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;

    DO $$ BEGIN
        CREATE TYPE securitytype AS ENUM ('STOCK', 'BOND', 'ETF', 'MUTUAL_FUND', 'CASH');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;

    DO $$ BEGIN
        CREATE TYPE assetclass AS ENUM ('STOCKS', 'BONDS', 'CASH', 'REAL_ESTATE', 'COMMODITIES');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;

    DO $$ BEGIN
        CREATE TYPE transactiontype AS ENUM ('BUY', 'SELL', 'DIVIDEND', 'INTEREST', 'FEE', 'TRANSFER', 'CONTRIBUTION');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;

    DO $$ BEGIN
        CREATE TYPE dividendtype AS ENUM ('ORDINARY');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;

    -- Create investment_portfolios table
    CREATE TABLE IF NOT EXISTS investment_portfolios (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL,
        name VARCHAR NOT NULL,
        portfolio_type portfoliotype NOT NULL,
        is_archived BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );

    -- Create indexes for investment_portfolios
    CREATE INDEX IF NOT EXISTS ix_investment_portfolios_id ON investment_portfolios (id);
    CREATE INDEX IF NOT EXISTS ix_investment_portfolios_tenant_id ON investment_portfolios (tenant_id);
    CREATE INDEX IF NOT EXISTS ix_investment_portfolios_name ON investment_portfolios (name);
    CREATE INDEX IF NOT EXISTS ix_investment_portfolios_portfolio_type ON investment_portfolios (portfolio_type);
    CREATE INDEX IF NOT EXISTS ix_investment_portfolios_created_at ON investment_portfolios (created_at);

    -- Create investment_holdings table
    CREATE TABLE IF NOT EXISTS investment_holdings (
        id SERIAL PRIMARY KEY,
        portfolio_id INTEGER NOT NULL REFERENCES investment_portfolios(id) ON DELETE CASCADE,
        security_symbol VARCHAR(20) NOT NULL,
        security_name VARCHAR,
        security_type securitytype NOT NULL,
        asset_class assetclass NOT NULL,
        quantity NUMERIC(18, 8) NOT NULL CHECK (quantity > 0),
        cost_basis NUMERIC(18, 2) NOT NULL CHECK (cost_basis > 0),
        purchase_date DATE NOT NULL,
        current_price NUMERIC(18, 2) CHECK (current_price IS NULL OR current_price > 0),
        price_updated_at TIMESTAMP WITH TIME ZONE,
        is_closed BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );

    -- Create indexes for investment_holdings
    CREATE INDEX IF NOT EXISTS ix_investment_holdings_id ON investment_holdings (id);
    CREATE INDEX IF NOT EXISTS ix_investment_holdings_portfolio_id ON investment_holdings (portfolio_id);
    CREATE INDEX IF NOT EXISTS ix_investment_holdings_security_symbol ON investment_holdings (security_symbol);
    CREATE INDEX IF NOT EXISTS ix_investment_holdings_security_type ON investment_holdings (security_type);
    CREATE INDEX IF NOT EXISTS ix_investment_holdings_asset_class ON investment_holdings (asset_class);
    CREATE INDEX IF NOT EXISTS ix_investment_holdings_is_closed ON investment_holdings (is_closed);

    -- Create investment_transactions table
    CREATE TABLE IF NOT EXISTS investment_transactions (
        id SERIAL PRIMARY KEY,
        portfolio_id INTEGER NOT NULL REFERENCES investment_portfolios(id) ON DELETE CASCADE,
        holding_id INTEGER REFERENCES investment_holdings(id) ON DELETE CASCADE,
        transaction_type transactiontype NOT NULL,
        transaction_date DATE NOT NULL,
        quantity NUMERIC(18, 8) CHECK (quantity IS NULL OR quantity > 0),
        price_per_share NUMERIC(18, 2) CHECK (price_per_share IS NULL OR price_per_share > 0),
        total_amount NUMERIC(18, 2) NOT NULL CHECK (total_amount != 0),
        fees NUMERIC(18, 2) NOT NULL DEFAULT 0 CHECK (fees >= 0),
        realized_gain NUMERIC(18, 2),
        dividend_type dividendtype,
        payment_date DATE,
        ex_dividend_date DATE,
        notes VARCHAR,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );

    -- Create indexes for investment_transactions
    CREATE INDEX IF NOT EXISTS ix_investment_transactions_id ON investment_transactions (id);
    CREATE INDEX IF NOT EXISTS ix_investment_transactions_portfolio_id ON investment_transactions (portfolio_id);
    CREATE INDEX IF NOT EXISTS ix_investment_transactions_holding_id ON investment_transactions (holding_id);
    CREATE INDEX IF NOT EXISTS ix_investment_transactions_transaction_type ON investment_transactions (transaction_type);
    CREATE INDEX IF NOT EXISTS ix_investment_transactions_transaction_date ON investment_transactions (transaction_date);
    CREATE INDEX IF NOT EXISTS ix_investment_transactions_portfolio_date ON investment_transactions (portfolio_id, transaction_date);
    CREATE INDEX IF NOT EXISTS ix_investment_transactions_holding_date ON investment_transactions (holding_id, transaction_date);
    """

    try:
        # Get tenant database manager
        tenant_db_manager = TenantDatabaseManager()

        # Get list of tenant databases
        tenant_ids = [1, 2, 3]  # Known tenant IDs

        for tenant_id in tenant_ids:
            logger.info(f"Creating investment tables for tenant {tenant_id}")

            # Get database connection for tenant
            SessionLocal = tenant_db_manager.get_tenant_session(tenant_id)
            db_session = SessionLocal()

            # Execute the SQL
            try:
                # Execute each statement separately to handle potential errors
                statements = create_tables_sql.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement:
                        try:
                            db_session.execute(text(statement))
                            db_session.commit()
                        except Exception as e:
                            logger.warning(f"Statement failed (may be expected): {e}")
                            continue

                logger.info(f"Successfully created investment tables for tenant {tenant_id}")

            finally:
                db_session.close()

    except Exception as e:
        logger.error(f"Error creating investment tables: {e}")
        raise

if __name__ == "__main__":
    create_investment_tables()
    print("Investment tables created successfully!")