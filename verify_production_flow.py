"""End-to-end verification script for production readiness.

This script will:
- Create a test user with a generated API key.
- Confirm unauthenticated requests are rejected.
- Exercise the project creation and upload -> processing flow with authentication.
- Clean up any inserted data.

Run with the Docker stack up and required env vars exported (see docker-compose.yml).
"""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Dict, Tuple

import requests
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

# Default env vars to allow local invocation without manual export
DEFAULT_ENV = {
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "forma3d",
    "POSTGRES_PASSWORD": "forma3d",
    "POSTGRES_DB": "forma3d",
    "REDIS_URL": "redis://localhost:6379/0",
}
for key, value in DEFAULT_ENV.items():
    os.environ.setdefault(key, value)

from app.core.db import AsyncSessionLocal
from app.core.security import hash_api_key
from app.models.entities import Project, User


API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
TEST_IMAGE_PATH = os.getenv(
    "TEST_IMAGE_PATH", Path(__file__).parent / "test_image.jpg"
)
api_key_context = ""


async def create_test_user(session: AsyncSession, api_key: str) -> User:
    user = User(email=f"verify-{uuid.uuid4().hex[:8]}@example.com", api_key=hash_api_key(api_key))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def cleanup_user(session: AsyncSession, user_id) -> None:
    await session.execute(delete(Project).where(Project.user_id == user_id))
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()


def require_file() -> Path:
    path = Path(TEST_IMAGE_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Test image missing at {path}")
    return path


def unauthorized_check() -> Tuple[int, int]:
    unauthenticated = requests.get(f"{API_BASE}/projects", timeout=5)
    authenticated = requests.get(
        f"{API_BASE}/projects", headers={"X-API-Key": api_key_context}, timeout=5
    )
    return unauthenticated.status_code, authenticated.status_code


def create_project(api_key: str) -> Tuple[int, Dict[str, str]]:
    payload = {"name": "verify-run", "description": "verification project", "assets": []}
    response = requests.post(
        f"{API_BASE}/projects",
        json=payload,
        headers={"X-API-Key": api_key},
        timeout=10,
    )
    return response.status_code, response.json() if response.content else {}


def upload_and_process(api_key: str) -> Tuple[int, Dict[str, str]]:
    image_path = require_file()
    with open(image_path, "rb") as img:
        files = [("files", (image_path.name, img, "image/jpeg"))]
        response = requests.post(
            f"{API_BASE}/jobs/upload",
            files=files,
            headers={"X-API-Key": api_key},
            timeout=30,
        )
    return response.status_code, response.json() if response.content else {}


async def main() -> None:
    global api_key_context
    api_key = f"key-{uuid.uuid4().hex}"
    api_key_context = api_key
    results: Dict[str, str] = {}

    async with AsyncSessionLocal() as session:  # type: AsyncSession
        user = await create_test_user(session, api_key)
        results["user_id"] = str(user.id)

        unauth_status, auth_status = unauthorized_check()
        results["unauthorized_status"] = str(unauth_status)
        results["authorized_status"] = str(auth_status)

        status_code, project_body = create_project(api_key)
        results["project_status"] = str(status_code)
        results["project_id"] = str(project_body.get("id")) if project_body else ""

        upload_status, upload_body = upload_and_process(api_key)
        results["upload_status"] = str(upload_status)
        results["job_id"] = upload_body.get("job_id", "") if upload_body else ""
        results["celery_task_id"] = upload_body.get("celery_task_id", "") if upload_body else ""

        await cleanup_user(session, user.id)

    print("Verification summary:")
    for key, value in results.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
