"""Credential destinations must be HTTPS or an exact loopback host."""

from urllib.parse import urlsplit, urlunsplit


def validate_api_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid API URL") from exc
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or "\\" in value
        or any(ord(char) <= 32 for char in value)
        or parsed.scheme not in {"http", "https"}
        or (parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"})
        or port == 0
    ):
        raise ValueError("API URL must use HTTPS except for exact loopback development")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))


def require_credential_destination(stored_url: str, requested_url: str) -> str:
    destination = validate_api_url(requested_url)
    if not stored_url or validate_api_url(stored_url) != destination:
        raise ValueError("credential belongs to a different API URL; log in for this destination")
    return destination
