from config import settings

from scheduler.job_schedule import JobSchedule

JOB_SCHEDULE = JobSchedule(
    job_id="question_invite_all",
    job_name="매일 새벽 1시 Batch 질문 전체 사용자 초대",
    timezone=settings.timezone,
    hour=1,
    minute=0,
    second=0,
)
