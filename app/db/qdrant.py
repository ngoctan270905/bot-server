import httpx
from loguru import logger
from app.core.config import settings

async def init_qdrant():
    """
    Khởi tạo Qdrant: Tạo collection nếu chưa tồn tại.
    """
    collection_name = settings.ai.qdrant_collection
    url = f"{settings.ai.qdrant_url}/collections/{collection_name}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # 1. Kiểm tra collection đã tồn tại chưa
            response = await client.get(url)
            if response.status_code == 200:
                logger.bind(context="Qdrant").info(f"Collection '{collection_name}' đã tồn tại.")
                return

            # 2. Nếu chưa tồn tại (404), tiến hành tạo mới
            logger.bind(context="Qdrant").info(f"Đang tạo collection '{collection_name}'...")
            
            # Cấu hình vector cho BGE-M3 thường là 1024. 
            # Nếu bạn dùng OpenAI thì là 1536.
            create_payload = {
                "vectors": {
                    "size": 1024, 
                    "distance": "Cosine"
                }
            }
            
            create_response = await client.put(url, json=create_payload)
            create_response.raise_for_status()
            
            logger.bind(context="Qdrant").success(f"Đã khởi tạo thành công collection '{collection_name}'.")
            
        except httpx.HTTPStatusError as e:
            logger.bind(context="Qdrant").error(f"Lỗi HTTP khi khởi tạo Qdrant: {e.response.text}")
        except Exception as e:
            logger.bind(context="Qdrant").error(f"Lỗi không xác định khi khởi tạo Qdrant: {e}")

async def check_qdrant_connection():
    """Kiểm tra kết nối tới Qdrant server."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ai.qdrant_url}/healthz")
            if response.status_code == 200:
                logger.bind(context="Qdrant").info("Kết nối Qdrant thành công.")
                return True
    except Exception as e:
        logger.bind(context="Qdrant").error(f"Không thể kết nối tới Qdrant: {e}")
        return False
