# Prompt: Xây dựng API khởi tạo phiên chat mới (New Chat)

## Vai trò
Bạn là một Senior Backend Engineer chuyên về FastAPI. Nhiệm vụ của bạn là xây dựng API cho phép người dùng bắt đầu một phiên chat mới.

## Yêu cầu Logic
1. **Mục tiêu:** Tạo một bản ghi mới trong MongoDB để quản lý phiên trò chuyện.
2. **Dữ liệu đầu vào:** 
   - `current_user`: Thông qua dependency xác thực (JWT).
   - `title`: Chuỗi ký tự (optional, mặc định: "New Chat").
3. **Dữ liệu đầu ra:** Đối tượng `ConversationResponse` chứa `id`, `title`, `created_at`.
4. **Cấu trúc Database (MongoDB):**
   - Collection: `conversations`
   - Schema: `{ "user_id": "...", "title": "...", "messages": [], "created_at": "...", "updated_at": "..." }`

## Yêu cầu Kỹ thuật (Tuân thủ coding_rules.md)
1. **Functional Approach:** Ưu tiên viết các function xử lý logic thay vì bọc trong Class nếu không cần thiết.
2. **RORO Pattern:** Các hàm nhận vào một Object (Pydantic/Dict) và trả về một Object.
3. **Early Returns:** Kiểm tra tính hợp lệ của User và dữ liệu ngay đầu hàm.
4. **Happy Path:** Đặt logic tạo bản ghi và trả về kết quả ở cuối cùng của hàm.
5. **Type Hints:** Khai báo đầy đủ kiểu dữ liệu cho tham số và giá trị trả về.
6. **Async/Await:** Sử dụng thao tác bất đồng bộ hoàn toàn khi làm việc với MongoDB.

## Các file cần triển khai
1. `backend/app/schemas/chat.py`: Định nghĩa `ChatCreate`, `ChatResponse`.
2. `backend/app/repositories/chat_repository.py`: Hàm `create_conversation`.
3. `backend/app/api/v1/endpoints/chat.py`: Endpoint `POST /`.

## Đầu ra Mong muốn
- Mã nguồn Python chuẩn FastAPI, sử dụng Pydantic v2.
- Tuân thủ quy trình xử lý lỗi và logging của hệ thống.
