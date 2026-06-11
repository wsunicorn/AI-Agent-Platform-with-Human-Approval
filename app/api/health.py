from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_engine
from app.core.redis import get_redis

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/ready")
async def ready() -> dict[str, object]:
    checks: dict[str, str] = {}

    engine = get_engine()
    async with engine.connect() as connection:
        await connection.execute(text("select 1"))
    checks["postgres"] = "ok"

    redis = get_redis()
    pong = await redis.ping()
    checks["redis"] = "ok" if pong else "failed"

    return {
        "status": "ok",
        "checks": checks,
    }
