# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Menu phụ [17]: lớp biên tập văn phong (bien_tap.py).

    uv run menu_bien_tap.py

Dùng lại các hàm vẽ khung/chạy lệnh của menu.py (phải nằm cùng thư mục).
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import menu as m  # menu.py của toolkit (không chạy menu chính khi import)

STYLE = HERE / "bien_tap_style.md"


def yes(prompt, default=False):
    a = m.ask(f"  {prompt} [{'Y/n' if default else 'y/N'}] ").lower()
    return default if not a else a.startswith("y")


def dirs():
    root = m.out_root()
    return root / "giang_bai", root / "raw", root / "polished"


def count_md(d):
    return sum(1 for p in Path(d).glob("*.md") if not p.name.startswith("_")) if Path(d).is_dir() else 0


def run_bt(*extra):
    if not m.need_uv():
        return
    if S()["bt_backend"] == "api" and not m.has_key():
        print(f"  {m.RD}Chưa có GEMINI_API_KEYS.{m.R} Đặt ở menu chính [15] rồi mục [7], hoặc chọn backend web ở mục [6] bên dưới.")
        return
    flags = ["--backend", S()["bt_backend"], "--thinking", S()["bt_thinking"]]
    if S()["bt_model"]:
        flags += ["--model", S()["bt_model"]]
    if not S()["bt_summary"]:
        flags.append("--no-summary")
    pre = ["--with", "gemini-webapi"] if S()["bt_backend"] == "web" else []
    m.exec_uv(*pre, "bien_tap.py", *flags, *extra)


def S():
    return m.S


def main_menu():
    while True:
        m.clear()
        raw_in, raw, pol = dirs()
        m.draw_menu("BIÊN TẬP VĂN PHONG", [
            f"INFO:Thô (NotebookLM): {count_md(raw_in)} | raw/: {count_md(raw)} | polished/: {count_md(pol)}",
            f"INFO:Backend: {S()['bt_backend']} | Mức suy luận: {S()['bt_thinking']} | Model: {m.short(S()['bt_model'] or 'mặc định', 18)}",
            f"INFO:Tóm ý cuối mục: {m.onoff(S()['bt_summary'])} | Groq dự phòng: {m.yn(m.has_groq_key())}",
            "MID",
            "1|Chạy thử (2 phần đầu của file đầu tiên, không lưu)",
            "2|Biên tập toàn bộ thư mục giang_bai",
            "3|Chọn file theo tên",
            "4|Làm lại, bỏ cache (--force)",
            "SEP",
            "5|Sửa khung văn phong (bien_tap_style.md)",
            "6|Đổi backend: api / web",
            "7|Đặt model",
            "8|Đổi mức suy luận",
            f"9|Dòng Tóm ý cuối mục: {m.onoff(S()['bt_summary'])}",
            "10|Xem báo cáo gần nhất",
            "11|Mở thư mục polished",
            "SEP",
            "0|Quay lại menu chính"])
        ch = m.ask("  Nhập lựa chọn của bạn : ").lower()
        if ch == "1":
            run_bt("--test")
            m.pause()
        elif ch == "2":
            run_bt()
            m.pause()
        elif ch == "3":
            name = m.ask("  Một phần tên file (ví dụ NÔN): ")
            if name:
                run_bt("--match", name)
                m.pause()
        elif ch == "4":
            if yes("Bỏ cache và biên tập lại TẤT CẢ?"):
                run_bt("--force")
                m.pause()
        elif ch == "5":
            m.edit_file(STYLE)
        elif ch == "6":
            m.cycle("bt_backend")
            if S()["bt_backend"] == "web":
                print("  Backend web dùng gemini-webapi (không chính thức) với cookie của tài khoản Google.")
                print("  Đặt GEMINI_SECURE_1PSID và GEMINI_SECURE_1PSIDTS trong .env. Xem README mục 15.")
                m.pause()
        elif ch == "7":
            v = re.sub(r"\s+", "", m.ask("  Model (nhiều model cách nhau dấu phẩy; Enter = mặc định): "))
            if re.fullmatch(r"[A-Za-z0-9._,-]*", v):
                S()["bt_model"] = v
                m.save_settings()
        elif ch == "8":
            m.cycle("bt_thinking")
        elif ch == "9":
            m.toggle("bt_summary")
        elif ch == "10":
            m.view_text(dirs()[2] / "_bao_cao.md")
        elif ch == "11":
            m.open_folder(dirs()[2])
        elif ch in ("0", "q"):
            return


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print()
