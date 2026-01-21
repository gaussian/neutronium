
import logging

try:
    from opentelemetry import trace
except ImportError:
    trace = None  # OpenTelemetry not installed

from neutron.telemetry.context import (
    client_ip_var,
    enterprise_id_var,
    request_id_var,
    user_id_var,
)


def _trace_id_hex(ctx) -> str:
    """Convert an OTel trace ID integer to hex string."""
    return format(ctx.trace_id, "032x")


def _span_id_hex(ctx) -> str:
    """Convert an OTel span ID integer to hex string."""
    return format(ctx.span_id, "016x")


class ContextFilter(logging.Filter):
    """
    Logging filter that injects request context and OpenTelemetry/X-Ray IDs into log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # App context from contextvars
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        record.client_ip = client_ip_var.get()
        record.enterprise_id = enterprise_id_var.get()

        # OTel / X-Ray context (trace_id, span_id)
        if trace:
            ctx = trace.get_current_span().get_span_context()
            if ctx.is_valid:
                record.trace_id = _trace_id_hex(ctx)
                record.span_id = _span_id_hex(ctx)
                record.trace_sampled = bool(ctx.trace_flags.sampled)
            else:
                record.trace_id = None
                record.span_id = None
                record.trace_sampled = None
        else:
            # OpenTelemetry not installed, skip trace context
            record.trace_id = None
            record.span_id = None
            record.trace_sampled = None

        return True
