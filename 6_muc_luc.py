# /// script
# requires-python = ">=3.10"
# dependencies = ["notebooklm-py"]
# ///
"""
Nhờ NotebookLM đọc mục lục của sách: Chương/Phần -> Bài.
Vừa để kiểm tra NotebookLM có đọc được sách không, vừa cho bạn danh sách chương/bài để chép
vào giao_trinh.txt.

Cách chạy (từ thư mục toolkit):
    uv run 6_muc_luc.py              # đọc mục lục, in ra màn hình và lưu file
    uv run 6_muc_luc.py --apply      # như trên và GHI luôn vào giao_trinh.txt (sao lưu bản cũ thành .bak)

Kết quả: <đầu ra gốc>/muc_luc/muc_luc.txt (danh sách để chép) và muc_luc.md (bản dễ đọc, có số trang).
Dòng chương trong muc_luc.txt có dạng "## CHƯƠNG ..." nên sau khi chép vào giao_trinh.txt,
các bài sẽ được nhóm theo chương trong Obsidian.
"""
import argparse
import asyncio
import re
import shutil
from datetime import datetime
from pathlib import Path

from notebooklm import NotebookLMClient

import common

TIMEOUT = 300
MAX_RETRY = 3
MASTER_OUT = "giao_trinh.txt"

PROMPT = """Hãy đọc mục lục của sách trong nguồn và liệt kê đầy đủ, theo đúng thứ tự: tên từng Chương/Phần, bên dưới là các Bài của chương đó (kể cả "Liên hệ thực tế", bài đọc thêm và phụ lục nếu mục lục có). Chép đúng nguyên văn tên như sách trình bày.

Định dạng bắt buộc: đặt TOÀN BỘ danh sách trong MỘT khối code, mỗi mục một dòng, không thêm giải thích ngoài khối code:
# CHƯƠNG 1: <tên chương>
Bài 1. <tên bài> [tr. <số trang đầu>]
Liên hệ thực tế 1: <tên> [tr. <số trang>]
# CHƯƠNG 2: <tên chương>
Bài 2. <tên bài> [tr. <số trang đầu>]
...
Dòng chương/phần bắt đầu bằng "# ". Dòng bài không có ký hiệu đầu dòng. Nếu mục lục không ghi số trang thì bỏ phần [tr. ...].
Dòng cuối cùng của khối code: "# KIỂM TRA NGUỒN: <khoảng trang nội dung (không tính trang mục lục) mà bạn thấy trong nguồn, hoặc nói rõ nếu chỉ thấy một phần>".
Nếu nguồn không có trang mục lục, hãy suy ra từ các tiêu đề chương/bài trong nội dung và ghi "# (mục lục suy ra từ nội dung)" ở dòng đầu tiên của khối code."""

PAGE_RE = re.compile(r"\s*\[tr\.?\s*([^\]]*)\]\s*$", re.IGNORECASE)


def extract_block(text):
    m = re.search(r"```[A-Za-z]*\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else text


def parse_toc(answer):
    """Trả về (danh sách chương, dòng kiểm tra nguồn, ghi chú).
    Mỗi chương: {'title': str, 'lessons': [{'title', 'page'}]}"""
    text = common.strip_citations(extract_block(answer))
    chapters, check, note = [], "", ""
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        if line.startswith("#"):
            content = line.lstrip("#").strip()
            low = content.lower()
            if low.startswith("kiểm tra nguồn") or low.startswith("kiem tra nguon"):
                check = content.split(":", 1)[1].strip() if ":" in content else content
            elif content.startswith("("):
                note = content
            elif content:
                current = {"title": content, "lessons": []}
                chapters.append(current)
            continue
        line = re.sub(r"^[-*•]\s+", "", line)
        page = ""
        m = PAGE_RE.search(line)
        if m:
            page = m.group(1).strip()
            line = line[:m.start()].strip()
        if not line:
            continue
        if current is None:
            current = {"title": "", "lessons": []}
            chapters.append(current)
        current["lessons"].append({"title": line, "page": page})
    return chapters, check, note


def build_txt(chapters):
    lines = [
        f"# Mục lục đọc tự động từ NotebookLM ngày {datetime.now():%d/%m/%Y %H:%M}",
        "# Dòng '## ...' là tên chương/phần (nhóm bài trong Obsidian). Mỗi dòng còn lại là một bài.",
        "# Có thể thêm sau tên bài: | lưu ý riêng | tn=15 | style=whiteboard ... hoặc xóa bài không cần.",
        "",
    ]
    for ch in chapters:
        if ch["title"]:
            lines += [f"## {ch['title']}"]
        lines += [lesson["title"] for lesson in ch["lessons"]]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_md(chapters, check):
    lines = ["# Mục lục sách", ""]
    for ch in chapters:
        if ch["title"]:
            lines += [f"## {ch['title']}", ""]
        for lesson in ch["lessons"]:
            page = f" (tr. {lesson['page']})" if lesson["page"] else ""
            lines.append(f"- {lesson['title']}{page}")
        lines.append("")
    if check:
        lines += ["---", f"Kiểm tra nguồn (do NotebookLM tự báo): {check}", ""]
    return "\n".join(lines)


def print_toc(chapters, check, note):
    total = sum(len(c["lessons"]) for c in chapters)
    print("\n" + "=" * 64)
    print(f" MỤC LỤC ĐỌC ĐƯỢC: {len([c for c in chapters if c['title']])} chương/phần, {total} bài")
    print("=" * 64)
    if note:
        print(f" {note}")
    for ch in chapters:
        if ch["title"]:
            print(f"\n {ch['title']}")
        for lesson in ch["lessons"]:
            page = f"   (tr. {lesson['page']})" if lesson["page"] else ""
            print(f"    - {lesson['title']}{page}")
    print("\n" + "-" * 64)
    if check:
        print(f" Kiểm tra nguồn (NotebookLM tự báo, chỉ để tham khảo): {check}")
    print("-" * 64)


def parse_args():
    ap = argparse.ArgumentParser(description="Đọc mục lục sách bằng NotebookLM")
    ap.add_argument("notebook_id", nargs="?",
                    help="ID hoặc URL notebook (bỏ trống thì đọc notebook_id.txt)")
    ap.add_argument("--out-root", help="thư mục đầu ra gốc (mặc định ket_qua)")
    ap.add_argument("--apply", action="store_true",
                    help=f"ghi mục lục vào {MASTER_OUT} (sao lưu bản cũ thành .bak)")
    return ap.parse_args()


async def main():
    args = parse_args()
    nb_id = common.read_notebook_id(args.notebook_id)
    out_dir = common.get_out_root(args.out_root) / "muc_luc"

    async with NotebookLMClient.from_storage() as client:
        print("Đang nhờ NotebookLM đọc mục lục (có thể mất vài chục giây)...")
        answer = await common.ask_with_retry(client, nb_id, PROMPT,
                                             max_retry=MAX_RETRY, timeout=TIMEOUT)
    if answer is None:
        raise SystemExit("Không lấy được câu trả lời từ NotebookLM.")

    chapters, check, note = parse_toc(answer)
    total = sum(len(c["lessons"]) for c in chapters)
    if total == 0:
        print("\nKHÔNG đọc được danh sách bài từ câu trả lời. Câu trả lời gốc:\n")
        print(answer)
        print("\nGợi ý: nguồn có thể chưa có lớp chữ (hãy OCR rồi tải lại) hoặc sách không có mục lục.")
        raise SystemExit(1)

    print_toc(chapters, check, note)

    out_dir.mkdir(parents=True, exist_ok=True)
    txt = build_txt(chapters)
    (out_dir / "muc_luc.txt").write_text(txt, encoding="utf-8")
    (out_dir / "muc_luc.md").write_text(build_md(chapters, check), encoding="utf-8")

    print("\n------- SAO CHÉP TỪ ĐÂY (dán vào giao_trinh.txt) -------")
    print(txt)
    print("------- HẾT -------")
    print(f"Đã lưu: {out_dir / 'muc_luc.txt'}  và  {out_dir / 'muc_luc.md'}")

    if args.apply:
        target = Path(MASTER_OUT)
        if target.exists() and target.read_text(encoding="utf-8-sig").strip():
            backup = target.with_suffix(".txt.bak")
            shutil.copy2(target, backup)
            print(f"Đã sao lưu bản cũ: {backup}")
        target.write_text(txt, encoding="utf-8")
        print(f"Đã ghi mục lục vào {target}. Hãy mở ra xem lại tên bài trước khi chạy các chức năng khác.")
    else:
        print(f"Muốn ghi thẳng vào {MASTER_OUT}: chạy lại với --apply (hoặc dùng mục tương ứng trong menu).")


if __name__ == "__main__":
    asyncio.run(main())
