from datetime import datetime
from zoneinfo import ZoneInfo

from config import settings


def now() -> datetime:
    return datetime.now(ZoneInfo(settings.timezone)).replace(tzinfo=None)
