# Dispatch Monitoring System

Hệ thống giám sát khu dispatch bếp thương mại, chạy detect & track item, cho phép cải thiện model qua feedback.

## 📂 Cấu trúc thư mục

dispatch-monitoring/
├── app/ # code FastAPI + models + utils
├── Dockerfile
├── docker-compose.yml
├── README.md
└── .gitignore


## 🚀 Cài đặt & Chạy

1. Clone repo:
   ```bash
   git clone https://github.com/USERNAME/dispatch-monitoring.git
   cd dispatch-monitoring

(Nếu dùng Git LFS cho model)
git lfs install
git lfs pull

(Build & chạy với Docker Compose)
docker-compose up --build -d

Mở browser
Đến http://localhost:8000/docs để xem Swagger UI.