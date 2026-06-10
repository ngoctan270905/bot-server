from langchain_community.vectorstores import Redis as RedisVectorStore
from app.core.config import settings

def get_redis_vector_store(bot_id: str, embeddings):
    """
    Create and return a Redis vector store using an existing index.

    Args:
        bot_id: Name of the Redis vector index.
        embeddings: Embedding model used for vector operations.

    Returns:
        RedisVectorStore instance connected to the existing index.
    """
    from langchain_community.vectorstores.redis.schema import RedisModel

    index_schema = RedisModel().as_dict()

    return RedisVectorStore.from_existing_index(
        embedding=embeddings,
        index_name=bot_id,
        redis_url=settings.redis.url,
        schema=index_schema
    )