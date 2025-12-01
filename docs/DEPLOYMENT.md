# Production Deployment Checklist

## Critical environment variables
Set these secrets in your production platform (e.g., AWS ECS, Render, Fly.io, or Kubernetes) before deploying:

- `POSTGRES_SERVER` – PostgreSQL host or service name
- `POSTGRES_PORT` – PostgreSQL port (default `5432`)
- `POSTGRES_USER` – database user with DDL/DML rights
- `POSTGRES_PASSWORD` – database password
- `POSTGRES_DB` – application database name
- `REDIS_URL` – Redis connection URL for rate limiting and Celery (e.g., `redis://redis:6379/0`)
- `LOG_LEVEL` – optional, defaults to `INFO`
- `RATE_LIMIT_UPLOAD_MAX_REQUESTS` – optional per-minute burst cap (default `30`)
- `RATE_LIMIT_UPLOAD_WINDOW_SECONDS` – optional window in seconds (default `60`)
- `NVIDIA_VISIBLE_DEVICES` / `NVIDIA_DRIVER_CAPABILITIES` – if GPUs are available for reconstruction
- **Frontend-only:** `NEXT_PUBLIC_API_URL` – public backend URL used by the client

### API key provisioning
Create at least one `User` record with a unique API key (stored hashed in the DB). Distribute the raw key securely to clients; never commit it.

## Build and run the stack

```bash
# 1) Build images (backend shares image with the Celery worker)
docker compose build

# 2) Start dependencies + backend + worker + frontend
docker compose up -d postgres redis
# initialize database schema
docker compose run --rm backend alembic upgrade head
# launch app + worker + frontend
docker compose up -d backend worker frontend

# 3) Check logs for readiness
docker compose logs -f backend worker frontend
```

## Operational notes
- Ensure the shared `storage/` volume is persisted and mounted for both API and worker containers so uploaded assets and generated meshes stay consistent.
- pgAdmin is available on port `5050` for DB inspection; secure or disable it in production.
- Health checks: `GET /health` is unauthenticated; all project/job endpoints require `X-API-Key`.
- Celery uses Redis for broker/result storage; scale workers horizontally with `docker compose up --scale worker=N worker`.

## Merge readiness
With migrations, API-key auth, Celery queueing, and sanitized uploads in place, this branch is ready to merge and deploy following the steps above.
