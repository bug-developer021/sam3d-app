import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router
from app.core.logging_config import (
    build_request_log_extra,
    generate_request_id,
    setup_logging,
)
from app.core.rate_limit import init_rate_limiter

# Configure structured logging for the whole application
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("forma3d.api")

api_description = """
Forma3D API for converting user photos into downloadable 3D assets.

**Auth**
- Controlled via `AUTH_MODE` env var (disabled/optional/required).

**Rate limits**
- Upload endpoints are rate limited to protect GPU workloads.

**Docs**
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI schema: `/openapi.json`
"""

tags_metadata = [
    {"name": "jobs", "description": "Upload photos, track reconstruction, and download 3D assets."},
    {"name": "projects", "description": "Manage Forma3D projects and registered assets."},
    {"name": "health", "description": "Liveness and readiness probes for orchestration."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=api_description,
    openapi_tags=tags_metadata,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
)


@app.on_event("startup")
async def startup_event():
    await init_rate_limiter()


# Configure CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Structured request/response logging with request IDs."""
    request_id = generate_request_id(request.headers.get("X-Request-ID"))
    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    except Exception:
        # Log exceptions with context, then bubble up to FastAPI's handlers
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request.error",
            extra=build_request_log_extra(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
                client=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        status_code = getattr(response, "status_code", 500)
        if response is not None:
            response.headers["X-Request-ID"] = request_id

        logger.info(
            "request.completed",
            extra=build_request_log_extra(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
                client=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            ),
        )


@app.get("/")
def root():
    return {"message": "Forma3D API is running"}


@app.get("/health")
def health_check():
    """Health check endpoint for container orchestration (Kubernetes, Docker Compose, etc.)"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }


@app.get("/ready")
def readiness_check():
    """Readiness check - verifies the service is ready to accept traffic."""
    import os

    # Check if critical directories exist
    checks = {
        "upload_dir": os.path.exists(settings.UPLOAD_DIR),
        "output_dir": os.path.exists(settings.OUTPUT_DIR),
    }

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks
    }
