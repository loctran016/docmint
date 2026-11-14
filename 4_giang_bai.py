# /// script
# requires-python = ">=3.10"
# dependencies = ["notebooklm-py"]
# ///
"""
Nhờ NotebookLM giảng từng bài trong sách, mỗi bài một prompt, lưu mỗi bài thành một file .md.

Cách chạy (từ thư mục toolkit):
    uv run 4_giang_bai.py --test          # thử bài đầu tiên, in ra màn hình, không lưu
    uv run 4_giang_bai.py                 # chạy toàn bộ bai.txt
    uv run 4_giang_bai.py --only 2,5-7    # chỉ chạy bài thứ 2 và 5 đến 7 trong bai.txt
    uv run 4_giang_bai.py --force         # làm lại cả những bài đã có file

Kết quả: ket_qua/giang_bai/01 - <tiêu đề bài>.md ...
"""
import argparse
import asyncio
import random
from pathlib import Path

from notebooklm import NotebookLMClient

import common

# ================= CẤU HÌNH =================
OUT_DIR = Path("ket_qua/giang_bai")
TOM_TAT_MAC_DINH = True       # thêm phần "Tóm tắt nhanh" cuối bài
CAU_HOI_MAC_DINH = True       # thêm phần "Câu hỏi tự kiểm tra" cuối bài
TIMEOUT = 300                 # giây, tối đa chờ một câu trả lời
MAX_RETRY = 3

# Cờ viết trong bai.txt (trường thứ 2 trở đi) để ghi đè mặc định cho từng bài
FLAGS = {"tomtat", "khongtomtat", "cauhoi", "khongcauhoi"}

PROMPT = """Hãy giảng cho tôi {BAI} trong sách. Bám sát bố cục của chính bài này trong sách: dùng đúng tên và thứ tự các mục, tiểu mục như sách trình bày. Chỉ dùng nội dung nằm trong bài này, bỏ qua các câu hỏi trước, không lấy từ các bài khác.

Định dạng Markdown:
- Tiêu đề bài là H1 (#), giữ đúng tên như sách.
- Mỗi mục lớn (1, 2, 3...) là H2 (##), giữ đúng số thứ tự và tên mục.
- Mỗi mục con (1.1, 1.2...) là H3 (###), giữ đúng số thứ tự và tên.
- Nếu có cấp nhỏ hơn thì dùng H4 (####).

Nội dung:
- Giảng như một giáo viên: giải thích khái niệm, lý do, ví dụ, số liệu, bảng biểu có trong sách, rồi tóm ý.
- Không bỏ sót mục nào; mục nào dài hoặc quan trọng thì giảng sâu hơn.
{LUU_Y}- Nếu không tìm thấy bài này trong tài liệu, chỉ trả lời "Không tìm thấy bài này trong nguồn", tuyệt đối không ghép từ các bài khác và không tìm kiếm web.
{KET_BAI}"""
# ============================================


def build_prompt(item, tom_tat, cau_hoi):
    luu_y = ""
    if item["note"]:
        luu_y = f"- Lưu ý riêng cho bài này (hãy ưu tiên làm theo): {item['note']}\n"

    if tom_tat and cau_hoi:
        ket_bai = '- Kết bài bằng "Tóm tắt nhanh" (3-5 gạch đầu dòng) và "Câu hỏi tự kiểm tra".'
    elif tom_tat:
        ket_bai = '- Kết bài bằng "Tóm tắt nhanh" (3-5 gạch đầu dòng), không cần câu hỏi tự kiểm tra.'
    elif cau_hoi:
        ket_bai = '- Kết bài bằng "Câu hỏi tự kiểm tra", không cần phần tóm tắt nhanh.'
    else:
        ket_bai = "- Không cần thêm phần tóm tắt nhanh hay câu hỏi tự kiểm tra ở cuối bài."

    return (PROMPT.replace("{BAI}", item["title"])
                  .replace("{LUU_Y}", luu_y)
                  .replace("{KET_BAI}", ket_bai))


def decide(flags, args):
    tom_tat = TOM_TAT_MAC_DINH and not args.no_tomtat
    cau_hoi = CAU_HOI_MAC_DINH and not args.no_cauhoi
    if "tomtat" in flags:
        tom_tat = True
    if "khongtomtat" in flags:
        tom_tat = False
    if "cauhoi" in flags:
        cau_hoi = True
    if "khongcauhoi" in flags:
        cau_hoi = False
    return tom_tat, cau_hoi


def parse_args():
    ap = argparse.ArgumentParser(description="Giảng bài bằng NotebookLM")
    ap.add_argument("notebook_id", nargs="?",
                    help="ID hoặc URL notebook (bỏ trống thì đọc notebook_id.txt)")
    ap.add_argument("--file", default="bai.txt", help="file danh sách bài (mặc định bai.txt)")
    ap.add_argument("--test", action="store_true",
                    help="chỉ chạy một bài, in kết quả ra màn hình, không lưu file")
    ap.add_argument("--only", help="chỉ chạy các bài theo số thứ tự trong file, ví dụ 1,3-5")
    ap.add_argument("--force", action="store_true", help="làm lại cả bài đã có file")
    ap.add_argument("--strip-cite", action="store_true",
                    help="xóa số trích dẫn kiểu [1], [2, 3] khỏi file")
    ap.add_argument("--frontmatter", action="store_true",
                    help="thêm YAML frontmatter (title, tags, created) cho Obsidian")
    ap.add_argument("--no-tomtat", action="store_true", help="không thêm phần tóm tắt nhanh")
    ap.add_argument("--no-cauhoi", action="store_true", help="không thêm câu hỏi tự kiểm tra")
    ap.add_argument("--delay", default="5,10",
                    help="nghỉ ngẫu nhiên giữa các bài, đơn vị giây (mặc định 5,10)")
    return ap.parse_args()


async def main():
    args = parse_args()
    nb_id = common.read_notebook_id(args.notebook_id)
    items = common.parse_list_file(args.file, known_flags=FLAGS)
    if not items:
        raise SystemExit(f"{args.file} chưa có bài nào.")

    only = common.parse_only(args.only)
    if args.test and not only:
        only = {1}
    delay = common.parse_delay(args.delay)
    state = common.State(OUT_DIR / ".state.json")

    done, skipped, not_found, failed = [], [], [], []

    async with NotebookLMClient.from_storage() as client:
        for idx, item in enumerate(items, 1):
            title = item["title"]
            if only and idx not in only:
                continue

            old = state.get_file(title)
            if old and not args.force and not args.test:
                print(f"[{idx}/{len(items)}] Bỏ qua (đã có file): {title}")
                skipped.append(title)
                continue

            tom_tat, cau_hoi = decide(item["flags"], args)
            print(f"[{idx}/{len(items)}] {title}")
            answer = await common.ask_with_retry(
                client, nb_id, build_prompt(item, tom_tat, cau_hoi),
                max_retry=MAX_RETRY, timeout=TIMEOUT)

            if answer is None:
                failed.append(title)
                continue

            if common.looks_not_found(answer):
                print("  CẢNH BÁO: NotebookLM báo không tìm thấy bài này trong nguồn.")
                print("  -> Kiểm tra tên bài có khớp mục lục, và nguồn đã được OCR đủ trang chưa.")
                not_found.append(title)
                continue

            if args.test:
                print("\n" + "=" * 60)
                print(answer)
                print("=" * 60)
                print("Kiểm tra: dấu # có còn không, cấu trúc H1/H2/H3 có bám sách không?")
                return

            path = common.save_markdown(
                OUT_DIR, idx, title, answer,
                strip_cite=args.strip_cite, frontmatter=args.frontmatter,
                tags=["giang-bai"], old_file=old)
            state.set_file(title, path)
            done.append(title)
            print(f"  -> Đã lưu: {path}")

            await asyncio.sleep(random.uniform(*delay))

    print("\n==== TỔNG KẾT ====")
    print(f"Xong: {len(done)} | Bỏ qua: {len(skipped)} | Không tìm thấy: {len(not_found)} | Lỗi: {len(failed)}")
    for label, lst in (("Không tìm thấy trong nguồn", not_found), ("Lỗi", failed)):
        if lst:
            print(f"{label} (chạy lại sẽ tự thử lại):")
            for t in lst:
                print("  -", t)
    print("Thư mục kết quả:", OUT_DIR)


if __name__ == "__main__":
    asyncio.run(main())
