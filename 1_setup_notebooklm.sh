#!/usr/bin/env bash
# Cài đặt notebooklm-py trên WSL Ubuntu và đăng nhập Google (chỉ cần làm một lần).
# Cách chạy:  bash 1_setup_notebooklm.sh
set -e
export PATH="$HOME/.local/bin:$PATH"

echo "== 1/5  Cài gói hệ thống (hỏi mật khẩu sudo của Ubuntu) =="
echo "   Lưu ý: gõ mật khẩu sẽ KHÔNG hiện ký tự nào, đó là bình thường."
sudo apt-get update
sudo apt-get install -y curl libatomic1

echo
echo "== 2/5  Cài uv (trình quản lý Python, tự tải Python khi cần) =="
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

echo
echo "== 3/5  Cài trình duyệt Chromium cho bước đăng nhập (có thể mất vài phút) =="
uv run --no-project --with "notebooklm-py[browser]" python -m playwright install --with-deps chromium

echo
echo "== 4/5  Đăng nhập Google =="
if [ -z "${DISPLAY:-}" ]; then
  echo "CẢNH BÁO: biến DISPLAY đang trống, WSL có thể không mở được cửa sổ trình duyệt."
  echo "          Xem mục 'Không mở được trình duyệt' trong README.md."
fi
echo "Cửa sổ Chromium sẽ mở ra: đăng nhập Google, vào được trang NotebookLM,"
echo "rồi quay lại terminal làm theo hướng dẫn (thường là nhấn Enter)."
uvx --from "notebooklm-py[browser]" notebooklm login

echo
echo "== 5/5  Kiểm tra phiên đăng nhập (cần thấy \"status\": \"ok\") =="
uvx --from "notebooklm-py[browser]" notebooklm auth check --test --json

echo
echo "Xong. Để xem danh sách notebook và ID của chúng:"
echo "   uvx --from notebooklm-py notebooklm list"
echo "Ghi ID notebook (hoặc URL) vào file notebook_id.txt rồi chuyển sang bước OCR/giảng bài."
