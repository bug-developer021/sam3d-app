import hashlib
import uuid
from typing import Optional

import redis.asyncio as redis
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.models.entities import User

_redis_client: Optional[redis.Redis] = None


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


async def _get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return _redis_client


async def _lookup_user_by_key(
    api_key: str, session: AsyncSession
) -> Optional[User]:
    key_hash = hash_api_key(api_key)
    cache_key = f"api-key:{key_hash}"

    try:
        redis_client = await _get_redis_client()
        cached_user_id = await redis_client.get(cache_key)
        if cached_user_id:
            cached_uuid = uuid.UUID(cached_user_id)
            user = await session.get(User, cached_uuid)
            if user:
                return user
    except Exception:
        # Cache failures should not prevent authentication when DB is reachable
        redis_client = None

    stmt = select(User).where(User.api_key == key_hash)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        return None

    try:
        if redis_client:
            await redis_client.setex(cache_key, 600, str(user.id))
    except Exception:
        pass
    return user


async def get_current_user(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    user = await _lookup_user_by_key(api_key, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return user

