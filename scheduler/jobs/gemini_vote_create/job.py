from scheduler.jobs.gemini_vote_create.config import JOB_SCHEDULE
from scheduler.jobs.gemini_vote_create.service import create_question_from_gemini
from scheduler.job_runner import run_scheduled_job


async def run() -> None:
    await run_scheduled_job(JOB_SCHEDULE.job_name, create_question_from_gemini)
