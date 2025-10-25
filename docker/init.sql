-- PostgreSQL initialization script for Ruth database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create database if not exists (in case we need multiple databases)
-- This is handled by Docker environment variables, but kept for reference
-- CREATE DATABASE ruth_db;

-- Grant all privileges to the ruth_user (handled by Docker, but explicit here)
GRANT ALL PRIVILEGES ON DATABASE ruth_db TO ruth_user;

-- Create schema if needed
CREATE SCHEMA IF NOT EXISTS public;

-- Set default search path
ALTER DATABASE ruth_db SET search_path TO public;

-- Optional: Create initial indexes for better performance
-- These will also be created by Alembic migrations, but having them
-- from the start can help with development

-- Set default timezone
SET timezone = 'UTC';

-- Add any custom database functions or triggers here as needed