import functools
import logging
import uuid

from django.http import JsonResponse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .exceptions import APIError, RateLimitExceededError


def api_error_handler(view_func):
    """Decorator for consistent API error handling"""

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        logger = logging.getLogger(f"{view_func.__module__}.{view_func.__name__}")

        try:
            logger.info(
                f"[{request_id}] API call started",
                extra={
                    "request_id": request_id,
                    "path": request.path,
                    "method": request.method,
                },
            )

            if getattr(request, "limited", False):
                logger.warning(f"[{request_id}] Rate limit exceeded")
                return RateLimitExceededError().to_response()

            response = view_func(request, *args, **kwargs)

            logger.info(f"[{request_id}] API call completed successfully")
            return response

        except APIError as e:
            logger.warning(f"[{request_id}] API error: {e}")
            return e.to_response()
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "request_id": request_id,
                    },
                    "timestamp": timezone.now().isoformat(),
                },
                status=500,
            )

    return wrapper


def api_rate_limit(group=None, key=None, rate="60/h", method="POST"):
    """Standard API rate limiting decorator"""
    return ratelimit(
        group=group or "api", key=key or "ip", rate=rate, method=method, block=False
    )
