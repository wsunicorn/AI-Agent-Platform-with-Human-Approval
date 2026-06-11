import asyncio
import uuid
from dataclasses import dataclass, field

from redis.asyncio import Redis

from app.core.redis import get_redis


class RedisLockError(RuntimeError):
    pass


RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""


@dataclass
class RedisLock:
    name: str
    ttl_seconds: int = 60
    redis: Redis = field(default_factory=get_redis)
    retry_delay_seconds: float = 0.1
    acquire_timeout_seconds: float = 5.0
    token: str = field(default_factory=lambda: str(uuid.uuid4()))
    acquired: bool = False

    async def acquire(self) -> None:
        deadline = asyncio.get_running_loop().time() + self.acquire_timeout_seconds

        while True:
            acquired = await self.redis.set(
                self.name,
                self.token,
                nx=True,
                ex=self.ttl_seconds,
            )
            if acquired:
                self.acquired = True
                return

            if asyncio.get_running_loop().time() >= deadline:
                raise RedisLockError(f"Could not acquire Redis lock: {self.name}")

            await asyncio.sleep(self.retry_delay_seconds)

    async def release(self) -> None:
        if not self.acquired:
            return

        await self.redis.eval(RELEASE_LOCK_SCRIPT, 1, self.name, self.token)
        self.acquired = False

    async def __aenter__(self) -> "RedisLock":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.release()
