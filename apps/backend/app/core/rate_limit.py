from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
import time

from fastapi import HTTPException, status


@dataclass
class Bucket:
    reset_at: float
    count: int = 0


class FixedWindowRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, Bucket] = {}
        self._lock = RLock()

    def hit(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None or bucket.reset_at <= now:
                bucket = Bucket(reset_at=now + window_seconds, count=0)
                self._buckets[key] = bucket
            bucket.count += 1
            retry_after = max(0, int(bucket.reset_at - now))
            return bucket.count <= limit, retry_after


rate_limiter = FixedWindowRateLimiter()


def enforce_rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    allowed, retry_after = rate_limiter.hit(key, limit=limit, window_seconds=window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "rate_limited", "retry_after_seconds": retry_after},
        )
