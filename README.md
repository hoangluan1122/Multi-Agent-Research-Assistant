# PaperFlow - Multi-Agent Research Assistant

## 🚀 Chạy ứng dụng chung một Port (Port 8000)

Ứng dụng đã được cấu hình để phục vụ cả Frontend (React SPA) và Backend (FastAPI API) chung một cổng `http://localhost:8000`.

### Cách 1: Chạy trực tiếp từ file `run.py` ở thư mục gốc
```bash
python run.py
```
*(Nếu chưa build frontend, script sẽ tự động chạy `npm run build` trước khi start server).*

### Cách 2: Chạy thủ công
1. Build Frontend:
```bash
cd Frontend
npm run build
cd ..
```
2. Khởi chạy Backend:
```bash
cd Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
3. Mở trình duyệt tại:
- **Giao diện Web:** [http://localhost:8000](http://localhost:8000)
- **API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠️ Chế độ Development (Hot-reload độc lập)
- **Backend:** `cd Backend && uvicorn app.main:app --port 8000 --reload`
- **Frontend (Vite Proxy sang port 8000):** `cd Frontend && npm run dev`
