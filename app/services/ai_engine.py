import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from loguru import logger

class AIEngine:
    """
    AI Engine xử lý logic RAG: Embedding -> Search -> Rerank -> LLM.
    Sử dụng một AsyncClient duy nhất để tận dụng Connection Pooling.
    """

    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self):
        """Khởi tạo client duy nhất (gọi trong lifespan)."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
            logger.bind(context="AIEngine").info("AI Engine HTTP Client đã khởi tạo (Connection Pooling enabled).")

    async def stop(self):
        """Đóng client (gọi trong lifespan shutdown)."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.bind(context="AIEngine").info("AI Engine HTTP Client đã đóng.")

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("AIEngine chưa được start(). Hãy gọi await ai_engine.start() trong lifespan.")
        return self._client

    async def get_embedding(self, texts: List[str]) -> List[List[float]]:
        """Chuyển danh sách văn bản thành vector embedding."""
        try:
            response = await self.client.post(
                settings.ai.embedding_url,
                json={
                    "model": settings.ai.embedding_model,
                    "input": texts
                }
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
        except Exception as e:
            logger.error(f"Error in get_embedding: {e}")
            raise

    async def search_qdrant(self, vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Tìm kiếm các vector tương đồng trên Qdrant."""
        try:
            url = f"{settings.ai.qdrant_url}/collections/{settings.ai.qdrant_collection}/points/search"
            response = await self.client.post(
                url,
                json={
                    "vector": vector,
                    "limit": limit,
                    "with_payload": True
                }
            )
            response.raise_for_status()
            return response.json().get("result", [])
        except Exception as e:
            logger.error(f"Error in search_qdrant: {e}")
            return []

    async def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """Sắp xếp lại kết quả tìm kiếm bằng Reranker API."""
        if not documents:
            return []
            
        try:
            response = await self.client.post(
                settings.ai.reranker_url,
                json={
                    "model": settings.ai.reranker_model,
                    "query": query,
                    "documents": [doc["payload"]["text"] for doc in documents],
                    "top_n": top_k
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results") or data.get("data")
            reranked = []
            for item in results:
                idx = item["index"]
                doc = documents[idx]
                reranked.append({
                    "text": doc["payload"]["text"],
                    "score": item.get("relevance_score") or item.get("score") or 0
                })
            return reranked
        except Exception as e:
            logger.error(f"Error in rerank: {e}")
            return [{"text": d["payload"]["text"], "score": 1.0} for d in documents[:top_k]]

    async def generate_answer(self, prompt: str, model: Optional[str] = None) -> str:
        """Gọi LLM API để sinh câu trả lời."""
        try:
            response = await self.client.post(
                settings.ai.llm_url,
                json={
                    "model": model or settings.ai.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error in generate_answer: {e}")
            return "Xin lỗi, tôi gặp trục trặc khi xử lý câu hỏi này."

    async def ask(self, question: str, bot_instructions: Optional[str] = "") -> str:
        """
        Luồng chính: Nhận câu hỏi -> RAG -> Trả lời.
        """
        # 1. Embedding
        vectors = await self.get_embedding([f"query: {question}"])
        if not vectors:
            return await self.generate_answer(question)

        # 2. Search
        search_results = await self.search_qdrant(vectors[0])

        # 3. Rerank
        context_docs = await self.rerank(question, search_results)
        
        # 4. Build Prompt
        context_text = "\n---\n".join([f"[Context]: {d['text']}" for d in context_docs])
        
        system_prompt = bot_instructions or "Bạn là một AI trợ lý hữu ích."
        if context_text:
            prompt = (
                f"{system_prompt}\n\n"
                f"Hãy dựa vào thông tin dưới đây để trả lời câu hỏi của người dùng. "
                f"Nếu thông tin không có, hãy dùng kiến thức của bạn.\n\n"
                f"Context:\n{context_text}\n\n"
                f"Câu hỏi: {question}\n\n"
                f"Trả lời:"
            )
        else:
            prompt = f"{system_prompt}\n\nCâu hỏi: {question}\n\nTrả lời:"

        # 5. LLM Call
        return await self.generate_answer(prompt)

# Singleton instance
ai_engine = AIEngine()
