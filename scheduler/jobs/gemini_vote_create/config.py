from config import settings

from scheduler.job_schedule import JobSchedule

BATCH_USERS_SEQ = "3a1093a2-7e89-44db-976d-f98f152041e8"

JOB_SCHEDULE = JobSchedule(
    job_id="gemini_vote_create",
    job_name="매일 오후 4시 50분 Gemini 투표 생성",
    timezone=settings.timezone,
    hour=16,
    minute=50,
    second=0,
)
