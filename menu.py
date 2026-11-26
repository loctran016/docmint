# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Menu tổng hợp cho bộ công cụ NotebookLM. Chạy được trên WSL/Linux, Windows và macOS.

    uv run menu.py          (hoặc: bash menu.sh  /  nhấp đúp menu.cmd trên Windows)

Mọi input/output nằm trong thư mục toolkit (hoặc thư mục đầu ra bạn đặt, ví dụ vault Obsidian).
Mục [5] gọi process_book.py (PDF scan -> Markdown bằng Gemini). Mục [13] là lớp biên tập văn phong (bien_tap.py).
"""
import getpass
import logging
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

os.environ.setdefault("PYTHONUNBUFFERED", "1")

from src.core import common

HERE = common.TOOLKIT_DIR
os.chdir(HERE)

IS_WIN, IS_MAC, IS_WSL = common.IS_WIN, common.IS_MAC, common.IS_WSL
if IS_WIN:
    os.system("")   # bật mã màu ANSI trong cửa sổ dòng lệnh Windows

# ------------------------------------------------------------------ cài đặt nhớ lại
SETTINGS_FILE = common.TOOLKIT_DIR / ".menu_settings.json"
DEFAULTS = {"strip": 0, "fm": 0, "obs": 0, "quiz_mode": "md", "quiz_fmt": "markdown",
            "mm_kind": "interactive", "book": "Sách giáo khoa", "out_root": str(common.KET_QUA_DIR),
            "md_split": 0, "md_model": "", "md_out": "", "md_paid": 0,
            "bt_backend": "api", "bt_model": "", "bt_thinking": "medium", "bt_summary": 1}
CHOICES = {"quiz_mode": ("md", "quiz", "both"), "quiz_fmt": ("markdown", "json", "html"),
           "mm_kind": ("interactive", "note-backed"), "bt_backend": ("api", "web"),
           "bt_thinking": ("minimal", "low", "medium", "high")}


def load_settings():
    s = dict(DEFAULTS)
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        s.update({k: v for k, v in data.items() if k in DEFAULTS})
    except Exception:  # noqa: BLE001
        pass
    for k in ("strip", "fm", "obs", "md_split", "md_paid", "bt_summary"):
        s[k] = 1 if s[k] in (1, True, "1") else 0
    for k, allowed in CHOICES.items():
        if s[k] not in allowed:
            s[k] = DEFAULTS[k]
    if not str(s["book"]).strip():
        s["book"] = DEFAULTS["book"]
    if not str(s["out_root"]).strip():
        s["out_root"] = DEFAULTS["out_root"]
    if not re.fullmatch(r"[A-Za-z0-9._,-]*", str(s["md_model"])):
        s["md_model"] = ""
    if not re.fullmatch(r"[A-Za-z0-9._,-]*", str(s["bt_model"])):
        s["bt_model"] = ""
    s["md_out"] = str(s["md_out"] or "")
    return s


S = load_settings()


def save_settings():
    SETTINGS_FILE.write_text(json.dumps(S, ensure_ascii=False, indent=2), encoding="utf-8")


def cycle(key):
    allowed = CHOICES[key]
    S[key] = allowed[(allowed.index(S[key]) + 1) % len(allowed)]
    save_settings()


def toggle(key):
    S[key] = 1 - S[key]
    save_settings()


# ------------------------------------------------------------------ màu và khung
if sys.stdout.isatty():
    R, B, ORG, CY = "\033[0m", "\033[1m", "\033[38;5;208m", "\033[36m"
    GR, RD, YL, DM = "\033[32m", "\033[31m", "\033[33m", "\033[2m"
else:
    R = B = ORG = CY = GR = RD = YL = DM = ""

W = 62   # độ rộng phần chữ bên trong khung


def row(plain, shown=None):
    shown = plain if shown is None else shown
    pad = max(0, W - len(plain))
    print(f"{ORG}│{R} {shown}{' ' * pad} {ORG}│{R}")


def center(s):
    left = max(0, (W - len(s)) // 2)
    row(" " * left + s, " " * left + B + s + R)


def item(key, label):
    row(f"[{key}] {label}", f"{CY}[{key}]{R} {label}")


def sep():
    row(" " * 23 + "─" * 16)


def draw_menu(title, entries):
    """entries: 'phím|nhãn', 'SEP', 'MID', 'INFO:chữ', 'CTR:chữ'"""
    print(f"{ORG}┌{'─' * (W + 2)}┐{R}")
    center(title)
    for e in entries:
        if e == "SEP":
            sep()
        elif e == "MID":
            print(f"{ORG}├{'─' * (W + 2)}┤{R}")
        elif e.startswith("INFO:"):
            row(" " + e[5:])
        elif e.startswith("CTR:"):
            center(e[4:])
        else:
            key, _, label = e.partition("|")
            item(key, label)
    print(f"{ORG}└{'─' * (W + 2)}┘{R}")


def onoff(v):
    return "BẬT" if v else "TẮT"


def yn(v):
    return "có" if v else "chưa"


def short(s, n):
    s = str(s)
    return s if len(s) <= n else "…" + s[-(n - 1):]


def clear():
    os.system("cls" if IS_WIN else "clear")


def ask(prompt):
    try:
        print(prompt, end="", flush=True)
        return input().strip()
    except EOFError:
        print()
        return ""
    except KeyboardInterrupt:
        print()
        return ""


def pause():
    common.wait_for_menu()


# ------------------------------------------------------------------ tiện ích
def find_uv():
    uv = shutil.which("uv")
    if uv:
        return uv
    for cand in (Path.home() / ".local" / "bin" / ("uv.exe" if IS_WIN else "uv"),
                 Path.home() / ".cargo" / "bin" / ("uv.exe" if IS_WIN else "uv")):
        if cand.exists():
            return str(cand)
    return None


UV = find_uv()


def get_id():
    try:
        return common.read_notebook_id()
    except SystemExit:
        return ""


def id_short():
    i = get_id()
    return f"{i[:8]}…" if i else "(chưa đặt)"


def count_items(path):
    p = Path(path)
    if not p.is_absolute():
        p = next((q for q in (common.CONFIG_DIR / p.name, common.ROOT_DIR / p.name) if q.exists()),
                 common.CONFIG_DIR / p.name)
    if not p.exists():
        return 0
    try:
        return len(common.parse_list_file(p))
    except SystemExit:
        return 0


def pick_list(*files):
    for f in list(files) + common.MASTER_FILES:
        if count_items(f) > 0:
            return f
    return "(chưa có)"


def out_root():
    return Path(S["out_root"])


_ocr_cache = {"ready": None}


def ocr_ready(refresh=False):
    if refresh or _ocr_cache["ready"] is None:
        _ocr_cache["ready"] = bool(common.ocr_ready())
    return _ocr_cache["ready"]


def need_uv():
    if not UV:
        print(f"  {RD}Chưa cài uv.{R} "
              + ("Mở PowerShell chạy:  winget install astral-sh.uv  rồi mở lại menu." if IS_WIN
                 else "Chạy:  curl -LsSf https://astral.sh/uv/install.sh | sh  rồi mở lại terminal."))
        return False
    return True


def need_id():
    if not get_id():
        print(f"  {RD}Chưa có ID notebook.{R} Hãy chọn [20] ở menu chính để đặt ID trước.")
        return False
    return True


def show_cmd(cmd):
    return subprocess.list2cmdline(cmd) if IS_WIN else " ".join(
        f"'{c}'" if (" " in c or not c) else c for c in cmd)


def run(cmd, show=True):
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    env.update({
        "NLM_OUT_ROOT": str(S["out_root"]),
        "NLM_BOOK": S["book"],
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
    })
    if show:
        print(f"\n{DM}Lệnh: {show_cmd(cmd)}{R}\n")
    try:
        return subprocess.run(cmd, env=env, cwd=common.REPO_ROOT).returncode
    except KeyboardInterrupt:
        print("\n(đã dừng)")
        return 130
    except FileNotFoundError:
        print(f"  Không tìm thấy lệnh: {cmd[0]}")
        return 127


def exec_uv(*args):
    if not need_uv():
        return 1
    rc = run([UV, "run", "--project", str(common.REPO_ROOT), *args])
    if rc != 0:
        print(f"\n  {RD}Chức năng kết thúc với mã lỗi {rc}.{R}")
        pause()
    return rc


def open_folder(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    try:
        if IS_WIN:
            os.startfile(str(path.resolve()))          # noqa: S606
        elif IS_WSL:
            subprocess.run(["explorer.exe", "."], cwd=path, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        elif IS_MAC:
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
    except Exception as e:  # noqa: BLE001
        print(f"  Không mở được thư mục: {e}")


def edit_file(path):
    path = Path(path)
    if not path.exists():
        path.write_text("# Danh sách (mỗi dòng một bài)\n", encoding="utf-8")
    editor = os.environ.get("EDITOR") or ("notepad" if IS_WIN else "nano")
    try:
        subprocess.run([editor, str(path)])
    except FileNotFoundError:
        print(f"  Không thấy trình soạn thảo '{editor}'. Đặt biến EDITOR hoặc mở file này bằng "
              f"chương trình bất kỳ:\n  {path.resolve()}")
        pause()
        return
    if IS_WIN:
        ask("  Lưu file xong (đóng Notepad) rồi nhấn Enter để tiếp tục... ")


def view_text(path):
    path = Path(path)
    if not path.exists():
        print(f"  Không thấy {path}")
        pause()
        return
    if shutil.which("less"):
        subprocess.run(["less", "-R", str(path)])
    elif IS_WIN:
        subprocess.run(["notepad", str(path)])
    else:
        print(path.read_text(encoding="utf-8"))
        pause()


# ------------------------------------------------------------------ 1-4. hướng dẫn, cài đặt, OCR
def show_guide():
    view_text(common.TOOLKIT_DIR / "README.md")


def setup_nlm():
    clear()
    print(f"{B}== Cài & set-up notebooklm-py =={R}")
    exec_uv("src/ingest/setup_notebooklm.py")
    if not get_id():
        print("\n  Bước tiếp theo: chọn [20] ở menu chính để đặt ID notebook.")
    pause()


def setup_ocr():
    clear()
    print(f"{B}== Cài & set-up OCR =={R}")
    exec_uv("src/ingest/setup_ocr.py")
    ocr_ready(refresh=True)
    pause()


def do_ocr():
    clear()
    print(f"{B}== OCR PDF =={R}\n")
    if not ocr_ready(refresh=True):
        print(f"  {RD}OCR chưa sẵn sàng{R} (thiếu Tesseract tiếng Việt hoặc Ghostscript). "
              "Hãy chọn [3] ở menu chính trước.")
        pause()
        return
    print("  Nhập thư mục chứa các file PDF:")
    print("   - Enter để dùng thư mục input_pdfs/ trong toolkit")
    print("   - hoặc dán/kéo thả đường dẫn thư mục (dạng C:\\... của Windows cũng được)\n")
    d = ask("  Thư mục: ") or str(common.DEFAULT_INPUT_PDFS)
    if d == common.INPUT_PDFS_DIR.name:
        d = str(common.DEFAULT_INPUT_PDFS)
        common.DEFAULT_INPUT_PDFS.mkdir(exist_ok=True)
        if not any(p.suffix.lower() == ".pdf" for p in common.DEFAULT_INPUT_PDFS.iterdir()):
            print("\n  input_pdfs/ đang trống. Mình mở thư mục này, hãy chép các file PDF vào rồi quay lại.")
            open_folder(common.DEFAULT_INPUT_PDFS)
            ask("  Nhấn Enter khi đã chép xong... ")
    exec_uv("src/ingest/ocr_pdfs.py", d)
    if ask("\n  Mở thư mục output_ocr? [y/N] ").lower().startswith("y"):
        open_folder(common.DEFAULT_OUTPUT_OCR)
    pause()


# ------------------------------------------------------------------ 15. PDF -> Markdown bằng Gemini
ENV_FILE = common.TOOLKIT_DIR / ".env"
KEY_NAMES = ("GEMINI_API_KEYS", "GEMINI_API_KEY", "GOOGLE_API_KEY")
GITIGNORE_PATTERNS = [".env", ".menu_settings.json", "workspace/", "tessdata/", ".cache/",
                      "__pycache__/"]


def has_key():
    """Đã có GEMINI_API_KEY (biến môi trường hoặc trong file .env) chưa."""
    if any(os.environ.get(k) for k in KEY_NAMES):
        return True
    try:
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"^\s*(?:export\s+)?(?:GEMINI_API_KEYS|GEMINI_API_KEY|GOOGLE_API_KEY)\s*=\s*(\S+)", line)
            if m and m.group(1).strip("\"'"):
                return True
    except OSError:
        pass
    return False


def ensure_ignored(*patterns):
    """Thêm các mẫu vào .gitignore nếu chưa có. Trả về danh sách mẫu vừa thêm."""
    gi = common.TOOLKIT_DIR / ".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    add = [p for p in patterns if p not in existing]
    if add:
        gi.write_text("\n".join(existing + add) + "\n", encoding="utf-8")
    return add


def has_paid_key():
    """Đã có GEMINI_PAID_API_KEY (biến môi trường hoặc trong file .env) chưa."""
    if os.environ.get("GEMINI_PAID_API_KEY"):
        return True
    try:
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"^\s*(?:export\s+)?GEMINI_PAID_API_KEY\s*=\s*(\S+)", line)
            if m and m.group(1).strip("\"'"):
                return True
    except OSError:
        pass
    return False


def has_groq_key():
    """Đã có GROQ_API_KEYS (biến môi trường hoặc trong file .env) chưa."""
    if os.environ.get("GROQ_API_KEYS"):
        return True
    try:
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"^\s*(?:export\s+)?GROQ_API_KEYS\s*=\s*(\S+)", line)
            if m and m.group(1).strip("\"'"):
                return True
    except OSError:
        pass
    return False


def md_out_dir():
    return Path(S["md_out"] or str(common.OUTPUT_MD_DIR))


def run_md(*extra):
    """Chạy process_book.py với các công tắc đã chọn trong menu."""
    if not need_uv():
        return 1
    if "--merge-only" not in extra and not has_key():
        print(f"  {RD}Chưa có GEMINI_API_KEY.{R} Hãy chọn [7] trong menu này để đặt key.")
        return 1
    flags = []
    if S["md_split"]:
        flags.append("--split")
    if S["md_paid"]:
        flags.append("--allow-paid")
    if S["md_model"]:
        flags += ["--model", S["md_model"]]
    if S["md_out"]:
        flags += ["--out", S["md_out"]]
    return exec_uv("src/ingest/process_book.py", *flags, *(x for x in extra if x))


def md_ask_input():
    print("  Nhập thư mục (hoặc 1 file) PDF cần chuyển sang Markdown:")
    print("   - Enter để dùng thư mục input_pdfs/ trong toolkit")
    print("   - hoặc dán/kéo thả đường dẫn (dạng C:\\... của Windows cũng được)")
    print("   - có thể trỏ vào output_ocr/ nếu muốn dùng bản đã OCR\n")
    p = ask("  Đường dẫn: ")
    if p == common.INPUT_PDFS_DIR.name:
        d = common.DEFAULT_INPUT_PDFS
        d.mkdir(exist_ok=True)
        if not any(x.suffix.lower() == ".pdf" for x in d.iterdir()):
            print("\n  input_pdfs/ đang trống. Mình mở thư mục này, hãy chép các file PDF vào rồi quay lại.")
            open_folder(d)
            ask("  Nhấn Enter khi đã chép xong... ")
    return p


def md_set_key():
    print("  Tạo key miễn phí tại: https://aistudio.google.com/apikey")
    print("  (khi dán key sẽ không hiện ký tự trên màn hình)")
    try:
        print("  (nhiều key từ nhiều Project: dán cách nhau dấu phẩy, ví dụ key1,key2,key3)")
        key = getpass.getpass("  Dán GEMINI_API_KEY (Enter để hủy): ")
    except (EOFError, KeyboardInterrupt):
        print()
        return
    key = re.sub(r"\s+", "", key)
    if not key:
        return
    lines = []
    if ENV_FILE.exists():
        lines = [ln for ln in ENV_FILE.read_text(encoding="utf-8-sig").splitlines()
                 if not re.match(r"^\s*(?:export\s+)?GEMINI_API_KEYS?\s*=", ln)]
    lines.append(f"{'GEMINI_API_KEYS' if ',' in key else 'GEMINI_API_KEY'}={key}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass
    added = ensure_ignored(".env")
    print("  Đã lưu key vào .env" + (" và thêm .env vào .gitignore." if added else " (.env đã có trong .gitignore)."))
    ask("  Nhấn Enter để tiếp tục... ")


def md_set_paid_key():
    print("  Key TRẢ PHÍ (Project có bật billing) chỉ được dùng khi mọi key miễn phí đã hết quota ngày,")
    print("  và chỉ khi mục [13] đang BẬT. Mỗi lần chạy có trần số trang (--paid-max-pages, mặc định 300).")
    try:
        key = getpass.getpass("  Dán GEMINI_PAID_API_KEY (Enter để hủy): ")
    except (EOFError, KeyboardInterrupt):
        print()
        return
    key = re.sub(r"\s+", "", key)
    if not key:
        return
    lines = []
    if ENV_FILE.exists():
        lines = [ln for ln in ENV_FILE.read_text(encoding="utf-8-sig").splitlines()
                 if not re.match(r"^\s*(?:export\s+)?GEMINI_PAID_API_KEY\s*=", ln)]
    lines.append(f"GEMINI_PAID_API_KEY={key}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass
    ensure_ignored(".env")
    print("  Đã lưu GEMINI_PAID_API_KEY vào .env.")
    ask("  Nhấn Enter để tiếp tục... ")


def md_set_groq_key():
    print("  Groq Vision là dự phòng khi Gemini từ chối chép một trang vì RECITATION (Groq không có bộ lọc này).")
    print("  Tạo key miễn phí tại: https://console.groq.com/keys")
    print("  Nhiều key: dán cách nhau dấu phẩy, ví dụ key1,key2")
    try:
        key = getpass.getpass("  Dán GROQ_API_KEYS (Enter để hủy): ")
    except (EOFError, KeyboardInterrupt):
        print()
        return
    key = re.sub(r"\s+", "", key)
    if not key:
        return
    lines = []
    if ENV_FILE.exists():
        lines = [ln for ln in ENV_FILE.read_text(encoding="utf-8-sig").splitlines()
                 if not re.match(r"^\s*(?:export\s+)?GROQ_API_KEYS\s*=", ln)]
    lines.append(f"GROQ_API_KEYS={key}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass
    ensure_ignored(".env")
    print("  Đã lưu GROQ_API_KEYS vào .env.")
    ask("  Nhấn Enter để tiếp tục... ")


def md_set_model():
    print("  Tên model Gemini. Có thể ghi nhiều model cách nhau dấu phẩy, ví dụ:")
    print("      gemini-3.8-flash,gemini-3.6-flash")
    print("  Model đầu hết quota ngày thì tự chuyển sang model sau; model không tồn tại thì bị bỏ qua.")
    print("  Enter (để trống) = dùng mặc định của script. Xem tên model hiện có bằng mục [9].\n")
    m = re.sub(r"\s+", "", ask("  Model: "))
    if re.fullmatch(r"[A-Za-z0-9._,-]*", m):
        S["md_model"] = m
        save_settings()
    else:
        print("  Tên model không hợp lệ (chỉ gồm chữ, số, . _ - và dấu phẩy).")
        ask("  Nhấn Enter để tiếp tục... ")


def md_set_out():
    print("  Thư mục lưu Markdown (có thể là thư mục trong vault Obsidian; C:\\... cũng được).")
    print("  Enter để quay về mặc định (output_md trong toolkit).")
    p = ask("  Thư mục: ")
    S["md_out"] = common.to_wsl_path(p) if p else ""
    if S["md_out"]:
        Path(S["md_out"]).mkdir(parents=True, exist_ok=True)
    save_settings()


def md_gitignore():
    added = ensure_ignored(*GITIGNORE_PATTERNS)
    if added:
        print("  Đã thêm vào .gitignore: " + ", ".join(added))
    else:
        print("  .gitignore đã có đủ các mẫu cần thiết.")
    print("  Lưu ý: .gitignore chỉ có tác dụng với file CHƯA được git theo dõi. Nếu đã `git add` trước đó,")
    print("  chạy thêm:  git rm -r --cached input_pdfs output_ocr output_md ket_qua")
    pause()


def md_menu():
    while True:
        clear()
        draw_menu("PDF → MARKDOWN (GEMINI)", [
            f"INFO:Model: {short(S['md_model'] or 'mặc định', 30)} | Key: {yn(has_key())}",
            f"INFO:Đầu ra: {short(S['md_out'] or common.OUTPUT_MD_DIR.name, 40)}",
            f"INFO:Key trả phí: {yn(has_paid_key())} | cho phép dùng: {onoff(S['md_paid'])} | Groq: {yn(has_groq_key())}",
            "MID",
            "1|Chạy thử vài trang (--test, không lưu gì)",
            "2|Chuyển toàn bộ PDF thành Markdown",
            "3|Chọn sách / khoảng trang cụ thể",
            "4|Làm lại từ đầu, bỏ tiến độ cũ (--force)",
            "5|Chỉ gộp lại từ các trang đã có (không gọi API)",
            "SEP",
            f"6|Chia file theo chương (H1): {onoff(S['md_split'])}",
            "7|Đặt GEMINI_API_KEY",
            "8|Đặt model",
            "9|Liệt kê model dùng được với key của tôi",
            "10|Mở thư mục đầu ra trong Explorer",
            "11|Đặt thư mục đầu ra Markdown",
            "12|Thêm .env và thư mục dữ liệu vào .gitignore",
            f"13|Cho phép key trả phí khi hết quota: {onoff(S['md_paid'])}",
            "14|Đặt GEMINI_PAID_API_KEY",
            "15|Đặt GROQ_API_KEYS (dự phòng RECITATION)",
            "SEP",
            "0|Quay lại menu chính"])
        ch = ask("  Nhập lựa chọn của bạn : ").lower()
        if ch == "1":
            clear()
            p = md_ask_input()
            tp = ask("  Trang để thử (Enter = 3 trang đầu, ví dụ 12 hoặc 10-12): ")
            run_md(p, "--test", *(["--pages", tp] if tp else []))
            pause()
        elif ch == "2":
            clear()
            p = md_ask_input()
            run_md(p)
            pause()
        elif ch == "3":
            clear()
            p = md_ask_input()
            bk = ask("  Tên sách (một phần tên file, Enter = tất cả): ")
            pg = ask("  Khoảng trang (ví dụ 1-20,25; Enter = tất cả): ")
            extra = []
            if bk:
                extra += ["--book", bk]
            if pg:
                extra += ["--pages", pg]
            run_md(p, *extra)
            pause()
        elif ch == "4":
            clear()
            p = md_ask_input()
            if ask("  Xóa tiến độ cũ và làm lại TẤT CẢ trang? [y/N] ").lower().startswith("y"):
                run_md(p, "--force")
                pause()
        elif ch == "5":
            clear()
            p = md_ask_input()
            run_md(p, "--merge-only")
            pause()
        elif ch == "6":
            toggle("md_split")
        elif ch == "7":
            md_set_key()
        elif ch == "8":
            md_set_model()
        elif ch == "9":
            clear()
            if need_uv():
                if has_key():
                    exec_uv("src/ingest/process_book.py", "--list-models")
                else:
                    print(f"  {RD}Chưa có GEMINI_API_KEY.{R} Hãy chọn [7] để đặt key trước.")
            pause()
        elif ch == "10":
            open_folder(md_out_dir())
        elif ch == "11":
            md_set_out()
        elif ch == "12":
            md_gitignore()
        elif ch == "13":
            toggle("md_paid")
        elif ch == "14":
            md_set_paid_key()
        elif ch == "15":
            md_set_groq_key()
        elif ch in ("0", "q"):
            return


# ------------------------------------------------------------------ 5. kiểm tra sách
def book_menu():
    while True:
        clear()
        draw_menu("KIỂM TRA SÁCH: ĐỌC MỤC LỤC", [
            f"INFO:Danh sách chung: {common.GIAO_TRINH_FILE.name} ({count_items(common.GIAO_TRINH_FILE.name)} bài) | Notebook: {id_short()}",
            "MID",
            "1|Đọc mục lục từ NotebookLM (in ra + lưu file)",
            f"2|Đọc mục lục và GHI vào {common.GIAO_TRINH_FILE.name} (có sao lưu)",
            "3|Xem lại mục lục đã lưu lần trước",
            "4|Kiểm tra lớp chữ của PDF (trang nào chưa có chữ)",
            f"5|Sửa {common.GIAO_TRINH_FILE.name}",
            "SEP",
            "0|Quay lại menu chính"])
        ch = ask("  Nhập lựa chọn của bạn : ").lower()
        if ch == "1":
            if need_id():
                exec_uv("src/notebook/muc_luc.py")
            pause()
        elif ch == "2":
            if need_id():
                if ask(f"  Ghi đè {common.GIAO_TRINH_FILE.name} bằng mục lục đọc được (bản cũ được sao lưu .bak)? [y/N] ").lower().startswith("y"):
                    exec_uv("src/notebook/muc_luc.py", "--apply")
            pause()
        elif ch == "3":
            view_text(out_root() / "muc_luc" / "muc_luc.md")
        elif ch == "4":
            print("  Nhập đường dẫn file PDF hoặc thư mục (Enter = tự tìm trong output_ocr/ rồi input_pdfs/)")
            p = ask("  Đường dẫn: ")
            exec_uv("src/ingest/check_pdf.py", *([p] if p else []))
            pause()
        elif ch == "5":
            edit_file(common.CONFIG_DIR / common.GIAO_TRINH_FILE.name)
        elif ch in ("0", "q"):
            return


# ------------------------------------------------------------------ 6-10. các chức năng tạo nội dung
FEATURES = {
    "giang": dict(title="GIẢNG BÀI", cmd=["src/notebook/giang_bai.py"], files=[common.GIANG_BAI_FILE.name], out="giang_bai"),
    "hoi": dict(title="TẠO CÂU HỎI", cmd=["src/notebook/tao_cau_hoi.py"], files=[common.CAU_HOI_FILE.name, "cauhoi.txt"], out="cau_hoi"),
    "mindmap": dict(title="TẠO MINDMAP", cmd=["src/notebook/tao_media.py", "mindmap"], files=[common.MINDMAPS_FILE.name], out="mindmap"),
    "infographic": dict(title="TẠO INFOGRAPHIC", cmd=["src/notebook/tao_media.py", "infographic"],
                        files=[common.INFOGRAPHICS_FILE.name], out="infographic"),
    "video": dict(title="TẠO VIDEO", cmd=["src/notebook/tao_media.py", "video"], files=[common.VIDEOS_FILE.name], out="video"),
}
MEDIA = ("mindmap", "infographic", "video")


def build_flags(kind):
    flags = []
    if kind in ("giang", "hoi") and S["strip"]:
        flags.append("--strip-cite")
    if S["fm"]:
        flags.append("--frontmatter")
    if S["obs"]:
        flags += ["--obsidian", "--book", S["book"]]
    if kind == "hoi":
        flags += ["--mode", S["quiz_mode"], "--quiz-format", S["quiz_fmt"]]
    if kind == "mindmap":
        flags += ["--mm-kind", S["mm_kind"]]
    return flags


def run_feature(kind, *extra):
    if not need_uv() or not need_id():
        return
    exec_uv(*FEATURES[kind]["cmd"], *build_flags(kind), *extra)


def feature_menu(kind):
    f = FEATURES[kind]
    while True:
        clear()
        lst = pick_list(*f["files"])
        test_label = ("Tạo thử bài đầu tiên (vẫn lưu file)" if kind in MEDIA
                      else "Chạy thử 1 bài đầu tiên (--test)")
        entries = [
            f"INFO:Danh sách: {lst} ({count_items(lst)} mục) | Notebook: {id_short()}",
            f"INFO:Đầu ra: {short(out_root() / f['out'], 34)} | Obsidian: {onoff(S['obs'])}",
            "MID",
            f"1|{test_label}",
            "2|Chạy toàn bộ danh sách",
            "3|Chạy một số bài (ví dụ 1,3-5)",
            "4|Làm lại toàn bộ, kể cả bài đã xong (--force)",
            f"5|Sửa danh sách riêng ({f['files'][0]})",
            f"6|Sửa danh sách chung ({common.GIAO_TRINH_FILE.name})",
            "SEP",
        ]
        if kind in ("giang", "hoi"):
            entries.append(f"7|Xóa số trích dẫn [1]: {onoff(S['strip'])}")
        entries.append(f"8|Thêm frontmatter (không Obsidian): {onoff(S['fm'])}")
        if kind == "hoi":
            entries += [f"9|Chế độ: {S['quiz_mode']}  (md / quiz / both)", f"10|Định dạng Quiz: {S['quiz_fmt']}"]
        if kind == "mindmap":
            entries.append(f"9|Loại mindmap: {S['mm_kind']}")
        if kind in MEDIA:
            entries.append("a|Xem tham số API của thư viện (gỡ lỗi)")
        entries += ["SEP", "0|Quay lại menu chính"]
        draw_menu(f["title"], entries)

        ch = ask("  Nhập lựa chọn của bạn : ").lower()
        if ch == "1":
            run_feature(kind, "--test")
            pause()
        elif ch == "2":
            run_feature(kind)
            pause()
        elif ch == "3":
            only = ask("  Nhập số thứ tự bài (ví dụ 1,3-5): ")
            if only:
                run_feature(kind, "--only", only)
                pause()
        elif ch == "4":
            if ask("  Làm lại TẤT CẢ và ghi đè file cũ? [y/N] ").lower().startswith("y"):
                run_feature(kind, "--force")
                pause()
        elif ch == "5":
            edit_file(common.CONFIG_DIR / f["files"][0])
        elif ch == "6":
            edit_file(common.CONFIG_DIR / common.GIAO_TRINH_FILE.name)
        elif ch == "7" and kind in ("giang", "hoi"):
            toggle("strip")
        elif ch == "8":
            toggle("fm")
        elif ch == "9" and kind == "hoi":
            cycle("quiz_mode")
        elif ch == "9" and kind == "mindmap":
            cycle("mm_kind")
        elif ch == "10" and kind == "hoi":
            cycle("quiz_fmt")
        elif ch == "a" and kind in MEDIA:
            run_feature(kind, "--api-info")
            pause()
        elif ch in ("0", "q"):
            return


# ------------------------------------------------------------------ 11. Obsidian
def obsidian_menu():
    while True:
        clear()
        draw_menu("OBSIDIAN: ĐỒNG BỘ VÀO VAULT", [
            f"INFO:Chế độ Obsidian : {onoff(S['obs'])}",
            f"INFO:Thư mục đầu ra  : {short(S['out_root'], 38)}",
            f"INFO:Tên note sách   : {short(S['book'], 38)}",
            "MID",
            "1|Bật/tắt chế độ Obsidian",
            "2|Đặt thư mục đầu ra (thư mục trong vault)",
            "3|Đặt tên note sách",
            "4|Cập nhật note mục lục của sách ngay",
            "5|Mở thư mục đầu ra trong Explorer",
            "SEP",
            "INFO:Khi BẬT: thêm frontmatter, đổi trích dẫn [1] thành",
            "INFO:[[wikilink]] về note sách, liên kết ngược về chương,",
            "INFO:và tạo note mục lục (Chương > Bài) gom mọi file.",
            "SEP",
            "0|Quay lại menu chính"])
        ch = ask("  Nhập lựa chọn của bạn : ").lower()
        if ch == "1":
            toggle("obs")
        elif ch == "2":
            print("  Dán đường dẫn thư mục trong vault (dạng C:\\... của Windows cũng được).")
            print("  Enter để quay về mặc định (ket_qua trong toolkit).")
            p = ask("  Thư mục: ")
            S["out_root"] = common.to_wsl_path(p) if p else DEFAULTS["out_root"]
            Path(S["out_root"]).mkdir(parents=True, exist_ok=True)
            save_settings()
        elif ch == "3":
            n = ask("  Tên note sách (Enter = giữ nguyên): ")
            if n:
                S["book"] = n
                save_settings()
        elif ch == "4":
            exec_uv("src/sync/cap_nhat_obsidian.py", "--out-root", str(S["out_root"]), "--book", S["book"])
            pause()
        elif ch == "5":
            open_folder(out_root())
        elif ch in ("0", "q"):
            return


# ------------------------------------------------------------------ 12. ID notebook
def set_id():
    while True:
        clear()
        draw_menu("ĐẶT ID NOTEBOOK", [
            f"INFO:ID hiện tại: {id_short()}", "MID",
            "1|Liệt kê notebook của tôi (để xem ID)",
            "2|Nhập ID hoặc URL notebook",
            "SEP", "0|Quay lại menu chính"])
        ch = ask("  Nhập lựa chọn của bạn : ").lower()
        if ch == "1":
            if need_uv():
                run([UV, "tool", "run", "--from", "notebooklm-py", "notebooklm", "list"])
            pause()
        elif ch == "2":
            raw = ask("  Dán ID hoặc URL notebook: ")
            if raw:
                (common.CONFIG_DIR / common.NOTEBOOK_ID_FILE.name).write_text(raw + "\n", encoding="utf-8")
                print(f"  Đã lưu. ID hiện tại: {id_short()}")
        elif ch in ("0", "q"):
            return


# ------------------------------------------------------------------ 13. trạng thái
def status():
    clear()
    print(f"{B}== Kiểm tra trạng thái =={R}\n")
    ok, bad = f"{GR}✔{R}", f"{RD}✘{R}"
    system = "Windows" if IS_WIN else ("WSL" if IS_WSL else platform.system())
    print(f" Hệ điều hành: {system}\n")

    print(f" {ok} uv {subprocess.run([UV, '--version'], capture_output=True, text=True).stdout.split()[-1]}"
          if UV else f" {bad} chưa cài uv  → chọn [2]")
    print(f" {ok} có dữ liệu đăng nhập NotebookLM (~/.notebooklm)"
          if (Path.home() / ".notebooklm").exists() else f" {bad} chưa đăng nhập NotebookLM  → chọn [2]")

    tess, gs = common.find_tesseract(), common.find_ghostscript()
    langs = common.tesseract_langs(tess) if tess else []
    print(f" {ok if tess else bad} Tesseract: {tess or 'chưa có  → chọn [3]'}")
    print(f" {ok if gs else bad} Ghostscript: {gs or 'chưa có  → chọn [3]'}")
    print(f" {ok if 'vie' in langs else bad} Gói tiếng Việt cho Tesseract: {'có' if 'vie' in langs else 'chưa có  → chọn [3]'}")
    _ocr_cache["ready"] = bool(tess and gs and "vie" in langs)

    print(f" {ok} ID notebook: {get_id()}" if get_id() else f" {bad} chưa có ID notebook  → chọn [20]")
    print(f" {ok} GEMINI_API_KEY đã được đặt" if has_key()
          else f" {bad} chưa có GEMINI_API_KEY  → chọn [5] rồi đặt key trong menu")

    print(f"\n Obsidian: {onoff(S['obs'])} | note sách: {S['book']}")
    print(f" Thư mục đầu ra: {S['out_root']}\n")
    pdfs = lambda d: sum(1 for p in Path(d).glob("*") if p.suffix.lower() == ".pdf") if Path(d).is_dir() else 0  # noqa: E731
    print(f" PDF trong input_pdfs/        : {pdfs(common.DEFAULT_INPUT_PDFS)}")
    print(f" PDF đã OCR trong output_ocr/ : {pdfs(common.DEFAULT_OUTPUT_OCR)}")
    md_dir = md_out_dir()
    n_md = sum(1 for p in md_dir.rglob("*.md") if ".pages" not in p.parts) if md_dir.is_dir() else 0
    print(f" File Markdown (Gemini)       : {n_md}  ({md_dir})")
    print(f" Số bài trong {common.GIAO_TRINH_FILE.name}  : {count_items(common.GIAO_TRINH_FILE.name)}")
    for sub in ("giang_bai", "cau_hoi", "mindmap", "infographic", "video"):
        d = out_root() / sub
        n = sum(1 for p in d.iterdir() if p.is_file() and p.name != ".state.json") if d.is_dir() else 0
        print(f" {('File đã tạo (' + sub + ')'):<29}: {n}")

    if ask("\n  Kiểm tra phiên đăng nhập trực tuyến (cần mạng, mất vài giây)? [y/N] ").lower().startswith("y"):
        if need_uv():
            run([UV, "tool", "run", "--from", "notebooklm-py[browser]", "notebooklm",
                 "auth", "check", "--test", "--json"])
    pause()


# ------------------------------------------------------------------ 14. mở thư mục
def open_menu():
    while True:
        targets = {"1": common.TOOLKIT_DIR, "2": common.DEFAULT_INPUT_PDFS, "3": common.DEFAULT_OUTPUT_OCR, "4": out_root(),
                   "5": out_root() / "giang_bai", "6": out_root() / "cau_hoi", "7": out_root() / "mindmap",
                   "8": out_root() / "infographic", "9": out_root() / "video", "10": md_out_dir()}
        clear()
        draw_menu("MỞ THƯ MỤC", [
            "1|Thư mục toolkit", "2|input_pdfs  (PDF gốc)", "3|output_ocr  (PDF đã OCR)",
            f"4|Thư mục đầu ra gốc ({short(S['out_root'], 24)})",
            "5|… giang_bai  (bài giảng)", "6|… cau_hoi  (câu hỏi)", "7|… mindmap",
            "8|… infographic", "9|… video", "10|Markdown từ Gemini (output_md)",
            "SEP", "0|Quay lại menu chính"])
        ch = ask("  Nhập lựa chọn của bạn : ").lower()
        if ch in targets:
            open_folder(targets[ch])
        elif ch in ("0", "q"):
            return


# ------------------------------------------------------------------ 23. thư mục input/output
def dir_specs():
    root = out_root()
    return [
        ("ocr_pdfs", "OCR PDF", [("input", common.INPUT_PDFS_DIR), ("output", common.OUTPUT_OCR_DIR)]),
        ("process_book", "PDF → Markdown", [("input", common.DEFAULT_INPUT_PDFS), ("output", common.DEFAULT_OUTPUT_MD)]),
        ("giai_de", "Giải đề y khoa", [("input", common.DE_THI_DIR), ("output", common.GIAI_DE_DIR)]),
        ("bien_tap", "Biên tập văn phong", [("input", root / "raw"), ("output", root / "polished")]),
        ("slides_to_md", "Slide → Markdown", [("input", common.SLIDES_OUT_DIR), ("output", common.SLIDES_OUT_DIR)]),
        ("build_transcript", "Làm sạch transcript", [("input", common.TRANSCRIPTS_DIR), ("output", common.TRANSCRIPTS_DIR)]),
        ("giang_bai", "Giảng bài", [("output", root / "giang_bai")]),
        ("tao_cau_hoi", "Tạo câu hỏi", [("output", root / "cau_hoi")]),
        ("tao_media", "Tạo media", [("output", root)]),
        ("ask_notebook", "Hỏi NotebookLM", [("output", root)]),
        ("generate_artifacts", "Tạo artifact", [("output", root / "artifacts_nguon")]),
        ("muc_luc", "Mục lục", [("output", root / "muc_luc")]),
    ]


def dir_menu():
    while True:
        clear()
        specs = dir_specs()
        values = common.read_dir_config()
        draw_menu("SỬA THƯ MỤC INPUT/OUTPUT", [
            "INFO:Enter để dùng thư mục mặc định; đường dẫn tương đối tính từ toolkit",
            "INFO:Có thể dán/kéo thả đường dẫn Windows dạng C:\\...",
            "MID",
            *[f"{i}|{label}" for i, (_, label, _) in enumerate(specs, 1)],
            "SEP", "0|Quay lại menu chính",
        ])
        choice = ask("  Chọn lệnh cần sửa: ").lower()
        if choice in ("0", "q"):
            return
        if not choice.isdigit() or not 1 <= int(choice) <= len(specs):
            continue
        key_base, label, fields = specs[int(choice) - 1]
        clear()
        print(f"{B}== {label} =={R}\n")
        for field, default in fields:
            key = f"{key_base}_{field}"
            current = values.get(key, "")
            print(f"  {field.upper()}: {current or '(mặc định)'}")
            print(f"  Nhập thư mục {field} (Enter = {default}):")
            raw = ask("  Đường dẫn: ")
            if not raw:
                common.write_dir_config(key, "")
                print(f"  Đã lưu: {key}=(mặc định)")
                continue
            path = common.to_wsl_path(raw)
            if field == "input" and not path.is_dir():
                print(f"  {RD}Thư mục input không tồn tại:{R} {path}")
                continue
            if field == "output" and not path.exists():
                if ask(f"  Thư mục chưa có. Tạo {path}? [y/N] ").lower().startswith("y"):
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    continue
            if not path.is_dir():
                print(f"  {RD}Đường dẫn không phải thư mục:{R} {path}")
                continue
            common.write_dir_config(key, str(path))
            print(f"  Đã lưu: {key}={path}")
        pause()


# ------------------------------------------------------------------ menu chính
def handle_pending_feature(title):
    clear()
    print(f"{B}== {title} =={R}\n")
    print("  Tính năng đang phát triển / chờ cấu hình backend LLM (DeepSeek).")
    pause()


def _log_benh_an_sv_environment(benh_an_sv, cfg, skills_dir):
    logger = logging.getLogger(__name__)
    logger.debug("=== Môi trường ===")
    logger.debug("Python: %s", sys.version.replace("\n", " "))
    logger.debug("File benh_an_sv.py: %s", Path(benh_an_sv.__file__).resolve())
    logger.debug("Config.skills_dir: %s (tồn tại: %s)", skills_dir, skills_dir.is_dir())
    logger.debug("Config.model: %s", cfg.model)
    logger.debug("Config.effort: %s", cfg.effort)
    logger.debug("DEEPSEEK_API_KEY: %s", "có" if os.getenv("DEEPSEEK_API_KEY") else "không")
    for package in ("openai", "PyMuPDF"):
        try:
            package_version = metadata.version(package)
        except metadata.PackageNotFoundError:
            package_version = "chưa cài"
        logger.debug("%s: %s", package, package_version)

    for name in ("skills", "checklists"):
        directory = skills_dir / name
        if not directory.is_dir():
            logger.debug("%s/: (không tồn tại)", name)
            continue
        files = sorted(path.relative_to(directory).as_posix()
                       for path in directory.rglob("*") if path.is_file())
        logger.debug("%s/: %s", name, ", ".join(files) if files else "(không có file)")


def run_benh_an_sv():
    clear()
    print(f"{B}== Phân tích bệnh án sinh viên =={R}\n")
    raw_case = ask("  Đường dẫn file bệnh án (.pdf/.txt/.md; có thể dán/kéo thả): ")
    if not raw_case:
        print("  Đã hủy, chưa chọn file bệnh án.")
        return
    case_path = common.to_wsl_path(raw_case)
    if not case_path.is_absolute():
        case_path = common.ROOT_DIR / case_path
    if not case_path.is_file():
        print(f"  {RD}Không tìm thấy file:{R} {case_path}")
        return
    if case_path.suffix.lower() not in {".pdf", ".txt", ".md"}:
        print(f"  {RD}Định dạng không hỗ trợ.{R} Chỉ nhận file .pdf, .txt hoặc .md.")
        return

    symptoms_input = ask(
        "  Triệu chứng chỉ định (tên cách nhau dấu phẩy, Enter = tự chọn theo lý do nhập viện): "
    )
    ly_do = ""
    if not symptoms_input:
        ly_do = ask("  Lý do nhập viện nhập tay (Enter = tự tách từ bệnh án): ")

    effort = ask("  Mức suy luận [high/max] (Enter = max): ").lower() or "max"
    while effort not in {"high", "max"}:
        print("  Hãy nhập high hoặc max.")
        effort = ask("  Mức suy luận [high/max] (Enter = max): ").lower() or "max"

    default_out = common.KET_QUA_DIR / "benh_an_sv"
    raw_out = ask(f"  Thư mục kết quả (Enter = {default_out}): ")
    out_dir = common.to_wsl_path(raw_out) if raw_out else default_out
    if not out_dir.is_absolute():
        out_dir = common.ROOT_DIR / out_dir

    force = ask("  Chạy lại từ đầu, bỏ kết quả cũ? [y/N] ").lower().startswith("y")

    from src.llm import benh_an_sv

    cfg = benh_an_sv.Config(effort=effort)
    log_dir = out_dir / case_path.stem
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "benh_an_sv.log"
    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.addFilter(lambda record: not record.exc_info)
    console_handler.setFormatter(logging.Formatter("  %(message)s"))

    root_logger = logging.getLogger()
    old_handlers = root_logger.handlers[:]
    old_level = root_logger.level
    for handler in old_handlers:
        root_logger.removeHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    try:
        skills_dir = cfg.skills_dir.resolve()
        _log_benh_an_sv_environment(benh_an_sv, cfg, skills_dir)
        symptoms = [item.strip() for item in symptoms_input.split(",") if item.strip()] or None
        result = benh_an_sv.run_pipeline(
            case_path,
            out_dir,
            symptoms=symptoms,
            cfg=cfg,
            force=force,
            chief_complaint=ly_do or None,
        )
    except benh_an_sv.ScannedPdfError as exc:
        logging.getLogger(__name__).exception("run_pipeline() thất bại")
        print(f"\n  PDF có vẻ là bản scan, chưa có lớp chữ: {exc}\n"
              "  Hãy OCR trước (mục [4]) rồi chọn file đã OCR.")
        print(f"  Lỗi {type(exc).__name__}: {exc} | Log: {log_path}")
    except benh_an_sv.BenhAnError as exc:
        logging.getLogger(__name__).exception("run_pipeline() thất bại")
        print(f"\n  Không thể phân tích bệnh án: {exc}")
        print(f"  Lỗi {type(exc).__name__}: {exc} | Log: {log_path}")
    except Exception as exc:
        logging.getLogger(__name__).exception("run_pipeline() thất bại")
        print(f"\n  Lỗi {type(exc).__name__}: {exc} | Log: {log_path}")
    else:
        print(f"\n  Kết quả nằm trong: {out_dir / case_path.stem}")
        print("  Mở file 04_gui_claude.md để dán sang Claude kiểm tra chéo.")
        print("\n  Các file kết quả:")
        for path in result.files.values():
            print(f"  - {path}")
    finally:
        root_logger.removeHandler(file_handler)
        root_logger.removeHandler(console_handler)
        file_handler.close()
        console_handler.close()
        root_logger.setLevel(old_level)
        for handler in old_handlers:
            root_logger.addHandler(handler)

def run_exam_solver():
    common.DE_THI_DIR.mkdir(parents=True, exist_ok=True)
    clear()
    print(f"{B}== Giải đề y khoa — 5 bước (NotebookLM + LLM) =={R}\n")
    print(f"  Thư mục đề thi: {common.DE_THI_DIR}")
    supported = (".pdf", ".md", ".txt", ".docx")
    files = sorted(
        (
            path for path in common.DE_THI_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in supported
        ),
        key=lambda path: str(path).lower(),
    )
    pdfs = [path for path in files if path.suffix.lower() == ".pdf"]
    if not files:
        print(f"\n  {RD}Chưa có file đề thi trong thư mục trên.{R}")
        print(f"  Hãy bỏ file .pdf, .md, .txt hoặc .docx vào:\n  {common.DE_THI_DIR}")
        legacy_dir = common.REPO_ROOT / "de_thi"
        if legacy_dir.is_dir():
            print(f"\n  {RD}Phát hiện thư mục cũ còn sót:{R} {legacy_dir}")
            print("  Hãy di chuyển đề thi sang workspace/de_thi/ sau refactor.")
        print("  Sau đó chọn lại mục [15].")
        pause()
        return 1
    if not pdfs:
        print(f"\n  {RD}Hiện pipeline giải đề chỉ đọc được file PDF.{R}")
        print("  Các file đã phát hiện:")
        for path in files:
            print(f"    - {path}")
        print(f"  Hãy chuyển/copy đề thi sang PDF trong:\n  {common.DE_THI_DIR}")
        pause()
        return 1
    return exec_uv("-m", "src.llm.exam_solver")


def main_menu():
    system = "Windows" if IS_WIN else ("WSL" if IS_WSL else platform.system())
    pretty = system
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                pretty = f"{line.split('=', 1)[1].strip(chr(34))} ({'WSL' if IS_WSL else 'Linux'})"
    except Exception:  # noqa: BLE001
        if IS_WIN:
            pretty = f"Windows {platform.release()}"
    handlers = {
        "1": show_guide,
        "2": setup_nlm,
        "3": setup_ocr,
        "4": do_ocr,
        "5": md_menu,
        "6": lambda: exec_uv("src/menus/menu_nguon_gv.py"),
        "7": book_menu,
        "8": lambda: feature_menu("giang"),
        "9": lambda: feature_menu("hoi"),
        "10": lambda: feature_menu("mindmap"),
        "11": lambda: feature_menu("infographic"),
        "12": lambda: feature_menu("video"),
        "13": lambda: exec_uv("src/menus/menu_bien_tap.py"),
        "14": lambda: exec_uv("src/llm/cau_hoi_llm.py"),
        "15": run_exam_solver,
        "16": lambda: handle_pending_feature("Tạo Anki, Flashcard"),
        "17": run_benh_an_sv,
        "18": lambda: handle_pending_feature("Đang chờ update"),
        "19": obsidian_menu,
        "20": set_id,
        "21": status,
        "22": open_menu,
        "23": dir_menu,
    }
    while True:
        clear()
        has_login = (Path.home() / ".notebooklm").exists()
        draw_menu("BỘ CÔNG CỤ NOTEBOOKLM", [
            f"CTR:{pretty}", "MID",
            f"INFO:Notebook ID: {id_short()} | Obsidian: {onoff(S['obs'])}",
            f"INFO:uv: {yn(UV)} | OCR: {yn(ocr_ready())} | đăng nhập: {yn(has_login)} | Gemini: {yn(has_key())}",
            "MID",
            "CTR:── CÀI ĐẶT & NHẬP LIỆU ──",
            "1|Hướng dẫn (README.md)",
            "2|Cài & set-up notebooklm-py",
            "3|Cài & set-up OCR",
            "4|OCR PDFs (cả thư mục)",
            "5|PDF → Markdown bằng Gemini (process_book.py)",
            "6|Nguồn giáo viên: transcript, slide, giảng theo nguồn",
            "MID",
            "CTR:── Gemini Notebook ──",
            "7|Kiểm tra sách: đọc mục lục Chương/Bài",
            "8|Giảng bài NotebookLM",
            "9|Tạo câu hỏi NotebookLM",
            "10|Tạo Mindmap",
            "11|Tạo Infographic",
            "12|Tạo Video",
            "13|Biên tập văn phong (lớp viết lại bài giảng)",
            "MID",
            "CTR:── Gemini Notebook + LLM ──",
            "14|Tạo bộ câu hỏi theo chủ đề",
            "15|Giải đề y khoa — 5 bước (NotebookLM + LLM)",
            "16|Tạo Anki, Flashcard",
            "17|Phân tích bệnh án sinh viên",
            "18|Đang chờ update",
            "MID",
            "CTR:── ĐỒNG BỘ & TIỆN ÍCH ──",
            "19|Obsidian: đồng bộ vào vault",
            "20|Đặt ID notebook",
            "21|Kiểm tra trạng thái",
            "22|Mở thư mục",
            "23|Sửa thư mục Input/Output",
            "SEP",
            "0|Thoát"])
        ch = ask("  Nhập lựa chọn của bạn [0-23] : ").lower()
        if ch in ("0", "q"):
            print()
            return
        if ch in handlers:
            try:
                handlers[ch]()
            except Exception as exc:  # noqa: BLE001
                print(f"\n  {RD}Chức năng gặp lỗi: {type(exc).__name__}: {exc}{R}")
            finally:
                common.wait_for_menu()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print()
