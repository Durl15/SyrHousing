from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from .config import settings
from .database import engine, Base
from .api import (
    health, programs, profiles, watchlist, scanner, ranking,
    chatbot, auth, ai, applications, admin, export,
    notifications, grant_writer, discovery,
)
from .api.grants_v2 import router as grants_v2_router
from .scheduler import start_scheduler, shutdown_scheduler

# Create all tables on startup (idempotent — safe to run on every start)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown."""
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
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
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
app.include_router(grants_v2_router)

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
