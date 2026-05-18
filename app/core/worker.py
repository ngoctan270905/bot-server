from arq.connections import RedisSettings
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from loguru import logger
from app.tasks.chat_tasks import save_chat_history_task, update_bot_token_usage_task


async def on_startup(ctx):
    """
    Hook chạy khi Worker bắt đầu khởi động.
    """
    await connect_to_mongo()
    logger.bind(context="Worker").info("Background Worker đang khởi động...")

async def on_shutdown(ctx):
    """
    Hook chạy khi Worker tắt.
    """
    await close_mongo_connection()
    logger.bind(context="Worker").info("Background Worker đang dừng...")



class WorkerSettings:
    """
    Cấu hình nền cho Arq Worker.
    File này sẽ được dùng bởi lệnh: `arq app.core.worker.WorkerSettings`
    """

    # Danh sách các hàm xử lý task
    functions = [save_chat_history_task, update_bot_token_usage_task]
    # Cấu hình kết nối Redis lấy từ settings
    redis_settings = RedisSettings(
        host=settings.redis.host,
        port=settings.redis.port,
        password=settings.redis.password,
        database=settings.redis.db
    )

    # Các hooks vòng đời
    on_startup = on_startup
    on_shutdown = on_shutdown

    # Các tùy chọn tối ưu hóa
    max_jobs = 10
    job_timeout = 3600 # 1 tiếng (cho các task nặng như training)
    keep_result = 600  # Giữ kết quả trong 10 phút
