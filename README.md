# Bot Server

## Cài đặt

1. Tạo môi trường ảo (khuyến nghị):
```bash
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate
```

2. Cài đặt các thư viện:
```bash
pip install -r requirements.txt
```

3. Cấu hình biến môi trường:
Sao chép file `.env.example` thành `.env` và cập nhật các giá trị cần thiết.
```bash
cp .env.example .env
```

## Chạy ứng dụng

### 1. Chạy API Server (FastAPI)

Sử dụng `uvicorn` để chạy server:

```bash
uvicorn main:app --reload --port 3041
```

*Lưu ý: Port mặc định trong .env.example là 3041.*

### 2. Chạy Background Worker (ARQ)

Sử dụng `arq` để chạy worker xử lý các tác vụ nền (như lưu lịch sử chat, cập nhật token usage):

```bash
arq app.core.worker.WorkerSettings
```

## Cấu trúc thư mục chính

- `app/api`: Các routers và endpoints.
- `app/core`: Cấu hình hệ thống, worker, bảo mật.
- `app/db`: Kết nối database (MongoDB, Redis).
- `app/repositories`: Lớp truy vấn dữ liệu.
- `app/services`: Logic xử lý nghiệp vụ, AI engine.
- `app/tasks`: Định nghĩa các background tasks cho ARQ.
- `app/schemas`: Pydantic models cho request/response.
