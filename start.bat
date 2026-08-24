@echo off
:: Thiết lập bảng mã UTF-8 cho console
chcp 65001 >nul
echo ===================================================
echo   Khởi chạy PaperFlow (Backend + Frontend Port 8000)
echo ===================================================

:: Di chuyển đến thư mục chứa script
cd /d "%~dp0"

:: Ưu tiên chạy run.py với môi trường ảo .venv nếu tồn tại, ngược lại dùng python mặc định
if exist Backend\.venv\Scripts\python.exe (
    Backend\.venv\Scripts\python.exe run.py
) else (
    python run.py
)

pause
