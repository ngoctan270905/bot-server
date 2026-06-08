from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

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
    
    # 1. Cấu hình Rephrase (Contextualize)
    llm = get_chat_model(temperature=0)
    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system", CONTEXTUALIZE_SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    embeddings = get_embeddings()
    vector_store = get_vector_store(bot_id, embeddings)
    retriever = vector_store.as_retriever(search_type="similarity")
    
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_prompt
    )

    # 2. Cấu hình Q&A (Generate)
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", "{bot_instructions}\n\nKIẾN THỨC ĐƯỢC CUNG CẤP:\n{context}\n\n--- HẾT KIẾN THỨC ---\n\nDựa trên kiến thức trên, hãy trả lời câu hỏi của người dùng."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # 3. Nối tất cả lại thành RAG Chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # 4. Định nghĩa Node duy nhất cho Graph
    async def call_model(state: AgentState):
        # Mặc định instructions nếu không có
        instructions = state.get("bot_instructions") or "Bạn là trợ lý AI hữu ích."
        
        response = await rag_chain.ainvoke({
            "input": state["input"],
            "chat_history": state["chat_history"],
            "bot_instructions": instructions
        })
        
        return {
            "answer": response["answer"],
            "context": response["context"]
        }

    # 5. Xây dựng Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("model", call_model)
    workflow.add_edge(START, "model")
    workflow.add_edge("model", END)

    return workflow.compile()
