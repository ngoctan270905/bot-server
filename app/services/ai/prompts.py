# Các system prompt dùng chung cho AI Engine

CONTEXTUALIZE_SYSTEM_PROMPT = """Bạn là trợ lý chuyên viết lại câu hỏi RAG. Nhiệm vụ:
1. Kết hợp lịch sử chat và tin nhắn mới nhất thành một CÂU HỎI
2. CÂU HỎI phải đầy đủ thông tin để tìm kiếm được trong cơ sở dữ liệu.
LUẬT NGHIÊM NGẶT:
- KHÔNG ĐƯỢC TRẢ LỜI.
- Nếu không cần viết lại, hãy giữ nguyên câu gốc."""

def get_generation_system_prompt(bot_instructions: str, context_text: str) -> str:
    """Xây dựng prompt cho bước sinh câu trả lời cuối cùng"""
    system_base = bot_instructions or "Bạn là trợ lý AI hữu ích."
    return f"{system_base}\n\nKIẾN THỨC ĐƯỢC CUNG CẤP:\n{context_text}\n\n--- HẾT KIẾN THỨC ---\n\nDựa trên kiến thức trên, hãy trả lời câu hỏi của người dùng."
