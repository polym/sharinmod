#!/bin/bash
# LiteLLM Database Initialization Script

set -e

# Create LiteLLM user
psql -v ON_ERROR_STOP=1 --no-password -U postgres <<-EOSQL
    DO \$\$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'llmproxy') THEN
            CREATE USER llmproxy WITH PASSWORD 'dbpassword9090';
        END IF;
    END \$\$;
EOSQL

# Create database if not exists
psql -v ON_ERROR_STOP=1 --no-password -U postgres <<-EOSQL
    SELECT 'CREATE DATABASE litellm OWNER llmproxy'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'litellm')\\gexec
EOSQL

# Grant privileges
psql -v ON_ERROR_STOP=1 --no-password -U postgres -c 'GRANT ALL PRIVILEGES ON DATABASE litellm TO llmproxy'

# Grant schema privileges on litellm database
psql -v ON_ERROR_STOP=1 --no-password -U postgres -d litellm -c "GRANT ALL ON SCHEMA public TO llmproxy"

echo "LiteLLM database initialization completed successfully."
