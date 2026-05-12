# Feature Prompt: User Registration (Demo Version)

## 1. Goal
Triển khai tính năng đăng ký tài khoản người dùng đơn giản nhưng chuẩn hóa, sử dụng Username và Password. Đảm bảo dữ liệu được lưu trữ an toàn trong MongoDB và tuân thủ kiến trúc Layered Architecture (API -> Service -> Repository).

---

## 2. Technical Requirements
- **Database:** MongoDB (Sử dụng Async PyMongo đã cấu hình).
- **Security:** 
  - Hashing password bằng `bcrypt` (sử dụng `app/core/security.py`).
  - Không bao giờ trả về password trong API response.
- **Validation:**
  - Username: Tối thiểu 3 ký tự, tối đa 20 ký tự, không chứa ký tự đặc biệt.
  - Password: Tối thiểu 6 ký tự.
  - Kiểm tra Username đã tồn tại (Unique constraint logic).

---

## 3. Implementation Phases

### Phase 1: Domain & Schema Design
- [ ] Định nghĩa `User` Domain Model trong `app/models/domain/user.py`.
- [ ] Định nghĩa Pydantic schemas trong `app/schemas/user.py`:
  - `UserCreate`: Schema cho request body.
  - `UserResponse`: Schema cho API response (loại bỏ field password).

### Phase 2: Repository Layer
- [ ] Tạo `UserRepository` trong `app/repositories/user_repository.py`.
- [ ] Implement hàm `get_by_username` và `create`.

### Phase 3: Service Layer
- [ ] Tạo `AuthService` trong `app/services/auth_service.py`.
- [ ] Implement logic `register_user`:
  - Kiểm tra username tồn tại.
  - Hash password.
  - Gọi Repository để lưu.
  - Xử lý các custom exceptions (ví dụ: `UserAlreadyExistsException`).

### Phase 4: API Endpoint Wiring
- [ ] Tạo file `app/api/v1/endpoints/auth.py`.
- [ ] Đăng ký router `auth` vào `app/api/v1/router.py`.
- [ ] Implement POST `/register`.

### Phase 5: Testing & Validation
- [ ] Viết Unit Test cho `AuthService`.
- [ ] Viết Integration Test cho API `/register`.
- [ ] Đảm bảo coverage > 80% theo `testing_rules.md`.

---

## 4. Coding Standards to Apply
- Sử dụng `BaseModel` từ `app/schemas/base.py` cho các response.
- Sử dụng `logging` để ghi lại quá trình đăng ký (không log password).
- Trả về response theo format chung của dự án.
- Tuân thủ nghiêm ngặt `coding_rules.md`.
