import json
from loguru import logger
from app.repositories.social_repository import SocialPageRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.ai.engine import ai_engine
from app.services.social_service import SocialService

async def handle_facebook_message_event(
    messaging_data: dict,
    social_repo: SocialPageRepository,
    customer_repo: CustomerRepository,
    conversation_repo: ConversationRepository,
    social_service: SocialService
):
    """
    Xử lý một sự kiện tin nhắn Facebook từ Redis Stream.
    Dữ liệu đầu vào (messaging_data) là object 'messaging' từ Facebook Webhook.
    """
    try:
        sender_id = messaging_data.get("sender", {}).get("id") # PSID
        recipient_id = messaging_data.get("recipient", {}).get("id") # Page ID
        message = messaging_data.get("message", {})
        
        # Chỉ xử lý tin nhắn văn bản (có thể mở rộng sau)
        text = message.get("text")
        if not text:
            return

        # 1. Tìm SocialPage dựa trên recipient_id (Page ID)
        social_page = await social_repo.get_by_page_id(recipient_id)
        if not social_page:
            logger.warning(f"SocialPage not found for page_id: {recipient_id}")
            return

        page_access_token = social_page["pageAccessToken"]
        bot_id = social_page["botId"]

        # 2. Tìm hoặc tạo Customer
        customer = await customer_repo.collection.find_one({
            "cid": sender_id,
            "socialPageId": social_page["_id"]
        })

        if not customer:
            # Lấy thông tin profile từ Facebook nếu là khách hàng mới
            profile = await social_service.get_user_profile(sender_id, page_access_token)
            customer_data = {
                "cid": sender_id,
                "name": profile.get("name") if profile else f"FB User {sender_id[:5]}",
                "avatar": profile.get("profile_pic") if profile else None,
                "socialPageId": social_page["_id"],
                "channel": "fb"
            }
            result = await customer_repo.collection.insert_one(customer_data)
            customer = {**customer_data, "_id": result.inserted_id}

        # 3. Tìm hoặc tạo Conversation
        conversation = await conversation_repo.collection.find_one({
            "customerId": customer["_id"]
        })

        if not conversation:
            conversation_data = {
                "customerId": customer["_id"],
                "botId": bot_id,
                "channel": "fb",
                "autoReply": True
            }
            result = await conversation_repo.collection.insert_one(conversation_data)
            conversation = {**conversation_data, "_id": result.inserted_id}

        # 4. Kiểm tra autoReply
        if not conversation.get("autoReply", True):
            return

        # 5. Hỏi AI phản hồi
        response_text = await ai_engine.ask(
            bot_id=str(bot_id),
            question=text,
            conversation_id=str(conversation["_id"])
        )

        # 6. Gửi phản hồi lại Facebook
        if response_text:
            await social_service.send_facebook_message(
                page_access_token=page_access_token,
                recipient_id=sender_id,
                message_text=response_text
            )
            logger.bind(context="FB-Handler").info(f"Replied to {sender_id}: {response_text[:50]}...")

    except Exception as e:
        logger.bind(context="FB-Handler").error(f"Error handling facebook message: {e}")
