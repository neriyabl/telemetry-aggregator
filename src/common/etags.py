def etag_from_ts(ts: float) -> str:
    """Generate ETag from timestamp.

    Args:
        ts: Unix timestamp as float.

    Returns:
        ETag string using milliseconds to avoid float formatting issues.
    """
    return str(int(ts * 1000))


def normalize_etag(value: str | None) -> str | None:
    """Normalize ETag value by removing quotes if present.

    Args:
        value: Raw ETag value that may be quoted or None.

    Returns:
        Normalized ETag value without quotes, or None if input was None/empty.
    """
    if not value:
        return None
    v = value.strip()
    # If-None-Match may arrive quoted: "123"
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        v = v[1:-1]
    return v
