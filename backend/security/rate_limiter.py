import time
from dataclasses import dataclass


@dataclass
class Bucket:
    tokens: float
    updated_at: float


class TokenBucketRateLimiter:
    def __init__(self, capacity: int = 10, refill_per_second: float = 0.2) -> None:
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._buckets: dict[str, Bucket] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        bucket = self._buckets.get(key)
        if bucket is None:
            self._buckets[key] = Bucket(tokens=self.capacity - 1, updated_at=now)
            return True

        elapsed = now - bucket.updated_at
        bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.refill_per_second)
        bucket.updated_at = now

        if bucket.tokens < 1:
            return False

        bucket.tokens -= 1
        return True
