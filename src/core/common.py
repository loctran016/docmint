"""Hàm dùng chung cho các script Python của bộ công cụ (chỉ dùng thư viện chuẩn)."""
import argparse
import asyncio
import json
import os
import asyncio
from contextlib import asynccontextmanager
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

# In tiếng Việt an toàn kể cả khi Windows chuyển hướng đầu ra
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_WSL = (not IS_WIN) and not IS_MAC and "microsoft" in os.uname().release.lower()


def _find_repo_root() -> Path:
    start = Path(__file__).resolve()
    for directory in (start, *start.parents):
        if (directory / ".git").exists() or (directory / "pyproject.toml").exists():
            return directory
    return Path.cwd().resolve()


REPO_ROOT = _find_repo_root()
ROOT_DIR = REPO_ROOT
CONFIG_DIR = REPO_ROOT / "config"
WORKSPACE_DIR = REPO_ROOT / "workspace"
TOOLKIT_DIR = REPO_ROOT


def _parse_env_fallback(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip("\"'")
        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def load_project_env() -> list[Path]:
    """Nạp .env ở repo root trước, sau đó .env trong config nếu có."""
    loaded: list[Path] = []
    paths: list[Path] = []
    for candidate in (REPO_ROOT / ".env", CONFIG_DIR / ".env"):
        candidate = candidate.resolve()
        if candidate.exists() and candidate not in paths:
            paths.append(candidate)

    try:
        from dotenv import load_dotenv
    except ImportError:
        for path in paths:
            for key, value in _parse_env_fallback(path).items():
                os.environ[key] = value
            loaded.append(path)
        return loaded

    for path in paths:
        load_dotenv(dotenv_path=path, override=True, encoding="utf-8-sig")
        loaded.append(path)
    return loaded


load_project_env()

GIAO_TRINH_FILE = CONFIG_DIR / "giao_trinh.txt"
GIANG_BAI_FILE = CONFIG_DIR / "giang_bai.txt"
CAU_HOI_FILE = CONFIG_DIR / "cau_hoi.txt"
MINDMAPS_FILE = CONFIG_DIR / "mindmaps.txt"
INFOGRAPHICS_FILE = CONFIG_DIR / "infographics.txt"
VIDEOS_FILE = CONFIG_DIR / "videos.txt"
NOTEBOOK_ID_FILE = CONFIG_DIR / "notebook_id.txt"
BIEN_TAP_STYLE_FILE = CONFIG_DIR / "bien_tap_style.md"
MEDICAL_TERMS_FILE = CONFIG_DIR / "medical_terms.txt"

INPUT_PDFS_DIR = WORKSPACE_DIR / "input_pdfs"
OUTPUT_OCR_DIR = WORKSPACE_DIR / "output_ocr"
OUTPUT_MD_DIR = WORKSPACE_DIR / "output_md"
KET_QUA_DIR = WORKSPACE_DIR / "ket_qua"
TRANSCRIPTS_DIR = WORKSPACE_DIR / "transcripts"
SLIDES_OUT_DIR = WORKSPACE_DIR / "slides_out"
GIANG_OUT_DIR = WORKSPACE_DIR / "giang_out"
DE_THI_DIR = WORKSPACE_DIR / "de_thi"
GIAI_DE_DIR = WORKSPACE_DIR / "ket_qua" / "giai_de"
EXAM_CACHE_DIR = ROOT_DIR / ".cache" / "exam_solver"
EXAM_IMG_DIR = ROOT_DIR / ".cache" / "exam_imgs"

NOT_FOUND_PHRASE = "không tìm thấy bài này trong nguồn"
MASTER_FILES = [GIAO_TRINH_FILE.name, "bai.txt"]   # danh sách chung (bai.txt là tên cũ)
DEFAULT_OUT_ROOT = str(KET_QUA_DIR)
DEFAULT_INPUT_PDFS = INPUT_PDFS_DIR
DEFAULT_OUTPUT_OCR = OUTPUT_OCR_DIR
DEFAULT_OUTPUT_MD = OUTPUT_MD_DIR
DEFAULT_TRANSCRIPTS = TRANSCRIPTS_DIR
DEFAULT_SLIDES_OUT = SLIDES_OUT_DIR
DEFAULT_GIANG_OUT = GIANG_OUT_DIR
DEFAULT_BOOK = "Sách giáo khoa"

# Dòng chú thích được hiểu là TÊN CHƯƠNG nếu:  "## Tên chương"  hoặc  "# Chương 1 ..." / "# Phần II ..."
CHAPTER_RE = re.compile(
    r"^(?:##(?!#)\s*(?P<a>.+)|#\s*(?P<b>(?:chương|phần|chuong|phan)\s+(?:\d+|[ivxlc]+)\b.*))$",
    re.IGNORECASE,
)
OPT_RE = re.compile(r"^([A-Za-z_]+)\s*=\s*(.+)$")
ALL_FLAGS = {"tomtat", "khongtomtat", "cauhoi", "khongcauhoi"}
CITE_RE = re.compile(r"\s?\[(\d+(?:\s*[,\-–]\s*\d+)*)\]")


# ------------------------------------------------------------ đường dẫn / cấu hình
def to_wsl_path(p):
    """Bỏ dấu nháy và mở rộng ~. Trên WSL/Linux đổi C:\\... sang /mnt/c/...; trên Windows giữ nguyên."""
    p = p.strip().strip('"').strip("'")
    if not IS_WIN and re.match(r"^[A-Za-z]:[\\/]", p):
        try:
            return subprocess.run(["wslpath", "-u", p], capture_output=True,
                                  text=True, check=True).stdout.strip()
        except Exception:  # noqa: BLE001
            return p
    return os.path.expanduser(p)


def get_out_root(cli_value=None):
    raw = cli_value or os.environ.get("NLM_OUT_ROOT") or str(WORKSPACE_DIR / "ket_qua")
    if raw in ("ket_qua", "./ket_qua"):
        raw = str(WORKSPACE_DIR / "ket_qua")
    return Path(to_wsl_path(raw))


def get_book(cli_value=None):
    return (cli_value or os.environ.get("NLM_BOOK") or DEFAULT_BOOK).strip()


def _clean_id(value):
    """Chấp nhận cả ID lẫn URL đầy đủ của notebook."""
    value = value.strip().rstrip("/")
    value = value.split("?")[0].split("#")[0]
    return value.split("/")[-1]


def read_notebook_id(cli_value=None):
    if cli_value:
        return _clean_id(cli_value)
    env = os.environ.get("NOTEBOOK_ID")
    if env:
        return _clean_id(env)
    for f in (CONFIG_DIR / NOTEBOOK_ID_FILE.name, ROOT_DIR / NOTEBOOK_ID_FILE.name):
        if f.exists():
            for line in f.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    return _clean_id(line)
    raise SystemExit(
        "Chưa có ID notebook. Hãy ghi ID (hoặc URL notebook) vào file notebook_id.txt,\n"
        "hoặc truyền trực tiếp trên dòng lệnh."
    )


@asynccontextmanager
async def notebooklm_client(*, chat_timeout: int = 300):
    """Mở client NotebookLM bằng đúng stored session của notebooklm-py."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError as exc:
        raise SystemExit(
            "Thiếu notebooklm-py. Cài bằng: uv run src/ingest/setup_notebooklm.py"
        ) from exc
    async with NotebookLMClient.from_storage(chat_timeout=chat_timeout) as client:
        yield client


# ------------------------------------------------------------------ công cụ OCR
LOCAL_TESSDATA = TOOLKIT_DIR / "tessdata"      # nơi setup OCR trên Windows tải vie/eng về


def _program_dirs():
    return [Path(v) for k in ("ProgramFiles", "ProgramFiles(x86)") if (v := os.environ.get(k))]


def find_tesseract():
    found = shutil.which("tesseract")
    if found:
        return found
    if IS_WIN:
        cands = [d / "Tesseract-OCR" / "tesseract.exe" for d in _program_dirs()]
        local = os.environ.get("LOCALAPPDATA")
        if local:
            cands += [Path(local) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
                      Path(local) / "Tesseract-OCR" / "tesseract.exe"]
        for c in cands:
            if c.exists():
                return str(c)
    return None


def find_ghostscript():
    for name in ("gs", "gswin64c", "gswin32c"):
        found = shutil.which(name)
        if found:
            return found
    if IS_WIN:
        for d in _program_dirs():
            for exe in sorted(d.glob("gs/gs*/bin/gswin64c.exe"), reverse=True):
                return str(exe)
    return None


def tesseract_env():
    """Môi trường chạy tesseract/ocrmypdf: dùng thư mục tessdata riêng của toolkit nếu có đủ vie + eng."""
    env = os.environ.copy()
    if all((LOCAL_TESSDATA / f"{lang}.traineddata").exists() for lang in ("vie", "eng")):
        env["TESSDATA_PREFIX"] = str(LOCAL_TESSDATA)
    return env


def tesseract_langs(tess=None):
    tess = tess or find_tesseract()
    if not tess:
        return []
    try:
        r = subprocess.run([tess, "--list-langs"], capture_output=True, text=True,
                           env=tesseract_env(), timeout=30)
    except Exception:  # noqa: BLE001
        return []
    langs = []
    for line in ((r.stdout or "") + "\n" + (r.stderr or "")).splitlines():
        line = line.strip()
        if line and " " not in line and not line.endswith(":"):
            langs.append(line)
    return langs


def ocr_ready():
    """Đã đủ Tesseract (có tiếng Việt) và Ghostscript chưa."""
    tess = find_tesseract()
    return bool(tess and find_ghostscript() and "vie" in tesseract_langs(tess))


# ------------------------------------------------------------- đọc danh sách
def parse_list_file(path):
    """Mỗi dòng: Tên bài | lưu ý | key=value | cờ ...

    - dòng trống bị bỏ qua; dòng bắt đầu bằng '#' là chú thích,
      trừ khi nó là tên chương (xem CHAPTER_RE) thì được ghi nhớ cho các bài phía sau
    - trường dạng key=value -> opts (mỗi chức năng tự chọn key nó dùng)
    - trường trùng một cờ trong ALL_FLAGS -> flags
    - các trường còn lại -> lưu ý riêng (note)
    """
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Không thấy file danh sách: {path}")
    items, chapter = [], ""
    for raw in p.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            m = CHAPTER_RE.match(line)
            if m:
                chapter = (m.group("a") or m.group("b")).strip()
            continue
        parts = [x.strip() for x in line.split("|")]
        notes, opts, flags = [], {}, set()
        for field in parts[1:]:
            if not field:
                continue
            m = OPT_RE.match(field)
            if m:
                opts[m.group(1).lower()] = m.group(2).strip()
            elif field.lower() in ALL_FLAGS:
                flags.add(field.lower())
            else:
                notes.append(field)
        items.append({"title": parts[0], "note": "; ".join(notes),
                      "opts": opts, "flags": flags, "chapter": chapter})
    return items


def resolve_list(feature_files, cli_file=None):
    """File riêng của chức năng được ưu tiên; nếu không có bài nào thì dùng danh sách chung."""
    candidates = [cli_file] if cli_file else list(feature_files) + MASTER_FILES
    for f in candidates:
        p = Path(f)
        if not p.is_absolute():
            candidates_for_name = (CONFIG_DIR / p.name, ROOT_DIR / p.name, ROOT_DIR / p)
            p = next((q for q in candidates_for_name if q.exists()), p)
        if p.exists():
            items = parse_list_file(p)
            if items:
                return p, items
    raise SystemExit(
        "Chưa có bài nào để làm. Hãy điền danh sách bài vào "
        f"{(cli_file or (list(feature_files) + MASTER_FILES)[0])} hoặc giao_trinh.txt.\n"
        "Mẹo: dùng menu [5] 'Kiểm tra sách' để tự đọc mục lục rồi ghi vào giao_trinh.txt."
    )


def parse_only(text):
    """'1,3-5' -> {1,3,4,5}; rỗng -> None (nghĩa là tất cả)."""
    if not text:
        return None
    result = set()
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            result.update(range(int(a), int(b) + 1))
        else:
            result.add(int(chunk))
    return result


def parse_delay(text):
    a, _, b = text.partition(",")
    lo = float(a)
    hi = float(b) if b else lo
    return (min(lo, hi), max(lo, hi))


def add_common_args(ap, delay_default="5,10"):
    """Các tùy chọn giống nhau ở mọi script."""
    ap.add_argument("notebook_id", nargs="?",
                    help="ID hoặc URL notebook (bỏ trống thì đọc notebook_id.txt)")
    ap.add_argument("--file", help="dùng danh sách này thay cho file riêng và giao_trinh.txt")
    ap.add_argument("--test", action="store_true",
                    help="chỉ làm một bài để thử (không lưu file)")
    ap.add_argument("--only", help="chỉ làm các bài theo số thứ tự trong danh sách, ví dụ 1,3-5")
    ap.add_argument("--force", action="store_true", help="làm lại cả bài đã có file")
    ap.add_argument("--strip-cite", action="store_true",
                    help="xóa số trích dẫn kiểu [1], [2, 3]")
    ap.add_argument("--frontmatter", action="store_true",
                    help="thêm YAML frontmatter (title, tags, created)")
    ap.add_argument("--obsidian", action="store_true",
                    help="chế độ Obsidian: frontmatter + [[wikilink]] trích dẫn + liên kết ngược + note mục lục")
    ap.add_argument("--book", help=f"tên note sách trong Obsidian (mặc định '{DEFAULT_BOOK}')")
    ap.add_argument("--out-root",
                    help=f"thư mục đầu ra gốc, ví dụ thư mục trong vault Obsidian (mặc định '{DEFAULT_OUT_ROOT}')")
    ap.add_argument("--delay", default=delay_default,
                    help=f"nghỉ ngẫu nhiên giữa các bài, giây (mặc định {delay_default})")


# -------------------------------------------------------------- xử lý văn bản
def safe_filename(s, max_len=80):
    """Bỏ ký tự cấm của Windows và ký tự làm hỏng link Obsidian (# ^ [ ] |)."""
    s = re.sub(r'[\\/:*?"<>|#^\[\]]', " ", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s[:max_len] or "khong_ten"


def extract_h1(markdown, fallback):
    m = re.search(r"^#\s+(.+?)\s*$", markdown, flags=re.MULTILINE)
    return m.group(1).strip() if m else fallback


def strip_citations(text):
    """Xóa số trích dẫn kiểu [1], [1, 2], [4-7, 10]."""
    return CITE_RE.sub("", text)


def cite_to_wikilinks(text, book):
    """[1, 2] -> ([[Tên sách|1, 2]]). Trong bảng Markdown dùng \\| để không vỡ bảng."""
    out = []
    for line in text.split("\n"):
        pipe = r"\|" if line.lstrip().startswith("|") else "|"
        out.append(CITE_RE.sub(lambda m, pipe=pipe: f" ([[{book}{pipe}{m.group(1)}]])", line))
    return "\n".join(out)


def looks_not_found(text):
    return NOT_FOUND_PHRASE in text.lower() and len(text) < 600


def chapter_heading(chapter):
    """Tên chương dùng làm heading và đích link (bỏ ký tự Obsidian không cho dùng trong link)."""
    s = re.sub(r"[#^|\\:\[\]]", " ", chapter)
    return re.sub(r"\s+", " ", s).strip()


def _q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', "'") + '"'


def make_frontmatter(title, tags, extra=None):
    lines = ["---", f"title: {_q(title)}", f"tags: [{', '.join(tags)}]",
             f"created: {date.today().isoformat()}"]
    for k, v in (extra or {}).items():
        lines.append(f"{k}: {_q(v)}")
    if not extra or "nguon" not in extra:
        lines.append("nguon: NotebookLM")
    lines += ["---", "", ""]
    return "\n".join(lines)


def backlinks(book, chapter):
    parts = [f"[[{book}]]"]
    if chapter:
        h = chapter_heading(chapter)
        parts.append(f"[[{book}#{h}|{h}]]")
    return "\n\n---\nLiên kết: " + " · ".join(parts) + "\n"


def make_obs(args, item, kind):
    """Thông tin Obsidian cho một mục (None nếu không bật --obsidian)."""
    if not getattr(args, "obsidian", False):
        return None
    return {"book": get_book(args.book), "chapter": item.get("chapter", ""),
            "kind": kind, "lesson": item["title"]}


def save_markdown(out_dir, index, fallback_title, text, *, strip_cite=False,
                  frontmatter=False, tags=None, old_file=None, obs=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if obs:
        text = strip_citations(text) if strip_cite else cite_to_wikilinks(text, obs["book"])
    elif strip_cite:
        text = strip_citations(text)
    title = extract_h1(text, fallback_title)
    if obs:
        text = text.rstrip() + backlinks(obs["book"], obs.get("chapter", ""))
        extra = {"nguon": f"[[{obs['book']}]]", "loai": obs["kind"], "bai": obs["lesson"]}
        if obs.get("chapter"):
            extra["chuong"] = f"[[{obs['book']}#{chapter_heading(obs['chapter'])}]]"
        text = make_frontmatter(title, tags or [], extra) + text
    elif frontmatter:
        text = make_frontmatter(title, tags or []) + text
    path = out_dir / f"{index:02d} - {safe_filename(title)}.md"
    if old_file and Path(old_file).exists() and Path(old_file) != path:
        Path(old_file).unlink()
    path.write_text(text, encoding="utf-8")
    return path


# ------------------------------------------------------- nhớ bài đã làm xong
class State:
    """Lưu 'bài nào đã ra file nào' để chạy lại thì bỏ qua bài đã xong."""

    def __init__(self, path):
        self.path = Path(path)
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            self.data = {}

    def get_file(self, key):
        p = self.data.get(key)
        return p if p and Path(p).exists() else None

    def set_file(self, key, file):
        self.data[key] = str(file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")


# ----------------------------------------------- note mục lục (hub) cho Obsidian
HUB_MARK = "<!-- nlm-hub: tự động tạo, sẽ bị ghi đè khi cập nhật -->"
FEATURES = [("giang_bai", "Bài giảng"), ("cau_hoi", "Đề"), ("mindmap", "Mindmap"),
            ("infographic", "Infographic"), ("video", "Video")]


def _wikilink(path, label):
    p = Path(path)
    target = p.stem if p.suffix.lower() == ".md" else p.name
    return f"[[{target}|{label}]]"


def update_hub(root, book):
    """Tạo/cập nhật note '<Tên sách>.md': mục lục Chương > Bài kèm link tới mọi file đã tạo.
    Mọi trích dẫn [[Tên sách|n]] trong các note đều trỏ về note này."""
    root = Path(root)
    lessons = {}
    for feat, label in FEATURES:
        sf = root / feat / ".state.json"
        if not sf.exists():
            continue
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for key, path in data.items():
            p = Path(path)
            if not p.exists() or p.suffix.lower() in (".json", ".html"):
                continue
            lbl = "Quiz" if "(Quiz)" in p.name else label
            lessons.setdefault(key.split("::")[0], {}).setdefault(lbl, []).append(p)

    items = []
    for f in MASTER_FILES:
        if Path(f).exists():
            items = parse_list_file(f)
            if items:
                break
    known = {it["title"] for it in items}
    for t in lessons:
        if t not in known:
            items.append({"title": t, "chapter": ""})

    groups, order = {}, []
    for it in items:
        ch = it.get("chapter") or ""
        if ch not in groups:
            groups[ch] = []
            order.append(ch)
        groups[ch].append(it["title"])

    lines = ["---", f"title: {_q(book)}", "tags: [sach, muc-luc]",
             f"created: {date.today().isoformat()}", "---", "",
             HUB_MARK, "", f"# {book}", "",
             "Note mục lục của sách. Các trích dẫn `([[" + book + "|n]])` trong bài giảng, đề... đều trỏ về đây.", ""]
    for ch in order:
        if len(order) > 1 or ch:
            lines += [f"## {chapter_heading(ch) if ch else 'Chưa phân chương'}", ""]
        for title in groups[ch]:
            links = []
            for label, paths in lessons.get(title, {}).items():
                for p in sorted(paths):
                    links.append(_wikilink(p, label))
            lines.append(f"- **{title}**" + (" — " + " · ".join(links) if links else ""))
        lines.append("")

    root.mkdir(parents=True, exist_ok=True)
    hub = root / f"{safe_filename(book)}.md"
    if hub.exists() and HUB_MARK not in hub.read_text(encoding="utf-8"):
        print(f"  Cảnh báo: {hub} là note của bạn (không có dấu hiệu tự động), không ghi đè.")
        print("  -> Đổi tên note sách bằng --book hoặc menu Obsidian, hoặc đổi tên note cũ.")
        return None
    hub.write_text("\n".join(lines), encoding="utf-8")
    return hub


def finish_obsidian(args, root):
    """Gọi cuối mỗi script khi bật --obsidian."""
    if getattr(args, "obsidian", False) and not getattr(args, "test", False):
        hub = update_hub(root, get_book(args.book))
        if hub:
            print(f"Note mục lục Obsidian: {hub}")


# ------------------------------------------------------------------- hỏi AI
async def ask_with_retry(client, notebook_id, prompt, *, max_retry=3, timeout=300):
    for attempt in range(1, max_retry + 1):
        try:
            result = await asyncio.wait_for(
                client.chat.ask(notebook_id, prompt), timeout=timeout)
            answer = getattr(result, "answer", None)
            if not answer or not str(answer).strip():
                raise RuntimeError("Câu trả lời rỗng")
            return str(answer)
        except Exception as e:  # noqa: BLE001
            msg = str(e) or "(không có nội dung lỗi)"
            print(f"  Lỗi (lần {attempt}/{max_retry}): {type(e).__name__}: {msg}")
            if attempt < max_retry:
                await asyncio.sleep(10 * attempt)
    return None
