from typing import Any, Dict

from app.core.redis_stream import RedisStreamConsumer
from app.event_handlers.telegram_handler import handle_telegram_message_event
from app.repositories.social_repository import SocialPageRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.telegram_service import TelegramService


class TelegramMessageConsumer(RedisStreamConsumer):
    """
    Redis Stream consumer responsible for processing Telegram message events.

    This consumer listens to TELEGRAM_MESSAGE_STREAM and delegates
    incoming events to the Telegram event handler for business logic
    processing.
    """

    def __init__(
        self,
        redis_client,
        social_repo: SocialPageRepository,
        customer_repo: CustomerRepository,
        conversation_repo: ConversationRepository,
        telegram_service: TelegramService,
        **kwargs
    ):
        super().__init__(
            redis_client,
            stream_name="TELEGRAM_MESSAGE_STREAM",
            group_name="MESSAGE_GROUP",
            **kwargs
        )

        # Repositories and services required by the event handler.
        self.social_repo = social_repo
        self.customer_repo = customer_repo
        self.conversation_repo = conversation_repo
        self.telegram_service = telegram_service

    async def handle_record(self, record: Dict[str, Any]):
        """
        Process a single Telegram event retrieved from Redis Stream.

        Expected payload format:
        {
            "telebotId": "<telegram bot id>",
            "payload": "<telegram update payload>"
        }
        """

        tele_id = record.get("telebotId")
        payload = record.get("payload")

        # Ignore malformed events that do not contain required fields.
        if tele_id and payload:
            await handle_telegram_message_event(
                tele_id,
                payload,
                self.social_repo,
                self.customer_repo,
                self.conversation_repo,
                self.telegram_service
            )