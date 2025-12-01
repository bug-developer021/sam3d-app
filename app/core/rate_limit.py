import asyncio
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import HTTPException, Request, status

from app.core.config import settings


class InMemoryRateLimiter:
    """
    Simple in-memory sliding window rate limiter.

    Suitable for single-instance deployments. For horizontal scaling, swap this
    out with a Redis/Upstash backed implementation.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def hit(self, key: str) -> None:
        now = time.monotonic()
        async with self._lock:
            events = self._events[key]

            # Drop events outside the window
            while events and now - events[0] > self.window_seconds:
                events.popleft()

            if len(events) >= self.max_requests:
                retry_after = int(self.window_seconds - (now - events[0]))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )

            events.append(now)


upload_rate_limiter = InMemoryRateLimiter(
    max_requests=settings.RATE_LIMIT_UPLOAD_MAX_REQUESTS,
    window_seconds=settings.RATE_LIMIT_UPLOAD_WINDOW_SECONDS,
)


async def enforce_upload_rate_limit(request: Request, user_id: Optional[str]) -> None:
    """
    Dependency to throttle GPU-intensive upload endpoints.
    """
    client_id = user_id or (request.client.host if request.client else "anonymous")
    key = f"upload:{client_id}"
    await upload_rate_limiter.hit(key)
