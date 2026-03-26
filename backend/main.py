from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging

_log = logging.getLogger(__name__)

from .config import settings
from .database import engine, Base
from .api import (
    health, programs, profiles, watchlist, scanner, ranking,
    chatbot, auth, ai, applications, admin, export,
    notifications, grant_writer, discovery,
)

try:
    from .api.grants_v2 import router as grants_v2_router
    _log.info("grants_v2 router imported successfully")
except Exception as _exc:
    _log.error("FAILED to import grants_v2 router: %s", _exc, exc_info=True)
    grants_v2_router = None

from .scheduler import start_scheduler, shutdown_scheduler

# Create all tables on startup (idempotent — safe to run on every start)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown."""
    # Seed grants data if not already seeded
    try:
        from .scripts.seed_grants_data import run_seed
        run_seed()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Seed skipped: %s", e)
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="SyrHousing API",
    version=settings.APP_VERSION,
    description="Syracuse Senior Housing Grant Agent – Backend API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Existing routers ──────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(programs.router)
app.include_router(profiles.router)
app.include_router(watchlist.router)
app.include_router(scanner.router)
app.include_router(ranking.router)
app.include_router(chatbot.router)
app.include_router(ai.router)
app.include_router(applications.router)
app.include_router(admin.router)
app.include_router(export.router)
app.include_router(notifications.router)
app.include_router(grant_writer.router)
app.include_router(discovery.router)

# ── Grants V2 router (new eligibility-matched grant system) ──────────────────
if grants_v2_router is not None:
    app.include_router(grants_v2_router)
    _log.info("grants_v2 router registered at /api/v2/grants")
else:
    _log.error("grants_v2 router NOT registered — import failed")

# ── Serve grants dashboard HTML as a static file ─────────────────────────────
_dashboard_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "grants_dashboard.html",
)

@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    from fastapi.responses import FileResponse
    if os.path.exists(_dashboard_path):
        return FileResponse(_dashboard_path, media_type="text/html")
    from fastapi.responses import JSONResponse
    return JSONResponse({"error": "Dashboard file not found"}, status_code=404)
