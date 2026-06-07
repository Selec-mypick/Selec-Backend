from scheduler.jobs.gemini_vote_create.config import JOB_SCHEDULE
from scheduler.jobs.gemini_vote_create.service import GeminiVoteCreateJob
from scheduler.job_runner import run_scheduled_job

gemini_vote_create_job = GeminiVoteCreateJob()


async def run() -> None:
    await run_scheduled_job(JOB_SCHEDULE.job_name, gemini_vote_create_job.execute)
