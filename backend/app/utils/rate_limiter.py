"""
Redis 滑动窗口限流器
"""

import time
import redis.asyncio as aioredis
from ..config import settings


class RateLimiter:
    def __init__(self):
        self.redis: aioredis.Redis | None = None

    async def connect(self):
        self.redis = aioredis.from_url(settings.redis_url)

    async def is_allowed(
        self,
        key: str,
        max_requests: int = 10,
        window_seconds: int = 60,
    ) -> bool:
        """滑动窗口限流检查"""
        if not self.redis:
            await self.connect()

        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"

        async with self.redis.pipeline() as pipe:
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zcard(redis_key)
            count = (await pipe.execute())[1]

        if count >= max_requests:
            return False

        await self.redis.zadd(redis_key, {str(now): now})
        await self.redis.expire(redis_key, window_seconds)
        return True


rate_limiter = RateLimiter()
