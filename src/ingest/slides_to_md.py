import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf", "pillow", "google-genai", "python-pptx", "python-dotenv"]
# ///
"""
Slide (.pptx / .ppt / .pdf) -> Markdown cho Obsidian + Markdown thuần chữ cho NotebookLM.

Mỗi slide được render thành ảnh nguyên trang, gửi Gemini để chép chữ và mô tả cấu trúc sơ đồ
(bị cấm thêm kiến thức ngoài slide). Ghi chú giảng viên lấy từ python-pptx (chỉ với .pptx).
Tiến độ lưu theo từng slide (.cache), chạy lại sẽ làm tiếp.

Dùng (từ thư mục gốc repo):
    uv run input/slides/slides_to_md.py "Sinh ly gan.pptx"
    uv run input/slides/slides_to_md.py slide.pdf -o slides_out --delay 5 --img-style wiki

Cần:
    sudo apt install libreoffice-impress     # chỉ khi đầu vào là .pptx/.ppt
    GEMINI_API_KEY trong file .env (cùng thư mục gốc) hoặc biến môi trường

Kết quả: slides_out/<tên>/<tên>.md (có ảnh, cho Obsidian) và <tên>.notebooklm.md (chỉ chữ).
"""
import argparse
import gc
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fitz  # PyMuPDF
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

try:  # dùng lại hàm đổi đường dẫn C:\... của toolkit nếu có
    from src.core import common
except Exception:  # noqa: BLE001
    common = None

load_dotenv(ROOT / ".env")

# Nhiều model cách nhau dấu phẩy: model không tồn tại hoặc hết quota ngày thì chuyển sang model kế.
# Cần khớp với process_book.py; kiểm tra tên bằng: uv run process_book.py --list-models
DEFAULT_MODEL = "gemini-3.8-flash,gemini-3.6-flash"
DPI = 150
MAX_RETRIES = 6

PROMPT = """Đây là một slide bài giảng y khoa (tiếng Việt). Hãy chuyển slide thành văn bản \
để một AI khác đọc. TUYỆT ĐỐI KHÔNG thêm bất kỳ kiến thức nào ngoài những gì có trên slide.

Quy tắc:
1. Chép lại chính xác toàn bộ chữ trên slide (giữ nguyên thuật ngữ, viết tắt, số liệu, đơn vị, dấu tiếng Việt).
2. Nếu có sơ đồ, quy trình, biểu đồ: mô tả cấu trúc bằng chữ gồm các thành phần, nhãn và quan hệ giữa chúng. \
Dùng danh sách lồng nhau, dùng mũi tên `-->` để thể hiện chiều (ví dụ: `A --> B --> C`).
3. Nếu có bảng: dùng bảng markdown.
4. Với hình giải phẫu, mô học, hình minh hoạ: chỉ nêu hình thể hiện gì và các nhãn có trên hình. \
Không suy diễn, không giải thích thêm.
5. Chữ không đọc rõ thì ghi [?], không đoán.
6. Không viết lời dẫn kiểu "Slide này nói về...".

Trả về JSON đúng dạng: {"title": "tiêu đề slide (để rỗng nếu không có)", "content": "nội dung markdown theo các quy tắc trên"}"""


def to_path(raw):
    return Path(common.to_wsl_path(raw)) if common is not None else Path(raw)


def parse_json(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        data = json.loads(text)
        return {
            "title": str(data.get("title", "")).strip(),
            "content": str(data.get("content", "")).strip(),
        }
    except Exception:  # noqa: BLE001
        return {"title": "", "content": text}


class Describer:
    """Gọi Gemini cho từng slide; nhớ model đang dùng giữa các slide."""

    def __init__(self, client, models):
        self.client = client
        self.models = models
        self.idx = 0

    def describe(self, img_bytes, hint):
        contents = [
            types.Part.from_bytes(data=img_bytes, mime_type="image/webp"),
            PROMPT + hint,
        ]
        attempt = 0
        delay = 10
        while self.idx < len(self.models):
            model = self.models[self.idx]
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                return parse_json(resp.text)
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                low = msg.lower()
                if "404" in msg or "not found" in low or "not_found" in low:
                    print(f"   Model '{model}' không dùng được với key này, thử model kế...")
                    self.idx += 1
                    attempt = 0
                    continue
                if re.search(r"per[\s_]?day|daily", low):
                    print(f"   Model '{model}' hết quota ngày, thử model kế...")
                    self.idx += 1
                    attempt = 0
                    continue
                if any(k in msg for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")):
                    attempt += 1
                    if attempt > MAX_RETRIES:
                        raise RuntimeError(
                            "Gemini lỗi liên tục, thử lại sau (checkpoint đã lưu, chạy lại sẽ tiếp tục).")
                    print(f"   Bị giới hạn/quá tải (lần {attempt}/{MAX_RETRIES}), chờ {delay}s...")
                    time.sleep(delay)
                    delay = min(delay * 2, 120)
                    continue
                raise
        raise RuntimeError(
            "Không còn model nào dùng được. Kiểm tra tên model (uv run process_book.py --list-models) "
            "hoặc đợi quota reset (checkpoint đã lưu).")


def pptx_to_pdf(path, tmpdir):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("Thiếu LibreOffice. Cài: sudo apt install libreoffice-impress")
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmpdir, str(path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return Path(tmpdir) / (path.stem + ".pdf")


def pptx_notes(path):
    """Ghi chú giảng viên theo thứ tự slide (bỏ slide ẩn vì LibreOffice cũng bỏ qua)."""
    from pptx import Presentation

    notes = []
    for slide in Presentation(str(path)).slides:
        if slide._element.get("show") == "0":
            continue
        text = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
            text = slide.notes_slide.notes_text_frame.text.strip()
        notes.append(text)
    return notes


def image_line(img_name, style):
    if style == "wiki":
        return f"![[{img_name}]]"
    return f"![{img_name}]()"  # kiểu đang dùng cho site notes


def build_outputs(out_dir, stem, src_name, total, img_style):
    cache = out_dir / ".cache"
    slides = []
    for n in range(1, total + 1):
        f = cache / f"{n:03d}.json"
        if f.exists():
            slides.append((n, json.loads(f.read_text(encoding="utf-8"))))

    head_obs = f"# {stem}\n- **Nguồn:** {src_name}\n- **Số slide:** {total}\n\n---\n\n"
    head_nlm = (
        f"# {stem} (slide bài giảng)\n- **Nguồn:** {src_name}\n"
        "- **Lưu ý:** Nội dung slide được chuyển từ hình sang chữ, chỉ gồm những gì có trên slide.\n\n---\n\n"
    )

    obs, nlm = [head_obs], [head_nlm]
    for n, d in slides:
        title = d.get("title") or ""
        heading = f"## Slide {n}: {title}".rstrip(": ").rstrip()
        content = d.get("content", "")
        notes = d.get("notes", "")

        block_obs = [heading, "", image_line(d["image"], img_style), "", content]
        block_nlm = [heading, "", content]
        if notes:
            note_line = f"> **Ghi chú của giảng viên:** {notes}"
            block_obs += ["", note_line]
            block_nlm += ["", note_line]
        obs.append("\n".join(block_obs) + "\n\n")
        nlm.append("\n".join(block_nlm) + "\n\n")

    (out_dir / f"{stem}.md").write_text("".join(obs), encoding="utf-8")
    (out_dir / f"{stem}.notebooklm.md").write_text("".join(nlm), encoding="utf-8")


def main():
    try:
        env_delay = float(os.environ.get("REQUEST_DELAY", 4.0))
    except ValueError:
        env_delay = 4.0

    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="File slide .pptx / .ppt / .pdf")
    ap.add_argument("-o", "--out", default=str(common.SLIDES_OUT_DIR),
                    help="Thư mục xuất (mặc định: workspace/slides_out)")
    ap.add_argument("--delay", type=float, default=env_delay,
                    help="Giây nghỉ giữa 2 slide (mặc định 4, hoặc biến REQUEST_DELAY)")
    ap.add_argument("--model", default=os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
                    help="Tên model, có thể nhiều model cách nhau dấu phẩy")
    ap.add_argument(
        "--img-style",
        choices=["empty", "wiki"],
        default="empty",
        help="empty: ![ten.webp]()  |  wiki: ![[ten.webp]]",
    )
    args = ap.parse_args()

    api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
               or (os.environ.get("GEMINI_API_KEYS") or "").split(",")[0].strip())
    if not api_key:
        sys.exit("Chưa đặt GEMINI_API_KEY (ghi vào file .env hoặc đặt biến môi trường).")
    models = [m.strip() for m in args.model.split(",") if m.strip()]
    describer = Describer(genai.Client(api_key=api_key), models)

    src = to_path(args.file)
    if not src.exists():
        sys.exit(f"Không thấy file: {src}")

    stem = src.stem
    slug = re.sub(r"\s+", "_", stem)
    out_dir = to_path(args.out) / stem
    cache = out_dir / ".cache"
    cache.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        notes = []
        if src.suffix.lower() in (".pptx", ".ppt"):
            print("Đang đổi sang PDF bằng LibreOffice...")
            pdf_path = pptx_to_pdf(src, tmp)
            if src.suffix.lower() == ".pptx":
                notes = pptx_notes(src)
        else:
            pdf_path = src

        doc = fitz.open(str(pdf_path))
        total = len(doc)
        if notes and len(notes) != total:
            print(f"Cảnh báo: số ghi chú ({len(notes)}) khác số slide ({total}), bỏ qua ghi chú.")
            notes = []

        zoom = fitz.Matrix(DPI / 72, DPI / 72)
        for i in range(total):
            n = i + 1
            cache_file = cache / f"{n:03d}.json"
            img_name = f"{slug}-{n:03d}.webp"
            img_path = out_dir / img_name

            if cache_file.exists() and img_path.exists():
                print(f"[{n}/{total}] đã có, bỏ qua")
                continue

            print(f"[{n}/{total}] đang xử lý...")
            page = doc[i]
            hint_text = page.get_text().strip()
            pix = page.get_pixmap(matrix=zoom, alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img.save(img_path, "WEBP", quality=85)
            img_bytes = img_path.read_bytes()
            del pix, img

            hint = ""
            if hint_text:
                hint = (
                    "\n\nText layer trích từ file gốc (có thể thiếu hoặc sai thứ tự, "
                    "chỉ dùng để đối chiếu chính tả):\n" + hint_text[:3000]
                )

            data = describer.describe(img_bytes, hint)
            data["image"] = img_name
            data["notes"] = notes[i] if notes else ""
            cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

            gc.collect()
            time.sleep(args.delay)

        doc.close()

    build_outputs(out_dir, stem, src.name, total, args.img_style)
    print(f"\nXong! Thư mục: {out_dir}")
    print(f"  - {stem}.md            (cho Obsidian, có ảnh)")
    print(f"  - {stem}.notebooklm.md (cho NotebookLM, chỉ có chữ)")


if __name__ == "__main__":
    main()
