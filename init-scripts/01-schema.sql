-- Database Schema Initialization Script
-- This script runs automatically when the container starts for the first time

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create prospects table
CREATE TABLE IF NOT EXISTS prospects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    company_country varchar(2) NOT NULL,
    company_state varchar(2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create prospects_users_matches table
-- create table if not exists prospects_users_matches (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
--     prospect_id UUID NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
--     company_country VARCHAR(2) NOT NULL,
--     company_state VARCHAR(2) DEFAULT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     CONSTRAINT unique_user_prospect UNIQUE(user_id, prospect_id)
-- );

-- Create prospects_users_matches table
create table if not exists prospects_users_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    prospect_id UUID NOT NULL,
    company_country VARCHAR(2) NOT NULL,
    company_state VARCHAR(2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_prospect UNIQUE(user_id, prospect_id)
);
-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_prospects_users_matches_prospect_id ON prospects_users_matches(prospect_id);
CREATE INDEX IF NOT EXISTS idx_prospects_users_matches_user_id ON prospects_users_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_prospects_users_matches_country ON prospects_users_matches(company_country);


-- Insert sample data 
INSERT INTO users (username, email, password_hash) VALUES
    ('admin', 'admin@example.com', 'hashed_password_here'),
    ('testuser', 'test@example.com', 'hashed_password_here')
ON CONFLICT (username) DO NOTHING;

INSERT INTO prospects (name, description, company_country, company_state) VALUES
    ('Sample Prospect 1', 'This is a sample prospect', 'US', 'CA'),
    ('Sample Prospect 2', 'Another sample prospect', 'US', NULL),
    ('Sample Prospect 3', 'Third sample prospect', 'US', NULL)
ON CONFLICT DO NOTHING;

