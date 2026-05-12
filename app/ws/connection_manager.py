import msgpack
from typing import Dict, Any, Optional
from fastapi import WebSocket
from loguru import logger

class SocketClient:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.context: Dict[str, Any] = {}

    async def send_json(self, message: Dict[str, Any]):
        """Gửi tin nhắn JSON cho client."""
        await self.websocket.send_json(message)

    async def send_msgpack(self, message: Dict[str, Any]):
        """Gửi tin nhắn được mã hóa MsgPack cho client."""
        binary_data = msgpack.packb(message, use_bin_type=True)
        await self.websocket.send_bytes(binary_data)

class ConnectionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance.active_connections: Dict[str, SocketClient] = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ConnectionManager":
        return cls()

    async def connect(self, socket_id: str, websocket: WebSocket):
        """Chấp nhận kết nối và lưu client."""
        await websocket.accept()
        self.active_connections[socket_id] = SocketClient(websocket)
        logger.bind(context="WS").info(f"Client connected: {socket_id}")

    def disconnect(self, socket_id: str):
        """Xóa client khỏi danh sách quản lý."""
        if socket_id in self.active_connections:
            del self.active_connections[socket_id]
            logger.bind(context="WS").info(f"Client disconnected: {socket_id}")

    def get_client(self, socket_id: str) -> Optional[SocketClient]:
        """Lấy thông tin client theo socket_id."""
        return self.active_connections.get(socket_id)

    async def broadcast(self, message: Dict[str, Any]):
        """Gửi tin nhắn cho tất cả các client đang kết nối."""
        for client in self.active_connections.values():
            await client.send_json(message)

# Singleton instance
manager = ConnectionManager.get_instance()
