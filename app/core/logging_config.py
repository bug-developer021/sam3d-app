import json
import logging
import logging.config
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """Lightweight JSON formatter to keep logs structured without extra deps."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach common HTTP/request fields when present
        for key in [
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client",
            "user_agent",
            "user_id",
        ]:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Fallback to string for anything not JSON serializable
        return json.dumps(payload, default=str)


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure application-wide structured logging.

    Uses stdout so containers/cloud runtimes can capture logs.
    """
    resolved_level = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "level": resolved_level,
                "handlers": ["console"],
            },
            # Keep uvicorn loggers but let them bubble to root so format stays consistent
            "loggers": {
                "uvicorn.error": {"level": resolved_level, "handlers": ["console"], "propagate": False},
                "uvicorn.access": {"level": resolved_level, "handlers": ["console"], "propagate": False},
            },
        }
    )


def build_request_log_extra(
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client: Optional[str],
    user_agent: Optional[str],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper to make middleware logging calls concise."""
    return {
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "client": client,
        "user_agent": user_agent,
        "user_id": user_id,
    }


def generate_request_id(existing: Optional[str] = None) -> str:
    """Use an incoming request ID if provided, otherwise generate a new one."""
    return existing or str(uuid.uuid4())
