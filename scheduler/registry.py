from scheduler.jobs.gemini_vote_create.config import JOB_SCHEDULE
from scheduler.jobs.gemini_vote_create.job import run as run_gemini_vote_create
from scheduler.manager import ScheduledJob

SCHEDULED_JOBS: list[ScheduledJob] = [
    (JOB_SCHEDULE, run_gemini_vote_create),
]
