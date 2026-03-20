# LiteLLM Database Setup

This document records the database setup for LiteLLM in Docker Compose environment.

## Automated Initialization (Recommended)

The LiteLLM database is now automatically initialized on first startup using the init script at `etc/init-litellm-db.sql`. This script:

- Creates the `llmproxy` user with password `dbpassword9090`
- Creates the `litellm` database owned by `llmproxy`
- Grants all privileges on the database

Simply start the services and the database will be initialized automatically:

```bash
docker-compose up -d
```

The init script is idempotent and can be run multiple times safely.

## Manual Database Initialization (Legacy)

The LiteLLM database can also be initialized manually if needed:

```bash
# Start database service
docker-compose up -d db redis

# Create llmproxy user
docker exec -i sharinmod-ws1-db-1 psql -U postgres -c "CREATE USER llmproxy WITH PASSWORD 'dbpassword9090';"

# Create litellm database
docker exec -i sharinmod-ws1-db-1 psql -U postgres -c "CREATE DATABASE litellm OWNER llmproxy;"

# Grant privileges
docker exec -i sharinmod-ws1-db-1 psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE litellm TO llmproxy;"
```

## Database Details

- **Database Name**: `litellm`
- **Owner**: `llmproxy`
- **Password**: `dbpassword9090`
- **Connection String**: `postgresql://llmproxy:dbpassword9090@db:5432/litellm`

## Verification

To verify the database was created correctly:

```bash
docker exec -i sharinmod-ws1-db-1 psql -U postgres -c "\l litellm"
```

Expected output should show the database owned by `llmproxy`.

## Environment Variables

The following environment variables are configured in `docker-compose.yml`:

```yaml
- DATABASE_URL=postgresql://${LITELLM_DB_USER:-llmproxy}:${LITELLM_DB_PASSWORD:-dbpassword9090}@db:5432/litellm
- STORE_MODEL_IN_DB=True
```

## Notes

- The database credentials can be customized using environment variables `LITELLM_DB_USER` and `LITELLM_DB_PASSWORD`
- The default values match the k8s.yaml configuration for consistency
- The database is shared with the main sharinmod database in the same PostgreSQL container
