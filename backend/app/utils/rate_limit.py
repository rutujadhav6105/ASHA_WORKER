def rate_limit(limit="100/minute"):
    """Stub decorator for future rate limiting.
    Currently does nothing; returns the original function unchanged.
    """
    def decorator(fn):
        return fn
    return decorator
