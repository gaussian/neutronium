
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestFacts:
    """
    Immutable container for request telemetry data.
    Collected by RequestTelemetryMiddleware and passed to all configured sinks.
    """

    # Request identification
    request_id: str | None = None

    # Enterprise context (from X-ENTERPRISE-ID header)
    enterprise_id: str | None = None

    # User context
    user_id: int | None = None
    user_is_authenticated: bool = False
    user_is_staff: bool = False

    # HTTP request info
    method: str = ""
    host: str = ""
    path: str = ""
    route: str | None = None
    view_name: str | None = None

    # Response info
    status_code: int | None = None

    # Timing
    duration_ms: int | None = None

    # Client info
    client_ip: str | None = None
    user_agent: str = ""
