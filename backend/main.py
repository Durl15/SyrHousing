from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .database import engine, Base
from .api import health, programs, profiles, watchlist, scanner, ranking, chatbot, auth, ai, applications, admin, export, notifications, grant_writer, discovery
from .scheduler import start_scheduler, shutdown_scheduler

# Create tables on startup (idempotent)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    """
    # Startup: Initialize scheduler
    start_scheduler()
    yield
    # Shutdown: Clean up scheduler
    shutdown_scheduler()


app = FastAPI(
    title="SyrHousing API",
    version=settings.APP_VERSION,
    description="Syracuse Senior Housing Grant Agent – Backend API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
