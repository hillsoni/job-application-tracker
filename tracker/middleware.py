import logging
import time

from typing import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("tracker.request_logger")


class RequestLoggerMiddleware:
    """Logs every incoming request with method, path, status code, and time taken.

    Output format: [2025-09-21 10:30:45] POST /api/applications/ → 201 | 45ms
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.monotonic()
        response = self.get_response(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        logger.info(
            "[%s] %s %s → %s | %.0fms",
            time.strftime("%Y-%m-%d %H:%M:%S"),
            request.method,
            request.path,
            response.status_code,
            elapsed_ms,
        )
        return response