import logging
from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from scheduler.job_schedule import JobSchedule
from config import settings

logger = logging.getLogger(__name__)

JobRunner = Callable[[], Awaitable[None]]
ScheduledJob = tuple[JobSchedule, JobRunner]

_apscheduler = AsyncIOScheduler(timezone=settings.timezone)


def register_scheduled_jobs(jobs: list[ScheduledJob]) -> None:
    for schedule, runner in jobs:
        _apscheduler.add_job(
            runner,
            CronTrigger(
                hour=schedule.hour,
                minute=schedule.minute,
                second=schedule.second,
                timezone=schedule.timezone,
            ),
            id=schedule.job_id,
            name=schedule.job_name,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )

        logger.info(
            "Scheduled job registered. job_id=%s, schedule=%02d:%02d:%02d, timezone=%s",
            schedule.job_id,
            schedule.hour,
            schedule.minute,
            schedule.second,
            schedule.timezone,
        )


def start_scheduler(jobs: list[ScheduledJob]) -> None:
    if not settings.scheduler_enabled:
        logger.info("Scheduler is disabled")
        return

    if _apscheduler.running:
        logger.info("Scheduler already running")
        return

    register_scheduled_jobs(jobs)
    _apscheduler.start()
    logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    if _apscheduler.running:
        _apscheduler.shutdown()
        logger.info("Scheduler shutdown")
