import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["notebooklm-py"]
# ///
"""
Giảng bài hàng loạt theo nguồn [SGK]/[GV]/[SLIDE], mỗi bài một file .md.

Danh sách bài: đọc giang_bai.txt trước; nếu chưa có bài nào thì dùng giao_trinh.txt
(cùng định dạng với toolkit: 'Tên bài | lưu ý | match=...').
  - Với chế độ có giáo viên, nguồn [GV]/[SLIDE] được chọn khi TÊN KHỚP tên bài
    (so sánh không dấu, bỏ 'Bài N.'). Muốn chỉ định tay: thêm 'match=chuỗi' vào dòng của bài.
  - [SGK] luôn lấy hết.

Dùng (từ thư mục gốc repo):
    uv run output/giang_hang_loat.py ca_hai --test            # thử bài đầu, in ra màn hình
    uv run output/giang_hang_loat.py giaovien --only 1,3
    uv run output/giang_hang_loat.py sach --obsidian --book "Sinh lý"

Kết quả: <đầu ra gốc>/giang_bai_nguon/<chế độ>/NN - <tiêu đề>.md  (đầu ra gốc mặc định: ket_qua)
"""
import argparse
import asyncio
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for _p in (str(HERE), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from src.core import common  # của toolkit

from notebooklm import NotebookLMClient, SourceStatus

from ask_notebook import GROUPS, ask_sources, match_lesson_sources, resolve_notebook
from src.notebook.prompts import build_prompt

OUT_NAME = "giang_bai_nguon"
MODE_LABEL = {"sach": "chỉ sách", "giaovien": "chỉ giáo viên", "ca_hai": "sách + giáo viên"}


def parse_args():
    ap = argparse.ArgumentParser(description="Giảng bài hàng loạt theo nguồn")
    ap.add_argument("mode", choices=["sach", "giaovien", "ca_hai"])
    common.add_common_args(ap)
    ap.add_argument("--plain", action="store_true", help="không thêm yêu cầu định dạng H1/H2/H3")
    ap.add_argument("--match", help="chỉ lấy [GV]/[SLIDE] có chuỗi này trong tên (áp cho mọi bài)")
    ap.add_argument("--timeout", type=float, default=600, help="giây chờ chat (mặc định 600)")
    ap.add_argument("--new-each", action="store_true",
                    help="XOÁ lịch sử chat trước mỗi bài để các bài không nối vào nhau (không khôi phục được)")
    return ap.parse_args()


async def main():
    args = parse_args()
    nb = resolve_notebook(args.notebook_id)
    list_path, items = common.resolve_list(["giang_bai.txt"], args.file)
    print(f"Danh sách đang dùng: {list_path} ({len(items)} bài) | chế độ: {MODE_LABEL[args.mode]}")

    root = common.get_out_root(args.out_root)
    out_dir = root / OUT_NAME / args.mode
    state = common.State(out_dir / ".state.json")
    only = common.parse_only(args.only)
    if args.test and not only:
        only = {1}
    delay = common.parse_delay(args.delay)

    done, skipped, no_source, failed = [], [], [], []

    async with NotebookLMClient.from_storage(chat_timeout=args.timeout) as client:
        sources = await client.sources.list(nb, statuses={SourceStatus.READY})
        print(f"Notebook có {len(sources)} nguồn sẵn sàng.")

        for idx, item in enumerate(items, 1):
            title = item["title"]
            if only and idx not in only:
                continue
            key = f"{title}::{args.mode}"
            old = state.get_file(key)
            if old and not args.force and not args.test:
                print(f"[{idx}/{len(items)}] Bỏ qua (đã có file): {title}")
                skipped.append(title)
                continue

            explicit = item["opts"].get("match") or args.match
            chosen, found = match_lesson_sources(sources, GROUPS[args.mode], title, explicit)
            has_teacher = bool(found & {"[GV]", "[SLIDE]"})
            if args.mode == "sach" and "[SGK]" not in found:
                print(f"[{idx}/{len(items)}] {title}: KHÔNG có nguồn [SGK] -> bỏ qua")
                no_source.append(title)
                continue
            if args.mode == "giaovien" and not has_teacher:
                print(f"[{idx}/{len(items)}] {title}: không tìm thấy nguồn [GV]/[SLIDE] khớp tên bài -> bỏ qua")
                print("   (kiểm tra tên nguồn hoặc thêm 'match=...' vào dòng của bài)")
                no_source.append(title)
                continue
            if args.mode == "ca_hai" and not chosen:
                print(f"[{idx}/{len(items)}] {title}: không có nguồn nào phù hợp -> bỏ qua")
                no_source.append(title)
                continue

            print(f"[{idx}/{len(items)}] {title}")
            for s in chosen:
                print(f"    - {s.title}")
            if args.mode == "ca_hai" and (not has_teacher or "[SGK]" not in found):
                print("    CẢNH BÁO: chỉ có một loại nguồn (sách hoặc giáo viên), "
                      "mục 'Khác biệt giữa sách và giáo viên' sẽ không có ý nghĩa.")

            prompt = build_prompt(args.mode, title, None, structured=not args.plain)
            if item["note"]:
                prompt += f"\n\nLưu ý riêng cho bài này (hãy ưu tiên làm theo): {item['note']}"

            if args.new_each:
                conv = await client.chat.get_conversation_id(nb)
                if conv:
                    await client.chat.delete_conversation(nb, conv)

            result = await ask_sources(client, nb, prompt, [s.id for s in chosen])
            if result is None:
                failed.append(title)
                continue
            text = result.answer

            if args.test:
                print("\n" + "=" * 60)
                print(text)
                print("=" * 60)
                print("Kiểm tra: nguồn được chọn có đúng không, nội dung có bám nguồn không?")
                return

            path = common.save_markdown(
                out_dir, idx, title, text,
                strip_cite=args.strip_cite, frontmatter=args.frontmatter,
                tags=["giang-bai", args.mode], old_file=old,
                obs=common.make_obs(args, item, f"Bài giảng ({MODE_LABEL[args.mode]})"))
            state.set_file(key, path)
            done.append(title)
            print(f"  -> Đã lưu: {path}")
            await asyncio.sleep(random.uniform(*delay))

    print("\n==== TỔNG KẾT ====")
    print(f"Xong: {len(done)} | Bỏ qua: {len(skipped)} | Thiếu nguồn: {len(no_source)} | Lỗi: {len(failed)}")
    for label, lst in (("Thiếu nguồn", no_source), ("Lỗi (chạy lại sẽ thử lại)", failed)):
        if lst:
            print(f"{label}:")
            for t in lst:
                print("  -", t)
    print("Thư mục kết quả:", out_dir)


if __name__ == "__main__":
    asyncio.run(main())
