# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
"""
Cài đặt notebooklm-py và đăng nhập Google (chỉ cần làm một lần). Chạy được trên WSL/Linux, Windows, macOS.

    uv run 1_setup_notebooklm.py
    uv run 1_setup_notebooklm.py --dry-run     # chỉ in các lệnh sẽ chạy, không chạy thật

Lưu ý: WSL và Windows có phiên đăng nhập RIÊNG (mỗi nơi lưu trong thư mục home của nó).
"""
import argparse
import os
import shutil
import subprocess
import sys

from src.core import common

PKG = "notebooklm-py[browser]"


def run(cmd, dry, check=True):
    print("\n$ " + " ".join(cmd))
    if dry:
        return 0
    try:
        code = subprocess.run(cmd).returncode
    except FileNotFoundError:
        print(f"  Không tìm thấy lệnh: {cmd[0]}")
        code = 127
    if check and code != 0:
        raise SystemExit(f"Lệnh trên bị lỗi (mã {code}). Xem README mục Debug rồi chạy lại.")
    return code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="chỉ in lệnh, không chạy")
    dry = ap.parse_args().dry_run

    uv = shutil.which("uv")
    if not uv:
        if common.IS_WIN:
            raise SystemExit("Chưa có uv. Mở PowerShell chạy:  winget install astral-sh.uv  "
                             "rồi mở lại terminal.")
        raise SystemExit("Chưa có uv. Chạy:  curl -LsSf https://astral.sh/uv/install.sh | sh  "
                         "rồi mở lại terminal.")

    total = 4 if (common.IS_WIN or common.IS_MAC) else 5
    step = 0

    if not (common.IS_WIN or common.IS_MAC):
        step += 1
        print(f"== {step}/{total}  Cài gói hệ thống (hỏi mật khẩu sudo của Ubuntu) ==")
        print("   Lưu ý: gõ mật khẩu sẽ KHÔNG hiện ký tự nào, đó là bình thường.")
        sudo = [] if (hasattr(os, "geteuid") and os.geteuid() == 0) else ["sudo"]
        run(sudo + ["apt-get", "update"], dry)
        run(sudo + ["apt-get", "install", "-y", "curl", "libatomic1"], dry)

    step += 1
    print(f"\n== {step}/{total}  Cài trình duyệt Chromium cho bước đăng nhập (có thể mất vài phút) ==")
    pw = [uv, "run", "--no-project", "--with", PKG, "python", "-m", "playwright", "install"]
    if not (common.IS_WIN or common.IS_MAC):
        pw.append("--with-deps")
    run(pw + ["chromium"], dry)

    step += 1
    print(f"\n== {step}/{total}  Đăng nhập Google ==")
    if common.IS_WSL and not os.environ.get("DISPLAY"):
        print("CẢNH BÁO: biến DISPLAY đang trống, WSL có thể không mở được cửa sổ trình duyệt.")
        print("          Xem mục 'Không mở được trình duyệt' trong README.md.")
    print("Cửa sổ Chromium sẽ mở ra: đăng nhập Google, vào được trang NotebookLM,")
    print("rồi quay lại terminal làm theo hướng dẫn (thường là nhấn Enter).")
    run([uv, "tool", "run", "--from", PKG, "notebooklm", "login"], dry)

    step += 1
    print(f"\n== {step}/{total}  Kiểm tra phiên đăng nhập (cần thấy \"status\": \"ok\") ==")
    run([uv, "tool", "run", "--from", PKG, "notebooklm", "auth", "check", "--test", "--json"],
        dry, check=False)

    print("\nXong. Để xem danh sách notebook và ID của chúng:")
    print("   uv tool run --from notebooklm-py notebooklm list")
    print("Ghi ID notebook (hoặc URL) vào notebook_id.txt, hoặc dùng mục 'Đặt ID notebook' trong menu.")


if __name__ == "__main__":
    main()
