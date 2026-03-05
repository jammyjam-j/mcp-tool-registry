import time
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from app.core.registry import ToolRegistry
from app.settings import Settings


class LoggingAndValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: "FastAPI") -> None:
        super().__init__(app)
        self.registry = ToolRegistry()
        self.settings = Settings()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        content_length = response.headers.get("content-length", "unknown")
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)

        log_data = {
            "client_ip": client_ip,
            "method": method,
            "url": url,
            "status_code": response.status_code,
            "process_time_ms": round(process_time, 2),
            "content_length": content_length,
        }

        self._log_request_response(log_data)

        if request.url.path.startswith("/tools/"):
            tool_name = request.url.path.split("/")[-1]
            if not self.registry.is_registered(tool_name):
                return Response(
                    content=f"Tool '{tool_name}' not found",
                    status_code=404,
                    media_type="text/plain",
                )

        return response

    def _log_request_response(self, data: dict) -> None:
        if self.settings.log_requests:
            print(f"[REQUEST] {data['client_ip']} - {data['method']} {data['url']} "
                  f"-> {data['status_code']} ({data['process_time_ms']} ms, {data['content_length']} bytes)")


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: "FastAPI") -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            status_code = 500
            detail = str(exc)
            if hasattr(exc, "status_code"):
                status_code = getattr(exc, "status_code")
            if hasattr(exc, "detail"):
                detail = getattr(exc, "detail")
            response_content = {"error": detail}
            return Response(
                content=response_content,
                status_code=status_code,
                media_type="application/json",
            )