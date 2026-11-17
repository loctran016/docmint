"""Chạy trên GitHub Actions (xem .github/workflows/transcribe.yml).

    python input/transcripts/build_transcript.py subs      # từ phụ đề .vtt đã tải
    python input/transcripts/build_transcript.py whisper   # từ audio.* bằng Faster-Whisper

Biến môi trường: VIDEO_TITLE, VIDEO_URL, VIDEO_LANG (vi hoặc en).
Kết quả: transcript_out/<tên video>.md
"""
import glob
import os
import sys

from transcript_utils import clean_vtt_to_text, safe_filename, write_markdown

mode = sys.argv[1]  # "subs" hoặc "whisper"
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
    prompt = (
        "Bài giảng y khoa, thuật ngữ y học, lâm sàng, cận lâm sàng, chẩn đoán, điều trị."
        if lang == "vi"
        else "Medical lecture, clinical medicine, pathology, pharmacology, diagnosis, treatment."
    )
    model = WhisperModel(
        "deepdml/faster-whisper-large-v3-turbo-ct2",
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
    )
    batched = BatchedInferencePipeline(model=model)
    segments, _ = batched.transcribe(
        audio,
        batch_size=8,
        language=lang,
        initial_prompt=prompt,
        vad_filter=True,
    )
    sentences = [s.text.strip() for s in segments if s.text.strip()]
    source_label = "Faster-Whisper large-v3-turbo"

write_markdown(output_path, title, url, source_label, sentences)
print(f"Đã tạo {output_path}")
