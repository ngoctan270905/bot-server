import time
from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware ghi log cho mọi request HTTP.
    Tái hiện middleware logRequest của dự án gốc (Elysia).
    """
    async def dispatch(self, request: Request, call_next):
        # Không log các request tới tài nguyên tĩnh hoặc docs để tránh loãng log
        if request.url.path.startswith(("/static", "/docs", "/openapi.json", "/redoc")):
            return await call_next(request)

        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        formatted_process_time = f"{process_time:.2f}ms"
        
        status_code = response.status_code
        method = request.method
        path = request.url.path
        
        # Logic màu sắc cho Status Code dựa trên Loguru tags
        status_color = "white" if status_code < 400 else "red"
        
        # Format log giống Middleware cũ: [Method] [Path] [Status] [Duration]
        log_msg = (
            f"<magenta>{method}</magenta> "
            f"<green>{path}</green> "
            f"<{status_color}>{status_code}</{status_color}> "
            f"<white>{formatted_process_time}</white>"
        )
        
        # Sử dụng .opt(colors=True) để Loguru render được các tag màu trong log_msg
        logger.bind(context="HTTP").opt(colors=True).info(log_msg)
        
        return response
