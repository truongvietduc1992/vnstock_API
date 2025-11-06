# Sử dụng Python base image nhẹ và ổn định
FROM python:3.11-slim

# Thiết lập biến môi trường để Python không tạo file .pyc và output logs trực tiếp
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file dependencies và cài đặt
# Chúng ta cài đặt chúng trước để tối ưu hóa caching Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng (main.py, v.v...)
COPY . /app

# Khai báo cổng mà container sẽ lắng nghe
EXPOSE 8000

# Lệnh chạy ứng dụng khi container khởi động
# Sử dụng Gunicorn với Uvicorn worker để tăng cường hiệu năng và ổn định khi deploy
# --workers 4: Số lượng worker (thường là 2*số_core + 1, ở đây dùng 4 làm mặc định)
# main:app: Trỏ đến biến 'app' trong file 'main.py'
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4"]