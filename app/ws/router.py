import uuid
import traceback
import msgpack
from loguru import logger
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from app.ws.connection_manager import manager
from app.ws.handler import handle_message
from app.api.v1.dependencies import get_chat_service
from app.services.chat_service import ChatService
from app.core.security import decode_token

router = APIRouter()

# Giới hạn kích thước message để tránh OOM attack
MAX_MESSAGE_SIZE_BYTES = 64 * 1024  # 64KB

@router.websocket("/websocket")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    chat_service: ChatService = Depends(get_chat_service)
):
    # ------------------------------------------------------------------ #
    # 1. Xác thực Token TRƯỚC khi accept connection                       #
    # ------------------------------------------------------------------ #
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        decoded = decode_token(token)
        user_id = decoded.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ------------------------------------------------------------------ #
    # 2. Khởi tạo kết nối sau khi xác thực thành công                    #
    # ------------------------------------------------------------------ #
    socket_id = str(uuid.uuid4())
    await manager.connect(socket_id, websocket)

    socket_client = manager.get_client(socket_id)
    if socket_client is None:
        # Nếu get_client() trả None sau khi connect() thành công → bug
        # trong manager, không nên silently skip.
        logger.error(
            "connect() succeeded but get_client() returned None "
            f"for socket_id={socket_id}. Possible bug in ConnectionManager."
        )
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    socket_client.context["userId"] = user_id
    logger.info(f"WebSocket connected: socket_id={socket_id}, user_id={user_id}")

    # ------------------------------------------------------------------ #
    # 3. Vòng lặp nhận message                                            #
    # ------------------------------------------------------------------ #
    try:
        while True:
            # --- Nhận dữ liệu nhị phân ---
            data = await websocket.receive_bytes()

            # --- Giới hạn kích thước payload ---
            if len(data) > MAX_MESSAGE_SIZE_BYTES:
                logger.warning(
                    f"Payload too large ({len(data)} bytes) "
                    f"from socket_id={socket_id}. Closing connection."
                )
                await websocket.close(code=status.WS_1009_MESSAGE_TOO_BIG)
                manager.disconnect(socket_id)
                return

            # --- Giải mã MsgPack ---
            try:
                decoded_data = msgpack.unpackb(data, raw=False)
            except (msgpack.UnpackException, msgpack.ExtraData, ValueError) as exc:
                logger.warning(
                    f"Invalid msgpack from socket_id={socket_id}: {exc}"
                )
                continue  # Bỏ qua message lỗi, giữ kết nối

            # --- Validate schema cơ bản ---
            if not isinstance(decoded_data, dict) or "type" not in decoded_data:
                logger.warning(
                    f"Malformed message (missing 'type') "
                    f"from socket_id={socket_id}: {decoded_data!r}"
                )
                continue

            # --- Xử lý message ---
            await handle_message(socket_id, decoded_data, chat_service)

    except WebSocketDisconnect as exc:
        logger.info(
            f"WebSocket disconnected: socket_id={socket_id}, "
            f"user_id={user_id}, code={exc.code}"
        )
        manager.disconnect(socket_id)

    except Exception as exc:
        logger.error(
            f"Unexpected WebSocket error: socket_id={socket_id}, "
            f"user_id={user_id}, error={exc}\n"
            + traceback.format_exc()
        )
        manager.disconnect(socket_id)


@router.websocket("/livechat")
async def livechat_endpoint(
    websocket: WebSocket,
    botId: str = Query(..., alias="botId"),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    WebSocket dành cho khách hàng chat trực tiếp (Live Chat).
    Không yêu cầu Token, chỉ cần botId.
    """
    await websocket.accept()
    logger.info(f"Khách hàng kết nối LiveChat: bot_id={botId}")

    try:
        while True:
            # Nhận tin nhắn JSON từ khách hàng
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("data", {})

            if msg_type == "init":
                # 1. Khởi tạo phiên chat (Tạo Customer & Conversation)
                conversation_id = await chat_service.start_chat(bot_id=botId, channel="live")
                
                # 2. Lấy thông tin Bot để gửi trả khách
                bot = await chat_service._bot_repo.get_by_id(botId)
                
                await websocket.send_json({
                    "type": "init",
                    "data": {
                        "conversationId": conversation_id,
                        "chatbot": {
                            "id": botId,
                            "name": bot.get("name", "Assistant") if bot else "Assistant"
                        }
                    }
                })

            elif msg_type == "message":
                content = payload.get("content")
                conversation_id = payload.get("conversationId")

                if not content or not conversation_id:
                    continue

                # 1. Gửi xác nhận nhận tin nhắn (Echo để UI hiện tin nhắn khách ngay)
                await websocket.send_json({
                    "type": "message",
                    "data": {
                        "content": content,
                        "role": "customer"
                    }
                })

                # 2. Gọi AI Engine lấy phản hồi
                try:
                    ai_response = await chat_service.get_ai_response(
                        bot_id=botId,
                        message=content,
                        conversation_id=conversation_id
                    )

                    # 3. Lưu lịch sử vào DB qua Task ngầm
                    await chat_service.save_message(conversation_id, botId, content, "customer")
                    await chat_service.save_message(conversation_id, botId, ai_response, "ai")

                    # 4. Gửi câu trả lời của AI cho khách
                    await websocket.send_json({
                        "type": "message",
                        "data": {
                            "content": ai_response,
                            "role": "ai"
                        }
                    })
                except Exception as e:
                    logger.error(f"Lỗi AI trong LiveChat: {e}")
                    await websocket.send_json({
                        "type": "message",
                        "data": {
                            "content": "Xin lỗi, tôi gặp sự cố trong quá trình suy nghĩ. Vui lòng thử lại sau.",
                            "role": "ai"
                        }
                    })

    except WebSocketDisconnect:
        logger.info(f"Khách hàng đã thoát LiveChat: bot_id={botId}")
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong LiveChat WebSocket: {e}")
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
