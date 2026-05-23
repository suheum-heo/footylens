"""
Background scheduler for fetching football data.
Uses APScheduler AsyncIOScheduler for async task scheduling.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from typing import Optional

from core.cache import get_cache
from services.football_data_client import RateLimitedClient

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Manages background scheduler for data fetching.
    """

    def __init__(self, client: RateLimitedClient):
        """
        Initialize scheduler.

        Args:
            client: RateLimitedClient for Football-Data.org API
        """
        self.client = client
        self.scheduler = AsyncIOScheduler()
        self._running = False

    async def start(self) -> None:
        """Start scheduler and register jobs."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self.scheduler.start()
        self._running = True

        # Register background jobs
        await self._register_jobs()

        logger.info("Scheduler started with background jobs")

    async def _register_jobs(self) -> None:
        """Register all background fetch jobs."""
        # Job 1: Fetch PL matches every 1 hour
        self.scheduler.add_job(
            self._fetch_pl_matches_job,
            IntervalTrigger(hours=1),
            id="fetch_pl_matches",
            name="Fetch PL Matches",
            max_instances=1,
        )
        logger.info("Registered job: fetch_pl_matches (every 1hr)")

        # Job 2: Fetch standings every 1 hour
        self.scheduler.add_job(
            self._fetch_standings_job,
            IntervalTrigger(hours=1),
            id="fetch_standings",
            name="Fetch PL Standings",
            max_instances=1,
        )
        logger.info("Registered job: fetch_standings (every 1hr)")

        # Job 3: Fetch historical data daily at midnight UTC
        self.scheduler.add_job(
            self._fetch_historical_job,
            CronTrigger(hour=0, minute=0),
            id="fetch_historical",
            name="Fetch Historical Data",
            max_instances=1,
        )
        logger.info("Registered job: fetch_historical (daily at 00:00 UTC)")

    async def _fetch_pl_matches_job(self) -> None:
        """Background job: Fetch and cache PL matches."""
        try:
            logger.info("Job started: fetch_pl_matches")
            response = await self.client.get_matches(
                competition="PL",
                status="SCHEDULED,LIVE,FINISHED",
            )

            cache = get_cache()
            cache.set("matches:PL", response, ttl_minutes=60)
            logger.info("Job completed: fetch_pl_matches (cached)")

        except Exception as e:
            logger.error(f"Job failed: fetch_pl_matches — {e}")

    async def _fetch_standings_job(self) -> None:
        """Background job: Fetch and cache standings."""
        try:
            logger.info("Job started: fetch_standings")
            response = await self.client.get_standings(competition="PL")

            cache = get_cache()
            cache.set("standings:PL", response, ttl_minutes=60)
            logger.info("Job completed: fetch_standings (cached)")

        except Exception as e:
            logger.error(f"Job failed: fetch_standings — {e}")

    async def _fetch_historical_job(self) -> None:
        """Background job: Fetch and cache historical data for all major competitions."""
        competitions = ["PL", "BL1", "SA", "PD", "FL1"]

        for comp in competitions:
            try:
                logger.info(f"Job started: fetch_historical[{comp}]")
                response = await self.client.get_matches(
                    competition=comp,
                    status="FINISHED",
                )

                cache = get_cache()
                cache.set(f"historical:{comp}", response, ttl_minutes=1440)  # 24hr
                logger.info(f"Job completed: fetch_historical[{comp}] (cached 24hr)")

            except Exception as e:
                logger.error(f"Job failed: fetch_historical[{comp}] — {e}")

    async def stop(self) -> None:
        """Stop scheduler."""
        if not self._running:
            logger.warning("Scheduler not running")
            return

        self.scheduler.shutdown(wait=False)
        self._running = False
        logger.info("Scheduler stopped")

    def get_jobs(self) -> list:
        """Get list of scheduled jobs."""
        return self.scheduler.get_jobs()


# Global scheduler instance
_scheduler: Optional[SchedulerService] = None


def get_scheduler() -> Optional[SchedulerService]:
    """Get global scheduler instance."""
    return _scheduler


def set_scheduler(scheduler: SchedulerService) -> None:
    """Set global scheduler instance."""
    global _scheduler
    _scheduler = scheduler
