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