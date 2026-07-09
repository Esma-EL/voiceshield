"""Lightweight, dependency-free access control.

Two concerns, both degrade gracefully so the demo keeps working out of the box:

* :func:`require_api_key` - a FastAPI dependency. When ``API_KEY`` is configured
  it enforces a matching ``X-API-Key`` header (constant-time compare); when it
  is empty the app runs in open demo mode.
* :class:`RateLimitMiddleware` - an in-memory sliding-window limiter keyed by
  client IP. No Redis / external store needed for a single-process demo; swap
  for a shared store before scaling horizontally.
"""
from __future__ import annotations

import hmac
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Reject the request unless a valid API key is presented.

    No-op when ``API_KEY`` is unset (demo mode). Uses a constant-time compare
    to avoid leaking the key through timing.
    """
    expected = settings.api_key
    if not expected:
        return
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="clé API invalide ou absente")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding-window rate limiter over a 60-second window."""

    def __init__(self, app, limit_per_minute: int) -> None:
        super().__init__(app)
        self._limit = limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_ip(self, request: Request) -> str:
        # Trust the socket peer; behind a proxy, terminate the limiter there or
        # parse a vetted X-Forwarded-For instead of trusting it blindly.
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if self._limit <= 0:
            return await call_next(request)

        now = time.monotonic()
        window_start = now - 60.0
        bucket = self._hits[self._client_ip(request)]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= self._limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "trop de requêtes, réessayez plus tard"},
                headers={"Retry-After": "60"},
            )
        bucket.append(now)
        return await call_next(request)
