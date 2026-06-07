"""Per-user rate limiting backed by Redis token buckets.

Algorithm: token bucket with refill. Each user+endpoint pair has a bucket
holding up to `capacity` tokens. Each request costs `cost` tokens. Tokens
refill at `refill_per_minute / 60` per second. A bucket that runs dry
returns 429 until enough time has passed to refill one token.

The bucket state is held in Redis as a hash with:
  sanctuary:ratelimit:{user}:{endpoint} -> { tokens: float, ts: float }

The check is implemented as a Lua script for atomicity: read current state,
compute new tokens, write back, return (allowed:bool, retry_after_seconds:int).
Running it in a single EVAL avoids the read-then-write race that a plain
GET/SET would have.

Configuration defaults are conservative:
- /generate/* and /advance/*: capacity=10, refill=10/min (1 every 6s)

If Redis is down, the limiter is a no-op (request is allowed). Failing
closed would be safer but would 503 the entire app if Redis hiccups; failing
open lets a brief outage pass through with no rate enforcement.
"""

from __future__ import annotations

import functools
import logging
import math
import time
from dataclasses import dataclass
from typing import Callable

from flask import jsonify, session

from cache import get_redis, k

logger = logging.getLogger(__name__)


# Lua script: token-bucket check + refill, atomic.
# KEYS[1] = bucket key
# ARGV[1] = capacity (max tokens)
# ARGV[2] = cost (tokens to consume)
# ARGV[3] = refill_per_minute
# ARGV[4] = now (unix seconds, float)
# ARGV[5] = ttl (seconds, for the key)
# Returns: { allowed:0|1, tokens_left (rounded), retry_after_ms (int) }
_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local cost = tonumber(ARGV[2])
local refill_per_min = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local ttl = tonumber(ARGV[5])

local data = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts = tonumber(data[2])

if tokens == nil or ts == nil then
    tokens = capacity
    ts = now
end

local elapsed = now - ts
if elapsed < 0 then elapsed = 0 end
local refill = (elapsed * refill_per_min) / 60.0
tokens = math.min(capacity, tokens + refill)

local allowed = 0
local retry_after_ms = 0
if tokens >= cost then
    tokens = tokens - cost
    allowed = 1
else
    local need = cost - tokens
    if refill_per_min > 0 then
        retry_after_ms = math.ceil((need / refill_per_min) * 60.0 * 1000)
    else
        retry_after_ms = 60000
    end
end

redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', key, ttl)

return { allowed, math.floor(tokens), retry_after_ms }
"""


@dataclass(frozen=True)
class LimitConfig:
    capacity: int
    cost: int
    refill_per_minute: int

    @property
    def ttl(self) -> int:
        # 2x the time to fully refill from 0, with a floor of 60s
        full_refill_s = (self.capacity / self.refill_per_minute) * 60.0 if self.refill_per_minute else 600.0
        return max(60, int(full_refill_s * 2))


# Endpoint-specific defaults. Override via the decorator.
DEFAULT_LIMITS: dict[str, LimitConfig] = {
    "/generate/tprompt": LimitConfig(capacity=10, cost=1, refill_per_minute=10),
    "/generate/tprompt/stream": LimitConfig(capacity=10, cost=1, refill_per_minute=10),
    "/generate/iprompt": LimitConfig(capacity=10, cost=1, refill_per_minute=10),
    "/generate/image": LimitConfig(capacity=6, cost=1, refill_per_minute=6),
    "/generate/irandom": LimitConfig(capacity=10, cost=1, refill_per_minute=10),
    "/generate/trandom": LimitConfig(capacity=10, cost=1, refill_per_minute=10),
    "/advance/generate": LimitConfig(capacity=10, cost=1, refill_per_minute=10),
    "/advance/igenerate": LimitConfig(capacity=10, cost=1, refill_per_minute=10),
    "/advance/image": LimitConfig(capacity=6, cost=1, refill_per_minute=6),
    "/refinement": LimitConfig(capacity=8, cost=1, refill_per_minute=8),
}


def _key_for(user: str, endpoint: str) -> str:
    return k("ratelimit", user, endpoint.replace("/", "_").lstrip("_"))


def _check(user: str, endpoint: str, cfg: LimitConfig) -> tuple[bool, int]:
    """Return (allowed, retry_after_ms)."""
    r = get_redis()
    if r is None:
        return True, 0
    try:
        result = r.eval(
            _LUA,
            1,
            _key_for(user, endpoint),
            cfg.capacity,
            cfg.cost,
            cfg.refill_per_minute,
            time.time(),
            cfg.ttl,
        )
        allowed = bool(int(result[0]))
        retry_after_ms = int(result[2]) if not allowed else 0
        return allowed, retry_after_ms
    except Exception as e:
        logger.debug("rate limit check failed for %s/%s: %s", user, endpoint, e)
        return True, 0


def rate_limit(endpoint_name: str | None = None, config: LimitConfig | None = None) -> Callable:
    """Decorator: enforce the per-user rate limit on a Flask view function.

    The endpoint is determined by `endpoint_name` if given, else the route
    function's `request.endpoint` (e.g. `main.generate` -> /generate). We
    match against DEFAULT_LIMITS by the request path, falling back to
    `config` if provided, else a conservative default of 10/min.
    """
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            from flask import request
            username = session.get("username")
            if not username:
                # Unauthenticated endpoints (login, signup) are not rate-limited
                # here; if needed, install a separate IP-based limiter.
                return view(*args, **kwargs)

            path = request.path
            cfg = (
                config
                or DEFAULT_LIMITS.get(path)
                or DEFAULT_LIMITS.get(endpoint_name or "")
                or LimitConfig(capacity=10, cost=1, refill_per_minute=10)
            )

            allowed, retry_after_ms = _check(username, path, cfg)
            if not allowed:
                retry_after_s = max(1, math.ceil(retry_after_ms / 1000))
                response = jsonify(
                    {
                        "success": False,
                        "error": "rate_limited",
                        "message": f"Too many requests. Try again in {retry_after_s}s.",
                        "retry_after_s": retry_after_s,
                    }
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(retry_after_s)
                return response
            return view(*args, **kwargs)
        return wrapped
    return decorator


__all__ = ["LimitConfig", "rate_limit", "DEFAULT_LIMITS"]
