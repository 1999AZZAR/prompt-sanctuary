"""Redis client and cache helpers.

Used for:
- Per-user rate limiting on AI generation endpoints (token bucket in Redis)
- Caching frequently-read small values (user points, prompt sharing status)
- Caching the system prompts list (read on every library page load)

Key namespace: `sanctuary:*` so we share the Redis instance with other apps
on the host without colliding.

Behaviour when Redis is unavailable:
- Reads: fall through to the underlying source. We log a warning once and
  continue. The user gets fresh data; performance degrades but nothing breaks.
- Writes: silently skipped. Rate limit then has no effect for the request —
  this is intentional; we'd rather serve the request than 5xx.

The Redis client uses a small connection pool (5 connections) which is
shared across gunicorn worker threads. redis-py's ConnectionPool is
thread-safe.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable

import redis

logger = logging.getLogger(__name__)

NAMESPACE = "sanctuary"
DEFAULT_TTL = 60

_client: redis.Redis | None = None
_redis_disabled: bool = False


def _redis_url() -> str | None:
    url = os.getenv("REDIS_URL")
    if url:
        return url
    return None


def get_redis() -> redis.Redis | None:
    """Return the shared Redis client, or None if Redis is not configured."""
    global _client, _redis_disabled
    if _redis_disabled:
        return None
    if _client is not None:
        return _client
    url = _redis_url()
    if not url:
        logger.info("REDIS_URL not set; cache + rate limiting are disabled.")
        _redis_disabled = True
        return None
    try:
        _client = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            health_check_interval=30,
            max_connections=20,
        )
        # Probe so we don't get surprised at runtime
        _client.ping()
    except Exception as e:
        logger.warning("Redis unavailable (%s); cache + rate limiting disabled.", e)
        _client = None
        _redis_disabled = True
        return None
    return _client


def k(*parts: Any) -> str:
    """Build a namespaced key: sanctuary:a:b:c."""
    return ":".join([NAMESPACE, *(str(p) for p in parts)])


def cache_get(key: str) -> Any | None:
    """Return the cached value (JSON-decoded) or None on miss/error."""
    r = get_redis()
    if r is None:
        return None
    try:
        raw = r.get(key)
    except Exception as e:
        logger.debug("cache_get(%s) failed: %s", key, e)
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.debug("cache_set(%s) failed: %s", key, e)


def cache_invalidate(key: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        r.delete(key)
    except Exception as e:
        logger.debug("cache_invalidate(%s) failed: %s", key, e)


def cache_invalidate_pattern(pattern: str) -> None:
    """Delete every key matching the pattern. Use sparingly on large DBs."""
    r = get_redis()
    if r is None:
        return
    try:
        # SCAN is O(n) and non-blocking, vs KEYS which is O(n) and blocks
        cursor = 0
        batch: list[str] = []
        while True:
            cursor, keys = r.scan(cursor=cursor, match=pattern, count=200)
            batch.extend(keys)
            if cursor == 0:
                break
        if batch:
            r.delete(*batch)
    except Exception as e:
        logger.debug("cache_invalidate_pattern(%s) failed: %s", pattern, e)


def cache_through(key: str, ttl: int, producer: Callable[[], Any]) -> Any:
    """Read-through cache helper.

    - Returns the cached value if present.
    - Otherwise calls producer(), caches the result, returns it.
    - On any Redis error, returns producer() directly (no cache write).
    """
    r = get_redis()
    if r is not None:
        try:
            raw = r.get(key)
            if raw is not None:
                return json.loads(raw)
        except Exception:
            pass
    value = producer()
    if r is not None and value is not None:
        try:
            r.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            pass
    return value


__all__ = [
    "NAMESPACE",
    "DEFAULT_TTL",
    "get_redis",
    "k",
    "cache_get",
    "cache_set",
    "cache_invalidate",
    "cache_invalidate_pattern",
    "cache_through",
]
