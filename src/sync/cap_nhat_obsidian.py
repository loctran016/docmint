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
Tạo/cập nhật note mục lục (hub) của sách trong Obsidian từ những gì đã tạo trong thư mục đầu ra.
Note này liệt kê Chương > Bài kèm link tới bài giảng, đề, mindmap, infographic, video;
mọi trích dẫn ([[Tên sách|n]]) trong các note đều trỏ về đây nên đồ thị (graph view) có hình ngôi sao quanh sách.

Cách chạy:
    uv run 9_cap_nhat_obsidian.py
    uv run 9_cap_nhat_obsidian.py --out-root "/mnt/c/Users/ten/Vault/Dinh duong" --book "Dinh dưỡng lâm sàng"
"""
import argparse

from src.core import common

ap = argparse.ArgumentParser(description="Cập nhật note mục lục Obsidian")
ap.add_argument("--out-root", help="thư mục đầu ra gốc (mặc định ket_qua hoặc NLM_OUT_ROOT)")
ap.add_argument("--book", help="tên note sách (mặc định lấy từ NLM_BOOK)")
args = ap.parse_args()

root = common.get_out_root(args.out_root)
book = common.get_book(args.book)
hub = common.update_hub(root, book)
if hub:
    print(f"Đã cập nhật: {hub}")
else:
    raise SystemExit(1)
