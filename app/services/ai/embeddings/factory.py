from typing import Optional
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.services.ai.embeddings.jina import get_jina_embeddings
from app.services.ai.embeddings.google import get_google_embeddings
from loguru import logger

def get_embeddings(model_name: Optional[str] = None):
    """
        Khởi tạo và trả về Embeddings phù hợp dựa trên tên model được cung cấp.

        Thứ tự ưu tiên:
        1. Jina AI Embeddings.
        2. OpenAI Embeddings.
        3. Google Embeddings.
        4. Local Embeddings thông qua Local Server.

        Args:
            model_name (Optional[str]):
                Tên model embeddings cần sử dụng.
                Nếu không truyền vào, hệ thống sẽ lấy model mặc định từ cấu hình.

        Returns:
            Embeddings:
                Đối tượng Embeddings tương ứng với nhà cung cấp được xác định.

        Supported Providers:
            - Jina AI.
            - OpenAI.
            - Google.
            - Local Server (ví dụ: bge-m3).

        Notes:
            - Các model chứa "jina" sẽ sử dụng Jina AI Embeddings.
            - Các model chứa "text-embedding" sẽ sử dụng OpenAI Embeddings.
            - Các model chứa "models/embedding" hoặc "gemini" sẽ sử dụng Google Embeddings.
            - Các trường hợp còn lại sẽ sử dụng Local Embeddings thông qua OpenAI-compatible API.
    """

    target_model = model_name or settings.ai.embedding_model
    
    # 1. Jina AI
    if "jina" in target_model.lower():
        logger.bind(context="AI-Engine").info(f"Using Jina AI Embeddings: {target_model}")
        return get_jina_embeddings(target_model)

    # 2. OpenAI Cloud
    if "text-embedding" in target_model.lower():
        logger.bind(context="AI-Engine").info(f"Using OpenAI Embeddings: {target_model}")
        return OpenAIEmbeddings(
            model=target_model,
            openai_api_key=settings.ai.openai_key
        )
    
    # 3. Google Cloud
    elif "models/embedding" in target_model.lower() or "gemini" in target_model.lower():
        logger.bind(context="AI-Engine").info(f"Using Google Embeddings: {target_model}")
        return get_google_embeddings(target_model)

    # 4. Mặc định dùng Local (bge-m3, v.v...) qua Local Server
    logger.bind(context="AI-Engine").info(f"Using Local Embeddings: {target_model}")
    return OpenAIEmbeddings(
        model=target_model,
        openai_api_key=settings.ai.openai_key or "local-no-key",
        openai_api_base=settings.ai.embedding_url.replace("/embeddings", "")
    )
