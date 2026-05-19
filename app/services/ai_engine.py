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

# --- Prompt ---
QA_SYSTEM_PROMPT = (
  "Bạn là một trợ lý AI chuyên thực hiện các tác vụ hỏi đáp.\n"

  "Hãy sử dụng kiến thức sẵn có của chính bạn để trả lời câu hỏi của người dùng.\n"

  "Bạn phải trả lời bằng đúng ngôn ngữ mà người dùng sử dụng trong câu hỏi.\n"

  "Nếu người dùng hỏi bằng tiếng Việt thì trả lời bằng tiếng Việt.\n"
  "Nếu người dùng hỏi bằng tiếng Anh thì trả lời bằng tiếng Anh.\n"

  "Hãy cố gắng trả lời rõ ràng, dễ hiểu và đúng trọng tâm.\n"

  "Nếu bạn không chắc chắn về câu trả lời hoặc không có đủ thông tin,\n"
  "không được tự bịa ra nội dung.\n"

  "Thay vào đó, hãy trả lời một cách trung thực bằng các câu như:\n"
  "'Tôi không chắc về điều này'\n"
  "hoặc\n"
  "'Tôi không có đủ thông tin để trả lời chính xác'\n"

  "Câu trả lời từ chối cũng phải sử dụng đúng ngôn ngữ của người dùng."
)

CONTEXTUALIZE_Q_SYSTEM_PROMPT = (
  "Dựa trên lịch sử cuộc trò chuyện và câu hỏi mới nhất của người dùng,\n"
  "hãy xác định xem câu hỏi hiện tại có đang tham chiếu đến thông tin,\n"
  "đối tượng hoặc ngữ cảnh xuất hiện trước đó trong cuộc trò chuyện hay không.\n"

  "Nếu có, hãy viết lại câu hỏi thành một câu hỏi hoàn chỉnh,\n"
  "độc lập và dễ hiểu mà không cần phải đọc lịch sử hội thoại trước đó.\n"

  "Câu hỏi sau khi viết lại phải giữ nguyên ý nghĩa ban đầu của người dùng.\n"

  "Không được tự thêm thông tin mới ngoài ngữ cảnh đã có.\n"

  "KHÔNG được trả lời câu hỏi.\n"

  "Nhiệm vụ của bạn chỉ là viết lại câu hỏi cho rõ nghĩa hơn nếu cần.\n"

  "Nếu câu hỏi hiện tại đã đủ rõ ràng và có thể hiểu độc lập,\n"
  "hãy giữ nguyên câu hỏi và trả về như ban đầu."
)

CONTEXT_QA_SYSTEM_PROMPT = (
  "Bạn là một trợ lý AI chuyên thực hiện các tác vụ hỏi đáp.\n"

  "Hãy sử dụng phần context được cung cấp bên dưới để trả lời câu hỏi của người dùng.\n"

  "Bạn phải ưu tiên sử dụng thông tin trong context trước khi dùng kiến thức riêng của mình.\n"

  "Context:\n"
  "{context}\n\n"

  "Hãy trả lời bằng đúng ngôn ngữ mà người dùng sử dụng.\n"

  "Nếu context có chứa thông tin liên quan,\n"
  "hãy trả lời dựa trên context đó một cách chính xác và ngắn gọn.\n"

  "Nếu context không chứa đủ thông tin cần thiết,\n"
  "bạn có thể sử dụng thêm kiến thức sẵn có của mình để hỗ trợ trả lời.\n"

  "Nếu bạn hoàn toàn không biết câu trả lời,\n"
  "không được tự bịa thông tin.\n"

  "Hãy phản hồi trung thực bằng các câu như:\n"
  "'Tôi không chắc về điều này'\n"
  "hoặc\n"
  "'Tôi không có đủ thông tin để trả lời chính xác'\n"

  "Các câu trả lời từ chối cũng phải sử dụng đúng ngôn ngữ của người dùng."
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
        """Kết nối vào Redis Vector Store"""
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
        Luồng RAG:
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
                ttl=3600 # 1 giờ
            )
            messages = chat_history.messages

            if has_vector_store:
                # 2.Prompt dùng để viết lại câu hỏi thành dạng đầy đủ,
                # giúp retriever hiểu đúng ngữ cảnh từ lịch sử chat
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
                if bot_instructions:
                  system_prompt = bot_instructions + "\n\nContext:\n{context}"
                else:
                  system_prompt = CONTEXT_QA_SYSTEM_PROMPT

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
            chat_history.add_ai_message(str(answer))

            return str(answer)

        except Exception as e:
            import traceback
            target_model = settings.ai.llm_model
            llm_url = settings.ai.llm_url
            logger.error(f"Lỗi AI Engine khi gọi model '{target_model}' tại '{llm_url}': {str(e)}")
            logger.debug(traceback.format_exc())
            return f"Xin lỗi, tôi gặp sự cố khi kết nối tới AI (Model: {target_model}). Vui lòng kiểm tra lại dịch vụ AI."

# Singleton instance
ai_engine = AIEngine()

