"""Bước 2 của pipeline transcript: làm sạch bản ghi thô bằng Gemini Flash.

Mới (chạy cả trên máy và trên Actions):
    python input/transcripts/build_transcript.py clean VIDEO_ID [--slides slide.notebooklm.md] [--out transcripts]
  Đọc .cache/transcripts/raw/{video_id}.json (do get_medical_transcript.py tạo bằng Groq Whisper), nhờ Gemini sửa thuật ngữ
  y khoa Việt - Anh - Latin, thêm dấu câu, bỏ từ đệm, chia đề mục; GIỮ NGUYÊN 100% nội dung, không tóm tắt.
  Gemini lỗi hoặc hết quota thì đoạn đó giữ bản thô (có ghi chú), không mất nội dung.

Bản cũ (giữ nguyên, dùng với --backend subs và workflow Faster-Whisper cũ):
    python input/transcripts/build_transcript.py subs      # từ phụ đề .vtt đã tải
    python input/transcripts/build_transcript.py whisper   # từ audio.* bằng Faster-Whisper
  Biến môi trường: VIDEO_TITLE, VIDEO_URL, VIDEO_LANG. Kết quả: transcript_out/<tên video>.md

Biến môi trường (clean): GEMINI_API_KEYS hoặc GEMINI_API_KEY; TRANSCRIPT_MODEL hoặc GEMINI_MODEL (nhiều model cách nhau
dấu phẩy); REQUEST_DELAY (giây nghỉ giữa hai lần gọi).
"""
from __future__ import annotations
import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))

import argparse
import glob
import os
import re
import sys
import time
from pathlib import Path
from src.core.prompts import render_prompt

try:
    from .transcript_utils import clean_vtt_to_text, load_raw, safe_filename, write_markdown
except ImportError:
    from transcript_utils import clean_vtt_to_text, load_raw, safe_filename, write_markdown

DEFAULT_CLEAN_MODELS = "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite"
WORDS_PER_CHUNK = 2200  # số từ thô mỗi lần gọi Gemini
SLIDE_CONTEXT_CHARS = 12000

CLEAN_PROMPT = render_prompt("transcript_clean")


# ---------------------------------------------------------------------------
# Gemini (xoay vòng key x model)
# ---------------------------------------------------------------------------
def needs_beta(model: str) -> bool:
    m = model.lower()
    return "preview" in m or m.startswith("gemma") or m in ("gemini-3-flash", "gemini-2.5-flash-lite")


def parse_list(raw) -> list[str]:
    out: list[str] = []
    for k in re.split(r"[,;\s]+", raw or ""):
        k = k.strip().strip("\"'")
        if k and k not in out:
            out.append(k)
    return out


class GeminiCleaner:
    def __init__(self, keys, models, delay=6.0, timeout=180.0, sleep=time.sleep, log=print):
        self.keys = list(keys)
        self.models = list(models)
        self.delay = delay
        self.timeout = timeout
        self._sleep = sleep
        self._log = log
        self._clients = {}
        self.bad_keys: set[str] = set()
        self.bad_models: set[str] = set()
        self.start = 0

    def _client(self, key, model):
        from google import genai
        from google.genai import types
        ver = "v1beta" if needs_beta(model) else "v1"
        if (key, ver) not in self._clients:
            self._clients[(key, ver)] = genai.Client(
                api_key=key, http_options=types.HttpOptions(timeout=int(self.timeout * 1000), api_version=ver))
        return self._clients[(key, ver)]

    def _call(self, key, model, prompt):
        from google.genai import types
        resp = self._client(key, model).models.generate_content(
            model=model, contents=[prompt],
            config=types.GenerateContentConfig(temperature=0.2, safety_settings=[
                types.SafetySetting(category=c, threshold="BLOCK_NONE") for c in (
                    "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")]))
        text, finish = "", ""
        try:
            c = (resp.candidates or [None])[0]
            finish = str(getattr(c, "finish_reason", "") or "")
            parts = getattr(getattr(c, "content", None), "parts", None) or []
            text = "".join((p.text or "") for p in parts if getattr(p, "text", None) and not getattr(p, "thought", False))
        except Exception:  # noqa: BLE001
            pass
        return text.strip(), finish

    def clean(self, prompt: str) -> tuple[str | None, str]:
        """Trả về (văn bản đã làm sạch hoặc None, ghi chú). Gọi tối đa 4 vòng qua mọi cặp (key, model)."""
        note = "không có cặp key/model nào dùng được"
        for round_no in range(4):
            pairs = [(k, m) for m in self.models for k in self.keys
                     if k not in self.bad_keys and m not in self.bad_models]
            if not pairs:
                return None, note
            for i in range(len(pairs)):
                key, model = pairs[(self.start + i) % len(pairs)]
                try:
                    text, finish = self._call(key, model, prompt)
                except Exception as e:  # noqa: BLE001
                    code = getattr(e, "code", None)
                    msg = re.sub(r"\s+", " ", str(e))[:140]
                    low = msg.lower()
                    if code in (401, 403) or "api key" in low:
                        self.bad_keys.add(key)
                        note = f"key bị từ chối: {msg}"
                    elif code == 404:
                        self.bad_models.add(model)
                        note = f"model {model} không dùng được: {msg}"
                    else:  # 429, 5xx, timeout, 400...
                        note = f"{model}: {msg}"
                    continue
                if text and "MAX_TOKENS" not in finish.upper():
                    self.start = (self.start + i) % len(pairs)
                    self._sleep(self.delay)
                    return text, ""
                if "RECITATION" in finish.upper() or not text:
                    return None, f"{model} trả về rỗng ({finish or 'rỗng'})"
                note = f"{model}: đầu ra bị cắt (MAX_TOKENS)"
            if round_no < 3:
                self._log(f"    ⏳ Gemini chưa dùng được ({note}); chờ {20 * (round_no + 1)}s rồi thử lại")
                self._sleep(20 * (round_no + 1))
        return None, note


# ---------------------------------------------------------------------------
# Làm sạch một bản ghi thô
# ---------------------------------------------------------------------------
def split_chunks(segments, words_per_chunk=WORDS_PER_CHUNK):
    """Gộp các segment liên tiếp thành các khối ~words_per_chunk từ (không cắt giữa segment)."""
    chunks, cur, n = [], [], 0
    for s in segments:
        w = len(s["text"].split())
        if cur and n + w > words_per_chunk:
            chunks.append(" ".join(cur))
            cur, n = [], 0
        cur.append(s["text"])
        n += w
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def load_slides(path, limit=SLIDE_CONTEXT_CHARS) -> str:
    if not path:
        return ""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""
    return text[:limit]


def build_prompt(chunk: str, title: str, slides: str, prev_tail: str) -> str:
    parts = [CLEAN_PROMPT, f"TIÊU ĐỀ BÀI: {title}"]
    if slides:
        parts.append("SLIDE THAM CHIẾU (chỉ để đối chiếu chính tả thuật ngữ, KHÔNG chép nội dung slide vào kết quả):\n" + slides)
    if prev_tail:
        parts.append("ĐOẠN TRƯỚC KẾT THÚC BẰNG (để nối mạch, KHÔNG lặp lại):\n" + prev_tail)
    parts.append("BẢN GHI THÔ CẦN XỬ LÝ:\n" + chunk)
    return "\n\n".join(parts)


def clean_raw(raw: dict, cleaner: GeminiCleaner | None, slides: str = "", log=print) -> tuple[str, list[str]]:
    """Trả về (nội dung Markdown, danh sách ghi chú). Đoạn Gemini không xử lý được giữ nguyên bản thô."""
    segments = raw.get("segments") or []
    if not segments and raw.get("raw_text"):
        segments = [{"start": 0, "end": 0, "text": raw["raw_text"]}]
    chunks = split_chunks(segments)
    out: list[str] = []
    notes: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        text = None
        if cleaner is not None:
            tail = out[-1][-300:] if out else ""
            log(f"  Gemini làm sạch đoạn {i}/{len(chunks)} ({len(chunk.split())} từ)...")
            text, why = cleaner.clean(build_prompt(chunk, raw.get("title", ""), slides, tail))
            if text is None:
                notes.append(f"Đoạn {i}/{len(chunks)} giữ bản thô: {why}")
                log(f"    ⚠ giữ bản thô: {why}")
        if text is None:
            text = chunk
        out.append(text)
    return "\n\n".join(out).strip(), notes


def write_clean_markdown(out_dir, raw: dict, body: str, notes: list[str], cleaned: bool) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe_filename(raw.get('title') or raw.get('video_id') or 'Medical_Lecture')}.md"
    label = f"Groq {raw.get('model', 'Whisper')}" + (" + Gemini làm sạch thuật ngữ" if cleaned else " (thô, chưa làm sạch)")
    lines = [f"# {raw.get('title') or 'Medical_Lecture'}", f"- **Nguồn:** {raw.get('url', '')}",
             f"- **Loại bản ghi:** {label}"]
    if cleaned:
        lines.append("- **Lưu ý:** Bản ghi tự động đã được sửa thuật ngữ và dấu câu, nội dung giữ đầy đủ; chỗ có [?] là chưa chắc chắn.")
    else:
        lines.append("- **Lưu ý:** Bản ghi thô tự động, có thể thiếu dấu câu hoặc sai thuật ngữ.")
    for n in notes:
        lines.append(f"- **Ghi chú:** {n}")
    path.write_text("\n".join(lines) + "\n\n---\n\n" + body + "\n", encoding="utf-8")
    return path


def make_cleaner(log=print) -> GeminiCleaner | None:
    keys = parse_list(os.environ.get("GEMINI_API_KEYS")) or parse_list(os.environ.get("GEMINI_API_KEY"))
    if not keys:
        return None
    models = parse_list(os.environ.get("TRANSCRIPT_MODEL") or os.environ.get("GEMINI_MODEL") or DEFAULT_CLEAN_MODELS)
    try:
        delay = float(os.environ.get("REQUEST_DELAY") or 6)
    except ValueError:
        delay = 6.0
    return GeminiCleaner(keys, models, delay=delay, log=log)


# ---------------------------------------------------------------------------
# Bản cũ (phụ đề .vtt / Faster-Whisper trên Actions) giữ nguyên
# ---------------------------------------------------------------------------
def legacy_main(mode):
    title = os.environ.get("VIDEO_TITLE") or "Medical_Lecture"
    url = os.environ.get("VIDEO_URL", "")
    lang = os.environ.get("VIDEO_LANG", "vi")

    os.makedirs("transcript_out", exist_ok=True)
    output_path = os.path.join("transcript_out", f"{safe_filename(title)}.md")

    if mode == "subs":
        files = glob.glob("sub*.vtt")
        target = next((f for f in files if f".{lang}." in f), files[0])
        sentences = clean_vtt_to_text(target)
        source_label = "Phụ đề YouTube (auto-generated hoặc do người đăng tải)"
    else:
        from faster_whisper import BatchedInferencePipeline, WhisperModel

        audio = glob.glob("audio.*")[0]
        prompt = render_prompt(
            "whisper_initial_vi" if lang == "vi" else "whisper_initial_en"
        )
        model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8", cpu_threads=4)
        batched = BatchedInferencePipeline(model=model)
        segments, _ = batched.transcribe(audio, batch_size=8, language=lang, initial_prompt=prompt, vad_filter=True)
        sentences = [s.text.strip() for s in segments if s.text.strip()]
        source_label = "Faster-Whisper large-v3-turbo"

    write_markdown(output_path, title, url, source_label, sentences)
    print(f"Đã tạo {output_path}")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("subs", "whisper"):
        legacy_main(argv[0])
        return 0
    ap = argparse.ArgumentParser(description="Làm sạch bản ghi thô (Groq Whisper) bằng Gemini")
    ap.add_argument("mode", choices=["clean"])
    ap.add_argument("video_id", help="ID video (file .cache/transcripts/raw/<id>.json)")
    ap.add_argument("--slides", help="file Markdown slide (*.notebooklm.md) để đối chiếu thuật ngữ")
    ap.add_argument("--out", default=str(common.TRANSCRIPTS_DIR))
    ap.add_argument("--no-clean", action="store_true", help="không gọi Gemini, chỉ xuất bản thô")
    args = ap.parse_args(argv)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    raw = load_raw(args.video_id)
    if raw is None:
        print(f"Không thấy cache thô cho {args.video_id}. Chạy get_medical_transcript.py trước.")
        return 2
    cleaner = None if args.no_clean else make_cleaner()
    if cleaner is None and not args.no_clean:
        print("Chưa có GEMINI_API_KEYS/GEMINI_API_KEY: xuất bản thô.")
    body, notes = clean_raw(raw, cleaner, load_slides(args.slides))
    path = write_clean_markdown(args.out, raw, body, notes, cleaner is not None)
    print(f"Đã tạo {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
