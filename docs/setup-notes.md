# LiteLLM Database Setup

This document records the database setup for LiteLLM in Docker Compose environment.

## Database Initialization

The LiteLLM database was initialized with the following steps:

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