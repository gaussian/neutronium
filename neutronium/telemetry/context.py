from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
client_ip_var: ContextVar[str | None] = ContextVar("client_ip", default=None)
enterprise_id_var: ContextVar[str | None] = ContextVar("enterprise_id", default=None)


def set_request_context(
    *,
    request_id: str | None = None,
    user_id: str | None = None,
    client_ip: str | None = None,
    enterprise_id: str | None = None,
) -> None:
    """Set request context variables for logging."""
    if request_id is not None:
        request_id_var.set(str(request_id))
    if user_id is not None:
        user_id_var.set(str(user_id))
    if client_ip is not None:
        client_ip_var.set(str(client_ip))
    if enterprise_id is not None:
        enterprise_id_var.set(str(enterprise_id))


def clear_request_context() -> None:
    """Clear all request context variables."""
    request_id_var.set(None)
    user_id_var.set(None)
    client_ip_var.set(None)
    enterprise_id_var.set(None)
