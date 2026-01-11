
import logging

from .context import (
    request_id_var,
    user_id_var,
    client_ip_var,
    x_amzn_trace_id_var,
)


def _hex_otel_id(value: int, width: int) -> str | None:
    """Convert an OTel ID integer to hex string."""
    return f"{value:0{width}x}" if value else None


class ContextFilter(logging.Filter):
    """
    Logging filter that injects request context and OpenTelemetry/X-Ray IDs into log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # App context from contextvars
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        record.client_ip = client_ip_var.get()
        record.x_amzn_trace_id = x_amzn_trace_id_var.get()
        record.enterprise_id = enterprise_id_var.get()

        # OTel / X-Ray context (trace_id, span_id, and friendly xray_trace_id)
        # Only import if available (optional dependency)
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            ctx = span.get_span_context() if span else None
            if ctx and ctx.is_valid:
                record.trace_id = _hex_otel_id(ctx.trace_id, 32)  # 32 hex chars
                record.span_id = _hex_otel_id(ctx.span_id, 16)  # 16 hex chars
                record.xray_trace_id = (
                    f"1-{record.trace_id[:8]}-{record.trace_id[8:]}"
                    if record.trace_id
                    else None
                )
            else:
                record.trace_id = None
                record.span_id = None
                record.xray_trace_id = None
        except ImportError:
            # OpenTelemetry not installed, skip trace context
            record.trace_id = None
            record.span_id = None
            record.xray_trace_id = None

        return True
