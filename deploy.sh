#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/Frontend"
BACKEND_DIR="$PROJECT_ROOT/Backend"
VENV_DIR="$BACKEND_DIR/.venv"
SERVICE_NAME="paperflow"
SERVICE_TEMPLATE="$PROJECT_ROOT/${SERVICE_NAME}.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PYTHON_BIN=""

if [[ ! -d "$FRONTEND_DIR" || ! -d "$BACKEND_DIR" ]]; then
  echo "[deploy] Không tìm thấy thư mục dự án. Kiểm tra lại đường dẫn." >&2
  exit 1
fi

ensure_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[deploy] Thiếu dependency: $cmd" >&2
    exit 1
  fi
}

detect_python() {
  local candidates=(
    "$VENV_DIR/bin/python"
    "$VENV_DIR/Scripts/python.exe"
    "$(command -v python3 || true)"
    "$(command -v python || true)"
  )

  for candidate in "${candidates[@]}"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      PYTHON_BIN="$candidate"
      return 0
    fi
  done

  echo "[deploy] Không tìm thấy Python hợp lệ trong môi trường hiện tại." >&2
  exit 1
}

setup_venv() {
  if [[ ! -f "$VENV_DIR/bin/python" && ! -f "$VENV_DIR/Scripts/python.exe" ]]; then
    echo "[deploy] Tạo virtualenv cho backend..."
    if command -v python3 >/dev/null 2>&1; then
      python3 -m venv "$VENV_DIR"
    elif command -v python >/dev/null 2>&1; then
      python -m venv "$VENV_DIR"
    else
      echo "[deploy] Không tìm thấy python3 hoặc python để tạo venv." >&2
      exit 1
    fi
  fi

  detect_python
  echo "[deploy] Sử dụng Python: $PYTHON_BIN"
}

install_backend() {
  echo "[deploy] Cài đặt dependencies backend..."
  "$PYTHON_BIN" -m pip install --upgrade pip
  "$PYTHON_BIN" -m pip install -r "$BACKEND_DIR/requirements.txt"
}

install_frontend() {
  echo "[deploy] Cài đặt dependencies frontend..."
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    (cd "$FRONTEND_DIR" && npm install)
  fi
}

build_frontend() {
  echo "[deploy] Build frontend..."
  (cd "$FRONTEND_DIR" && npm run build)
}

write_service_file() {
  cat > "$SERVICE_TEMPLATE" <<EOF
[Unit]
Description=PaperFlow Multi-Agent Research Assistant
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_ROOT
ExecStart=/usr/bin/env bash -lc 'cd "$PROJECT_ROOT" && "$PYTHON_BIN" "$PROJECT_ROOT/run.py"'
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

  echo "[deploy] Tạo file service mẫu tại: $SERVICE_TEMPLATE"
}

install_systemd_service() {
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "[deploy] Không phát hiện systemctl. Bỏ qua cài đặt systemd."
    echo "[deploy] Chạy thủ công: cd $PROJECT_ROOT && $PYTHON_BIN run.py"
    return 0
  fi

  if [[ $(id -u) -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      echo "[deploy] Cần quyền root, đang copy service bằng sudo..."
      sudo install -m 644 "$SERVICE_TEMPLATE" "$SERVICE_FILE"
    else
      echo "[deploy] Cần chạy script với sudo/root để cài systemd service." >&2
      return 1
    fi
  else
    install -d -m 755 "$(dirname "$SERVICE_FILE")"
    install -m 644 "$SERVICE_TEMPLATE" "$SERVICE_FILE"
  fi

  systemctl daemon-reload
  systemctl enable --now "$SERVICE_NAME"
  systemctl status "$SERVICE_NAME" --no-pager || true
}

main() {
  echo "[deploy] Bắt đầu deploy PaperFlow..."
  ensure_command npm
  detect_python
  setup_venv
  install_backend
  install_frontend
  build_frontend
  write_service_file
  install_systemd_service

  echo "[deploy] Hoàn tất!"
  echo "[deploy] Ứng dụng có thể truy cập tại: http://localhost:8000"
}

main "$@"
