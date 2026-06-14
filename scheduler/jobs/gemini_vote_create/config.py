from config import settings

from scheduler.job_schedule import JobSchedule

JOB_SCHEDULE = JobSchedule(
    job_id="gemini_vote_create",
    job_name="매일 자정 Gemini 투표 생성",
    timezone=settings.timezone,
    hour=0,
    minute=0,
    second=0,
)
