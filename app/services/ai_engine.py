import os
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Redis as RedisVectorStore
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from app.core.config import settings
from loguru import logger

# --- 1. Đồng bộ Prompts từ Node.js ---
QA_SYSTEM_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use your own knowledge to answer user's question, in its original language. "
    "if you dont know the answer, you can respond with something like 'I am not sure' in the user's question language."
)

CONTEXTUALIZE_Q_SYSTEM_PROMPT = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

CONTEXT_QA_SYSTEM_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following context to answer "
    "the user's question, in its original language.\n\n"
    "{context}\n"
    "if no context is provided, you can use your own knowledge. "
    "if you dont know the answer, you can respond with something like 'I am not sure' in the user's question language."
)

class AIEngine:
    def __init__(self):
        self.redis_url = settings.redis.url
        self._started = False

    async def start(self):
        """Khởi tạo (nếu cần thiết cho các connection pool sau này)"""
        self._started = True
        logger.bind(context="AIEngine").info("AI Engine (LangChain) đã sẵn sàng.")

    async def stop(self):
        """Đóng kết nối (nếu cần)"""
        self._started = False
        logger.bind(context="AIEngine").info("AI Engine (LangChain) đã đóng.")

    def get_llm(self, model_name: Optional[str] = None, temperature: float = 0.3):
        """Khởi tạo LLM (Hỗ trợ cả Local API, OpenAI và Gemini)"""
        target_model = model_name or settings.ai.llm_model
        
        # Luồng dùng API Local hoặc OpenAI
        if "gpt" in target_model or "gemma" in target_model or "bge" in target_model:
            return ChatOpenAI(
                model=target_model,
                temperature=temperature,
                openai_api_key=settings.ai.openai_key or "local-no-key",
                openai_api_base=settings.ai.llm_url.replace("/chat/completions", ""),
            )
        # Luồng dùng Gemini
        elif "gemini" in target_model:
            return ChatGoogleGenerativeAI(
                model=target_model,
                google_api_key=settings.ai.gemini_key,
                temperature=temperature
            )
        return ChatOpenAI(model=target_model, temperature=temperature)

    def get_embeddings(self):
        """Khởi tạo Embedding Model (Local hoặc OpenAI)"""
        return OpenAIEmbeddings(
            model=settings.ai.embedding_model,
            openai_api_key=settings.ai.openai_key or "local-no-key",
            openai_api_base=settings.ai.embedding_url.replace("/embeddings", "")
        )

    def get_vector_store(self, bot_id: str):
        """Kết nối vào Redis Vector Store (Dùng chung Index với Node.js)"""
        from langchain_community.vectorstores.redis.schema import RedisModel
        
        # Mặc định schema để tránh lỗi thiếu tham số ở bản 0.3.x
        index_schema = RedisModel().as_dict()
        
        return RedisVectorStore.from_existing_index(
            embedding=self.get_embeddings(),
            index_name=bot_id,
            redis_url=self.redis_url,
            schema=index_schema
        )

    async def ask(self, bot_id: str, question: str, conversation_id: str, bot_instructions: Optional[str] = None) -> str:
        """
        Luồng RAG đồng bộ 100% với Node.js:
        History Aware -> Retrieval -> QA
        """
        try:
            llm = self.get_llm()
            
            # Khởi tạo Vector Store Retriever
            try:
                vector_store = self.get_vector_store(bot_id)
                retriever = vector_store.as_retriever()
                has_vector_store = True
            except ValueError:
                # Nếu Index chưa tồn tại trên Redis (Bot chưa train)
                logger.warning(f"Index {bot_id} chưa tồn tại trên Redis. Chuyển sang trả lời không có context.")
                has_vector_store = False

            # 1. Khôi phục lịch sử từ Redis
            chat_history = RedisChatMessageHistory(
                session_id=conversation_id,
                url=self.redis_url,
                ttl=3600 # 1 giờ giống Node.js
            )

            # Lấy lịch sử chat
            messages = chat_history.messages

            if has_vector_store:
                # 2. Tạo Rephrase Prompt
                contextualize_q_prompt = ChatPromptTemplate.from_messages([
                    ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ])

                # 3. Tạo History-Aware Retriever
                history_aware_retriever = create_history_aware_retriever(
                    llm, retriever, contextualize_q_prompt
                )

                # 4. Tạo QA Prompt
                system_prompt = bot_instructions if bot_instructions else CONTEXT_QA_SYSTEM_PROMPT
                qa_prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ])

                # 5. Xây dựng Chain cuối cùng
                question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
                chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
            else:
                # Nếu không có Vector Store, chỉ trả lời bằng LLM + History
                system_prompt = bot_instructions if bot_instructions else QA_SYSTEM_PROMPT
                qa_prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ])
                chain = qa_prompt | llm

            # 6. Thực thi
            if has_vector_store:
                result = await chain.ainvoke({
                    "input": question,
                    "chat_history": messages
                })
                answer = result["answer"]
            else:
                result = await chain.ainvoke({
                    "input": question,
                    "chat_history": messages
                })
                answer = result.content

            # 7. Lưu câu trả lời của AI vào Redis History
            chat_history.add_user_message(question)
            chat_history.add_ai_message(answer)

            return answer

        except Exception as e:
            import traceback
            target_model = settings.ai.llm_model
            llm_url = settings.ai.llm_url
            logger.error(f"Lỗi AI Engine khi gọi model '{target_model}' tại '{llm_url}': {str(e)}")
            logger.debug(traceback.format_exc())
            return f"Xin lỗi, tôi gặp sự cố khi kết nối tới AI (Model: {target_model}). Vui lòng kiểm tra lại dịch vụ AI."

# Singleton instance
ai_engine = AIEngine()

