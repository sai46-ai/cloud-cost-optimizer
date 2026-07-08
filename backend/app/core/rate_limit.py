import time
import threading
from fastapi import HTTPException, Request, status
from app.core.config import get_settings

settings = get_settings()

# Thread-safe in-memory request log: IP address -> list of request timestamps
_request_history = {}
_lock = threading.Lock()


def rate_limiter(request: Request):
    """Enforce a thread-safe in-memory rate limiter based on client IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    with _lock:
        # Clean up timestamps older than 60 seconds
        if client_ip in _request_history:
            _request_history[client_ip] = [
                t for t in _request_history[client_ip] if now - t < 60
            ]
        else:
            _request_history[client_ip] = []

        # Check rate limit
        if len(_request_history[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

        # Log current request timestamp
        _request_history[client_ip].append(now)
