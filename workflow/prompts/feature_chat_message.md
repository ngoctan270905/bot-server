# Prompt: Triển khai API Gửi tin nhắn & Tích hợp Gemini (Lazy Creation)

## Vai trò
Bạn là một Senior Backend Engineer. Nhiệm vụ của bạn là xây dựng API xử lý hội thoại, đảm bảo tính năng tự động khởi tạo cuộc trò chuyện (Lazy Creation) và tích hợp AI Gemini.

## Yêu cầu Logic
1. **Endpoint:** `POST /api/v1/chat/message`
2. **Dữ liệu đầu vào (Request):**
   - `content`: Nội dung tin nhắn của người dùng.
   - `conversation_id`: ID của phiên chat (Gửi `null` nếu là tin nhắn đầu tiên từ trang chủ).
3. **Luồng xử lý:**
   - **Xác thực:** Lấy `current_user` từ JWT token.
   - **Xử lý Hội thoại:**
     - Nếu `conversation_id` là `null`:
       - Tạo mới một `Conversation` trong MongoDB.
       - Tự động đặt `title` (ví dụ: lấy 10 từ đầu của `content`).
     - Nếu `conversation_id` có giá trị:
       - Kiểm tra cuộc trò chuyện có tồn tại và thuộc về `current_user` không. Nếu không, ném lỗi 404/403 ngay lập tức (**Early Return**).
   - **Tích hợp AI (Gemini):**
     - Gọi Gemini API (Sử dụng `google-generativeai`).
     - Nếu thiếu `GEMINI_API_KEY` trong cấu hình, ném lỗi `500` hoặc trả về thông báo "AI configuration missing" để test luồng trước.
   - **Lưu trữ:**
     - Lưu tin nhắn của `user` và phản hồi của `assistant` vào mảng `messages`.
     - Cập nhật `updated_at`.
4. **Dữ liệu trả về (Response):**
   - Trả về tin nhắn của AI và `conversation_id` (để Frontend chuyển trạng thái từ "New Chat" sang "Existing Chat").

## Yêu cầu Kỹ thuật (Tuân thủ coding_rules.md)
- **Functional Service:** Viết logic gọi AI và điều phối tại `backend/app/services/chat_service.py` bằng các plain functions (không dùng class cho service).
- **Class-based Repository:** Sử dụng `ChatRepository` đã có để thực hiện các thao tác CRUD với MongoDB.
- **RORO Pattern:** Các hàm service nhận vào một Object và trả về một Object.
- **Early Returns:** Xử lý các điều kiện lỗi/ngăn chặn ngay đầu hàm.
- **Happy Path:** Đặt logic thành công ở cuối cùng của hàm.

## Các file cần triển khai/chỉnh sửa
1. `backend/app/schemas/chat.py`: Thêm `ChatInput`, `ChatMessageResponse`.
2. `backend/app/repositories/chat_repository.py`: Bổ sung hàm `update_messages` hoặc `add_message`.
3. `backend/app/services/chat_service.py`: Viết logic `process_chat_message`.
4. `backend/app/api/v1/endpoints/chat.py`: Thêm endpoint `POST /message`.
