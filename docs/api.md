# Forma3D API Guide

Base URL (default): `http://localhost:8000/api/v1`

## Auth
- Controlled by `AUTH_MODE` (`disabled`, `optional`, `required`).
- When enabled, pass `Authorization: Bearer <token>` (Supabase JWT). Anonymous uploads are allowed when `AUTH_MODE=optional`.

## Endpoints
- `POST /jobs/upload` — Upload 1..20 images (max 50MB each, 200MB total). Rate limited (default 30 req / 60s per user/IP).
  ```bash
  curl -X POST "http://localhost:8000/api/v1/jobs/upload" \
    -F "files=@test_image.jpg"
  ```
- `GET /jobs/status/{job_id}` — Poll job status (`queued`, `processing`, `completed`, `completed_partial`, `failed`).
- `GET /jobs` — List jobs for the current user (or all when auth is disabled).
- `GET /jobs/download/{job_id}?format=obj|stl|gltf|glb|ply` — Download converted mesh.
- `POST /jobs/{job_id}/scale` — Scale a completed mesh to a target dimension (axes: `x|y|z`).
- `GET /health` — Liveness probe.
- `GET /ready` — Readiness probe.

## Docs
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI schema: `/openapi.json`
