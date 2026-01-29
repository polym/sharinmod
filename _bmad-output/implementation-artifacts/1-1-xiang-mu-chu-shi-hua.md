# Story 1.1: xiang-mu-chu-shi-hua

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to set up the project using the fastapi-nextjs starter template,
So that the development environment is ready.

## Acceptance Criteria

1. Given the starter template repository URL,
   When I clone and run the setup commands,
   Then the project has basic structure with FastAPI backend and Next.js frontend.

## Tasks / Subtasks

- [x] Clone the fastapi-nextjs repository
- [x] Configure .env file with necessary environment variables
- [x] Run docker-compose up --build to start services
- [x] Verify API access at http://localhost:8000
- [x] Verify frontend access at http://localhost:3000
- [x] Adapt the template structure for sharinmod project (rename directories if needed)

## Dev Notes

- Use the fastapi-nextjs starter template as specified in architecture.md
- Template includes FastAPI backend, Next.js frontend, PostgreSQL, Redis, Prometheus monitoring
- Latest template version is from 2 years ago (commit 9fef470), but technologies (FastAPI, Next.js) are still current and compatible
- Follow Docker Compose setup for consistent development environment
- Template has example models (towns, people) that need to be replaced with sharinmod models (users, tokens)
- Ensure .env configuration includes database URLs, secrets, etc.

### Project Structure Notes

- Align with unified project structure defined in architecture.md
- Backend in backend/ directory, frontend in frontend/
- Use provided docker-compose.yml for multi-container setup
- Database migrations with Alembic as specified
- Monitoring with Prometheus and Grafana included

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Starter Template Evaluation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- Template repository: https://github.com/Nneji123/fastapi-nextjs (last updated 2 years ago)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5

### Implementation Plan

Followed red-green-refactor cycle:
- RED: Created failing tests for each task (repository cloning, env config, docker-compose setup, structure adaptation)
- GREEN: Implemented minimal code to pass tests (cloned template, configured env/docker-compose, adapted structure)
- REFACTOR: Cleaned up configuration to match sharinmod requirements

### Debug Log References

#### Issue 1: PostgreSQL Image Not Found
- **Error**: `docker.io/bitnami/postgresql:13.3.0: not found`
- **Root Cause**: The bitnami/postgresql:13.3.0 image was not available or deprecated
- **Fix**: Updated to official `postgres:15-alpine` image
- **Files Modified**: docker-compose.yml (db service image and environment variables)

#### Issue 2: Database Connection Failed
- **Error**: Backend trying to connect to `postgres` host instead of `db`
- **Root Cause**: Service name mismatch between docker-compose.yml and configuration
- **Fix**: 
  - Updated docker-compose.yml backend environment to use service name `db`
  - Updated config.py default DATABASE_URI to use `db` as hostname
  - Added env_file reference in docker-compose.yml
- **Files Modified**: docker-compose.yml, backend/api/config.py

#### Issue 3: Frontend Port Mismatch
- **Error**: Frontend container listening on port 8080 instead of 3000
- **Root Cause**: Dockerfile CMD specified port 8080
- **Fix**: Updated Dockerfile to use port 3000
- **Files Modified**: frontend/Dockerfile

#### Issue 4: Missing Frontend Utils Module
- **Error**: `Module not found: Can't resolve '@/lib/utils'`
- **Root Cause**: Template missing utility function file
- **Fix**: Created utils.ts with cn() helper function for className merging
- **Files Modified**: frontend/src/lib/utils.ts (created)

### Completion Notes List

✅ All tasks completed with comprehensive test coverage:
1. Cloned fastapi-nextjs template to template/ subdirectory
2. Moved backend/, frontend/, docker-compose.yaml to project root
3. Created backend/.env with PostgreSQL configuration for sharinmod database
4. Updated docker-compose.yml:
   - Frontend port: 8080 → 3000
   - Database service: postgres → db (with postgres:15-alpine image)
   - Database name: dbname → sharinmod
   - Grafana port: 3000 → 3001 (避免与前端冲突)
   - Environment variables aligned with .env
   - Simplified volume configurations
5. Fixed database connection issues and verified all services running
6. Created missing frontend utility file
7. Verified project structure with tests covering all acceptance criteria

✅ All services verified and accessible:
- Database (PostgreSQL): localhost:5454 ✓
- Redis: localhost:6379 ✓
- Backend API: http://localhost:8000 ✓
- Frontend: http://localhost:3000 ✓
- Prometheus: http://localhost:9090 ✓
- Grafana: http://localhost:3001 ✓

📝 Note: Template example models (towns, people) remain for now - will be replaced with sharinmod models (users, tokens) in future stories

### File List

- backend/.env (created)
- backend/api/config.py (modified - database URI default)
- docker-compose.yml (modified - services, ports, images, volumes)
- frontend/Dockerfile (modified - port configuration)
- frontend/src/lib/utils.ts (created)
- test_clone.py (created)
- test_env.py (created)
- test_docker_compose.py (created)
- test_docker_verification.py (created)
- test_structure_adapted.py (created)
- test_integration.py (created)
- _bmad-output/implementation-artifacts/1-1-xiang-mu-chu-shi-hua.md (this file - updated)