"""
Main FastAPI application
Entry point for the Wishlist API backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import auth, wishlists, items, metadata, debug
from app.routers import groups as groups_router
from app.utils.reminders import run_daily_reminders

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Birthday Wishlist Application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(wishlists.router, prefix=settings.API_V1_PREFIX)
app.include_router(items.router, prefix=settings.API_V1_PREFIX)
app.include_router(metadata.router, prefix=settings.API_V1_PREFIX)
app.include_router(debug.router, prefix=settings.API_V1_PREFIX)
app.include_router(groups_router.router, prefix=settings.API_V1_PREFIX)

_scheduler: BackgroundScheduler | None = None


@app.on_event("startup")
async def _startup():
    """
    Start daily reminders scheduler if enabled.
    """
    global _scheduler
    if not settings.EMAIL_REMINDERS_ENABLED:
        return
    if _scheduler is not None:
        return
    tz = ZoneInfo(settings.EMAIL_TIMEZONE)
    _scheduler = BackgroundScheduler(timezone=tz)
    _scheduler.add_job(
        run_daily_reminders,
        CronTrigger(hour=settings.EMAIL_DAILY_HOUR, minute=settings.EMAIL_DAILY_MINUTE, timezone=tz),
        id="daily_email_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()


@app.on_event("shutdown")
async def _shutdown():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Wishlist API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
