import logging
import sys
import os
import time
from loguru import logger
from app.core.config import settings
from app.core.context import get_request_id, get_client_ip, get_user_agent

# Biến toàn cục để tính toán khoảng cách thời gian giữa các lần log (+ms)
_last_log_time = time.time()

class InterceptHandler(logging.Handler):
    """
    Custom logging handler dùng để chuyển hướng (intercept)
    toàn bộ log từ thư viện logging chuẩn của Python (stdlib)
    sang hệ thống Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Tự động gán context từ tên logger nếu chưa có
        logger.opt(depth=depth, exception=record.exc_info).bind(context=record.name).log(
            level, record.getMessage()
        )


def inject_request_context(record):
    """
    Patch function dùng để inject request context vào mỗi log record.
    Tái hiện phong cách NestJS của dự án gốc.
    """
    global _last_log_time
    
    # 1. Tính toán khoảng cách thời gian (+ms)
    now = time.time()
    duration = (now - _last_log_time) * 1000
    record["extra"]["diff_ms"] = f" +{int(duration)}ms"
    _last_log_time = now

    # 2. Inject Request Context
    try:
        rid = get_request_id()
        # Chỉ trả về ID thuần, việc tô màu sẽ do formatter đảm nhận
        record["extra"]["request_id"] = f" [RID:{rid}]" if rid else ""

        cip = get_client_ip()
        record["extra"]["client_ip"] = f" [IP:{cip}]" if cip else ""

        ua = get_user_agent()
        if ua:
            record["extra"]["user_agent"] = ua

    except Exception:
        pass

    # 3. Đảm bảo luôn có context
    if "context" not in record["extra"]:
        # Mặc định lấy tên file/module phát ra log
        record["extra"]["context"] = record["name"]

    return True


def configure_logging():
    """
    Cấu hình toàn bộ hệ thống logging cho application.
    Format: [App] <PID> - <Timestamp> <LEVEL> [Context][RID] <Message> +<ms>
    """
    logger.remove()

    log_level = settings.LOG_LEVEL.upper()
    log_file = settings.LOG_FILE
    is_production = getattr(settings, "ENVIRONMENT", "development") == "production"

    if log_dir := os.path.dirname(log_file):
        os.makedirs(log_dir, exist_ok=True)

    # Patch logger gốc — tất cả import logger đều được inject context
    logger.configure(patcher=inject_request_context)

    # Console logging - NestJS Style
    # [App] PID - MM/DD/YYYY, h:mm:ss A  LEVEL [Context][RID][IP] Message +ms
    nestjs_format = (
        "<green>[App] {process}</green> - "
        "<white>{time:MM/DD/YYYY, h:mm:ss A}</white> "
        "<level>{level: ^7}</level> "
        "<yellow>[{extra[context]}]</yellow>"
        "<cyan>{extra[request_id]}</cyan>"
        "<magenta>{extra[client_ip]}</magenta> "
        "<level>{message}</level>"
        "<yellow>{extra[diff_ms]}</yellow>"
    )

    if is_production:
        # Production vẫn ưu tiên JSON để ELK/Loki dễ parse
        logger.add(
            sys.stdout,
            level=log_level,
            enqueue=True,
            serialize=True,
        )
    else:
        logger.add(
            sys.stdout,
            level=log_level,
            enqueue=True,
            serialize=False,
            format=nestjs_format,
            colorize=True,
        )

    # File logging (Luôn lưu dạng JSON để dễ truy vấn sau này)
    logger.add(
        log_file,
        level=log_level,
        enqueue=True,
        serialize=True,
        rotation=settings.LOG_MAX_BYTES,
        retention=settings.LOG_BACKUP_COUNT,
        compression="zip",
    )

    # Intercept stdlib logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Redirect log của ASGI stack
    for name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "starlette"]:
        _logger = logging.getLogger(name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

    # SQLAlchemy — chỉ log WARNING trở lên
    _sq = logging.getLogger("sqlalchemy")
    _sq.handlers = [InterceptHandler()]
    _sq.setLevel(logging.WARNING)
    _sq.propagate = False