import logging

from neutronium.telemetry.facts import RequestFacts

audit_logger = logging.getLogger("app.audit.request")


class AccessLogSink:
    """
    Sink that logs authenticated HTTP requests to the audit logger.

    Replicates the behavior of the legacy AccessLogMiddleware:
    - Only logs authenticated requests
    - Uses the same log message and extra fields
    - Writes to 'app.audit.request' logger
    """

    def emit(self, facts: RequestFacts) -> None:
        """
        Log authenticated request to the audit logger.

        Only logs if the request was from an authenticated user,
        matching the behavior of the original AccessLogMiddleware.
        """
        if not facts.user_is_authenticated:
            return

        audit_logger.info(
            "Authenticated HTTP request",
            extra={
                "http.method": facts.method,
                "http.path": facts.path,
                "http.route": facts.route,
                "http.status_code": facts.status_code,
                "http.user_agent": facts.user_agent[:512] if facts.user_agent else "",
                "duration_ms": facts.duration_ms,
                "user.is_privileged": facts.user_is_staff,
                "django.view": facts.view_name,
            },
        )
