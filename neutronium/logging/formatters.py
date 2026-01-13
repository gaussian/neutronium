
import json
import logging
import os
from datetime import datetime, timezone
from uuid import UUID

SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME")


def _json_default(obj):
    """Handle JSON serialization of non-standard types."""
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class JsonFormatter(logging.Formatter):
    """JSON formatter with ordered fields and null value omission."""

    # Maps record attribute names to JSON output field names
    CONTEXT_FIELDS = {
        "request_id": "request_id",
        "client_ip": "client_ip",
        "user_id": "user.id",
        "enterprise_id": "enterprise.id",
        "trace_id": "trace_id",
        "span_id": "span_id",
        "trace_sampled": "trace.sampled",
        # HTTP request fields from AccessLogMiddleware
        "http.method": "http.method",
        "http.path": "http.path",
        "http.route": "http.route",
        "http.status_code": "http.status_code",
        "http.user_agent": "http.user_agent",
        "duration_ms": "duration_ms",
        "user.is_privileged": "user.is_privileged",
        "django.view": "django.view",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Build payload with explicit field ordering
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "logger": record.name,
        }

        if SERVICE_NAME:
            payload["service.name"] = SERVICE_NAME

        # Add context fields (injected by ContextFilter)
        for attr, output_name in self.CONTEXT_FIELDS.items():
            value = getattr(record, attr, None)
            if value is not None:
                payload[output_name] = value

        # Include structured exception info if present
        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            if exc_type is not None:
                payload["error.type"] = exc_type.__name__
            if exc_value is not None:
                payload["error.message"] = str(exc_value)
            payload["error.stack_trace"] = self.formatException(record.exc_info)

        # Include stack_info if requested (e.g., logger.info("msg", stack_info=True))
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(payload, default=_json_default)


class DevConsoleFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    # Standard LogRecord attributes to exclude when looking for extra fields
    # _STANDARD_ATTRS = frozenset(
    #     {
    #         "name",
    #         "msg",
    #         "args",
    #         "created",
    #         "filename",
    #         "funcName",
    #         "levelname",
    #         "levelno",
    #         "lineno",
    #         "module",
    #         "msecs",
    #         "pathname",
    #         "process",
    #         "processName",
    #         "thread",
    #         "threadName",
    #         "exc_info",
    #         "exc_text",
    #         "stack_info",
    #         "message",
    #         "relativeCreated",
    #         "taskName",
    #     }
    # )

    def format(self, record: logging.LogRecord) -> str:
        base = f"[{record.levelname}] {record.getMessage()} ({record.pathname}:{record.lineno})"

        # Collect extra fields (anything not in standard LogRecord attributes)
        extras = {
            # k: v for k, v in record.__dict__.items()
            # if k not in self._STANDARD_ATTRS and not k.startswith("_")
        }

        if extras:
            extra_str = " ".join(f"{k}={v!r}" for k, v in extras.items())
            return f"{base} | {extra_str}"

        return base
