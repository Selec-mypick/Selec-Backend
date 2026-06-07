from scheduler.manager import shutdown_scheduler as _shutdown_scheduler
from scheduler.manager import start_scheduler as _start_scheduler
from scheduler.registry import SCHEDULED_JOBS


def start_scheduler() -> None:
    _start_scheduler(SCHEDULED_JOBS)


def shutdown_scheduler() -> None:
    _shutdown_scheduler()


__all__ = [
    "shutdown_scheduler",
    "start_scheduler",
]
