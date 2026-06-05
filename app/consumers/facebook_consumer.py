import json
from typing import Any, Dict
from app.core.redis_stream import RedisStreamConsumer
from app.event_handlers.facebook_handler import handle_facebook_message_event
from app.repositories.social_repository import SocialPageRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.social_service import SocialService

class FacebookMessageConsumer(RedisStreamConsumer):
    def __init__(
        self, 
        redis_client, 
        social_repo: SocialPageRepository,
        customer_repo: CustomerRepository,
        conversation_repo: ConversationRepository,
        social_service: SocialService,
        **kwargs
    ):
        super().__init__(
            redis_client, 
            stream_name="FACEBOOK_MESSAGE_STREAM", 
            group_name="MESSAGE_GROUP", 
            **kwargs
        )
        self.social_repo = social_repo
        self.customer_repo = customer_repo
        self.conversation_repo = conversation_repo
        self.social_service = social_service

    async def handle_record(self, record: Dict[str, Any]):
        message_json = record.get("message")
        if message_json:
            event_payload = json.loads(message_json)
            if event_payload.get("type") == "FACEBOOK_MESSAGE":
                await handle_facebook_message_event(
                    event_payload.get("data"),
                    self.social_repo, 
                    self.customer_repo, 
                    self.conversation_repo, 
                    self.social_service
                )
