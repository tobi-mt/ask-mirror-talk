-- Neon Database Initialization Script
-- Run this in Neon SQL Editor to set up your database

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- The rest of the schema will be created by SQLAlchemy when the app starts
-- This script just ensures pgvector is available

-- Optional: Create read-only user for analytics (if needed)
-- CREATE USER readonly WITH PASSWORD 'your-secure-password';
-- GRANT CONNECT ON DATABASE neondb TO readonly;
-- GRANT USAGE ON SCHEMA public TO readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;

-- Check database is ready
SELECT 
    'Database ready!' as status,
    current_database() as database,
    version() as postgres_version;
