import asyncio
import json
from typing import Any, Callable, Dict, Optional
from loguru import logger
from redis.asyncio import Redis

class EventBus:
    """
    Hệ thống Event Bus sử dụng Redis Pub/Sub.
    Thay thế cho EventEmitter của dự án gốc, hỗ trợ giao tiếp giữa các services.
    """
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.pubsub = self.redis.pubsub()
        self._listeners: Dict[str, list] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def publish(self, channel: str, message: Any):
        """Đẩy một sự crate lên một channel."""
        try:
            payload = json.dumps(message)
            await self.redis.publish(channel, payload)
            logger.bind(context="EventBus").debug(f"Published to {channel}")
        except Exception as e:
            logger.bind(context="EventBus").error(f"Publish error: {e}")

    async def subscribe(self, channel: str, handler: Callable):
        """Đăng ký lắng nghe một channel."""
        if channel not in self._listeners:
            self._listeners[channel] = []
            await self.pubsub.subscribe(channel)
        
        self._listeners[channel].append(handler)
        logger.bind(context="EventBus").info(f"Subscribed to channel: {channel}")

    async def _listen_loop(self):
        """Vòng lặp lắng nghe tin nhắn từ Redis Pub/Sub."""
        while self._running:
            try:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = json.loads(message['data'])
                    
                    if channel in self._listeners:
                        # Gọi tất cả các handlers đã đăng ký cho channel này
                        tasks = [handler(data) for handler in self._listeners[channel]]
                        await asyncio.gather(*tasks, return_exceptions=True)
                
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.bind(context="EventBus").error(f"Listen loop error: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """Bắt đầu chạy Event Bus."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._listen_loop())
            logger.bind(context="EventBus").info("EventBus started")

    async def stop(self):
        """Dừng Event Bus."""
        self._running = False
        if self._task:
            self._task.cancel()
        await self.pubsub.unsubscribe()
        logger.bind(context="EventBus").info("EventBus stopped")

# Khởi tạo instance (Sẽ được gán redis client trong lifespan)
# Note: Trong thực tế, bạn có thể khởi tạo trực tiếp ở đây hoặc thông qua Dependency Injection
