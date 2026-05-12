# Prompt: Refactor Kiến trúc Lưu trữ Chat (Tách Collection Messages)

## Vai trò
Bạn là một Senior Backend Engineer. Nhiệm vụ của bạn là tái cấu trúc (refactor) hệ thống lưu trữ chat từ việc nhúng tin nhắn trong `conversations` sang việc sử dụng một collection `messages` riêng biệt.

## Lý do Refactor
- Tối ưu hiệu năng khi cuộc trò chuyện có hàng nghìn tin nhắn (tránh document size limit của MongoDB).
- Dễ dàng quản lý, tìm kiếm và phân trang (pagination) tin nhắn trong tương lai.

## Yêu cầu Kỹ thuật
1. **Cấu trúc Database mới:**
   - **Collection `conversations`**:
     - `id`: ObjectId
     - `user_id`: string
     - `title`: string
     - `created_at`, `updated_at`: datetime
   - **Collection `messages`**:
     - `id`: ObjectId
     - `conversation_id`: string (Liên kết với conversations)
     - `role`: string ("user" hoặc "assistant")
     - `content`: string
     - `timestamp`: datetime

2. **Repository (`ChatRepository`):**
   - Cập nhật Class để quản lý cả hai collection: `conversations` và `messages`.
   - Viết hàm `create_message`: Lưu một tin nhắn mới vào collection `messages`.
   - Viết hàm `get_messages_by_conversation_id`: Lấy danh sách tin nhắn thuộc về một chat (sắp xếp theo thời gian).
   - Cập nhật hàm `get_conversation_by_id`: Không còn lấy tin nhắn nhúng sẵn, thay vào đó sẽ phối hợp gọi hàm lấy tin nhắn từ collection mới.

3. **Service (`chat_service.py`):**
   - Cập nhật `process_chat_message` để lưu User Message và AI Message vào collection `messages`.
   - Đảm bảo `updated_at` của `conversations` vẫn được cập nhật khi có tin nhắn mới.

4. **Schema (`schemas/chat.py`):**
   - Đảm bảo các schema `ConversationResponse` và `ChatMessageResponse` vẫn tương thích với Frontend.

## Quy tắc tuân thủ (rules.md)
- **Class-based Repository**: Duy trì phong cách class cho Repository.
- **Functional Service**: Sử dụng các plain functions cho logic AI và điều phối.
- **RORO & Early Returns**: Xử lý logic sạch sẽ, kiểm tra lỗi sớm.

## Các file cần chỉnh sửa
1. `backend/app/repositories/chat_repository.py`
2. `backend/app/services/chat_service.py`
3. `backend/app/api/v1/endpoints/chat.py` (Cập nhật dependency injection nếu cần).
