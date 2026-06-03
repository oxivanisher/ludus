import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.metrics import router as metrics_router
from api.push import router as push_router
from api.sessions import router as sessions_router
from api.websocket import router as ws_router
from core.config import settings
from core.plugin_loader import load_plugins
from core.redis_client import close_redis

logger = logging.getLogger("ludus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    logger.info("Ludus starting — commit %s", settings.git_commit)
    load_plugins()
    if settings.metrics_token:
        logger.info("Prometheus metrics endpoint enabled at /metrics")
    yield
    await close_redis()


app = FastAPI(title="Ludus", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics_router)
app.include_router(sessions_router)
app.include_router(push_router)
app.include_router(ws_router)

_static = Path("static")

if _static.is_dir():
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """
        Serve static files by exact path, or fall back to index.html for
        any path the SPA router handles (e.g. /game/{uuid}).
        """
        candidate = _static / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_static / "index.html")
