from arq import cron
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.tasks.chat_tasks import save_chat_history_task, update_bot_token_usage_task, cron_sync_all_bots_analytics_task
from app.tasks.training_tasks import train_bot_task
from app.services.ai.engine import ai_engine

async def startup(ctx):
    """Khởi tạo kết nối DB khi worker bắt đầu."""
    await connect_to_mongo()
    await ai_engine.start()

async def shutdown(ctx):
    """Đóng kết nối DB khi worker dừng."""
    await ai_engine.stop()
    await close_mongo_connection()

class WorkerSettings:
    """
    Cấu hình Worker cho Arq.
    Chạy lệnh: `arq app.tasks.worker.WorkerSettings`
    """
    redis_settings = settings.redis.redis_arq
    
    on_startup = startup
    on_shutdown = shutdown
    
    functions = [
        save_chat_history_task,
        update_bot_token_usage_task,
        cron_sync_all_bots_analytics_task,
        train_bot_task
    ]
    
    # Thiết lập chạy định kỳ (Cron) giống Node.js
    cron_jobs = [
        cron(
            cron_sync_all_bots_analytics_task, 
            hour=None,  # Chạy mỗi giờ
            minute=0,   # Vào phút thứ 0
            second=0,
            run_at_startup=True # Chạy ngay khi khởi động để có dữ liệu
        )
    ]
