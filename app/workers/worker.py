import asyncio
import logging

from sqlalchemy import text

from app.core.database import get_engine
from app.core.redis import get_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("humangate.worker")


async def check_dependencies() -> None:
    engine = get_engine()
    async with engine.connect() as connection:
        await connection.execute(text("select 1"))

    redis = get_redis()
    await redis.ping()


async def main() -> None:
    await check_dependencies()
    logger.info("worker started")

    while True:
        logger.info("worker heartbeat")
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())

