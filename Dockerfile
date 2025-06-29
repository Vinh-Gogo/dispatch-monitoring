FROM python:3.11.0-slim

# 1. Cài thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copy & cài đặt dependencies từ file requirements.txt tại gốc
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy toàn bộ mã nguồn (app/, templates/, static/)
COPY ./app ./app
COPY ./templates ./templates
COPY ./static ./static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
