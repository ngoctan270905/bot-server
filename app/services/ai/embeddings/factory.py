from typing import Optional
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.services.ai.embeddings.jina import get_jina_embeddings
from app.services.ai.embeddings.google import get_google_embeddings
from loguru import logger

def get_embeddings(model_name: Optional[str] = None):
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
