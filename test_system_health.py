"""Ad-hoc connectivity checks for the Forma3D stack.

This script expects the same environment variables as the backend service and
will attempt to verify PostgreSQL, Redis, and the FastAPI health endpoint. It
also inserts a throwaway user record to validate ORM writes.
"""
import asyncio
import os
import uuid
from typing import Dict, Tuple

import requests
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

# Provide sensible defaults that align with docker-compose.yml so the script can
# run locally without exporting the variables. Explicit exports will still take
# precedence.
DEFAULT_ENV = {
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "forma3d",
    "POSTGRES_PASSWORD": "forma3d",
    "POSTGRES_DB": "forma3d",
    "REDIS_URL": "redis://localhost:6379/0",
    "API_HEALTH_URL": "http://localhost:8000/health",
}
for key, value in DEFAULT_ENV.items():
    os.environ.setdefault(key, value)

from app.core.config import settings  # noqa: E402
from app.core.db import AsyncSessionLocal  # noqa: E402
from app.models.entities import User  # noqa: E402


async def check_postgres() -> bool:
    """Verify PostgreSQL connectivity with a simple SELECT 1."""
    try:
        async with AsyncSessionLocal() as session:  # type: AsyncSession
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except SQLAlchemyError as exc:  # pragma: no cover - connectivity probe
        print(f"PostgreSQL check failed: {exc}")
        return False


async def insert_dummy_user() -> Tuple[str, str]:
    """Insert a dummy user to ensure ORM writes succeed."""
    email = f"health-{uuid.uuid4().hex[:8]}@example.com"
    api_key_hash = uuid.uuid4().hex

    async with AsyncSessionLocal() as session:
        user = User(email=email, api_key_hash=api_key_hash)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return str(user.id), user.email


async def check_redis() -> bool:
    """Confirm Redis is reachable via PING."""
    client = redis.from_url(settings.REDIS_URL)
    try:
        pong = await client.ping()
        return bool(pong)
    except Exception as exc:  # pragma: no cover - connectivity probe
        print(f"Redis check failed: {exc}")
        return False
    finally:
        await client.close()


async def check_health_endpoint() -> Tuple[bool, int]:
    """Hit the FastAPI /health endpoint and return status code."""
    health_url = os.environ.get("API_HEALTH_URL", DEFAULT_ENV["API_HEALTH_URL"])
    try:
        response = requests.get(health_url, timeout=5)
        return response.ok, response.status_code
    except Exception as exc:  # pragma: no cover - connectivity probe
        print(f"Health endpoint check failed: {exc}")
        return False, 0


async def main() -> None:
    results: Dict[str, str] = {}

    results["postgres_ok"] = str(await check_postgres())
    results["redis_ok"] = str(await check_redis())

    health_ok, status_code = await check_health_endpoint()
    results["health_ok"] = str(health_ok)
    results["health_status_code"] = str(status_code)

    user_id, email = await insert_dummy_user()
    results["dummy_user_id"] = user_id
    results["dummy_user_email"] = email

    print("System health summary:")
    for key, value in results.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
