# Sử dụng Python 3.11 slim để giảm kích thước image
FROM python:3.12-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Sao chép file requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Tạo thư mục cho logs và uploads (đảm bảo quyền ghi)
RUN mkdir -p logs static/uploads && chmod -R 777 logs static

# Mở port (theo config mặc định là 3041)
EXPOSE 8000

# Lệnh khởi chạy ứng dụng
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
