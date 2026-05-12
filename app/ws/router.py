import uuid
import msgpack
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from app.ws.connection_manager import manager
from app.ws.handler import handle_message
from app.api.v1.dependencies import get_chat_service
from app.services.chat_service import ChatService
from app.core.security import decode_token

router = APIRouter()

@router.websocket("/websocket")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    chat_service: ChatService = Depends(get_chat_service)
):
    # 1. Kiểm tra xác thực Token (Giống beforeHandle bên Node.js)
    if not token:
        # Nếu dùng browser client, token thường truyền qua query ?token=...
        # hoặc sec-websocket-protocol header. Ở đây ta ưu tiên query.
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        # Giải mã và kiểm tra token
        decoded = decode_token(token)
        user_id = decoded.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Khởi tạo kết nối sau khi đã xác thực thành công
    socket_id = str(uuid.uuid4())
    await manager.connect(socket_id, websocket)
    
    # Lưu userId vào context của socket để sử dụng sau này nếu cần
    socket_client = manager.get_client(socket_id)
    if socket_client:
        socket_client.context["userId"] = user_id

    try:
        while True:
            # Nhận dữ liệu nhị phân (Binary) từ client
            data = await websocket.receive_bytes()
            # Giải mã MsgPack (tương đương decode của notepack.io)
            decoded_data = msgpack.unpackb(data, raw=False)
            await handle_message(socket_id, decoded_data, chat_service)
    except WebSocketDisconnect:
        manager.disconnect(socket_id)
    except Exception as e:
        import traceback
        print(f"WS Exception: {e}")
        traceback.print_exc()
        manager.disconnect(socket_id)
