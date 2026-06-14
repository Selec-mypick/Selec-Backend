from config import settings

from scheduler.job_schedule import JobSchedule

JOB_SCHEDULE = JobSchedule(
    job_id="gemini_vote_create",
    job_name="매일 밤 11시 30분 Gemini 투표 생성",
    timezone=settings.timezone,
    hour=23,
    minute=30,
    second=0,
)
