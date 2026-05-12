from typing import Any, Dict
from loguru import logger
from app.ws.connection_manager import manager
from app.ws.schemas import (
    WSMessage, 
    ClientStartChatPayload, 
    ClientSendMessagePayload,
    ServerConversationCreatedPayload,
    ServerSendMessagePayload
)
from app.services.chat_service import ChatService

async def handle_message(socket_id: str, data: Dict[str, Any], chat_service: ChatService):
    """
    Hàm điều hướng xử lý tin nhắn từ client.
    """
    try:
        # Parse tin nhắn thô sang object WSMessage
        msg = WSMessage(**data)
        socket_client = manager.get_client(socket_id)
        if not socket_client:
            return

        if msg.type == "ClientStartChat":
            payload = ClientStartChatPayload(**msg.payload)
            conversation_id = await chat_service.start_chat(payload.bot_id, payload.channel)
            
            # Lưu vào context của socket
            socket_client.context["conversationId"] = conversation_id
            socket_client.context["botId"] = payload.bot_id
            
            # Gửi lại thông báo cho client
            response = WSMessage(
                type="ServerConversationCreated",
                payload=ServerConversationCreatedPayload(conversationId=conversation_id).model_dump(by_alias=True)
            )
            await socket_client.send_json(response.model_dump(by_alias=True))

        elif msg.type == "ClientSendMessage":
            payload = ClientSendMessagePayload(**msg.payload)
            conv_id = socket_client.context.get("conversationId")
            bot_id = socket_client.context.get("botId")
            
            if not conv_id or not bot_id:
                logger.error(f"Message received but no conversation started for socket: {socket_id}")
                return

            # 1. Lưu tin nhắn của khách
            await chat_service.save_message(conv_id, bot_id, payload.message, "customer")

            # 2. Ack gửi lại cho khách (echo)
            ack = WSMessage(
                type="ServerSendMessage",
                payload=ServerSendMessagePayload(
                    conversationId=conv_id,
                    message=payload.message,
                    isCustomerSend=True
                ).model_dump(by_alias=True)
            )
            await socket_client.send_json(ack.model_dump(by_alias=True))

            # 3. Lấy AI Response
            ai_text = await chat_service.get_ai_response(bot_id, payload.message, conv_id)

            # 4. Lưu tin nhắn AI
            await chat_service.save_message(conv_id, bot_id, ai_text, "ai")

            # 5. Gửi tin nhắn AI xuống client
            ai_msg = WSMessage(
                type="ServerSendMessage",
                payload=ServerSendMessagePayload(
                    conversationId=conv_id,
                    message=ai_text,
                    isCustomerSend=False
                ).model_dump(by_alias=True)
            )
            await socket_client.send_json(ai_msg.model_dump(by_alias=True))

        elif msg.type == "ClientEndChat":
            # Xử lý khi client chủ động kết thúc chat
            socket_client.context = {}
            logger.info(f"Chat ended by client: {socket_id}")

    except Exception as e:
        logger.bind(context="WS").error(f"Lỗi khi xử lý tin nhắn: {str(e)}")
