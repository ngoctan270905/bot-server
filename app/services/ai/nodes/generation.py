from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.services.ai.state import AgentState
from app.services.ai.prompts import get_generation_system_prompt

async def generate_node(state: AgentState, llm_builder) -> dict:
    """
    Node 3: Tạo câu trả lời cuối cùng dựa trên context và chat history.
    """
    llm = llm_builder()

    # Chuẩn bị context text từ tài liệu tìm được
    context_text = ""
    if state.get("context"):
        context_text = "\n\n".join([d.page_content for d in state["context"]])

    # Xây dựng Prompt hệ thống
    bot_instructions = state.get("bot_instructions") or "No instructions"
    
    system_prompt = get_generation_system_prompt(bot_instructions, context_text)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    chain = prompt | llm
    
    result = await chain.ainvoke({
        "input": state["input"],
        "chat_history": state["chat_history"],
        "context": context_text
    })
    
    return {"answer": result.content}
