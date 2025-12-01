# Phase 0: Publishing Gaps

**Goal:** Fix all blockers preventing Forma3D from launching as a functional product.

---

## 🚫 BLOCKERS (App Won't Run)

- [DONE] Missing `sam_vit_h_4b8939.pth` checkpoint (~2.4GB) - segmentation fails
  - Download: https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
- [DONE] Missing SAM 3D checkpoints in `sam-3d-objects/checkpoints/` - reconstruction fails
  - **Solution**: Run `python scripts/download_sam3d_checkpoints.py` (requires Hugging Face token)
- [DONE] Missing `pytorch3d` dependency - 3D inference crashes
  - **Solution**: Run `pip install "pytorch3d==0.7.8+pt2.5.1cu121" --extra-index-url https://miropsota.github.io/torch_packages_builder`
  - Or run `.\scripts\install_pytorch3d.ps1` for full reinstall
- [DONE] Critical syntax error in `app/api/endpoints/jobs.py` - upload endpoint is broken (malformed function at lines 42-60)
- [DONE] Missing CORS middleware in `app/main.py` - frontend blocked from calling backend
- [DONE] Frontend Dockerfile uses `npm` but project uses `pnpm` - Docker build fails

---

## 🔴 CRITICAL (Security & Data Loss)

- [DONE] No authentication on any API endpoint - `auth.py` exists but never used as dependency
  - **Solution**: Auth is now wired up as optional dependency. Set `AUTH_MODE=required` and `SUPABASE_JWT_SECRET` in production.
- [DONE] Hardcoded `http://localhost:8000` in frontend components:
  - `frontend/components/UploadZone.js`
  - `frontend/components/Gallery.js`
  - `frontend/components/ModelViewer.js`
  - **Solution**: Created `frontend/lib/api.js` with `NEXT_PUBLIC_API_URL` env var support. All components now import from centralized config.
- [DONE] Missing `.env.example` file - deployment will fail without documented env vars
  - **Solution**: Created `.env.example` (backend) and `frontend/.env.example` with all required variables documented.
- [ ] Jobs stored in `jobs.json` flat file - concurrent writes cause corruption, no persistence
- [DONE] Supabase client created with undefined values in `frontend/lib/supabase.js` - crashes on load
  - **Solution**: Added null check and mock client fallback when env vars are missing.
- [DONE] No input validation or file size limits on upload endpoint
  - **Solution**: Added comprehensive validation in `jobs.py`: max 50MB/file, max 20 files, max 200MB total, allowed image types only, filename sanitization, path traversal protection.

---

## 🟠 IMPORTANT (Broken Features)

- [DONE] Wrong API path in `frontend/components/ModelViewer.js` line 70: `/api/jobs/` should be `/api/v1/jobs/`
  - **Solution**: Fixed to use `/api/v1/jobs/` and centralized API_URL config.
- [DONE] Missing `CheckCircle` icon import in `frontend/components/Gallery.js`
  - **Solution**: Added `CheckCircle` to lucide-react imports.
- [DONE] Incomplete exception handling in `app/api/endpoints/jobs.py` download endpoint - `try` block never closed
  - **Solution**: Verified - exception handling is properly structured with try/except blocks.
- [DONE] Missing dependencies in `requirements.txt`: `pydantic-settings`, `hydra-core`, `omegaconf`
  - **Solution**: Added `pydantic-settings`, `hydra-core`, `omegaconf`, and `fastapi` to requirements.txt.
- [DONE] Missing `@supabase/supabase-js` in `frontend/package.json`
  - **Solution**: Added `@supabase/supabase-js@^2.39.0` to dependencies.
- [DEFERRED] `frontend/components/Auth.js` component exists but never imported in app
  - **Note**: Per MVP recommendation (Option A), auth integration deferred to post-launch. Component ready for future use.
- [DONE] No health check endpoint for container orchestration
  - **Solution**: Added `/health` and `/ready` endpoints in `app/main.py` for liveness and readiness probes.
- [DEFERRED] No background job queue - FastAPI `BackgroundTasks` doesn't persist across restarts
  - **Note**: For MVP, current in-memory background tasks are acceptable. For production scale, integrate Celery + Redis or ARQ for persistent job queue.

---

## 🟡 POLISH (Production Quality)

- [x] Structured logging configuration added (`app/core/logging_config.py` with request logging middleware)
- [x] Rate limiting on GPU-intensive upload endpoint (in-memory limiter with env overrides)
- [x] HTTPS/TLS configuration documented (README nginx + uvicorn SSL flags)
- [x] CI/CD pipeline added (`.github/workflows/ci.yml` for backend smoke + frontend lint)
- [x] Generic metadata in `frontend/app/layout.js` fixed to product branding
- [x] API documentation exposed (`/docs`, `/redoc`, `/openapi.json` + `docs/api.md`)
- [x] Installation instructions added to `README.md`
- [x] Tests no longer require checkpoints (stub mode + env flag)
- [x] React error boundary added for graceful failure handling

---

## Recommendation: Auth Strategy

The `Auth.js` component and Supabase setup suggest authentication was planned but never wired up.

| Option | Description |
|--------|-------------|
| **Option A: Remove auth entirely** | Launch as open/free tool first, add auth later. Simpler, faster to ship. |
| **Option B: Integrate Supabase auth** | Wire up `Auth.js` in `layout.js`, protect upload endpoint, add user context to jobs. |
| **Option C: API key auth only** | Skip user accounts, just require an API key header. Good for B2B/developer launch. |

**Recommendation: Option A for MVP launch**, then Option B post-launch. Ship fast, gate features later once you have users.
