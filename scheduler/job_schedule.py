from dataclasses import dataclass


@dataclass(frozen=True)
class JobSchedule:
    job_id: str
    job_name: str
    timezone: str
    hour: int
    minute: int
    second: int = 0
