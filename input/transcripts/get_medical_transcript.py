# /// script
# requires-python = ">=3.10"
# dependencies = ["yt-dlp"]
# ///
"""
Lấy transcript bài giảng YouTube thành Markdown.

Tầng 1 (máy cá nhân): tải phụ đề bằng yt-dlp, làm sạch, ghi ra transcripts/<tên video>.md.
Tầng 2 (GitHub Actions + Faster-Whisper): chỉ khi video không có phụ đề. Cần GitHub CLI (gh)
đã đăng nhập (gh auth login) và workflow .github/workflows/transcribe.yml đã được đẩy lên repo.

Chạy từ thư mục gốc repo:
    uv run input/transcripts/get_medical_transcript.py
    uv run input/transcripts/get_medical_transcript.py --url "https://youtu.be/..." --lang vi --yes
    uv run input/transcripts/get_medical_transcript.py --url "..." --whisper    # bỏ qua phụ đề, dùng Whisper
"""
import argparse
import glob
import importlib.util
import os
import shutil
import subprocess
import sys
import time

from transcript_utils import clean_vtt_to_text, safe_filename, write_markdown

WORKFLOW_FILE = "transcribe.yml"
ARTIFACT_NAME = "medical-transcript"


# Gọi yt-dlp bằng chính Python đang chạy: không phụ thuộc PATH (uv run, Windows, WSL đều được).
YTDLP = [sys.executable, "-m", "yt_dlp"]


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


def parse_args():
    ap = argparse.ArgumentParser(description="Transcript video YouTube -> Markdown")
    ap.add_argument("--url", help="link video (bỏ trống thì hỏi)")
    ap.add_argument("--lang", help="vi hoặc en (bỏ trống thì hỏi, mặc định vi)")
    ap.add_argument("--out", default="transcripts", help="thư mục kết quả (mặc định transcripts)")
    ap.add_argument("--yes", action="store_true",
                    help="không có phụ đề thì tự chuyển sang Actions + Whisper, không hỏi")
    ap.add_argument("--whisper", action="store_true",
                    help="bỏ qua phụ đề, dùng thẳng GitHub Actions + Whisper")
    return ap.parse_args()


def main():
    args = parse_args()
    if importlib.util.find_spec("yt_dlp") is None:
        sys.exit("Không thấy yt-dlp. Chạy bằng 'uv run ...' (tự cài) hoặc: pip install yt-dlp")

    os.makedirs(args.out, exist_ok=True)
    url = args.url or input("Nhập link video YouTube: ").strip()
    lang = args.lang or input("Ngôn ngữ chính của video (vi / en) [mặc định: vi]: ").strip() or "vi"
    if not url:
        sys.exit("Chưa có link video.")

    if not args.whisper:
        title = get_title(url)
        result = fetch_local_subs(url, lang, title, args.out)
        if result:
            print(f"Hoàn tất (từ phụ đề)! File: {result}")
            return
        print("Video không có phụ đề sẵn.")

    go = args.whisper or args.yes
    if not go:
        go = input("Chuyển sang GitHub Actions + Whisper? (y/n) [y]: ").strip().lower() in ("", "y")
    if go:
        folder = run_github_whisper(url, lang, args.out)
        if folder:
            print(f"Hoàn tất (từ Whisper)! File nằm trong: {folder}/")


if __name__ == "__main__":
    main()
