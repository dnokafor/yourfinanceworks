-- Initialize PostgreSQL database for Invoice App
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Create a function to update the updated_at column automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create AI configs table if it doesn't exist (for new tenant databases)
CREATE TABLE IF NOT EXISTS ai_configs (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR NOT NULL,
    provider_url VARCHAR,
    api_key VARCHAR,
    model_name VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    tested BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for ai_configs table
CREATE INDEX IF NOT EXISTS idx_ai_configs_provider_name ON ai_configs (provider_name);
CREATE INDEX IF NOT EXISTS idx_ai_configs_is_active ON ai_configs (is_active);
CREATE INDEX IF NOT EXISTS idx_ai_configs_is_default ON ai_configs (is_default);
CREATE INDEX IF NOT EXISTS idx_ai_configs_tested ON ai_configs (tested); 