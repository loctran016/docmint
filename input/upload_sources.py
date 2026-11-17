#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["notebooklm-py"]
# ///
"""
Tải các file .md lên notebook NotebookLM, đặt tên nguồn theo quy ước để bước giảng bài
chọn nguồn được theo tiền tố:

    [SGK]    sách giáo khoa Markdown            ví dụ: [SGK] Sinh lý học - Tiêu hoá
    [GV]     transcript bài giảng của giáo viên ví dụ: [GV] Sinh lý gan
    [SLIDE]  slide bản *.notebooklm.md          ví dụ: [SLIDE] Sinh lý gan

Dùng (từ thư mục gốc repo):
    uv run input/upload_sources.py --prefix SGK output_md/
    uv run input/upload_sources.py --prefix GV transcripts/
    uv run input/upload_sources.py --prefix SLIDE slides_out/
    uv run input/upload_sources.py --prefix SLIDE --merge-as "Sinh lý gan" slides_out/Gan1 slides_out/Gan2
    uv run input/upload_sources.py --prefix GV transcripts/ --dry-run     # chỉ xem kế hoạch

Notebook: tham số -n, biến NOTEBOOKLM_NOTEBOOK, hoặc file notebook_id.txt của toolkit.
Nguồn đã có (trùng tên) được bỏ qua nên chạy lại an toàn.
"""
import argparse
import asyncio
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import common  # của toolkit (đọc ID notebook, đổi đường dẫn Windows)

from notebooklm import NotebookLMClient

PREFIXES = {"SGK": "[SGK]", "GV": "[GV]", "SLIDE": "[SLIDE]"}
NLM_SUFFIX = ".notebooklm.md"


def resolve_notebook(cli_value=None):
    value = cli_value or os.environ.get("NOTEBOOKLM_NOTEBOOK")
    return common.read_notebook_id(value)


def source_name(path):
    """Tên hiển thị (không gồm tiền tố): bỏ đuôi .md và .notebooklm."""
    name = path.name
    if name.lower().endswith(NLM_SUFFIX):
        name = name[: -len(NLM_SUFFIX)]
    elif name.lower().endswith(".md"):
        name = name[:-3]
    return name.strip()


def wanted(path, tag, explicit):
    """File .md này có đúng loại cho tiền tố không (khi quét thư mục)."""
    if explicit:
        return True
    is_nlm = path.name.lower().endswith(NLM_SUFFIX)
    if tag == "[SLIDE]":
        return is_nlm            # chỉ bản thuần chữ; bản .md có ảnh chỉ để đọc trong Obsidian
    return not is_nlm


def collect(inputs, tag):
    files = []
    for raw in inputs:
        p = Path(common.to_wsl_path(raw))
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*.md")):
                rel = f.relative_to(p)
                if any(part.startswith(".") for part in rel.parts):   # .cache, .pages...
                    continue
                if wanted(f, tag, explicit=False):
                    files.append(f)
        else:
            print(f"Không thấy: {raw}")
    seen, unique = set(), []
    for f in files:
        key = f.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def parse_args():
    ap = argparse.ArgumentParser(description="Tải nguồn .md lên NotebookLM với tên có tiền tố")
    ap.add_argument("inputs", nargs="+", help="file .md hoặc thư mục chứa .md")
    ap.add_argument("--prefix", required=True, choices=list(PREFIXES), help="loại nguồn")
    ap.add_argument("-n", "--notebook", help="ID hoặc URL notebook")
    ap.add_argument("--merge-as", metavar="TÊN",
                    help="gộp tất cả file đầu vào thành MỘT nguồn tên '[PREFIX] TÊN' (vd gộp nhiều slide cùng bài)")
    ap.add_argument("--dry-run", action="store_true", help="chỉ in kế hoạch, không tải lên")
    ap.add_argument("--no-wait", action="store_true", help="không chờ nguồn xử lý xong")
    ap.add_argument("--wait-timeout", type=float, default=300, help="giây chờ mỗi nguồn xử lý (mặc định 300)")
    return ap.parse_args()


async def main():
    args = parse_args()
    tag = PREFIXES[args.prefix]
    notebook = resolve_notebook(args.notebook)

    files = collect(args.inputs, tag)
    if not files:
        sys.exit("Không có file .md phù hợp để tải lên "
                 f"(với [SLIDE] chỉ lấy file *{NLM_SUFFIX} khi quét thư mục).")

    # Danh sách việc cần làm: (đường dẫn thật, tên nguồn)
    jobs = []
    tmpdir = None
    if args.merge_as:
        tmpdir = tempfile.TemporaryDirectory()
        merged = Path(tmpdir.name) / f"{common.safe_filename(args.merge_as)}.md"
        parts = [f.read_text(encoding="utf-8").strip() for f in files]
        merged.write_text("\n\n---\n\n".join(parts) + "\n", encoding="utf-8")
        jobs.append((merged, f"{tag} {args.merge_as}"))
        print(f"Gộp {len(files)} file thành một nguồn: {tag} {args.merge_as}")
    else:
        for f in files:
            jobs.append((f, f"{tag} {source_name(f)}"))

    try:
        async with NotebookLMClient.from_storage() as client:
            existing = await client.sources.list(notebook)
            have = {(s.title or "").strip().lower() for s in existing}
            todo = [(p, t) for p, t in jobs if t.strip().lower() not in have]
            for p, t in jobs:
                if (p, t) not in todo:
                    print(f"  bỏ qua (đã có): {t}")

            # Hạn mức nguồn mỗi notebook: đọc từ tài khoản, không ghi cứng con số
            limit = None
            try:
                limits = await client.settings.get_account_limits()
                limit = limits.source_limit
            except Exception as e:  # noqa: BLE001
                print(f"  (không đọc được hạn mức nguồn: {type(e).__name__})")
            if limit:
                room = limit - len(existing)
                print(f"Notebook đang có {len(existing)}/{limit} nguồn, còn chỗ cho {max(room, 0)}.")
                if room < len(todo):
                    print(f"CẢNH BÁO: cần {len(todo)} chỗ nhưng chỉ còn {max(room, 0)}. "
                          "Chỉ tải phần vừa đủ; hãy gộp bớt (--merge-as) hoặc dùng notebook khác.")
                    todo = todo[: max(room, 0)]

            print(f"\nKế hoạch: tải {len(todo)} nguồn.")
            for p, t in todo:
                print(f"  + {t}   <- {p.name}")
            if args.dry_run or not todo:
                print("(dry-run hoặc không có gì để tải)" if args.dry_run else "Không có nguồn mới.")
                return

            uploaded, failed = [], []
            for p, t in todo:
                try:
                    src = await client.sources.add_file(notebook, str(p), title=t)
                    uploaded.append(src)
                    print(f"  đã tải: {t}")
                except Exception as e:  # noqa: BLE001
                    failed.append(t)
                    state = getattr(e, "commit_state", None)
                    sid = getattr(e, "source_id", None)
                    print(f"  LỖI khi tải '{t}': {type(e).__name__}: {e}")
                    if state is not None:
                        print(f"    trạng thái ghi: {state}")
                    if sid:
                        print(f"    có thể đã tạo dòng nguồn id={sid}; kiểm tra trước khi tải lại.")

            if uploaded and not args.no_wait:
                print("\nChờ NotebookLM xử lý các nguồn...")
                try:
                    await client.sources.wait_for_sources(
                        notebook, [s.id for s in uploaded], timeout=args.wait_timeout)
                    print("Tất cả nguồn đã sẵn sàng.")
                except Exception as e:  # noqa: BLE001
                    print(f"Chưa xác nhận được trạng thái sẵn sàng: {type(e).__name__}: {e}")
                    print("Kiểm tra lại trong NotebookLM, hoặc chạy lại lệnh này.")

            print(f"\nXong: {len(uploaded)} nguồn mới, {len(failed)} lỗi.")
            if failed:
                sys.exit(1)
    finally:
        if tmpdir is not None:
            tmpdir.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
