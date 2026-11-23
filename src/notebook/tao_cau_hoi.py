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
Nhờ NotebookLM soạn câu hỏi ôn tập cho từng bài trong sách.

Danh sách bài: đọc cau_hoi.txt trước (hoặc cauhoi.txt, tên cũ); nếu chưa có bài nào thì dùng giao_trinh.txt.

Hai chế độ (--mode):
    md    (mặc định) NotebookLM viết đề dạng Markdown (trắc nghiệm + tự luận + đáp án) -> file .md
    quiz  dùng tính năng Quiz của NotebookLM rồi tải về (markdown/json/html)
    both  làm cả hai

Cách chạy (từ thư mục toolkit):
    uv run 5_tao_cau_hoi.py --test            # thử bài đầu tiên, in ra màn hình
    uv run 5_tao_cau_hoi.py                   # chế độ md cho toàn bộ danh sách
    uv run 5_tao_cau_hoi.py --mode both       # md + Quiz
    uv run 5_tao_cau_hoi.py --quiz-info       # xem tham số thật của hàm tạo Quiz trong thư viện

Kết quả: <đầu ra gốc>/cau_hoi/
"""
import argparse
import asyncio
import inspect
import random

from notebooklm import NotebookLMClient
from src.core.prompts import render_prompt

from src.core import common

# ================= CẤU HÌNH =================
FEATURE_FILES = [common.CAU_HOI_FILE.name, "cauhoi.txt"]
OUT_NAME = "cau_hoi"
SO_TRAC_NGHIEM = 10           # mặc định, có thể ghi đè từng bài bằng tn=...
SO_TU_LUAN = 2                # mặc định, ghi đè bằng tl=... (0 = không có tự luận)
DO_KHO = "vừa"                # mặc định, ghi đè bằng kho=de|vua|kho
TIMEOUT = 300
QUIZ_TIMEOUT = 600
MAX_RETRY = 3

KHO_MAP = {"de": "dễ", "dễ": "dễ", "vua": "vừa", "vừa": "vừa", "kho": "khó", "khó": "khó"}

PROMPT = "tao_cau_hoi"
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
    return render_prompt(
        PROMPT, bai=item["title"], tn=tn, tl_dong=tl_dong, kho=kho,
        luu_y=luu_y, tl_format=tl_format, tl_goi_y=tl_goi_y,
    )


async def make_quiz(client, nb_id, idx, item, fmt, out_dir):
    """Tạo Quiz bằng tính năng của NotebookLM rồi tải về. Trả về đường dẫn hoặc None."""
    title = item["title"]
    gen = client.artifacts.generate_quiz
    params = inspect.signature(gen).parameters
    instruction = render_prompt(
        "quiz_instruction",
        lesson=title,
        note=f" Lưu ý: {item['note']}" if item["note"] else "",
    )
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
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{idx:02d} - {common.safe_filename(title)} (Quiz).{ext}"
        await client.artifacts.download_quiz(nb_id, str(path), output_format=fmt)
        return path
    except Exception as e:  # noqa: BLE001
        print(f"  Lỗi khi tạo Quiz: {type(e).__name__}: {e}")
        return None


def parse_args():
    ap = argparse.ArgumentParser(description="Tạo câu hỏi ôn tập bằng NotebookLM")
    common.add_common_args(ap)
    ap.add_argument("--mode", choices=["md", "quiz", "both"], default="md")
    ap.add_argument("--quiz-format", choices=["markdown", "json", "html"], default="markdown")
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
    list_path, items = common.resolve_list(FEATURE_FILES, args.file)
    print(f"Danh sách đang dùng: {list_path} ({len(items)} bài)")

    default_out = common.get_out_root() / OUT_NAME
    if args.out_root:
        out_dir, out_default = common.get_out_root(args.out_root) / OUT_NAME, False
    else:
        out_dir, out_default = common.resolve_dir("tao_cau_hoi_output", default_out)
    common.announce_default_dirs([("tao_cau_hoi_output", out_default)])
    only = common.parse_only(args.only)
    if args.test and not only:
        only = {1}
    delay = common.parse_delay(args.delay)
    state = common.State(out_dir / ".state.json")
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
                            out_dir, idx, f"Đề kiểm tra: {title}", answer,
                            strip_cite=args.strip_cite, frontmatter=args.frontmatter,
                            tags=["de-kiem-tra"], old_file=old,
                            obs=common.make_obs(args, item, "Đề kiểm tra"))
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
                    path = await make_quiz(client, nb_id, idx, item, args.quiz_format, out_dir)
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

    common.finish_obsidian(args, root)
    print("\n==== TỔNG KẾT ====")
    print(f"Xong: {len(done)} | Bỏ qua: {len(skipped)} | Không tìm thấy: {len(not_found)} | Lỗi: {len(failed)}")
    for label, lst in (("Không tìm thấy trong nguồn", not_found), ("Lỗi", failed)):
        if lst:
            print(f"{label} (chạy lại sẽ tự thử lại):")
            for t in lst:
                print("  -", t)
    print("Thư mục kết quả:", out_dir)


if __name__ == "__main__":
    asyncio.run(main())
