-- LiteLLM Database Initialization Script
-- This script is idempotent and can be run multiple times safely

-- Create LiteLLM user (ignore if exists)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'llmproxy') THEN
    CREATE USER llmproxy WITH PASSWORD 'dbpassword9090';
  END IF;
END
$$;

-- Create LiteLLM database (ignore if exists)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'litellm') THEN
    CREATE DATABASE litellm OWNER llmproxy;
  END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE litellm TO llmproxy;
