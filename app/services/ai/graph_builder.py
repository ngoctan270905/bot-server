from langgraph.graph import StateGraph, START, END
from app.services.ai.state import AgentState
from app.services.ai.nodes.analysis import contextualize_node
from app.services.ai.nodes.retrieval import retrieve_node
from app.services.ai.nodes.generation import generate_node

def build_workflow(bot_id: str, ai_engine_instance):
    """
    Xây dựng đồ thị logic tuyến tính cho Bot (Linear RAG).
    Nối các node lại với nhau.
    """
    workflow = StateGraph(AgentState)

    # Wrappers để truyền tham số bổ sung cho các hàm async
    async def analysis_wrapper(state: AgentState):
        return await contextualize_node(state, ai_engine_instance.get_llm)

    async def retrieve_wrapper(state: AgentState):
        return await retrieve_node(state, bot_id, ai_engine_instance)

    async def generate_wrapper(state: AgentState):
        return await generate_node(state, ai_engine_instance.get_llm)

    # Thêm các Node
    workflow.add_node("analysis", analysis_wrapper)
    workflow.add_node("retrieve", retrieve_wrapper)
    workflow.add_node("generate", generate_wrapper)

    # Kết nối tuần tự
    workflow.add_edge(START, "analysis")
    workflow.add_edge("analysis", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()
