#!/usr/bin/env bash
# Mở menu trên WSL/Linux/macOS. Chạy:  bash menu.sh
cd "$(cd "$(dirname "$0")" && pwd)" || exit 1
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "Chưa có uv (trình quản lý Python, tự tải Python khi cần)."
  read -rp "Cài uv ngay bây giờ? [y/N] " a
  if [[ "$a" =~ ^[yY] ]]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  else
    exit 1
  fi
fi
exec uv run menu.py
