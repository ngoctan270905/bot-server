from langchain_community.vectorstores import Redis as RedisVectorStore
from app.services.ai.state import AgentState

async def retrieve_node(state: AgentState, bot_id: str, ai_engine_instance) -> dict:
    """
    Node 2: Tìm kiếm tài liệu từ Redis VectorDB.
    """
    query = state.get("standalone_question") or state.get("input")
    
    try:
        if bot_id in ai_engine_instance._vs_cache:
            vector_store = ai_engine_instance._vs_cache[bot_id]
        else:
            from langchain_community.vectorstores.redis.schema import RedisModel
            index_schema = RedisModel().as_dict()

            vector_store = RedisVectorStore.from_existing_index(
                embedding=ai_engine_instance.get_embeddings(),
                index_name=bot_id,
                redis_url=ai_engine_instance.redis_url,
                schema=index_schema
            )
            ai_engine_instance._vs_cache[bot_id] = vector_store

        # Tìm kiếm tài liệu (không truyền k để dùng mặc định giống dự án gốc)
        docs = await vector_store.asearch(query, search_type="similarity")
        
        if not docs:
            return {"context": []}

        return {"context": docs}
    except Exception:
        return {"context": []}
