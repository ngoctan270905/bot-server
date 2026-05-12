# Feature Prompt: User Login (JWT Authentication)

## 1. Goal
Triển khai tính năng đăng nhập để xác thực người dùng. Sau khi đăng nhập thành công, hệ thống sẽ trả về một JWT Access Token. Đảm bảo tính bảo mật cao và tuân thủ kiến trúc đã tối ưu (DI Collection).

---

## 2. Technical Requirements
- **Authentication**: Xác thực bằng Username và Password.
- **Security**:
  - Sử dụng `verify_password` từ `app/core/security.py` để kiểm tra mật khẩu.
  - Sử dụng `create_access_token` để tạo JWT.
  - Sử dụng `UnauthorizedException` (HTTP 401) khi xác thực thất bại.
- **Standards**:
  - Trả về token theo chuẩn OAuth2 (access_token, token_type).
  - Tích hợp với `oauth2_scheme` hiện có trong `app/api/v1/dependencies.py`.

---

## 3. Implementation Phases

### Phase 1: Schema Design
- [ ] Định nghĩa Pydantic schemas trong `app/schemas/token.py`:
  - `Token`: Schema trả về cho client (access_token, token_type).
  - `TokenData`: Schema chứa payload của token (sub/username).
- [ ] Cập nhật `app/schemas/user.py` nếu cần thiết cho login request (hoặc dùng `OAuth2PasswordRequestForm`).

### Phase 2: Service Layer
- [ ] Cập nhật `AuthService` trong `app/services/auth_service.py`.
- [ ] Implement hàm `authenticate_user`:
  - Tìm user theo username qua `UserRepository`.
  - Kiểm tra mật khẩu bằng `bcrypt`.
  - Ném lỗi `UnauthorizedException` nếu không khớp hoặc không tìm thấy.
- [ ] Implement hàm tạo token tổng quát (có thể gọi `create_access_token`).

### Phase 3: API Endpoint Wiring
- [ ] Thêm endpoint POST `/login` vào `app/api/v1/endpoints/auth.py`.
- [ ] Sử dụng `OAuth2PasswordRequestForm` để tương thích với Swagger UI (Authorize button).
- [ ] Mapping kết quả trả về đúng chuẩn `UnifiedResponse[Token]`.

### Phase 4: Dependency Completion
- [ ] Hoàn thiện hàm `get_current_user` trong `app/api/v1/dependencies.py` để query DB thực tế dựa trên token payload thay vì chỉ là stub.

### Phase 5: Testing & Validation
- [ ] Viết Unit Test cho logic xác thực trong `AuthService`.
- [ ] Viết Integration Test cho API `/login`.

---

## 4. Coding Standards to Apply
- Tiếp tục sử dụng DI sạch: Inject `Collection` vào Repository.
- Tuân thủ Pydantic v2 (ConfigDict, field_validator).
- Đảm bảo log đầy đủ các sự kiện đăng nhập (thành công/thất bại) nhưng không log mật khẩu.
