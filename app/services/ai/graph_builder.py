from loguru import logger
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import (
    create_history_aware_retriever,
)

from app.services.ai.state import AgentState
from app.services.ai.prompts import CONTEXTUALIZE_SYSTEM_PROMPT
from app.services.ai.embeddings.factory import get_embeddings
from app.services.ai.chat_models.factory import get_chat_model
from app.services.ai.vector_stores.factory import get_vector_store


def build_workflow(bot_id: str, ai_engine_instance):
    """
    Xây dựng đồ thị logic cho Bot.
    Gom 3 bước Analysis -> Retrieve -> Generate vào 1 Node duy nhất dùng Chain.
    """
    logger.bind(context="AI-Engine").info(
        f"Bắt đầu khởi tạo workflow cho bot {bot_id}"
    )

    # 1. Cấu hình Rephrase (Contextualize)
    logger.bind(context="AI-Engine").info(
        "Khởi tạo Chat Model"
    )
    llm = get_chat_model(temperature=0)

    # logger.bind(context="AI-Engine").info(
    #     "Khởi tạo Prompt tái diễn giải câu hỏi"
    # )
    # contextualize_prompt = ChatPromptTemplate.from_messages([
    #     ("system", CONTEXTUALIZE_SYSTEM_PROMPT),
    #     MessagesPlaceholder("chat_history"),
    #     ("human", "{input}"),
    # ])

    logger.bind(context="AI-Engine").info(
        "Khởi tạo Embeddings"
    )
    embeddings = get_embeddings()

    logger.bind(context="AI-Engine").info(
        f"Khởi tạo Vector Store cho bot {bot_id}"
    )
    vector_store = get_vector_store(bot_id, embeddings)

    logger.bind(context="AI-Engine").info(
        "Khởi tạo Retriever"
    )
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    # logger.bind(context="AI-Engine").info(
    #     "Khởi tạo History Aware Retriever"
    # )
    # history_aware_retriever = create_history_aware_retriever(
    #     llm,
    #     retriever,
    #     contextualize_prompt
    # )

    # 2. Cấu hình Q&A (Generate)
    logger.bind(context="AI-Engine").info(
        "Khởi tạo Prompt trả lời câu hỏi"
    )
    qa_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "{bot_instructions}\n\n"
            "KIẾN THỨC ĐƯỢC CUNG CẤP:\n"
            "{context}\n\n"
            "--- HẾT KIẾN THỨC ---\n\n"
            "Dựa trên kiến thức trên, hãy trả lời câu hỏi của người dùng."
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    logger.bind(context="AI-Engine").info(
        "Khởi tạo Question Answer Chain"
    )
    question_answer_chain = create_stuff_documents_chain(
        llm,
        qa_prompt
    )

    # 3. Nối tất cả lại thành RAG Chain
    logger.bind(context="AI-Engine").info(
        "Khởi tạo RAG Chain"
    )
    # rag_chain = create_retrieval_chain(
    #     history_aware_retriever,
    #     question_answer_chain
    # )

    rag_chain = create_retrieval_chain(
        retriever,
        question_answer_chain
    )

    # 4. Định nghĩa Node duy nhất cho Graph
    async def call_model(state: AgentState):
        """
        Thực thi RAG Chain và trả về câu trả lời.
        """
        logger.bind(context="AI-Engine").info(
            "Bắt đầu thực thi node model"
        )

        instructions = (state.get("bot_instructions") or "Bạn là trợ lý AI hữu ích.")

        logger.bind(context="AI-Engine").info(
            f"Câu hỏi hiện tại: {state['input']}"
        )

        logger.bind(context="AI-Engine").info(
            f"Số lượng tin nhắn lịch sử: {len(state['chat_history'])}"
        )

        logger.bind(context="AI-Engine").info(
            "Bắt đầu thực hiện Embedding và truy xuất tài liệu"
        )

        response = await rag_chain.ainvoke({
            "input": state["input"],
            "chat_history": state["chat_history"],
            "bot_instructions": instructions
        })

        logger.bind(context="AI-Engine").info(
            "Hoàn thành Embedding và truy xuất tài liệu"
        )

        logger.bind(context="AI-Engine").info(
            f"Đã truy xuất {len(response['context'])} tài liệu liên quan"
        )

        logger.bind(context="AI-Engine").info(
            f"Đã sinh câu trả lời: {response['answer'][:100]}..."
        )

        logger.bind(context="AI-Engine").info(
            "Hoàn thành node model"
        )

        return {
            "answer": response["answer"],
            "context": response["context"]
        }

    # 5. Xây dựng Graph
    logger.bind(context="AI-Engine").info(
        "Khởi tạo StateGraph"
    )

    workflow = StateGraph(AgentState)

    logger.bind(context="AI-Engine").info(
        "Thêm node model vào graph"
    )
    workflow.add_node("model", call_model)

    logger.bind(context="AI-Engine").info(
        "Kết nối START -> model"
    )
    workflow.add_edge(START, "model")

    logger.bind(context="AI-Engine").info(
        "Kết nối model -> END"
    )
    workflow.add_edge("model", END)

    logger.bind(context="AI-Engine").info(
        f"Khởi tạo workflow cho bot {bot_id} thành công"
    )

    return workflow.compile()