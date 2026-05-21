from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.services.ai.state import AgentState
from app.services.ai.prompts import CONTEXTUALIZE_SYSTEM_PROMPT

async def contextualize_node(state: AgentState, llm_builder) -> dict:
    """
    Node 1: Tái cấu trúc câu hỏi.
    Nếu có lịch sử thì viết lại, nếu không thì dùng câu gốc.
    """
    if not state.get("chat_history") or len(state["chat_history"]) == 0:
        return {"standalone_question": state["input"]}

    llm = llm_builder(temperature=0) 
    
    # Chỉ lấy 5 tin nhắn gần nhất để tiết kiệm token và tránh nhiễu
    recent_history = state["chat_history"][-5:] if len(state["chat_history"]) > 5 else state["chat_history"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", CONTEXTUALIZE_SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "Hãy viết lại câu này thành câu hỏi độc lập: {input}"),
    ])
    chain = prompt | llm
    result = await chain.ainvoke({
        "chat_history": recent_history,
        "input": state["input"]
    })

    standalone_q = result.content.strip()
    standalone_q = standalone_q.replace("Câu hỏi độc lập:", "").replace("Viết lại:", "").strip()
    
    return {"standalone_question": standalone_q}
