# /// script
# requires-python = ">=3.10"
# dependencies = ["notebooklm-py"]
# ///
import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
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

from src.core import common
from src.core.prompts import render_prompt

TIMEOUT = 300
MAX_RETRY = 3
MASTER_OUT = common.GIAO_TRINH_FILE

PROMPT = render_prompt("muc_luc")

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


def apply_toc(txt, target=None):
    """Ghi mục lục vào file cấu hình trong config/."""
    target = target or (common.CONFIG_DIR / common.GIAO_TRINH_FILE.name)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_text(encoding="utf-8-sig").strip():
        backup = target.with_suffix(".txt.bak")
        shutil.copy2(target, backup)
        print(f"Đã sao lưu bản cũ: {backup}")
    target.write_text(txt, encoding="utf-8")
    print(f"Đã ghi mục lục vào {target}. Hãy mở ra xem lại tên bài trước khi chạy các chức năng khác.")
    return target


async def main():
    args = parse_args()
    nb_id = common.read_notebook_id(args.notebook_id)
    default_out = common.get_out_root() / "muc_luc"
    if args.out_root:
        out_dir, out_default = common.get_out_root(args.out_root) / "muc_luc", False
    else:
        out_dir, out_default = common.resolve_dir("muc_luc_output", default_out)
    common.announce_default_dirs([("muc_luc_output", out_default)])

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
        apply_toc(txt)
    else:
        print(f"Muốn ghi thẳng vào {MASTER_OUT}: chạy lại với --apply (hoặc dùng mục tương ứng trong menu).")


if __name__ == "__main__":
    asyncio.run(main())
