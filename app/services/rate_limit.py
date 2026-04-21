from __future__ import annotations

from time import time
from uuid import uuid4

import redis
from redis.exceptions import RedisError

from app.core.config import settings


class RateLimitUnavailable(RuntimeError):
    pass


class RedisRateLimiter:
    def __init__(
        self,
        *,
        redis_url: str,
        max_failures: int,
        window_seconds: int,
        key_prefix: str = "school-fee-portal",
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix
        self._client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

    def is_limited(self, key: str) -> bool:
        return self._failure_count(key) >= self.max_failures

    def record_failure(self, key: str) -> None:
        now = time()
        redis_key = self._redis_key(key)
        try:
            pipeline = self._client.pipeline()
            pipeline.zremrangebyscore(redis_key, 0, now - self.window_seconds)
            pipeline.zadd(redis_key, {f"{now}:{uuid4().hex}": now})
            pipeline.expire(redis_key, self.window_seconds)
            pipeline.execute()
        except RedisError as exc:
            raise RateLimitUnavailable("Redis rate limiter is unavailable") from exc

    def reset(self, key: str) -> None:
        try:
            self._client.delete(self._redis_key(key))
        except RedisError as exc:
            raise RateLimitUnavailable("Redis rate limiter is unavailable") from exc

    def _failure_count(self, key: str) -> int:
        now = time()
        redis_key = self._redis_key(key)
        try:
            pipeline = self._client.pipeline()
            pipeline.zremrangebyscore(redis_key, 0, now - self.window_seconds)
            pipeline.zcard(redis_key)
            pipeline.expire(redis_key, self.window_seconds)
            _, count, _ = pipeline.execute()
            return int(count)
        except RedisError as exc:
            raise RateLimitUnavailable("Redis rate limiter is unavailable") from exc

    def _redis_key(self, key: str) -> str:
        return f"{self.key_prefix}:rate-limit:{key}"


auth_rate_limiter = RedisRateLimiter(
    redis_url=settings.redis_url,
    max_failures=settings.rate_limit_max_failures,
    window_seconds=settings.rate_limit_window_seconds,
)
