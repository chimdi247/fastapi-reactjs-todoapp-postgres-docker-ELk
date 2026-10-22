import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import telemetry
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.database import AsyncSessionLocal, engine
from app.dependencies import get_current_user
from app.models.todos import Todo
from app.routers import auth_api, todo_api

# Must run at import time: uvicorn has already applied its own logging config by
# the time it imports this module, and `opentelemetry-instrument` has already
# attached its OTLP handler to the root logger.
configure_logging()
logger = logging.getLogger("app")


async def _refresh_todo_stats() -> None:
    """Samples business KPIs from the DB for the `todos_current` gauge."""
    while True:
        try:
            async with AsyncSessionLocal() as session:
                row = (
                    await session.execute(
                        select(
                            func.count(Todo.id),
                            func.count(Todo.id).filter(Todo.is_completed.is_(True)),
                        )
                    )
                ).one()
            total, completed = int(row[0]), int(row[1])
            telemetry.set_todo_state(total - completed, completed)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let KPI sampling take the app down
            logger.exception("failed to refresh todo stats")
        await asyncio.sleep(settings.TODO_STATS_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("starting up", extra={"event": "app.startup"})
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("database connection ok", extra={"event": "db.connected"})
    except Exception:
        logger.exception("database connection failed", extra={"event": "db.connect_failed"})

    stats_task = asyncio.create_task(_refresh_todo_stats(), name="todo-stats")

    yield

    # --- SHUTDOWN ---
    logger.info("shutting down", extra={"event": "app.shutdown"})
    stats_task.cancel()
    await asyncio.gather(stats_task, return_exceptions=True)
    await engine.dispose()
    logger.info("database pool closed", extra={"event": "db.closed"})


app = FastAPI(
    title="Todo App",
    description="A nice todo app",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,  # bearer tokens, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_log(request: Request, call_next):
    """One structured log line per request (trace-correlated)."""
    if request.url.path.startswith("/health"):
        return await call_next(request)

    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        level = logging.ERROR if status_code >= 500 else logging.INFO
        logger.log(
            level,
            "%s %s -> %s",
            request.method,
            request.url.path,
            status_code,
            extra={
                "event": "http.request",
                "http.method": request.method,
                "http.path": request.url.path,
                "http.status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else None,
            },
        )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Same envelope as ApiResponse, plus `detail` for backwards compatibility.
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "message": exc.detail, "detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


app.include_router(auth_api.router)
# Every todo route requires a valid bearer token.
app.include_router(todo_api.router, dependencies=[Depends(get_current_user)])


@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to the Todo API!", "version": settings.SERVICE_VERSION}


@app.get("/health", tags=["health"])
async def liveness():
    """Process is up. Excluded from tracing/metrics (OTEL_PYTHON_FASTAPI_EXCLUDED_URLS)."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def readiness():
    """Dependencies are reachable (used by the uptime probe)."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("readiness check failed", extra={"event": "health.not_ready"})
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}
