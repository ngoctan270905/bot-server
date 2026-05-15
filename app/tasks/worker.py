from arq import cron
from app.core.config import settings
from app.tasks.chat_tasks import save_chat_history_task, update_bot_token_usage_task, cron_sync_all_bots_analytics_task
from app.tasks.training_tasks import train_bot_task

class WorkerSettings:
    """
    Cấu hình Worker cho Arq.
    Chạy lệnh: `arq app.tasks.worker.WorkerSettings`
    """
    redis_settings = settings.redis_arq
    
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
