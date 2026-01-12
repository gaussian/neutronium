
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
            "level": record.levelname,
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

        return json.dumps(payload, default=_json_default)


class DevConsoleFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        return f"[{record.levelname}] {record.getMessage()} ({record.pathname}:{record.lineno})"
