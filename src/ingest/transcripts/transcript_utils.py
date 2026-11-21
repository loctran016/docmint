import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
"""Hàm dùng chung cho pipeline transcript (máy cá nhân và GitHub Actions).

Phần mới (Groq Whisper): bóc metadata/playlist và tải audio bằng yt-dlp, nén và cắt audio bằng ffmpeg,
cache STT thô theo video_id (.cache/transcripts/raw/{video_id}.json).
Phần cũ (phụ đề .vtt, Markdown thô) vẫn giữ nguyên để dùng với --backend subs.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.core import common

BRACKET_NOISE = re.compile(r"^\[[^\]]*\]$")  # [Âm nhạc], [Music], [Applause]


def safe_filename(title):
    name = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    return name[:120] or "Medical_Lecture"


def clean_vtt_to_text(vtt_file_path):
    """Trả về list các câu đã làm sạch (chưa gộp đoạn)."""
    with open(vtt_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned = []
    last_line = ""

    for line in lines:
        line = line.strip()
        if (
            not line
            or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE"))
            or "-->" in line
            or line.isdigit()
        ):
            continue

        text = re.sub(r"<[^>]+>", "", line)
        text = html.unescape(text)
        text = text.replace(">>", "").strip()
        text = re.sub(r"\s+", " ", text)

        if not text or BRACKET_NOISE.match(text):
            continue

        if text != last_line:
            cleaned.append(text)
            last_line = text

    return cleaned


def group_paragraphs(sentences, size=15):
    return [" ".join(sentences[i:i + size]) for i in range(0, len(sentences), size)]


def write_markdown(output_path, title, url, source_label, sentences):
    body = "\n\n".join(group_paragraphs(sentences))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n")
        f.write(f"- **Nguồn:** {url}\n")
        f.write(f"- **Loại bản ghi:** {source_label}\n")
        f.write("- **Lưu ý:** Bản ghi thô tự động, có thể thiếu dấu câu hoặc sai thuật ngữ.\n\n---\n\n")
        f.write(body)



# ---------------------------------------------------------------------------
# Pipeline Groq Whisper: metadata, audio, cache thô
# ---------------------------------------------------------------------------
CACHE_ROOT = common.REPO_ROOT / ".cache"
RAW_DIR = CACHE_ROOT / "transcripts" / "raw"
CHUNK_DIR = CACHE_ROOT / "transcripts" / "chunks"
AUDIO_DIR = CACHE_ROOT / "audio"
CHUNK_SECONDS = 900          # mỗi đoạn audio ~15 phút
MAX_CHUNK_BYTES = 20 * 1024 * 1024  # dưới giới hạn 25MB của Groq

# Gọi yt-dlp bằng chính Python đang chạy: không phụ thuộc PATH (uv run, Windows, WSL đều được).
YTDLP = [sys.executable, "-m", "yt_dlp"]
YTDLP_CLIENT_PROFILES = (
    ["--remote-components", "ejs:github"],
    ["--remote-components", "ejs:github", "--extractor-args", "youtube:player_client=web_safari,web,mweb"],
    ["--remote-components", "ejs:github", "--extractor-args", "youtube:player_client=android,mweb"],
)

class PipelineError(Exception):
    """Lỗi có thể giải thích cho người dùng (thiếu ffmpeg, yt-dlp bị chặn, file hỏng...)."""


def run_cmd(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-6:]
        raise PipelineError(f"Lệnh lỗi ({os.path.basename(cmd[0])} {' '.join(cmd[1:3])}...): " + " | ".join(tail))
    return r


def run_ytdlp(args):
    """Thử các cấu hình client của yt-dlp thay vì phụ thuộc một cấu hình duy nhất."""
    last_error = None
    for profile in YTDLP_CLIENT_PROFILES:
        try:
            return run_cmd([*YTDLP, *profile, *args])
        except PipelineError as e:
            last_error = e
            continue
    raise PipelineError(f"Không trích xuất được YouTube sau khi thử nhiều client: {last_error}")


def cookie_args(cookies_file=None, browser=None):
    """Cấu hình xác thực yt-dlp: --cookies <file> (ưu tiên) hoặc --cookies-from-browser <trình duyệt>.
    Đọc thêm từ biến môi trường YT_COOKIES_FILE và YT_COOKIES_BROWSER."""
    cookies_file = cookies_file or os.environ.get("YT_COOKIES_FILE")
    browser = browser or os.environ.get("YT_COOKIES_BROWSER")
    if cookies_file:
        path = Path(cookies_file)
        if not path.is_file():
            raise PipelineError(f"Cookie file không tồn tại: {cookies_file}")
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as e:
            raise PipelineError(f"Không đọc được cookie file: {e}") from e
        if not any(not line.startswith("#") and len(line.split("\t")) >= 7
                   for line in lines):
            raise PipelineError("Cookie file không đúng định dạng Netscape cookies.txt.")
        return ["--cookies", str(path)]
    if browser:
        return ["--cookies-from-browser", browser]
    return []


def is_playlist_url(url: str) -> bool:
    """Link gốc playlist (youtube.com/playlist?list=...). Link video lẻ có &list=... vẫn là video lẻ."""
    u = urlparse(url)
    return u.path.rstrip("/") == "/playlist" and "list" in parse_qs(u.query)

def fetch_metadata(url: str, cookies=()):
    """Metadata MỘT video (kể cả khi URL có &list=...). Trả về dict id, title, duration, url."""
    r = run_ytdlp([*cookies, "--dump-single-json", "--skip-download", "--no-playlist", "--no-warnings", url])
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise PipelineError(f"Không đọc được metadata của {url}: {e}") from e
    return {"id": d.get("id"), "title": d.get("title") or "Medical_Lecture",
            "duration": float(d.get("duration") or 0), "url": d.get("webpage_url") or url}


def list_playlist(url: str, cookies=()):
    """Danh sách video trong playlist: [{id, title, url}]."""
    r = run_ytdlp([*cookies, "--flat-playlist", "--dump-single-json", "--no-warnings", url])
    d = json.loads(r.stdout)
    out = []
    for e in d.get("entries") or []:
        if e and e.get("id"):
            out.append({"id": e["id"], "title": e.get("title") or e["id"],
                        "url": e.get("url") or f"https://www.youtube.com/watch?v={e['id']}"})
    return out


def download_audio(url: str, video_id: str, cookies=(), audio_dir=AUDIO_DIR):
    """Tải luồng âm thanh nhẹ nhất của MỘT video, trả về đường dẫn file."""
    audio_dir = Path(audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    for old in audio_dir.glob(f"{video_id}.*"):
        old.unlink()
    run_ytdlp([
        *cookies,
        "-f", "ba/b",
        "--no-playlist", "--no-warnings",
        "--sleep-interval", "2", "--max-sleep-interval", "5",
        "-o", str(audio_dir / f"{video_id}.%(ext)s"),
        url,
    ])
    files = [
        p for p in audio_dir.glob(f"{video_id}.*")
        if p.is_file() and p.suffix not in (".part", ".ytdl", ".temp")
    ]
    if not files:
        raise PipelineError("yt-dlp không tải được audio (thử thêm cookies: YT_COOKIES_FILE hoặc YT_COOKIES_BROWSER).")
    return files[0]


def ffprobe_duration(path) -> float:
    r = run_cmd(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                check=False)
    try:
        return float((r.stdout or "").strip().splitlines()[0])
    except (ValueError, IndexError):
        return 0.0


def compress_and_split(src, out_dir, chunk_seconds=CHUNK_SECONDS):
    """Nén về mono 16kHz 48kbps mp3 và cắt thành các đoạn ~chunk_seconds. Trả về [(đường dẫn, thời lượng)]."""
    if not shutil.which("ffmpeg"):
        raise PipelineError("Chưa cài ffmpeg (Ubuntu/WSL: sudo apt install ffmpeg; Windows: winget install ffmpeg).")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("chunk_*.mp3"):
        old.unlink()
    run_cmd(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k",
             "-f", "segment", "-segment_time", str(chunk_seconds), "-reset_timestamps", "1",
             str(out_dir / "chunk_%03d.mp3")])
    chunks = sorted(out_dir.glob("chunk_*.mp3"))
    if not chunks:
        raise PipelineError("ffmpeg không tạo được đoạn audio nào.")
    for c in chunks:
        if c.stat().st_size > MAX_CHUNK_BYTES:
            raise PipelineError(f"{c.name} lớn hơn 20MB; giảm CHUNK_SECONDS.")
    return [(c, ffprobe_duration(c) or float(chunk_seconds)) for c in chunks]


def _atomic_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def raw_cache_path(video_id: str) -> Path:
    return RAW_DIR / f"{video_id}.json"


def load_raw(video_id: str):
    p = raw_cache_path(video_id)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_raw(data: dict) -> Path:
    p = raw_cache_path(data["video_id"])
    _atomic_json(p, data)
    return p
