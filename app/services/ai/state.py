from typing import List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document

class AgentState(TypedDict):
    """
    Trạng thái xuyên suốt các Node trong đồ thị LangGraph.
    Lưu trữ toàn bộ thông tin cần thiết cho một lượt hội thoại.
    """
    input: str                         # Câu hỏi gốc của khách
    chat_history: List[BaseMessage]    # Lịch sử chat lấy từ Redis
    standalone_question: str           # Câu hỏi đã được AI viết lại
    context: List[Document]            # Danh sách tài liệu tìm được từ VectorDB
    answer: str                        # Câu trả lời cuối cùng
    bot_instructions: Optional[str]    # Chỉ dẫn riêng cho bot
