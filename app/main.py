from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.agent_runs import router as agent_runs_router
from app.api.approvals import router as approvals_router
from app.api.audit_logs import router as audit_logs_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.settings import router as settings_router
from app.api.tickets import router as tickets_router
from app.api.websockets import router as websockets_router
from app.core.config import get_settings
from app.tools.mock_tools import register_mock_tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup.
    register_mock_tools()
    
    # Start Redis listener for WebSockets
    from app.api.websockets import start_redis_listener_task, stop_redis_listener_task
    start_redis_listener_task()
    
    yield
    # Shutdown.
    stop_redis_listener_task()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI Agent Platform with Human Approval",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Normalize every error response to the documented {data, error, meta}
    # envelope (docs/API_DESIGN.md) so the frontend's `body.error.message`
    # unwrapping always finds a real message instead of falling back to a
    # bare "HTTP 404" string.
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "data": None,
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "details": {},
                },
                "meta": {},
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "data": None,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request payload is invalid.",
                    "details": {"errors": jsonable_encoder(exc.errors())},
                },
                "meta": {},
            },
        )

    # REST API routers.
    app.include_router(health_router)
    app.include_router(tickets_router)
    app.include_router(agent_runs_router)
    app.include_router(approvals_router)
    app.include_router(knowledge_router)
    app.include_router(audit_logs_router)
    app.include_router(settings_router, prefix="/settings")

    # WebSocket router.
    app.include_router(websockets_router)

    return app


app = create_app()
