"""Hàm dùng chung cho 4_giang_bai.py và 5_tao_cau_hoi.py (chỉ dùng thư viện chuẩn)."""
import asyncio
import json
import os
import re
from datetime import date
from pathlib import Path

NOT_FOUND_PHRASE = "không tìm thấy bài này trong nguồn"


# ---------------------------------------------------------------- notebook id
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
    f = Path("notebook_id.txt")
    if f.exists():
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                return _clean_id(line)
    raise SystemExit(
        "Chưa có ID notebook. Hãy ghi ID (hoặc URL notebook) vào file notebook_id.txt,\n"
        "hoặc truyền trực tiếp: uv run 4_giang_bai.py ID_NOTEBOOK"
    )


# ------------------------------------------------------------- đọc danh sách
def parse_list_file(path, known_opts=(), known_flags=()):
    """Mỗi dòng: Tên bài | lưu ý | key=value | cờ ...

    - dòng trống và dòng bắt đầu bằng '#' bị bỏ qua
    - trường dạng key=value (key nằm trong known_opts) -> opts
    - trường trùng một từ trong known_flags -> flags
    - các trường còn lại -> lưu ý riêng (note)
    """
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Không thấy file danh sách: {path}")
    opt_re = re.compile(r"^([A-Za-z_]+)\s*=\s*(.+)$")
    items = []
    for raw in p.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [x.strip() for x in line.split("|")]
        notes, opts, flags = [], {}, set()
        for field in parts[1:]:
            if not field:
                continue
            m = opt_re.match(field)
            if m and m.group(1).lower() in known_opts:
                opts[m.group(1).lower()] = m.group(2).strip()
            elif field.lower() in known_flags:
                flags.add(field.lower())
            else:
                notes.append(field)
        items.append({"title": parts[0], "note": "; ".join(notes),
                      "opts": opts, "flags": flags})
    return items


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
    return re.sub(r"\s?\[\d+(?:\s*[,\-–]\s*\d+)*\]", "", text)


def looks_not_found(text):
    return NOT_FOUND_PHRASE in text.lower() and len(text) < 600


def make_frontmatter(title, tags):
    safe_title = title.replace('"', "'")
    tag_text = ", ".join(tags)
    return (
        "---\n"
        f'title: "{safe_title}"\n'
        f"tags: [{tag_text}]\n"
        f"created: {date.today().isoformat()}\n"
        "nguon: NotebookLM\n"
        "---\n\n"
    )


def save_markdown(out_dir, index, fallback_title, text, *, strip_cite=False,
                  frontmatter=False, tags=None, old_file=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if strip_cite:
        text = strip_citations(text)
    title = extract_h1(text, fallback_title)
    if frontmatter:
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
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


# ------------------------------------------------------------------- hỏi AI
async def ask_with_retry(client, notebook_id, prompt, *, max_retry=3, timeout=300):
    for attempt in range(1, max_retry + 1):
        try:
            result = await asyncio.wait_for(
                client.chat.ask(notebook_id, prompt), timeout=timeout
            )
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
