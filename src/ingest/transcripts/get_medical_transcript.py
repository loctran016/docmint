# /// script
# requires-python = ">=3.10"
# dependencies = ["yt-dlp", "google-genai", "python-dotenv"]
# ///
import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
"""
Transcript bài giảng YouTube -> Markdown sạch, dùng Groq Whisper (mặc định).

Luồng mặc định (--backend groq):
  yt-dlp tải audio -> ffmpeg nén mono 16kHz 48kbps và cắt đoạn ~15 phút -> Groq Whisper (whisper-large-v3, hết quota thì
  whisper-large-v3-turbo, xoay vòng GROQ_API_KEYS) -> cache thô .cache/transcripts/raw/{video_id}.json
  -> Gemini Flash làm sạch thuật ngữ y khoa, dấu câu, đề mục (build_transcript.py) -> transcripts/<tên video>.md
Cache thô có rồi thì bỏ qua tải audio và STT (trừ khi --upgrade-stt). Từng đoạn audio cũng được cache nên chạy dở
có thể chạy lại tiếp.

Các backend cũ vẫn dùng được:
  --backend subs      tải phụ đề YouTube bằng yt-dlp (không có thì hỏi chuyển sang actions)
  --backend actions   gửi sang GitHub Actions (workflow transcribe.yml) rồi tải kết quả về; --whisper = cờ cũ cùng ý nghĩa

Chạy từ thư mục gốc repo:
    uv run input/transcripts/get_medical_transcript.py --url "https://youtu.be/..." --lang vi
    uv run input/transcripts/get_medical_transcript.py --url "https://www.youtube.com/playlist?list=..." --slides slide.notebooklm.md
    uv run input/transcripts/get_medical_transcript.py --url "..." --upgrade-stt      # chép lại audio, bỏ cache cũ
    uv run input/transcripts/get_medical_transcript.py --url "..." --no-clean         # chỉ STT, không gọi Gemini

Biến môi trường (.env): GROQ_API_KEYS, GROQ_STT_MODELS, GEMINI_API_KEYS, TRANSCRIPT_MODEL, REQUEST_DELAY,
YT_COOKIES_FILE hoặc YT_COOKIES_BROWSER (video Unlisted hoặc YouTube chặn IP).
"""
import argparse
import glob
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    from . import transcript_utils as tu
    from .transcript_utils import PipelineError, clean_vtt_to_text, safe_filename, write_markdown
except ImportError:
    import transcript_utils as tu
    from transcript_utils import PipelineError, clean_vtt_to_text, safe_filename, write_markdown

from src.core import common
from src.core.prompts import render_prompt

WORKFLOW_FILE = "transcribe.yml"
ARTIFACT_NAME = "medical-transcript"

# Mồi ngữ cảnh cho Whisper (tối đa vài trăm ký tự)
STT_PROMPT_VI = render_prompt("whisper_context_vi")
STT_PROMPT_EN = render_prompt("whisper_context_en")


# Gọi yt-dlp bằng chính Python đang chạy: không phụ thuộc PATH (uv run, Windows, WSL đều được).
YTDLP = tu.YTDLP


def run_text(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def get_title(youtube_url):
    result = run_text([*YTDLP, "--skip-download", "--print", "title", youtube_url])
    lines = result.stdout.strip().splitlines()
    return lines[0] if lines else "Medical_Lecture"


def fetch_local_subs(youtube_url, lang, title, out_folder):
    for old in glob.glob("temp_sub*.vtt"):
        os.remove(old)

    run_text([
        *YTDLP, "--write-sub", "--write-auto-sub",
        "--sub-lang", lang, "--sub-format", "vtt",
        "--skip-download", "-o", "temp_sub", youtube_url,
    ])

    vtt_files = glob.glob("temp_sub*.vtt")
    if not vtt_files:
        return None

    target = next((f for f in vtt_files if f".{lang}." in f), vtt_files[0])
    sentences = clean_vtt_to_text(target)

    output_path = os.path.join(out_folder, f"{safe_filename(title)}.md")
    write_markdown(
        output_path, title, youtube_url,
        "Phụ đề YouTube (auto-generated hoặc do người đăng tải)", sentences,
    )

    for f in vtt_files:
        os.remove(f)
    return output_path


def list_run_ids():
    """ID các lần chạy gần đây của workflow (dùng để nhận ra lần chạy vừa kích hoạt)."""
    out = run_text([
        "gh", "run", "list", "--workflow", WORKFLOW_FILE,
        "--event", "workflow_dispatch", "--limit", "20",
        "--json", "databaseId", "-q", ".[].databaseId",
    ]).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def run_github_whisper(youtube_url, lang, out_folder):
    if not shutil.which("gh"):
        print("Chưa cài GitHub CLI (gh). Cài và chạy 'gh auth login' trước.")
        return None

    before = list_run_ids()
    print("Gửi video sang GitHub Actions (Faster-Whisper)...")
    trigger = run_text([
        "gh", "workflow", "run", WORKFLOW_FILE,
        "-f", f"youtube_url={youtube_url}",
        "-f", f"lang={lang}",
        "-f", "force_whisper=true",
    ])
    if trigger.returncode != 0:
        print("Không kích hoạt được workflow:", trigger.stderr)
        return None

    # Chờ GitHub tạo run mới: lấy run có ID chưa từng thấy trước khi kích hoạt
    run_id = ""
    for _ in range(12):
        time.sleep(5)
        new_ids = list_run_ids() - before
        if new_ids:
            run_id = max(new_ids, key=int)
            break
    if not run_id:
        print("Không tìm thấy lần chạy vừa tạo. Xem tab Actions trên GitHub.")
        return None

    print(f"Đang chạy (run {run_id}), chờ hoàn tất (có thể vài chục phút)...")
    watch = subprocess.run(["gh", "run", "watch", run_id, "--exit-status"])
    if watch.returncode != 0:
        print(f"Workflow lỗi. Xem log: gh run view {run_id} --log-failed")
        return None

    dl = subprocess.run(["gh", "run", "download", run_id, "-n", ARTIFACT_NAME, "-D", out_folder])
    if dl.returncode != 0:
        print("Tải kết quả về thất bại.")
        return None
    return out_folder



# ---------------------------------------------------------------------------
# Luồng mới: Groq Whisper + Gemini
# ---------------------------------------------------------------------------
def load_terms(limit=80):
    """Vài thuật ngữ từ medical_terms.txt (nếu có) để mồi cho Whisper."""
    try:
        terms = []
        terms_path = common.CONFIG_DIR / common.MEDICAL_TERMS_FILE.name
        if not terms_path.exists():
            terms_path = common.ROOT_DIR / common.MEDICAL_TERMS_FILE.name
        for line in terms_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.split("#", 1)[0].strip()
            terms += line.split()
        return terms[:limit]
    except OSError:
        return []


def stt_prompt(lang):
    base = STT_PROMPT_VI if lang == "vi" else STT_PROMPT_EN
    terms = load_terms()
    return (base + " Thuật ngữ: " + ", ".join(terms))[:900] if terms else base


def prepare_chunks(meta, cookies, upgrade):
    """Trả về [(đường dẫn đoạn mp3, thời lượng)]: dùng lại đoạn đã cắt nếu còn, không thì tải audio và cắt mới."""
    vid = meta["id"]
    audio_dir = tu.AUDIO_DIR / vid
    manifest = tu.CHUNK_DIR / vid / "manifest.json"
    if not upgrade and manifest.exists():
        try:
            info = json.loads(manifest.read_text(encoding="utf-8"))
            chunks = [(audio_dir / n, d) for n, d in info["chunks"]]
            if chunks and all(p.exists() for p, _ in chunks):
                return chunks
        except (OSError, ValueError, KeyError):
            pass
    if meta.get("audio_path"):
        src = Path(meta["audio_path"])
    else:
        print("  Tải audio bằng yt-dlp...")
        src = tu.download_audio(meta["url"], vid, cookies, tu.AUDIO_DIR / "_dl")
    print("  Nén và cắt audio bằng ffmpeg...")
    chunks = tu.compress_and_split(src, audio_dir)
    if not meta.get("audio_path"):
        src.unlink(missing_ok=True)
    tu._atomic_json(manifest, {"chunks": [[p.name, d] for p, d in chunks]})
    return chunks


def stt_groq(meta, args, stt, cookies):
    """Chép audio của một video bằng Groq, lưu cache thô. Trả về dict cache thô."""
    vid = meta["id"]
    chunk_dir = tu.CHUNK_DIR / vid
    if args.upgrade_stt and chunk_dir.exists():
        shutil.rmtree(chunk_dir)
    chunks = prepare_chunks(meta, cookies, args.upgrade_stt)
    prompt = stt_prompt(args.lang)
    segments, texts, models, offset = [], [], [], 0.0
    for i, (path, dur) in enumerate(chunks):
        cache = chunk_dir / f"chunk_{i:03d}.json"
        data = None
        if cache.exists():
            try:
                data = json.loads(cache.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = None
        if data is None:
            print(f"  Groq Whisper: đoạn {i + 1}/{len(chunks)} ({dur / 60:.1f} phút)...")
            data = stt.transcribe_file(path, language=args.lang, prompt=prompt, max_wait=args.max_wait)
            tu._atomic_json(cache, data)
        else:
            print(f"  Đoạn {i + 1}/{len(chunks)}: dùng lại kết quả đã cache.")
        for s in data["segments"]:
            segments.append({"start": round(s["start"] + offset, 2), "end": round(s["end"] + offset, 2), "text": s["text"]})
        texts.append(data["text"])
        models.append(data["model"])
        offset += dur
    raw = {
        "video_id": vid, "title": meta["title"], "url": meta["url"],
        "duration": meta["duration"] or offset, "stt_provider": "groq_whisper",
        "model": models[0] if len(set(models)) == 1 else "+".join(sorted(set(models))),
        "language": args.lang, "raw_text": " ".join(texts), "segments": segments,
    }
    tu.save_raw(raw)
    shutil.rmtree(tu.AUDIO_DIR / vid, ignore_errors=True)  # xong rồi: bỏ audio, giữ cache thô
    return raw


def process_video(meta, args, stt, cleaner, cookies, slides_text):
    import build_transcript as bt
    out_dir = Path(args.out)
    target = out_dir / f"{safe_filename(meta['title'])}.md"
    if target.exists() and not args.force and not args.upgrade_stt:
        print(f"  Đã có {target}, bỏ qua (dùng --force để làm lại).")
        return target
    raw = None if args.upgrade_stt else tu.load_raw(meta["id"])
    if raw is not None:
        print(f"  Dùng cache thô ({raw.get('stt_provider')}, {raw.get('model')}), bỏ qua tải audio và STT.")
    else:
        raw = stt_groq(meta, args, stt, cookies)
    body, notes = bt.clean_raw(raw, cleaner, slides_text, log=print)
    return bt.write_clean_markdown(out_dir, raw, body, notes, cleaner is not None)


def run_groq_backend(args):
    try:
        from . import groq_stt
    except ImportError:
        import groq_stt
    import build_transcript as bt
    keys = groq_stt.parse_list(os.environ.get("GROQ_API_KEYS"))
    if not keys:
        sys.exit("Chưa có GROQ_API_KEYS. Tạo key miễn phí ở https://console.groq.com/keys rồi ghi vào .env "
                 "(GROQ_API_KEYS=key1,key2), hoặc dùng --backend subs.")
    models = groq_stt.parse_list(os.environ.get("GROQ_STT_MODELS")) or None
    stt = groq_stt.GroqSTT(keys, models, log=print)
    cookies = tu.cookie_args(args.cookies, args.browser)
    cleaner = None if args.no_clean else bt.make_cleaner(log=print)
    if cleaner is None and not args.no_clean:
        print("Chưa có GEMINI_API_KEYS/GEMINI_API_KEY: chỉ xuất bản thô (chưa làm sạch).")
    slides_text = bt.load_slides(args.slides)

    try:
        if args.audio:
            audio_path = Path(args.audio)
            if not audio_path.is_file():
                sys.exit(f"Không tìm thấy file audio: {audio_path}")
            videos = [{
                "id": safe_filename(audio_path.stem),
                "title": args.title or audio_path.stem,
                "duration": tu.ffprobe_duration(audio_path),
                "url": f"file://{audio_path.resolve()}",
                "audio_path": str(audio_path),
            }]
        elif tu.is_playlist_url(args.url):
            videos = tu.list_playlist(args.url, cookies)
            print(f"Playlist có {len(videos)} video.")
            if not videos:
                sys.exit("Không đọc được video nào trong playlist.")
        else:
            videos = [tu.fetch_metadata(args.url, cookies)]
    except PipelineError as e:
        sys.exit(f"Lỗi yt-dlp: {e}\nGợi ý: video Unlisted hoặc YouTube chặn IP thì đặt YT_COOKIES_BROWSER=chrome "
                 "(hoặc YT_COOKIES_FILE=cookies.txt) trong .env.")

    done, failed = [], []
    for n, v in enumerate(videos, 1):
        print(f"\n[{n}/{len(videos)}] {v['title']}")
        try:
            meta = v if "duration" in v else tu.fetch_metadata(v["url"], cookies)
            done.append(process_video(meta, args, stt, cleaner, cookies, slides_text))
        except (PipelineError, groq_stt.GroqSTTError) as e:
            print(f"  ✘ Lỗi: {e}")
            failed.append(v["title"])
        except KeyboardInterrupt:
            print("\nĐã dừng. Các đoạn đã xong được giữ trong .cache, chạy lại để làm tiếp.")
            break
    print(f"\nXong: {len(done)} file trong {args.out}/" + (f" | Lỗi: {len(failed)}" if failed else ""))
    for f in failed:
        print(f"  ✘ {f}")
    return 1 if failed else 0


def parse_args():
    ap = argparse.ArgumentParser(description="Transcript video YouTube -> Markdown (Groq Whisper + Gemini)")
    ap.add_argument("--url", help="link video hoặc playlist (bỏ trống thì hỏi)")
    ap.add_argument("--audio", help="file audio đã tải sẵn (dùng thay cho --url)")
    ap.add_argument("--title", help="tiêu đề dùng cho file audio local")
    ap.add_argument("--lang", help="vi hoặc en (bỏ trống thì hỏi, mặc định vi)")
    ap.add_argument("--out", default=str(common.TRANSCRIPTS_DIR),
                    help="thư mục kết quả (mặc định workspace/transcripts)")
    ap.add_argument("--backend", choices=["groq", "subs", "actions"], default="groq",
                    help="groq (mặc định), subs (phụ đề yt-dlp, cũ) hoặc actions (GitHub Actions, cũ)")
    ap.add_argument("--whisper", action="store_true", help="cờ cũ, tương đương --backend actions")
    ap.add_argument("--yes", action="store_true",
                    help="(backend subs) không có phụ đề thì tự chuyển sang Actions, không hỏi")
    ap.add_argument("--upgrade-stt", action="store_true", help="bỏ cache STT cũ và chép lại audio")
    ap.add_argument("--no-clean", action="store_true", help="không gọi Gemini, chỉ xuất bản thô")
    ap.add_argument("--force", action="store_true", help="làm lại kể cả khi file .md đã có")
    ap.add_argument("--slides", help="file Markdown slide (*.notebooklm.md) để Gemini đối chiếu thuật ngữ")
    ap.add_argument("--cookies", help="file cookies.txt cho yt-dlp (hoặc biến YT_COOKIES_FILE)")
    ap.add_argument("--browser", help="lấy cookie từ trình duyệt, ví dụ chrome, edge (hoặc biến YT_COOKIES_BROWSER)")
    ap.add_argument("--max-wait", type=float, default=1800.0,
                    help="tổng giây tối đa chờ Groq hết giới hạn cho mỗi đoạn audio (mặc định 1800)")
    return ap.parse_args()


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    args = parse_args()
    if args.whisper:
        args.backend = "actions"
    if not args.audio and importlib.util.find_spec("yt_dlp") is None:
        sys.exit("Không thấy yt-dlp. Chạy bằng 'uv run ...' (tự cài) hoặc: pip install yt-dlp")

    os.makedirs(args.out, exist_ok=True)
    url = args.url or ("" if args.audio else input("Nhập link video hoặc playlist YouTube: ").strip())
    args.lang = args.lang or input("Ngôn ngữ chính của video (vi / en) [mặc định: vi]: ").strip() or "vi"
    if not url and not args.audio:
        sys.exit("Chưa có link video.")
    args.url = url

    if args.backend == "groq":
        sys.exit(run_groq_backend(args))

    if args.backend == "subs":
        title = get_title(url)
        result = fetch_local_subs(url, args.lang, title, args.out)
        if result:
            print(f"Hoàn tất (từ phụ đề)! File: {result}")
            return
        print("Video không có phụ đề sẵn.")
        go = args.yes or input("Chuyển sang GitHub Actions? (y/n) [y]: ").strip().lower() in ("", "y")
        if not go:
            return
    folder = run_github_whisper(url, args.lang, args.out)
    if folder:
        print(f"Hoàn tất (từ GitHub Actions)! File nằm trong: {folder}/")


if __name__ == "__main__":
    main()
