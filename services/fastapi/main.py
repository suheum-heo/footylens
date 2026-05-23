"""
FastAPI main application for FootyLens data collection service.
Entry point: uvicorn main:app --reload
"""

import asyncio
from fastapi import FastAPI
from datetime import datetime
from schemas.responses import HealthCheckResponse
from routers import matches, standings, teams, cache_status, analytics
from services.scheduler import SchedulerService, set_scheduler
from services.football_data_client import RateLimitedClient
from core.config import get_settings

# Initialize FastAPI app
app = FastAPI(
    title="FootyLens Data Service",
    description="Football match analysis data collection API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register routers
app.include_router(matches.router)
app.include_router(standings.router)
app.include_router(teams.router)
app.include_router(analytics.router)
app.include_router(cache_status.router)

# Global references for lifecycle management
_scheduler: SchedulerService = None
_client: RateLimitedClient = None


@app.on_event("startup")
async def startup_event():
    """Initialize scheduler and background jobs on app startup."""
    global _scheduler, _client

    settings = get_settings()
    _client = RateLimitedClient(
        api_key=settings.football_data_api_key,
        base_url=settings.football_data_base_url,
        rate_limit_requests=settings.rate_limit_requests,
        rate_limit_period_seconds=settings.rate_limit_period_seconds,
    )

    _scheduler = SchedulerService(_client)
    await _scheduler.start()
    set_scheduler(_scheduler)

    print("✅ Startup complete: Scheduler started with background jobs")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on app shutdown."""
    global _scheduler

    if _scheduler:
        await _scheduler.stop()
        print("✅ Shutdown complete: Scheduler stopped")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "FootyLens Data Service",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "cache_status": "/api/cache/status",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
