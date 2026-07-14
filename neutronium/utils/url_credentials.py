from urllib.parse import quote, urlparse, urlunparse


def inject_credentials_into_url(url: str, username: str, password: str) -> str:
    """
    Inject credentials into a URL, replacing any existing credentials.

    Handles URL-encoding of credentials to support special characters
    like @, /, #, :, %, etc.

    Args:
        url: The base URL (e.g., amqp://host:5672/vhost or https://api.example.com)
        username: The username to inject
        password: The password to inject

    Returns:
        The URL with credentials included

    Example:
        >>> inject_credentials_into_url("amqp://host:5672/vhost", "user", "p@ss!")
        'amqp://user:p%40ss%21@host:5672/vhost'
    """
    parsed_url = urlparse(url)

    # URL-encode credentials to handle special characters
    encoded_username = quote(username, safe="")
    encoded_password = quote(password, safe="")

    # Build new netloc with credentials
    new_netloc = f"{encoded_username}:{encoded_password}@{parsed_url.hostname}"
    if parsed_url.port:
        new_netloc += f":{parsed_url.port}"

    return urlunparse(
        (
            parsed_url.scheme,
            new_netloc,
            parsed_url.path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
    )
