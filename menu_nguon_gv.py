# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Menu phụ: nguồn giáo viên (transcript, slide), tải nguồn lên notebook, giảng/kiểm tra theo nguồn.

    uv run menu_nguon_gv.py

Dùng lại các hàm vẽ khung/chạy lệnh của menu.py (phải nằm cùng thư mục).
Muốn gắn vào menu chính: xem mục "Gắn vào menu.py" trong README_nguon_gv.md.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import menu as m  # menu.py của toolkit (không chạy menu chính khi import)
import common

def has_key():
    """Có GEMINI_API_KEY chưa (menu.py cũ chưa có hàm này thì coi như chưa)."""
    return bool(m.has_key()) if hasattr(m, "has_key") else False


def choose(title, options):
    """options: {'1': ('nhãn', giá_trị)}. Trả về giá trị hoặc None nếu bỏ qua."""
    print(f"\n  {title}")
    for k, (label, _) in options.items():
        print(f"    [{k}] {label}")
    ch = m.ask("  Chọn: ")
    return options[ch][1] if ch in options else None


def pick_mode():
    return choose("Nguồn dùng để giảng:", {
        "1": ("Chỉ sách [SGK]", "sach"),
        "2": ("Chỉ giáo viên [GV] + [SLIDE]", "giaovien"),
        "3": ("Cả hai (sách + giáo viên)", "ca_hai"),
    })


def yes(prompt, default=False):
    a = m.ask(f"  {prompt} [{'Y/n' if default else 'y/N'}] ").lower()
    return default if not a else a.startswith("y")


def need_key():
    if not has_key():
        print(f"  {m.RD}Chưa có GEMINI_API_KEY.{m.R} Chọn [8] trong menu này để đặt key.")
        return False
    return True


# ------------------------------------------------------------------ các việc
def do_transcript():
    m.clear()
    print(f"{m.B}== Transcript từ video YouTube =={m.R}")
    print("  Thử lấy phụ đề trước; không có thì (nếu bạn đồng ý) gửi sang GitHub Actions + Whisper.")
    print("  Cần GitHub CLI (gh) đã đăng nhập nếu dùng Whisper.\n")
    url = m.ask("  Link video YouTube (Enter để hủy): ")
    if not url:
        return
    lang = m.ask("  Ngôn ngữ (vi / en) [vi]: ") or "vi"
    extra = []
    if yes("Dùng thẳng Whisper (bỏ qua phụ đề)?"):
        extra.append("--whisper")
    m.exec_uv("input/transcripts/get_medical_transcript.py", "--url", url, "--lang", lang, *extra)
    m.pause()


def do_slides():
    m.clear()
    print(f"{m.B}== Slide → Markdown (Gemini) =={m.R}")
    if not need_key():
        m.pause()
        return
    print("  Nhập đường dẫn file slide (.pptx / .ppt / .pdf); dạng C:\\... cũng được.")
    p = m.ask("  Đường dẫn (Enter để hủy): ")
    if not p:
        return
    m.exec_uv("input/slides/slides_to_md.py", p, "-o", "slides_out")
    m.pause()


def do_upload():
    m.clear()
    print(f"{m.B}== Tải nguồn .md lên notebook =={m.R}")
    if not m.need_uv() or not m.need_id():
        m.pause()
        return
    prefix = choose("Loại nguồn (quyết định tiền tố tên):", {
        "1": ("Sách giáo khoa  -> [SGK]", "SGK"),
        "2": ("Transcript giáo viên -> [GV]", "GV"),
        "3": ("Slide (*.notebooklm.md) -> [SLIDE]", "SLIDE"),
    })
    if not prefix:
        return
    hints = {"SGK": "output_md/", "GV": "transcripts/", "SLIDE": "slides_out/"}
    p = m.ask(f"  File hoặc thư mục .md (Enter = {hints[prefix]}): ") or hints[prefix]
    args = ["input/upload_sources.py", "--prefix", prefix, p]
    merge = m.ask("  Gộp tất cả thành MỘT nguồn tên (Enter = không gộp): ")
    if merge:
        args += ["--merge-as", merge]
    dry = yes("Chỉ xem kế hoạch, chưa tải lên (--dry-run)?", default=True)
    if dry:
        args.append("--dry-run")
    m.exec_uv(*args)
    m.pause()


def do_batch():
    m.clear()
    print(f"{m.B}== Giảng bài hàng loạt theo nguồn =={m.R}")
    if not m.need_uv() or not m.need_id():
        m.pause()
        return
    mode = pick_mode()
    if not mode:
        return
    print(f"  Danh sách bài: {m.pick_list('giang_bai.txt')} (sửa ở mục Giảng bài của menu chính)")
    extra = []
    if yes("Chạy thử 1 bài đầu tiên (--test)?", default=True):
        extra.append("--test")
    if m.S.get("obs"):
        extra += ["--obsidian", "--book", m.S["book"]]
    if yes("XOÁ lịch sử chat trước mỗi bài (không khôi phục được)?"):
        extra.append("--new-each")
    m.exec_uv("output/giang_hang_loat.py", mode, *extra)
    m.pause()


def do_ask():
    m.clear()
    print(f"{m.B}== Hỏi một bài =={m.R}")
    if not m.need_uv() or not m.need_id():
        m.pause()
        return
    lesson = m.ask("  Tên bài (Enter để hủy): ")
    if not lesson:
        return
    mode = pick_mode()
    if not mode:
        return
    out = m.out_root() / "hoi_nguon" / f"{common.safe_filename(lesson)} ({mode}).md"
    m.exec_uv("output/ask_notebook.py", mode, lesson, "-o", str(out))
    print(f"\n  File: {out}")
    m.pause()


def do_check_note():
    m.clear()
    print(f"{m.B}== Kiểm tra note của tôi so với nguồn =={m.R}")
    if not m.need_uv() or not m.need_id():
        m.pause()
        return
    lesson = m.ask("  Tên bài (Enter để hủy): ")
    if not lesson:
        return
    note = m.ask("  Đường dẫn file note (.txt/.md): ")
    if not note:
        return
    note = common.to_wsl_path(note)
    out = m.out_root() / "hoi_nguon" / f"{common.safe_filename(lesson)} (kiem tra note).md"
    m.exec_uv("output/ask_notebook.py", "kiemtra_note", lesson, "--note", note, "-o", str(out))
    print(f"\n  File: {out}")
    m.pause()


def do_artifacts():
    m.clear()
    print(f"{m.B}== Quiz / flashcards / mindmap / infographic theo nguồn =={m.R}")
    if not m.need_uv() or not m.need_id():
        m.pause()
        return
    kind = choose("Loại cần tạo:", {
        "1": ("Quiz", "quiz"), "2": ("Flashcards", "flashcards"),
        "3": ("Mindmap", "mindmap"), "4": ("Infographic", "infographic"),
    })
    if not kind:
        return
    lesson = m.ask("  Tên bài (Enter để hủy): ")
    if not lesson:
        return
    mode = pick_mode()
    if not mode:
        return
    m.exec_uv("output/generate_artifacts.py", kind, lesson, "--source", mode)
    m.pause()


# ------------------------------------------------------------------ menu
def main_menu():
    while True:
        m.clear()
        m.draw_menu("NGUỒN GIÁO VIÊN & GIẢNG THEO NGUỒN", [
            f"INFO:Notebook: {m.id_short()} | Gemini key: {m.yn(has_key())}",
            "MID",
            "1|Transcript từ video YouTube (phụ đề / Whisper)",
            "2|Slide (.pptx/.pdf) → Markdown (Gemini)",
            "3|Tải nguồn .md lên notebook ([SGK]/[GV]/[SLIDE])",
            "SEP",
            "4|Giảng bài hàng loạt theo nguồn",
            "5|Hỏi một bài (sách / giáo viên / cả hai)",
            "6|Kiểm tra note của tôi so với nguồn",
            "7|Quiz / flashcards / mindmap / infographic",
            "SEP",
            "8|Đặt GEMINI_API_KEY",
            "9|Mở thư mục kết quả",
            "SEP",
            "0|Quay lại"])
        ch = m.ask("  Nhập lựa chọn của bạn [0-9] : ").lower()
        if ch == "1":
            do_transcript()
        elif ch == "2":
            do_slides()
        elif ch == "3":
            do_upload()
        elif ch == "4":
            do_batch()
        elif ch == "5":
            do_ask()
        elif ch == "6":
            do_check_note()
        elif ch == "7":
            do_artifacts()
        elif ch == "8":
            if hasattr(m, "md_set_key"):
                m.md_set_key()
            else:
                print("  menu.py của bạn chưa có mục đặt key; tạo file .env với dòng GEMINI_API_KEY=...")
                m.pause()
        elif ch == "9":
            m.open_folder(m.out_root())
        elif ch in ("0", "q"):
            return


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print()
