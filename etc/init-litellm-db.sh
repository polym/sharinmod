#!/bin/bash
# LiteLLM Database Initialization Script

set -e

# Create LiteLLM user
psql -v ON_ERROR_STOP=1 -U postgres -d sharinmod -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'llmproxy') THEN CREATE USER llmproxy WITH PASSWORD 'dbpassword9090'; END IF; END \$\$;"

# Create database if not exists using conditional execution
psql -U postgres -d sharinmod -tAc "SELECT 1 FROM pg_database WHERE datname = 'litellm'" > /dev/null || psql -U postgres -d sharinmod -c "CREATE DATABASE litellm OWNER llmproxy"

# Grant privileges
psql -U postgres -d sharinmod -c "GRANT ALL PRIVILEGES ON DATABASE litellm TO llmproxy"

# Grant schema privileges on litellm database
psql -U postgres -d litellm -c "GRANT ALL ON SCHEMA public TO llmproxy"

echo "LiteLLM database initialization completed successfully."
