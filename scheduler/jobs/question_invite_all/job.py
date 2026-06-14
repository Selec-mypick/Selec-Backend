from scheduler.job_runner import run_scheduled_job
from scheduler.jobs.question_invite_all.config import JOB_SCHEDULE
from scheduler.jobs.question_invite_all.service import QuestionInviteAllJob

question_invite_all_job = QuestionInviteAllJob()


async def run() -> None:
    await run_scheduled_job(JOB_SCHEDULE.job_name, question_invite_all_job.execute)
