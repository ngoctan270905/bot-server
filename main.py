from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException
from slowapi.errors import RateLimitExceeded
from loguru import logger
from app.schemas.base import UnifiedResponse
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.db.mongodb import mongo_manager
from app.db.redis import redis_manager
from app.db.qdrant import init_qdrant
from app.services.ai.engine import ai_engine
from app.middlewares.request_id import RequestIDMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.api.v1.router import api_router
from app.webhooks import telegram as telegram_webhook, facebook as facebook_webhook
from starlette.staticfiles import StaticFiles
from pathlib import Path
from app.event_handlers.listener import start_listener
import asyncio

# Configure logging before FastAPI app initialization
configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Đảm bảo thư mục uploads tồn tại
    uploads_path = Path(settings.UPLOADS_DIR)
    uploads_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Đảm bảo thư mục uploads '{uploads_path}' tồn tại.")

    # 2. Khởi tạo các kết nối Database Pool
    try:
        await mongo_manager.connect()
        await redis_manager.connect()
        await ai_engine.start()
        
        # Lưu vào app.state để các Router có thể truy cập qua Request
        app.state.mongodb = mongo_manager.client
        app.state.redis = redis_manager
        app.state.arq_pool = redis_manager.arq_pool

        # Khởi chạy Stream Listener
        asyncio.create_task(start_listener())
        
        logger.info("Tất cả các kết nối Database & AI Engine đã sẵn sàng. Stream Listener đã khởi chạy.")
    except Exception as e:
        logger.critical(f"Lỗi khởi động hệ thống: {e}")
        raise

    yield

    # 3. Đóng các kết nối khi tắt app (Graceful Shutdown)
    await ai_engine.stop()
    await redis_manager.disconnect()
    await mongo_manager.close()
    logger.info("Ứng dụng đã được tắt và dọn dẹp tài nguyên.")

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FASTAPI Production Bot Server",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory=settings.UPLOADS_DIR.split('/')[0]),
    name="static"
)

# ---- CORS Middleware ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Exception Handlers ----

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    simplified_errors = [{"field": ".".join(map(str, err["loc"])), "message": err["msg"]} for err in exc.errors()]
    logger.bind(context="Validation").error(f"Dữ liệu không hợp lệ: {simplified_errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=UnifiedResponse(success=False, message="Dữ liệu đầu vào không hợp lệ", data=simplified_errors).model_dump()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.bind(context="HTTPException").warning(f"Lỗi {exc.status_code}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content=UnifiedResponse(success=False, message=str(exc.detail), data=None).model_dump())

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.bind(context="Critical").exception(f"Lỗi hệ thống nghiêm trọng: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=UnifiedResponse(
            success=False, 
            message="Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.", 
            data=str(exc) if settings.ENVIRONMENT == "development" else None
        ).model_dump()
    )

# Setup SlowAPI Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ---- Middlewares ----
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# ---- Routers ----
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(telegram_webhook.router, prefix="/webhook", tags=["Webhooks"])
app.include_router(facebook_webhook.router, prefix="/webhook", tags=["Webhooks"])
