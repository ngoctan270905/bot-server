from app.services.ai.vector_stores.redis import get_redis_vector_store

def get_vector_store(bot_id: str, embeddings, store_type: str = "redis"):
    if store_type == "redis":
        return get_redis_vector_store(bot_id, embeddings)
    return get_redis_vector_store(bot_id, embeddings)
