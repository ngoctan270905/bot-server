from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas.base import UnifiedResponse

# Khởi tạo limiter với định danh mặc định là địa chỉ IP của client.
limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Xử lý ngoại lệ vượt quá giới hạn request (rate limit)
    và trả về response theo định dạng UnifiedResponse.

    Args:
        request (Request): Đối tượng request từ client.
        exc (Exception): Ngoại lệ được phát sinh.

    Returns:
        JSONResponse: Response HTTP 429 với định dạng dữ liệu thống nhất.
    """
    response_data = UnifiedResponse[None](
        success=False,
        message="Too many requests. Please try again later.",
        data=None,
    )

    return JSONResponse(
        status_code=429,
        content=response_data.model_dump(),
    )