import sys
from pathlib import Path as _Path
from src.core.prompts import render_prompt
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
"""Prompt tách riêng để chỉnh lời lẽ mà không đụng logic.

Quy ước tiền tố nguồn: [SGK] sách, [GV] transcript giáo viên, [SLIDE] slide.
"""

COMMON = render_prompt("notebook_common")

MODES = {
    "sach": "notebook_sach",
    "giaovien": "notebook_giaovien",
    "ca_hai": "notebook_ca_hai",
}

# Thêm vào các chế độ giảng bài để kết quả có cấu trúc, tiện đưa vào Obsidian
FORMAT_MD = render_prompt("notebook_format_md")

NOTE_CHECK = "notebook_note_check"


def build_prompt(mode, lesson, note_text=None, structured=True):
    """mode: sach | giaovien | ca_hai | kiemtra_note.
    structured: thêm yêu cầu định dạng H1/H2/H3 (không áp dụng cho kiemtra_note)."""
    if mode == "kiemtra_note":
        if not note_text:
            raise ValueError("Chế độ kiểm tra note cần nội dung note.")
        body = render_prompt(NOTE_CHECK, lesson=lesson, note=note_text)
        return COMMON + "\n\n" + body
    body = render_prompt(MODES[mode], lesson=lesson)
    parts = [COMMON, body]
    if structured:
        parts.append(FORMAT_MD)
    return "\n\n".join(parts)
