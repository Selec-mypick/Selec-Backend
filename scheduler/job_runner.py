import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


async def run_scheduled_job(job_name: str, task: Callable[[], Awaitable[None]]) -> None:
    try:
        await task()
        logger.info("%s 실행 완료", job_name)
    except Exception:
        logger.exception("%s 실행 실패", job_name)
