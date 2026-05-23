"""
FastAPI main application for FootyLens data collection service.
Entry point: uvicorn main:app --reload
"""

from fastapi import FastAPI
from datetime import datetime
from schemas.responses import HealthCheckResponse
from routers import matches, standings, teams

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
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
