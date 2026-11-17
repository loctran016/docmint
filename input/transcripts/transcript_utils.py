"""Hàm dùng chung cho cả hai tầng transcript (máy cá nhân và GitHub Actions).

Hai tầng cùng gọi các hàm này để file Markdown đầu ra giống hệt nhau.
"""
import html
import re

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
