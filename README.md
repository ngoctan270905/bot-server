# Bot Server - AI Chatbot Backend

Bot Server là hệ thống backend mạnh mẽ được xây dựng bằng **FastAPI**, được thiết kế để quản lý và vận hành các bot AI tích hợp đa kênh (Facebook, Telegram, Zalo). Hệ thống hỗ trợ xử lý tác vụ nền (background tasks), kiến trúc hướng sự kiện (event-driven) và tích hợp các Engine AI tiên tiến.

---

## 🚀 Tính năng chính

- **AI Engine Mạnh Mẽ**: Tích hợp LangChain, LangGraph hỗ trợ các model hàng đầu như Google Gemini, OpenAI.
- **Tích hợp Đa Kênh**: Hỗ trợ Webhooks cho Facebook Messenger, Telegram và Zalo.
- **Kiến Trúc Event-Driven**: Sử dụng Redis Streams để xử lý các sự kiện tin nhắn từ mạng xã hội một cách bất đồng bộ và ổn định.
- **Background Worker**: Xử lý các tác vụ nặng (lưu lịch sử, phân tích token, gửi email) qua ARQ (Redis-based).
- **Quản lý Dữ liệu**: 
  - **MongoDB**: Cơ sở dữ liệu chính cho người dùng, bot và hội thoại.
  - **Redis**: Caching, Session và Message Queue.
- **Bảo mật & Hiệu năng**: JWT Authentication, Logging tập trung (Loguru).

---

## 🛠 Tech Stack

- **Ngôn ngữ**: Python 3.12
- **Framework**: FastAPI
- **AI/LLM**: LangChain, LangGraph, Google Generative AI, OpenAI
- **Database**: MongoDB, Redis
- **Task Queue**: ARQ
- **Logging & Monitoring**: Loguru
- **Infrastructure**: Docker & Docker Compose

---

## 📂 Cấu trúc dự án

```text
Bot-Server/
├── app/
│   ├── api/            # Các API endpoints (v1)
│   ├── core/           # Cấu hình hệ thống, worker, bảo mật (JWT)
│   ├── db/             # Kết nối & quản lý Database (Mongo, Redis, Qdrant)
│   ├── consumers/      # Xử lý Redis Streams (Event consumers)
│   ├── event_handlers/ # Logic xử lý các sự kiện cụ thể (FB, Tele,...)
│   ├── helper/         # Các hàm tiện ích (xử lý tài liệu, string,...)
│   ├── middlewares/    # Custom middlewares (Logging, Request ID,...)
│   ├── repositories/   # Lớp truy vấn dữ liệu (Abstraction layer)
│   ├── services/       # Logic nghiệp vụ & AI Engine
│   ├── schemas/        # Pydantic models (Request/Response)
│   ├── tasks/          # Định nghĩa ARQ background tasks
│   ├── webhooks/       # Handlers cho Telegram, Facebook
│   └── ws/             # WebSocket router & manager
├── logs/               # Lưu trữ file log
├── static/             # Static files & Uploads
├── tests/              # Unit & Integration tests
├── main.py             # Entry point của ứng dụng
├── requirements.txt    # Danh sách thư viện
└── docker-compose.yml  # File chạy hạ tầng (Mongo, Redis)
```

---

## ⚙️ Cài đặt & Chạy ứng dụng

### 1. Chuẩn bị môi trường
Yêu cầu Python 3.12.

```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Sao chép file `.env.example` thành `.env` và cập nhật các thông tin.

```bash
cp .env.example .env
```

### 3. Khởi chạy hạ tầng (Docker)
Sử dụng Docker Compose để chạy MongoDB và Redis:

```bash
docker-compose up -d
```

### 4. Chạy API Server môi trường phát triển:
```bash
uvicorn main:app --reload
```
API Docs sẽ có sẵn tại: `http://localhost:8000/docs`

### 5. Chạy Background Worker (ARQ)
Để xử lý các task nền:
```bash
arq app.core.worker.WorkerSettings
```
