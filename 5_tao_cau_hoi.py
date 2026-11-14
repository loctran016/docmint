# /// script
# requires-python = ">=3.10"
# dependencies = ["notebooklm-py"]
# ///
"""
Nhờ NotebookLM soạn câu hỏi ôn tập cho từng bài trong sách.

Hai chế độ (--mode):
    md    (mặc định) NotebookLM viết đề dạng Markdown (trắc nghiệm + tự luận + đáp án) -> file .md
    quiz  dùng tính năng Quiz của NotebookLM rồi tải về (markdown/json/html)
    both  làm cả hai

Cách chạy (từ thư mục toolkit):
    uv run 5_tao_cau_hoi.py --test            # thử bài đầu tiên, in ra màn hình
    uv run 5_tao_cau_hoi.py                   # chế độ md cho toàn bộ cauhoi.txt
    uv run 5_tao_cau_hoi.py --mode both       # md + Quiz
    uv run 5_tao_cau_hoi.py --quiz-info       # xem tham số thật của hàm tạo Quiz trong thư viện

Kết quả: ket_qua/cau_hoi/
"""
import argparse
import asyncio
import inspect
import random
from pathlib import Path

from notebooklm import NotebookLMClient

import common

# ================= CẤU HÌNH =================
OUT_DIR = Path("ket_qua/cau_hoi")
SO_TRAC_NGHIEM = 10           # mặc định, có thể ghi đè từng bài bằng tn=...
SO_TU_LUAN = 2                # mặc định, ghi đè bằng tl=... (0 = không có tự luận)
DO_KHO = "vừa"                # mặc định, ghi đè bằng kho=de|vua|kho
TIMEOUT = 300
QUIZ_TIMEOUT = 600
MAX_RETRY = 3

OPTS = {"tn", "tl", "kho"}
KHO_MAP = {"de": "dễ", "dễ": "dễ", "vua": "vừa", "vừa": "vừa", "kho": "khó", "khó": "khó"}

PROMPT = """Hãy soạn một đề kiểm tra để tôi tự ôn tập {BAI} trong sách. Chỉ dùng nội dung nằm trong bài này, bỏ qua các câu hỏi trước, không lấy từ các bài khác.

Yêu cầu:
- {TN} câu trắc nghiệm, mỗi câu có 4 đáp án A, B, C, D và chỉ một đáp án đúng.
{TL_DONG}- Độ khó: {KHO}.
- Bao phủ đều các mục của bài, không hỏi lặp; tránh câu hỏi vụn vặt về số trang hay chi tiết không quan trọng; ưu tiên khái niệm, so sánh, số liệu quan trọng và ứng dụng.
- Chỉ dùng thông tin có trong sách, không tự bịa số liệu.
{LUU_Y}
Định dạng Markdown:
- Tiêu đề là H1 (#): "Đề kiểm tra: <tên bài đúng như sách>".
- "Phần I. Trắc nghiệm" là H2 (##); mỗi câu bắt đầu bằng **Câu n.**, mỗi đáp án một dòng.
{TL_FORMAT}- "Đáp án và giải thích" là H2 (##) đặt ở cuối đề: ghi đáp án đúng của từng câu kèm giải thích ngắn gọn (nêu rõ mục nào của sách){TL_GOI_Y}.
- Nếu không tìm thấy bài này trong tài liệu, chỉ trả lời "Không tìm thấy bài này trong nguồn", tuyệt đối không ghép từ các bài khác và không tìm kiếm web."""
# ============================================


def get_int(item, key, default):
    raw = item["opts"].get(key)
    if raw is None:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        print(f"  Cảnh báo: {key}={raw} không phải số, dùng mặc định {default}")
        return default


def resolve(item):
    tn = max(1, get_int(item, "tn", SO_TRAC_NGHIEM))
    tl = get_int(item, "tl", SO_TU_LUAN)
    kho_raw = item["opts"].get("kho", DO_KHO).strip().lower()
    kho = KHO_MAP.get(kho_raw, item["opts"].get("kho", DO_KHO))
    return tn, tl, kho


def build_prompt(item):
    tn, tl, kho = resolve(item)
    luu_y = f"- Lưu ý riêng cho bài này (hãy ưu tiên làm theo): {item['note']}\n" if item["note"] else ""
    if tl > 0:
        tl_dong = f"- {tl} câu tự luận ngắn.\n"
        tl_format = '- "Phần II. Tự luận" là H2 (##).\n'
        tl_goi_y = ", và gợi ý trả lời cho các câu tự luận"
    else:
        tl_dong = tl_format = tl_goi_y = ""
    return (PROMPT.replace("{BAI}", item["title"])
                  .replace("{TN}", str(tn))
                  .replace("{TL_DONG}", tl_dong)
                  .replace("{KHO}", kho)
                  .replace("{LUU_Y}", luu_y)
                  .replace("{TL_FORMAT}", tl_format)
                  .replace("{TL_GOI_Y}", tl_goi_y))


async def make_quiz(client, nb_id, idx, item, fmt):
    """Tạo Quiz bằng tính năng của NotebookLM rồi tải về. Trả về đường dẫn hoặc None."""
    title = item["title"]
    gen = client.artifacts.generate_quiz
    params = inspect.signature(gen).parameters
    instruction = (f"Chỉ tạo câu hỏi về {title} trong sách, không lấy từ các bài khác."
                   + (f" Lưu ý: {item['note']}" if item["note"] else ""))
    kwargs = {}
    for name in ("instructions", "prompt", "custom_prompt"):
        if name in params:
            kwargs[name] = instruction
            break
    if not kwargs:
        print("  Cảnh báo: hàm tạo Quiz không nhận hướng dẫn riêng, Quiz sẽ lấy từ toàn bộ nguồn.")
    try:
        status = await gen(nb_id, **kwargs)
        await asyncio.wait_for(
            client.artifacts.wait_for_completion(nb_id, status.task_id),
            timeout=QUIZ_TIMEOUT)
        ext = {"markdown": "md", "json": "json", "html": "html"}[fmt]
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / f"{idx:02d} - {common.safe_filename(title)} (Quiz).{ext}"
        await client.artifacts.download_quiz(nb_id, str(path), output_format=fmt)
        return path
    except Exception as e:  # noqa: BLE001
        print(f"  Lỗi khi tạo Quiz: {type(e).__name__}: {e}")
        return None


def parse_args():
    ap = argparse.ArgumentParser(description="Tạo câu hỏi ôn tập bằng NotebookLM")
    ap.add_argument("notebook_id", nargs="?",
                    help="ID hoặc URL notebook (bỏ trống thì đọc notebook_id.txt)")
    ap.add_argument("--file", default="cauhoi.txt", help="file danh sách (mặc định cauhoi.txt)")
    ap.add_argument("--mode", choices=["md", "quiz", "both"], default="md")
    ap.add_argument("--quiz-format", choices=["markdown", "json", "html"], default="markdown")
    ap.add_argument("--test", action="store_true",
                    help="chỉ chạy một bài, in kết quả ra màn hình, không lưu file md")
    ap.add_argument("--only", help="chỉ chạy các bài theo số thứ tự, ví dụ 1,3-5")
    ap.add_argument("--force", action="store_true", help="làm lại cả bài đã có file")
    ap.add_argument("--strip-cite", action="store_true", help="xóa số trích dẫn [1], [2, 3]")
    ap.add_argument("--frontmatter", action="store_true", help="thêm YAML frontmatter cho Obsidian")
    ap.add_argument("--delay", default="5,10", help="nghỉ ngẫu nhiên giữa các bài (giây)")
    ap.add_argument("--quiz-info", action="store_true",
                    help="in tham số của hàm tạo/tải Quiz rồi thoát")
    return ap.parse_args()


async def main():
    args = parse_args()

    if args.quiz_info:
        async with NotebookLMClient.from_storage() as client:
            for name in ("generate_quiz", "download_quiz", "wait_for_completion"):
                fn = getattr(client.artifacts, name, None)
                print(name, inspect.signature(fn) if fn else "(không có)")
        return

    nb_id = common.read_notebook_id(args.notebook_id)
    items = common.parse_list_file(args.file, known_opts=OPTS)
    if not items:
        raise SystemExit(f"{args.file} chưa có bài nào.")

    only = common.parse_only(args.only)
    if args.test and not only:
        only = {1}
    delay = common.parse_delay(args.delay)
    state = common.State(OUT_DIR / ".state.json")
    do_md = args.mode in ("md", "both")
    do_quiz = args.mode in ("quiz", "both")

    done, skipped, not_found, failed = [], [], [], []

    async with NotebookLMClient.from_storage() as client:
        for idx, item in enumerate(items, 1):
            title = item["title"]
            if only and idx not in only:
                continue
            print(f"[{idx}/{len(items)}] {title}")

            if do_md:
                key = f"{title}::md"
                old = state.get_file(key)
                if old and not args.force and not args.test:
                    print("  (md) bỏ qua, đã có file")
                    skipped.append(key)
                else:
                    answer = await common.ask_with_retry(
                        client, nb_id, build_prompt(item),
                        max_retry=MAX_RETRY, timeout=TIMEOUT)
                    if answer is None:
                        failed.append(key)
                    elif common.looks_not_found(answer):
                        print("  CẢNH BÁO: NotebookLM báo không tìm thấy bài này trong nguồn.")
                        not_found.append(key)
                    elif args.test:
                        print("\n" + "=" * 60)
                        print(answer)
                        print("=" * 60)
                    else:
                        path = common.save_markdown(
                            OUT_DIR, idx, f"Đề kiểm tra: {title}", answer,
                            strip_cite=args.strip_cite, frontmatter=args.frontmatter,
                            tags=["de-kiem-tra"], old_file=old)
                        state.set_file(key, path)
                        done.append(key)
                        print(f"  -> Đã lưu: {path}")

            if do_quiz:
                key = f"{title}::quiz"
                old = state.get_file(key)
                if old and not args.force and not args.test:
                    print("  (quiz) bỏ qua, đã có file")
                    skipped.append(key)
                else:
                    path = await make_quiz(client, nb_id, idx, item, args.quiz_format)
                    if path is None:
                        failed.append(key)
                    else:
                        state.set_file(key, path)
                        done.append(key)
                        print(f"  -> Đã lưu Quiz: {path}")

            if args.test:
                print("Kiểm tra: đề có bám bài không, đáp án có đúng không?")
                return
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
