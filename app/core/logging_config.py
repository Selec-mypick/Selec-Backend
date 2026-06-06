import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from logging import LogRecord
from typing import Any, Optional


request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

LOG_RECORD_RESERVED_KEYS = {
    "args",
    "asctime",
    "color_message",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


class JsonLogFormatter(logging.Formatter):
    def __init__(self, service_name: str, active_profile: str) -> None:
        super().__init__()
        self.service_name = service_name
        self.active_profile = active_profile

    def format(self, record: LogRecord) -> str:
        log_data: dict[str, Any] = {
            "@timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "service": self.service_name,
            "env": self.active_profile,
            "message": record.getMessage(),
        }

        request_id = request_id_context.get()
        if request_id:
            log_data["request_id"] = request_id

        for key, value in record.__dict__.items():
            if not key.startswith("_") and key not in LOG_RECORD_RESERVED_KEYS:
                log_data[key] = value

        if record.exc_info:
            log_data["stack_trace"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(log_level: str, active_profile: str, service_name: str = "selec-backend") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter(service_name, active_profile))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level.upper())
    root_logger.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
