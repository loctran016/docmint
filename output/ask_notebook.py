#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["notebooklm-py"]
# ///
"""
Giảng bài / kiểm tra note bằng NotebookLM, CHỌN NGUỒN THẬT SỰ (source_ids) theo tiền tố tên nguồn.

    sach          chỉ nguồn [SGK]
    giaovien      chỉ nguồn [GV] và [SLIDE]
    ca_hai        [SGK] + [GV] + [SLIDE]
    kiemtra_note  như ca_hai, đối chiếu từng ý trong note của bạn

Dùng (từ thư mục gốc repo):
    uv run output/ask_notebook.py ca_hai "Sinh lý gan"
    uv run output/ask_notebook.py giaovien "Sinh lý gan" --match gan -o bai.md
    uv run output/ask_notebook.py kiemtra_note "Sinh lý gan" --note note.txt

Notebook: -n <id>, biến NOTEBOOKLM_NOTEBOOK, hoặc file notebook_id.txt của toolkit.
Hỏi không truyền conversation_id thì NỐI vào cuộc trò chuyện hiện tại của notebook;
--new XOÁ lịch sử chat trước khi hỏi (không khôi phục được).
"""
import argparse
import asyncio
import os
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for _p in (str(HERE), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import common  # có trong toolkit; trên GitHub Actions có thể không cần
except ImportError:  # pragma: no cover
    common = None

from notebooklm import NotebookLMClient, SourceStatus

from prompts import build_prompt

GROUPS = {
    "sach": ["[SGK]"],
    "giaovien": ["[GV]", "[SLIDE]"],
    "ca_hai": ["[SGK]", "[GV]", "[SLIDE]"],
    "kiemtra_note": ["[SGK]", "[GV]", "[SLIDE]"],
}

# Xoá số trích dẫn [1], [2], [1, 3], [2-4] trong câu trả lời
CITATION = re.compile(r"\s?\[\d+(?:\s*[,\-–]\s*\d+)*\]")


# ------------------------------------------------------------------ chuẩn hoá tên
def strip_accents(s):
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def norm(s):
    return re.sub(r"\s+", " ", strip_accents(s or "").lower()).strip()


def lesson_key(title):
    """'Bài 5. Sinh lý gan' -> 'sinh ly gan' (bỏ tiền tố 'Bài N.', 'Chương N:'...)."""
    t = norm(title)
    t = re.sub(r"^(bai|chuong|phan|lien he thuc te)\s*\d+\s*[.:\-–]?\s*", "", t)
    return t.strip()


def source_tag(title):
    """Trả về tiền tố ('[SGK]', '[GV]', '[SLIDE]') của tên nguồn, hoặc None."""
    up = (title or "").strip().upper()
    for tag in ("[SGK]", "[GV]", "[SLIDE]"):
        if up.startswith(tag):
            return tag
    return None


# ------------------------------------------------------------------ chọn nguồn
def pick_sources(sources, prefixes, match=None):
    """Lấy nguồn có tiền tố phù hợp. --match chỉ áp dụng cho [GV]/[SLIDE],
    còn [SGK] luôn lấy hết."""
    chosen = []
    for s in sources:
        title = (s.title or "").strip()
        tag = source_tag(title)
        if tag is None or tag not in prefixes:
            continue
        if tag != "[SGK]" and match and norm(match) not in norm(title):
            continue
        chosen.append(s)
    return chosen


def match_lesson_sources(sources, prefixes, lesson, explicit_match=None):
    """Chọn nguồn cho MỘT bài: [SGK] lấy hết; [GV]/[SLIDE] chỉ lấy nguồn có tên khớp tên bài
    (hoặc khớp chuỗi explicit_match). Trả về (danh sách nguồn, tập tiền tố tìm thấy)."""
    key = lesson_key(lesson)
    chosen, found = [], set()
    for s in sources:
        title = (s.title or "").strip()
        tag = source_tag(title)
        if tag is None or tag not in prefixes:
            continue
        if tag != "[SGK]":
            body = norm(re.sub(r"^\[[A-Za-z]+\]\s*", "", title))
            if explicit_match:
                ok = norm(explicit_match) in norm(title)
            else:
                ok = bool(key) and (key in body or (body and body in key))
            if not ok:
                continue
        chosen.append(s)
        found.add(tag)
    return chosen, found


def resolve_notebook(cli_value=None):
    value = cli_value or os.environ.get("NOTEBOOKLM_NOTEBOOK")
    if common is not None:
        return common.read_notebook_id(value)   # tự đọc notebook_id.txt nếu value rỗng
    if not value:
        sys.exit("Thiếu notebook id (-n hoặc NOTEBOOKLM_NOTEBOOK).")
    return value.strip().rstrip("/").split("?")[0].split("/")[-1]


# ------------------------------------------------------------------ hỏi
async def ask_sources(client, notebook, prompt, source_ids, retries=3):
    """Hỏi với danh sách nguồn đã chọn; thử lại khi lỗi tạm thời. Trả về AskResult hoặc None."""
    for attempt in range(1, retries + 1):
        try:
            result = await client.chat.ask(notebook, prompt, source_ids=source_ids)
            answer = getattr(result, "answer", "")
            if answer and answer.strip():
                return result
            raise RuntimeError("Câu trả lời rỗng")
        except Exception as e:  # noqa: BLE001
            print(f"  Lỗi (lần {attempt}/{retries}): {type(e).__name__}: {e or '(không có nội dung)'}",
                  file=sys.stderr)
            if attempt < retries:
                await asyncio.sleep(10 * attempt)
    return None


async def run(args):
    notebook = resolve_notebook(args.notebook)
    note = Path(args.note).read_text(encoding="utf-8") if args.note else None
    prompt = build_prompt(args.mode, args.lesson, note, structured=not args.plain)

    async with NotebookLMClient.from_storage(chat_timeout=args.timeout) as client:
        sources = await client.sources.list(notebook, statuses={SourceStatus.READY})
        chosen = pick_sources(sources, GROUPS[args.mode], args.match)
        if not chosen:
            sys.exit(f"Không có nguồn READY nào có tiền tố {GROUPS[args.mode]}. Kiểm tra tên nguồn.")

        print("Nguồn được chọn:", file=sys.stderr)
        for s in chosen:
            print(f"  - {s.title}", file=sys.stderr)

        if args.new:  # XOÁ lịch sử chat của notebook (không khôi phục được)
            conv = await client.chat.get_conversation_id(notebook)
            if conv:
                await client.chat.delete_conversation(notebook, conv)

        result = await ask_sources(client, notebook, prompt, [s.id for s in chosen])

    if result is None:
        sys.exit("Không nhận được câu trả lời từ NotebookLM.")
    text = result.answer if args.keep_citations else CITATION.sub("", result.answer)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Đã lưu: {out}", file=sys.stderr)
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=list(GROUPS))
    ap.add_argument("lesson", help="Tên bài")
    ap.add_argument("-n", "--notebook")
    ap.add_argument("--note", help="File note (chế độ kiemtra_note)")
    ap.add_argument("--match", help="Chỉ lấy [GV]/[SLIDE] có chuỗi này trong tên")
    ap.add_argument("--timeout", type=float, default=600, help="Giây chờ chat (mặc định 600)")
    ap.add_argument("--new", action="store_true",
                    help="Xoá lịch sử chat trước khi hỏi (không khôi phục được)")
    ap.add_argument("--plain", action="store_true", help="không thêm yêu cầu định dạng H1/H2/H3")
    ap.add_argument("--keep-citations", action="store_true")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    if args.mode == "kiemtra_note" and not args.note:
        sys.exit("Chế độ kiemtra_note cần --note file.txt")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
