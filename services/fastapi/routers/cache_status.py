"""
Cache status endpoint router.
GET /api/cache/status — inspect cache state and scheduler jobs
"""

from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from logging import getLogger

from core.config import Settings, get_settings
from core.cache import get_cache
from services.scheduler import get_scheduler

logger = getLogger(__name__)
router = APIRouter(prefix="/api", tags=["cache"])


@router.get("/cache/status")
async def get_cache_status() -> Dict[str, Any]:
    """
    Get cache status and scheduler information.

    **Returns:**
    - Cache statistics (count, size, entries)
    - Scheduler jobs list (if running)
    """
    cache = get_cache()
    cache_status = cache.status()

    scheduler = get_scheduler()
    jobs_info = []
    if scheduler:
        for job in scheduler.get_jobs():
            jobs_info.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "trigger": str(job.trigger),
                    "next_run_time": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                }
            )

    return {
        "cache": cache_status,
        "scheduler": {
            "running": scheduler is not None and scheduler._running,
            "jobs_count": len(jobs_info),
            "jobs": jobs_info,
        },
    }


@router.delete("/cache/clear")
async def clear_cache() -> Dict[str, str]:
    """
    Clear entire cache.

    **Returns:**
    - Status message
    """
    cache = get_cache()
    cache.clear_all()
    logger.info("Cache cleared via API")
    return {"status": "ok", "message": "Cache cleared"}
