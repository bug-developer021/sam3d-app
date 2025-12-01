import redis.asyncio as redis
from fastapi import Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from app.core.config import settings


async def init_rate_limiter() -> None:
    redis_connection = redis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)


def rate_limit_upload_dependency():
    return RateLimiter(
        times=settings.RATE_LIMIT_UPLOAD_MAX_REQUESTS,
        seconds=settings.RATE_LIMIT_UPLOAD_WINDOW_SECONDS,
        key_func=upload_rate_limit_key,
    )


async def upload_rate_limit_key(request: Request) -> str:
    user_token = request.headers.get("Authorization")
    if user_token:
        return user_token
    client_host = getattr(request.client, "host", None)
    return client_host or "anonymous"
