from langchain_community.embeddings import JinaEmbeddings
from app.core.config import settings

def get_jina_embeddings(model_name: str = "jina-embeddings-v2-base-en"):
    return JinaEmbeddings(
        jina_api_key=settings.ai.jina_key,
        model_name=model_name
    )
