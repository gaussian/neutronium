
from contextvars import ContextVar

request_id_var = ContextVar("request_id", default=None)
user_id_var = ContextVar("user_id", default=None)
client_ip_var = ContextVar("client_ip", default=None)
x_amzn_trace_id_var = ContextVar("x_amzn_trace_id", default=None)
enterprise_id_var = ContextVar("enterprise_id", default=None)


def set_request_context(*, request_id=None, user_id=None, client_ip=None, x_amzn_trace_id=None, enterprise_id=None):
    """Set request context variables for logging."""
    if request_id is not None:
        request_id_var.set(request_id)
    if user_id is not None:
        user_id_var.set(user_id)
    if client_ip is not None:
        client_ip_var.set(client_ip)
    if x_amzn_trace_id is not None:
        x_amzn_trace_id_var.set(x_amzn_trace_id)
    if enterprise_id is not None:
        enterprise_id_var.set(enterprise_id)


def clear_request_context():
    """Clear all request context variables."""
    request_id_var.set(None)
    user_id_var.set(None)
    client_ip_var.set(None)
    x_amzn_trace_id_var.set(None)
    enterprise_id_var.set(None)
