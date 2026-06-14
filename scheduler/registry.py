from scheduler.jobs.gemini_vote_create.config import JOB_SCHEDULE as GEMINI_VOTE_CREATE_JOB_SCHEDULE
from scheduler.jobs.gemini_vote_create.job import run as run_gemini_vote_create
from scheduler.manager import ScheduledJob
from scheduler.jobs.question_invite_all.config import JOB_SCHEDULE as QUESTION_INVITE_ALL_JOB_SCHEDULE
from scheduler.jobs.question_invite_all.job import run as run_question_invite_all

SCHEDULED_JOBS: list[ScheduledJob] = [
    (GEMINI_VOTE_CREATE_JOB_SCHEDULE, run_gemini_vote_create),
    (QUESTION_INVITE_ALL_JOB_SCHEDULE, run_question_invite_all),
]
