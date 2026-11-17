#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pymupdf",
#     "pillow",
#     "google-genai",
#     "python-dotenv",
# ]
# ///
"""
Chuyển PDF scan sách y khoa tiếng Việt thành Markdown bằng Gemini (Google AI Studio).

Mỗi lần xử lý MỘT HOẶC VÀI trang (--pages-per-req): render ảnh (PyMuPDF) -> tăng tương phản (Pillow)
-> gửi Gemini (mỗi trang một ảnh JPEG riêng) -> lưu ngay từng trang thành file p00001.md -> giải phóng RAM.
Tiến độ lưu theo từng trang nên bị ngắt hoặc hết quota ngày thì chạy lại sẽ làm tiếp.

Nhiều key x nhiều model:
  - GEMINI_API_KEYS=key1,key2,key3 (mỗi key nên thuộc một Project khác nhau, vì quota tính theo Project)
  - GEMINI_MODEL=modelA,modelB,modelC
  Script tạo các cặp (key, model) và đi theo vòng xoay hai chiều (ping-pong) 0->1->...->N->N->...->1->0.
  Một cặp lỗi liên tiếp --switch-after lần thì nhảy sang cặp kế.
  Máy chủ quá tải (503/504 "high demand") thì model đó nghỉ --peak-wait giây (mặc định 5 phút) và script
  chuyển sang model khác còn quota; nếu mọi model đều quá tải thì chờ đủ 5 phút rồi thử lại.
  Gemini từ chối chép một trang (RECITATION, nghi trùng văn bản có bản quyền) thì chỉ trang đó được thử lại
  bằng model KHÁC (model cũ không bị phạt nghỉ); model thứ hai cũng từ chối thì ghi nhận thất bại, chạy lại sau.
  Hết quota ngày thì cặp đó nghỉ --cooldown giây (mặc định 15 phút) rồi được thử lại để vét "soft limit";
  báo hết quota ngày 3 lần liên tiếp thì khóa cứng đến hết hôm nay. Chỉ khi MỌI cặp đều khóa cứng mới dừng (exit 0).

Key trả phí (chốt chặn cuối): đặt GEMINI_PAID_API_KEY và chạy với --allow-paid. Chỉ dùng khi MỌI cặp miễn phí đã
khóa cứng vì hết quota ngày; tối đa --paid-max-pages trang mỗi lần chạy; cuối phiên in số trang/token đã dùng.
Flash-Lite luôn chạy --lite-pages trang/request (mặc định 1). Mỗi trang ghi lại model đã chép (sources.json);
--redo-models modelA,modelB làm lại riêng các trang do model đó chép (khi quota model tốt hơn đã hồi).
Trang chụp thiếu sáng được tăng tương phản mạnh hơn tự động (--dark-threshold, 0 = tắt).

Gộp trang: --pages-per-req 2 gửi 2 ảnh rời trong 1 request (tiết kiệm RPD). Nếu Gemini trả thiếu/sai thẻ
<<<PAGE_xxxxx>>> hoặc bị cắt (MAX_TOKENS) thì tự chạy lại từng trang một.

Giới hạn thời gian: --max-runtime 20400 (giây) dừng êm, gộp file rồi thoát exit 0 (dùng cho GitHub Actions).

Cách dùng (thường chạy qua menu -> [15]):
    uv run process_book.py                       # mọi PDF trong input_pdfs/
    uv run process_book.py "đường/dẫn/thư_mục"   # hoặc 1 file PDF; chấp nhận cả C:\\...
    uv run process_book.py --test                # thử 3 trang đầu của sách đầu tiên, in ra màn hình, không lưu
    uv run process_book.py --test --pages 12     # thử riêng trang 12
    uv run process_book.py --split               # chia mỗi sách thành nhiều file theo chương (H1)
    uv run process_book.py --list-models         # xem model nào dùng được với key của bạn
    uv run process_book.py --pages-per-req 3     # gộp 3 trang mỗi request (1, 2 hoặc 3)
    uv run process_book.py --keys k1,k2          # nhiều key (hoặc GEMINI_API_KEYS trong .env)
    uv run process_book.py --max-runtime 20400   # tối đa 5 giờ 40 phút
    uv run process_book.py --peak-wait 600       # quá tải thì chờ 10 phút thay vì 5 phút
    uv run process_book.py --timeout 60 --switch-after 1   # chuyển cặp ngay sau lỗi đầu tiên

API key: GEMINI_API_KEYS (nhiều key, cách nhau dấu phẩy) hoặc GEMINI_API_KEY trong file .env / biến môi trường.
"""
from __future__ import annotations

import argparse
import gc
import io
import json
import os
import random
import re
import shutil
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

# In tiếng Việt và ký hiệu an toàn trên Windows (kể cả khi đầu ra bị chuyển hướng)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

try:
    import pymupdf as fitz  # tên mới của PyMuPDF
except ImportError:  # bản cũ
    import fitz

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from PIL import Image, ImageEnhance, ImageOps, ImageStat

# ----------------------------------------------------------------------------
# Cấu hình mặc định (đổi bằng tham số dòng lệnh hoặc biến môi trường / .env)
# ----------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
DEFAULT_IN = BASE / "input_pdfs"
DEFAULT_OUT = BASE / "output_md"

# Tên model có thể đổi theo thời gian: kiểm tra bằng --list-models.
# Có thể ghi nhiều model, cách nhau dấu phẩy. Mỗi (key, model) có quota riêng; model không tồn tại thì bị bỏ qua.
# Thứ tự ưu tiên (theo bảng quota gói miễn phí): Flash chất lượng cao 20 RPD/key, rồi Flash-Lite 500 RPD/key.
# Model quota 0 trên gói miễn phí (2 Flash, 2 Flash Lite, 2.5 Pro, 3.1 Pro) cố ý không đưa vào.
DEFAULT_MODEL = ("gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,"
                 "gemini-2.5-flash,gemini-2.5-flash-lite")
DEFAULT_DELAY = 6.0      # giây giữa hai request (REQUEST_DELAY)
DEFAULT_TIMEOUT = 120.0  # giây tối đa chờ MỖI lần gọi Gemini (REQUEST_TIMEOUT); quá hạn coi là lỗi tạm thời
DEFAULT_SWITCH_AFTER = 2  # số lần lỗi liên tiếp trên một cặp thì chuyển sang cặp kế
DEFAULT_DPI = 250
DEFAULT_CONTRAST = 1.2   # 1.0 = không đổi
DEFAULT_RETRIES = 6      # số lần thử lại khi bị 429 theo phút / lỗi mạng (khi không còn cặp nào để chuyển)
DEFAULT_PAGES_PER_REQ = 2
DEFAULT_COOLDOWN = 900.0  # giây nghỉ của một cặp sau khi báo hết quota ngày (15 phút)
HARD_AFTER = 3            # báo hết quota ngày liên tiếp ngần này lần thì khóa cứng trong ngày
DEFAULT_PEAK_WAIT = 300.0  # giây một model nghỉ khi máy chủ báo quá tải (high demand)
DEFAULT_PEAK_RETRIES = 6   # số đợt quá tải liên tiếp cho MỘT request trước khi bỏ qua trang đó (tránh kẹt vô hạn)

DEFAULT_LITE_PAGES = 1     # Flash-Lite: số trang tối đa mỗi request (1 trang an toàn nhất, request còn thừa)
DEFAULT_PAID_MODEL = "gemini-3.1-flash-lite"
DEFAULT_PAID_MAX_PAGES = 300  # trần số trang được phép dùng key trả phí trong MỘT lần chạy
DEFAULT_PAID_DELAY = 1.0   # giây nghỉ giữa hai request khi dùng key trả phí (không bị giới hạn 5-15 RPM)
DARK_MEAN = 150            # độ sáng trung bình (0-255) dưới mức này coi là trang chụp thiếu sáng

SENTINEL = "<<TRANG_TRONG>>"
TEMPERATURES = [0.1, 0.3, 0.5]  # lần đầu 0.1; chỉ tăng nếu Gemini trả về rỗng

SYSTEM_PROMPT = """\
Bạn là công cụ chép lại (transcribe) MỘT hoặc VÀI trang sách y khoa tiếng Việt từ ảnh scan sang Markdown (mỗi ảnh là một trang riêng biệt).
Mục tiêu: văn bản sạch, đúng từng chữ, cấu trúc rõ ràng để một hệ thống AI khác đọc và trả lời câu hỏi.

QUY TẮC BẮT BUỘC
1. Chép trung thực những gì in trên trang. Tuyệt đối KHÔNG thêm kiến thức bên ngoài, KHÔNG tóm tắt, KHÔNG giải thích, KHÔNG bình luận, KHÔNG dịch.
2. Đoạn văn: viết thành đoạn liền mạch theo đúng thứ tự đọc (trang nhiều cột thì đọc hết cột này rồi mới sang cột kia). Nối các dòng bị ngắt do hết dòng trong cùng một đoạn; các đoạn cách nhau một dòng trống. Nếu câu hoặc đoạn bị cắt ở đầu hoặc cuối trang thì giữ nguyên chỗ cắt, không tự viết thêm cho trọn câu.
3. Tiêu đề: dùng `#` CHỈ cho tên chương hoặc tên bài lớn có in trên trang. Các mục con dùng `##`, `###`, `####` theo đúng cấp bậc đánh số/trình bày của sách. Giữ nguyên số thứ tự mục. Không tự tạo tiêu đề không có trên trang.
4. Danh sách: dùng `-` cho gạch đầu dòng, giữ đúng số thứ tự nếu sách đánh số. Giữ in đậm (**...**) cho thuật ngữ được in đậm trong sách.
5. Bảng: chuyển thành bảng Markdown (có dòng tiêu đề và dòng `---`). Ô trống để trống; ô gộp thì lặp lại nội dung ở các ô liên quan. Giữ nguyên số liệu, đơn vị, ký hiệu.
6. Sơ đồ, infographic, mind map, lưu đồ: chuyển thành danh sách lồng nhau (thụt lề 2 khoảng trắng mỗi cấp), nút trung tâm hoặc tiêu đề sơ đồ ở cấp cao nhất, các nhánh con thụt vào. Bắt đầu bằng một dòng `**Sơ đồ: <tên sơ đồ nếu có>**`. Với mỗi mũi tên (quan hệ nguyên nhân -> kết quả, trình tự, dẫn đến) viết `-->` ngay trong dòng, ví dụ `- Nút A --> Nút B`. CHỈ viết `-->` khi trong ảnh thật sự có mũi tên; nếu không chắc quan hệ thì chỉ liệt kê, không tự suy ra.
7. Hình minh họa (giải phẫu, ảnh lâm sàng, biểu đồ): chỉ chép các chữ có trong hình (chú thích, nhãn, số liệu trên trục) theo dạng `[Hình: <chú thích gốc>]` và danh sách nhãn nếu có. Không mô tả hình bằng lời của bạn.
8. Số liệu, liều thuốc, công thức, đơn vị (µg, mmol/L, ≥, ±...) phải chép chính xác từng chữ số. Ảnh mờ có thể làm sai dấu tiếng Việt: được sửa dấu dựa trên ngữ cảnh y khoa NẾU chắc chắn. Chữ hoặc số nào không đọc được hoặc không chắc thì ghi `[không rõ]`, KHÔNG được đoán số liệu.
9. Bỏ qua số trang, đầu trang và chân trang lặp lại (tên sách, tên chương in ở lề trang).
10. Chú thích cuối trang: giữ ở cuối trang dưới dạng đoạn văn bình thường.
11. Trang trống, hoặc chỉ có hình trang trí không có chữ: trả về đúng một dòng `<<TRANG_TRONG>>`.
12. CHỈ trả về nội dung Markdown của trang. Không lời dẫn, không giải thích, không bọc trong ```. (Khi lượt hỏi yêu cầu nhiều trang kèm thẻ `<<<PAGE_xxxxx>>>` thì làm đúng theo lượt hỏi: chỉ có các thẻ và nội dung từng trang.)
13. Công thức tính toán, ký hiệu hóa học/sinh hóa có chỉ số trên/dưới phức tạp (ví dụ đồng vị phóng xạ $^{99m}\\text{Tc}$): viết bằng LaTeX, `$...$` nếu nằm cùng dòng với chữ, `$$...$$` đứng riêng một dòng nếu là công thức đứng riêng. Ký hiệu đơn giản (µg, mmol/L, ≥, ±, Na+...) giữ nguyên như quy tắc 8.
14. Khung nhấn mạnh đặc biệt trong sách (như "Lưu ý lâm sàng", "Điểm mấu chốt", "Cần nhớ"): định dạng bằng blockquote, mỗi dòng bắt đầu bằng `> `, để tách khỏi văn bản chính. Giữ nguyên tiêu đề của khung nếu có.
15. Chữ cái đầu đoạn được phóng to (drop cap) phải được nối liền với phần còn lại của từ: ví dụ chữ `D` lớn đứng trước `ịch tễ học` thì viết `Dịch tễ học`.
16. Vệt bút dạ quang (vàng, xanh, cam...) chỉ là màu nền: vẫn đọc đầy đủ chữ nằm dưới vệt đó. Nét chữ hoặc hình mờ, ngược chiều (như chữ in ngược) thấm từ mặt sau tờ giấy không thuộc trang này nên bỏ qua. Chỉ bỏ khi chắc chắn là chữ ngược hoặc hằn từ mặt sau; chữ mờ nhưng thuộc dòng chữ của trang thì vẫn chép, không chắc thì ghi `[không rõ]`.
17. Bỏ rác ở lề và chân trang: số trang đứng riêng lẻ (số Ả Rập hoặc số La Mã như `VI`), watermark của phần mềm scan (như `Scanned with CamScanner`). Nét gạch bút bi đánh dấu thủ công ở lề (nhất là lề phải) không phải chữ: không chép thành ký tự `/` hay bất kỳ ký tự nào.
"""


# ----------------------------------------------------------------------------
# Tiện ích chung
# ----------------------------------------------------------------------------
class QuotaExhausted(Exception):
    """Mọi cặp (key, model) đều đã khóa cứng vì hết quota ngày."""


class FatalError(Exception):
    """Lỗi không thể tự khắc phục (sai key, sai tên model... ở MỌI cặp)."""


class RuntimeLimit(Exception):
    """Chạm giới hạn thời gian --max-runtime."""


def log(msg: str = "") -> None:
    print(msg, flush=True)


def one_line(s: str, n: int = 300) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def to_wsl_path(raw: str) -> Path:
    """Bỏ dấu nháy; trên WSL/Linux đổi C:\\... sang /mnt/c/...; trên Windows giữ nguyên."""
    s = raw.strip().strip('"').strip("'")
    if os.name != "nt":
        m = re.match(r"^([A-Za-z]):[\\/](.*)$", s)
        if m:
            s = f"/mnt/{m.group(1).lower()}/" + m.group(2).replace("\\", "/")
    return Path(s).expanduser()


def natural_key(p: Path):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


def safe_filename(s: str, max_len: int = 80) -> str:
    s = nfc(s)
    s = re.sub(r'[#^\[\]|:/\\?*"<>\x00-\x1f]', " ", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s[:max_len].strip(" .") or "untitled"


def book_name(pdf: Path) -> str:
    stem = nfc(pdf.stem)
    return re.sub(r"\s*[-_]\s*OCR$", "", stem, flags=re.I).strip() or stem


def fmt_ranges(nums: list[int]) -> str:
    nums = sorted(nums)
    if not nums:
        return ""
    parts: list[str] = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        parts.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = n
    parts.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(parts)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def parse_pages(spec: str, total: int) -> list[int]:
    if not spec:
        return list(range(1, total + 1))
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", part)
        if not m:
            raise ValueError(f"Khoảng trang không hợp lệ: '{part}' (ví dụ đúng: 1-20,25)")
        a = int(m.group(1))
        b = int(m.group(2) or a)
        if b < a:
            a, b = b, a
        out.update(range(max(a, 1), min(b, total) + 1))
    return sorted(out)


def find_pdfs(target: Path, book_filter: str | None) -> list[Path]:
    if target.is_file():
        pdfs = [target] if target.suffix.lower() == ".pdf" else []
    elif target.is_dir():
        pdfs = sorted(
            (p for p in target.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"),
            key=natural_key,
        )
    else:
        pdfs = []
    if book_filter:
        key = nfc(book_filter).lower()
        pdfs = [p for p in pdfs if key in nfc(p.name).lower()]
    return pdfs


# ----------------------------------------------------------------------------
# Ảnh trang: render -> xám -> tăng tương phản -> JPEG (một trang một lần)
# ----------------------------------------------------------------------------
def enhance_image(img, contrast: float, autocontrast: bool, dark_threshold: float):
    """Tăng tương phản. Trang quá tối (độ sáng trung bình < dark_threshold, thường là ảnh chụp thiếu sáng)
    được kéo giãn mạnh hơn tự động, không cần cờ riêng."""
    dark = bool(dark_threshold) and ImageStat.Stat(img).mean[0] < dark_threshold
    if autocontrast or dark:
        img = ImageOps.autocontrast(img, cutoff=2 if dark else 1)
    factor = max(contrast or 1.0, 1.3) if dark else contrast
    if factor and abs(factor - 1.0) > 1e-6:
        img = ImageEnhance.Contrast(img).enhance(factor)
    return img


def render_page(doc, index0: int, dpi: int, contrast: float, autocontrast: bool,
                dark_threshold: float = DARK_MEAN) -> bytes:
    page = doc.load_page(index0)
    zoom = dpi / 72.0
    pix = page.get_pixmap(
        matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY, alpha=False
    )
    img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    del pix, page
    img = enhance_image(img, contrast, autocontrast, dark_threshold)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=True)
    img.close()
    return buf.getvalue()


# ----------------------------------------------------------------------------
# Gọi Gemini, phân loại lỗi
# ----------------------------------------------------------------------------
SAFETY_OFF = [
    types.SafetySetting(category=c, threshold="BLOCK_NONE")
    for c in (
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
    )
]


def classify_error(e: Exception) -> tuple[str, float | None]:
    """Trả về (loại, số giây chờ gợi ý).
    Loại: daily | rate | overload | transient | badrequest | nomodel | fatal
    """
    msg = str(e)
    low = msg.lower()
    code = getattr(e, "code", None)
    status = str(getattr(e, "status", "") or "").upper()

    retry_after = None
    m = re.search(r"retry(?:\s+in|delay)\D{0,10}(\d+(?:\.\d+)?)\s*s", low)
    if m:
        retry_after = float(m.group(1))

    if isinstance(e, errors.APIError):
        if code == 429 or status == "RESOURCE_EXHAUSTED":
            # quota theo NGÀY (hoặc model không có quota miễn phí)
            if re.search(r"per[\s_]?day|daily|limit:\s*0\b", low):
                return "daily", retry_after
            if retry_after and retry_after > 180:
                return "daily", retry_after
            return "rate", retry_after
        # máy chủ quá tải (peak demand): 503 UNAVAILABLE / 504 DEADLINE_EXCEEDED -> nghỉ model đó vài phút
        if (code in (503, 504) or status in ("UNAVAILABLE", "DEADLINE_EXCEEDED")
                or re.search(r"high demand|overloaded", low)):
            return "overload", retry_after
        if code in (500, 502) or status == "INTERNAL":
            return "transient", retry_after
        if code in (401, 403) or "api key not valid" in low or "api_key_invalid" in low:
            return "fatal", None
        if code == 404:
            return "nomodel", None
        if code == 400:
            if "api key" in low:
                return "fatal", None
            return "badrequest", None
        return "transient", retry_after
    # lỗi mạng, timeout...
    return "transient", None


def describe_error(e: Exception, n: int = 300) -> str:
    """Mô tả lỗi để in ra màn hình: loại lỗi, mã (nếu có) và nội dung đã rút gọn."""
    code = getattr(e, "code", None)
    head = type(e).__name__ + (f" [{code}]" if code else "")
    body = one_line(str(e), n) or "(không có nội dung lỗi)"
    return f"{head}: {body}"


def extract_text(resp) -> tuple[str, str, str]:
    """Trả về (văn bản, finish_reason, block_reason). Bỏ qua phần 'thought' của model."""
    text = ""
    finish = ""
    try:
        cands = resp.candidates or []
        if cands:
            c = cands[0]
            finish = str(getattr(c, "finish_reason", "") or "")
            parts = getattr(getattr(c, "content", None), "parts", None) or []
            text = "".join(
                (p.text or "")
                for p in parts
                if getattr(p, "text", None) and not getattr(p, "thought", False)
            )
    except Exception:
        pass
    block = ""
    pf = getattr(resp, "prompt_feedback", None)
    if pf is not None and getattr(pf, "block_reason", None):
        block = str(pf.block_reason)
    return text.strip(), finish, block


def unfence(text: str) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    m = re.match(r"^```(?:markdown|md)?[ \t]*\n(.*?)\n```[ \t]*$", t, re.S | re.I)
    if m:
        t = m.group(1).strip()
    return t


def clean_output(text: str) -> str:
    t = nfc(unfence(text))
    if t == SENTINEL or (SENTINEL in t and len(t) < len(SENTINEL) + 20):
        return SENTINEL
    return t


# ----------------------------------------------------------------------------
# Nhiều key x nhiều model: vòng xoay ping-pong, cooldown, giới hạn thời gian
# ----------------------------------------------------------------------------
def parse_keys(raw: str | None) -> list[str]:
    """Tách danh sách key (cách nhau dấu phẩy, chấm phẩy hoặc xuống dòng), bỏ trùng, giữ thứ tự."""
    out: list[str] = []
    for k in re.split(r"[,;\s]+", raw or ""):
        k = k.strip().strip("\"'")
        if k and k not in out:
            out.append(k)
    return out


def get_keys(cli_keys: str | None) -> list[str]:
    """Thứ tự ưu tiên: --keys > GEMINI_API_KEYS > GEMINI_API_KEY > GOOGLE_API_KEY."""
    for raw in (cli_keys, os.environ.get("GEMINI_API_KEYS"),
                os.environ.get("GEMINI_API_KEY"), os.environ.get("GOOGLE_API_KEY")):
        keys = parse_keys(raw)
        if keys:
            return keys
    log("Chưa có API key.\n"
        "  1) Tạo key miễn phí tại https://aistudio.google.com/apikey\n"
        f"  2) Ghi vào file {BASE / '.env'} một dòng:  GEMINI_API_KEY=khóa_của_bạn\n"
        "     (nhiều key: GEMINI_API_KEYS=key1,key2,key3; hoặc chọn [15] -> [7] trong menu)")
    sys.exit(2)


def get_client(key: str, timeout: float = DEFAULT_TIMEOUT) -> genai.Client:
    # timeout của google-genai tính bằng MILLI-GIÂY; không đặt thì một kết nối "lặng thinh" có thể treo rất lâu
    return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=int(timeout * 1000)))


def is_lite(model: str) -> bool:
    return "flash-lite" in model.lower()


def model_rpm(model: str) -> int:
    """Giới hạn request/phút của gói miễn phí (theo bảng quota của AI Studio): Flash-Lite 15, Flash 5."""
    return 15 if is_lite(model) else 5


@dataclass
class Slot:
    """Một cặp (api_key, model) với trạng thái quota riêng."""
    key: str
    key_no: int
    model: str
    label: str
    paid: bool = False            # True = key trả phí (chốt chặn cuối cùng)
    cooldown_until: float = 0.0   # mốc thời gian (monotonic) cặp được dùng lại sau khi hết quota ngày
    rate_until: float = 0.0       # mốc thời gian được dùng lại sau khi bị 429 theo phút
    last_call: float = 0.0        # lần gọi gần nhất (để giữ đúng giới hạn request/phút)
    errs: int = 0                 # số lỗi liên tiếp (reset khi thành công)
    daily_hits: int = 0           # số lần liên tiếp báo hết quota ngày (reset khi thành công)
    hard: bool = False            # khóa cứng đến hết hôm nay
    reason: str = ""              # daily | nomodel | badkey


class NeedSplit(Exception):
    """Cặp hiện tại không nhận được ngần ấy ảnh trong một request: phải tách thành từng trang."""


class Transcriber:
    def __init__(self, keys: list[str], models: list[str], system_prompt: str, single_text: str,
                 topic: str, timeout: float, max_retries: int, delay: float,
                 switch_after: int = DEFAULT_SWITCH_AFTER, cooldown: float = DEFAULT_COOLDOWN,
                 deadline: float | None = None, peak_wait: float = DEFAULT_PEAK_WAIT,
                 peak_retries: int = DEFAULT_PEAK_RETRIES, lite_pages: int = DEFAULT_LITE_PAGES,
                 paid_key: str = "", paid_model: str = DEFAULT_PAID_MODEL,
                 paid_max_pages: int = DEFAULT_PAID_MAX_PAGES, paid_delay: float = DEFAULT_PAID_DELAY):
        self.clients = {k: get_client(k, timeout) for k in keys}
        multi = len(keys) > 1
        # model đứng trước (ưu tiên) được trải đều qua mọi key trước khi tới model sau
        self.slots = [
            Slot(key=k, key_no=i, model=m, label=(f"k{i}/{m}" if multi else m))
            for m in models for i, k in enumerate(keys, 1)
        ]
        n = len(self.slots)
        self.order = list(range(n)) + list(range(n - 1, -1, -1))  # ping-pong: 0..N-1, N-1..0, rồi lặp lại
        self.pos = 0
        self.cur = self.slots[0]
        # Key trả phí: KHÔNG nằm trong vòng xoay, chỉ dùng khi mọi cặp miễn phí đã khóa cứng vì hết quota ngày
        self.paid: Slot | None = None
        if paid_key:
            if paid_key not in self.clients:
                self.clients[paid_key] = get_client(paid_key, timeout)
            self.paid = Slot(key=paid_key, key_no=0, model=paid_model, label=f"trả phí/{paid_model}", paid=True)
        self.paid_max_pages = max(0, paid_max_pages)
        self.paid_delay = max(0.0, paid_delay)
        self.paid_pages = 0
        self.paid_reqs = 0
        self.paid_tokens = 0
        self.lite_pages = max(1, lite_pages)
        self.system_prompt = system_prompt
        self.single_text = single_text
        self.topic = topic
        self.max_retries = max_retries
        self.delay = delay
        self.switch_after = max(1, switch_after)
        self.cooldown = max(0.0, cooldown)
        self.deadline = deadline
        self.peak_wait = max(0.0, peak_wait)
        self.peak_retries = max(1, peak_retries)
        self.model_peak: dict[str, float] = {}  # model -> mốc monotonic được dùng lại sau khi quá tải
        self.no_media_res: set[str] = set()     # model từ chối tham số media_resolution
        self.last_label = self.cur.label
        self.last_source = self.cur.model
        self.last_fatal = ""

    # ---- thời gian -------------------------------------------------------
    def out_of_time(self) -> bool:
        return bool(self.deadline) and time.monotonic() >= self.deadline

    def sleep(self, sec: float) -> None:
        """Ngủ, nhưng nếu giấc ngủ vượt quá --max-runtime thì dừng ngay (RuntimeLimit)."""
        if self.deadline and time.monotonic() + sec >= self.deadline:
            raise RuntimeLimit()
        if sec > 0:
            time.sleep(sec)

    def delay_now(self, delay: float) -> float:
        """Giây nghỉ giữa hai request: key trả phí không bị giới hạn 5-15 RPM nên nghỉ ngắn hơn."""
        return min(delay, self.paid_delay) if self.cur.paid else delay

    def _pace(self, slot: Slot) -> None:
        """Giữ đúng giới hạn request/phút của từng model (Flash 5 RPM, Flash-Lite 15 RPM)."""
        if slot.paid:
            return
        gap = 60.0 / model_rpm(slot.model)
        wait = gap - (time.monotonic() - slot.last_call)
        if wait > 0:
            self.sleep(wait)

    # ---- chọn cặp --------------------------------------------------------
    def cap(self, slot: Slot) -> int:
        """Số trang tối đa gộp trong một request cho cặp này (Flash-Lite: --lite-pages, mặc định 1)."""
        return self.lite_pages if is_lite(slot.model) else 3

    def _ready_at(self, s: Slot) -> float:
        return max(s.cooldown_until, s.rate_until, self.model_peak.get(s.model, 0.0))

    def _usable(self, s: Slot, now: float) -> bool:
        return (not s.hard) and self._ready_at(s) <= now

    def _paid_ok(self) -> bool:
        return (self.paid is not None and not self.paid.hard and self.paid_pages < self.paid_max_pages)

    def _set_cur(self, s: Slot) -> None:
        self.cur = s
        for i, idx in enumerate(self.order):
            if self.slots[idx] is s:
                self.pos = i
                break

    def _advance(self, exclude_models: set[str] | None = None) -> bool:
        """Nhảy sang cặp dùng được kế tiếp theo vòng ping-pong (bỏ qua chính cặp hiện tại
        và các cặp thuộc model trong exclude_models)."""
        now = time.monotonic()
        cur = self.cur
        for _ in range(len(self.order)):
            self.pos = (self.pos + 1) % len(self.order)
            s = self.slots[self.order[self.pos]]
            if s is cur or (exclude_models and s.model in exclude_models):
                continue
            if self._usable(s, now):
                self.cur = s
                return True
        # không có cặp nào khác dùng được: đặt lại pos về cặp hiện tại cho nhất quán
        for i, idx in enumerate(self.order):
            if self.slots[idx] is cur:
                self.pos = i
                break
        return False

    def acquire(self) -> Slot:
        """Trả về cặp dùng được ngay; nếu mọi cặp đang nghỉ thì ngủ đến khi có cặp đầu tiên hết nghỉ."""
        while True:
            now = time.monotonic()
            if all(s.hard for s in self.slots):
                p = self.paid
                if any(s.reason == "daily" for s in self.slots) and self._paid_ok():
                    if self.cur is not p:
                        log(f"    💳 mọi key miễn phí đã hết quota → chuyển sang key TRẢ PHÍ ({p.model}), "
                            f"tối đa {self.paid_max_pages} trang mỗi lần chạy")
                        self.cur = p
                    if self._usable(p, now):
                        return p
                    wait = max(self._ready_at(p) - now, 0.5)
                    log(f"    ⏳ key trả phí đang nghỉ/quá tải: chờ {wait / 60:.1f} phút")
                    self.sleep(wait)
                    continue
                if all(s.reason in ("nomodel", "badkey") for s in self.slots):
                    raise FatalError(self.last_fatal or "không còn cặp key/model nào dùng được")
                raise QuotaExhausted()
            if self._usable(self.cur, now):
                return self.cur
            if self._advance():
                return self.cur
            alive = [s for s in self.slots if not s.hard]
            soonest = min(alive, key=self._ready_at)
            wait = max(self._ready_at(soonest) - now, 0.5)
            hard_n = sum(1 for s in self.slots if s.hard)
            log(f"    ⏳ mọi cặp đang nghỉ/quá tải/giới hạn ({hard_n}/{len(self.slots)} đã khóa cứng): "
                f"chờ {wait / 60:.1f} phút đến khi {soonest.label} dùng lại được")
            self.sleep(wait)
            self.cur = soonest

    # ---- đánh dấu trạng thái ----------------------------------------------
    def _pool(self, slot: Slot) -> list[Slot]:
        return [self.paid] if (slot.paid and self.paid) else self.slots

    def _daily(self, slot: Slot, short: str) -> None:
        slot.errs = 0
        slot.daily_hits += 1
        if slot.daily_hits >= HARD_AFTER:
            slot.hard = True
            slot.reason = "daily"
            log(f"    ⛔ {slot.label}: báo hết quota ngày {slot.daily_hits} lần liên tiếp → khóa cứng đến hết hôm nay"
                f" — {short[:120]}")
        else:
            slot.cooldown_until = time.monotonic() + self.cooldown
            log(f"    ⚠ {slot.label}: hết quota (thường là quota ngày) lần {slot.daily_hits}/{HARD_AFTER}"
                f" → nghỉ {self.cooldown / 60:.0f} phút rồi thử lại — {short[:120]}")

    def _kill_model(self, slot: Slot, short: str) -> None:
        self.last_fatal = short
        log(f"    ⚠ model '{slot.model}' không tồn tại hoặc không dùng được với key này — {short[:140]}")
        for s in self._pool(slot):
            if s.model == slot.model:
                s.hard, s.reason = True, "nomodel"

    def _kill_key(self, slot: Slot, short: str) -> None:
        self.last_fatal = short
        if slot.paid:
            log(f"    ⚠ key TRẢ PHÍ bị từ chối (sai key, chưa bật billing hoặc không có quyền) — {short[:140]}")
        else:
            log(f"    ⚠ key số {slot.key_no} bị từ chối (sai key hoặc không có quyền) — {short[:140]}")
        for s in self._pool(slot):
            if s.key_no == slot.key_no:
                s.hard, s.reason = True, "badkey"

    # ---- gọi API ---------------------------------------------------------
    def batch_text(self, nums: list[int]) -> str:
        tags = ", ".join(f"<<<PAGE_{n:05d}>>>" for n in nums)
        return (
            f"Có {len(nums)} ảnh, lần lượt là các trang {', '.join(str(n) for n in nums)} của sách (đúng thứ tự gửi). "
            "Mỗi ảnh là MỘT trang riêng: chép từng trang độc lập theo đúng các quy tắc, KHÔNG gộp nội dung giữa "
            "các trang, KHÔNG bỏ trang nào. "
            f"Với mỗi trang, mở đầu bằng MỘT dòng thẻ chính xác, lần lượt là: {tags} — rồi tới nội dung Markdown "
            "của trang đó. Trang trống thì sau thẻ chỉ ghi <<TRANG_TRONG>>. "
            "Không viết lời dẫn hay bất cứ gì khác ngoài các thẻ và nội dung." + self.topic
        )

    def _call(self, slot: Slot, images: list[bytes], user_text: str, temperature: float):
        contents = [types.Part.from_bytes(data=img, mime_type="image/jpeg") for img in images]
        contents.append(user_text)
        cfg = dict(system_instruction=self.system_prompt, temperature=temperature, safety_settings=SAFETY_OFF)
        if slot.model not in self.no_media_res and hasattr(types, "MediaResolution"):
            cfg["media_resolution"] = types.MediaResolution.MEDIA_RESOLUTION_HIGH  # giữ dấu tiếng Việt, chỉ số nhỏ
        return self.clients[slot.key].models.generate_content(
            model=slot.model, contents=contents, config=types.GenerateContentConfig(**cfg),
        )

    def run_request(self, images: list[bytes], user_text: str) -> tuple[str | None, str, bool]:
        """Gửi một request (1 hoặc nhiều ảnh rời).
        Trả về (văn bản thô hoặc None nếu thất bại, ghi chú, bị cắt do MAX_TOKENS).
        Ném NeedSplit nếu cặp hiện tại không nhận ngần ấy ảnh (Flash-Lite): người gọi tách thành từng trang."""
        empty_tries = 0
        peaks = 0
        recited: set[str] = set()      # các model đã từ chối chép (RECITATION) cho request này
        home: Slot | None = None       # cặp ban đầu, để quay về sau khi đổi model vì RECITATION
        while True:
            slot = self.acquire()
            if len(images) > self.cap(slot):
                raise NeedSplit()
            temperature = TEMPERATURES[min(empty_tries, len(TEMPERATURES) - 1)]
            self._pace(slot)
            try:
                slot.last_call = time.monotonic()
                resp = self._call(slot, images, user_text, temperature)
            except Exception as e:  # noqa: BLE001
                kind, retry_after = classify_error(e)
                short = one_line(str(e))
                detail = describe_error(e)
                if kind == "badrequest" and "resolution" in short.lower() and slot.model not in self.no_media_res:
                    self.no_media_res.add(slot.model)
                    log(f"    ⚠ {slot.model}: không nhận tham số media_resolution → bỏ tham số này cho model đó")
                    continue
                if kind == "fatal":
                    self._kill_key(slot, short)
                    continue
                if kind == "nomodel":
                    self._kill_model(slot, short)
                    continue
                if kind == "daily":
                    self._daily(slot, short)
                    continue
                if kind == "badrequest":
                    return None, short, False
                if kind == "overload":
                    # Quá tải là của CẢ model (mọi key): nghỉ model này, chuyển sang model khác còn quota.
                    # Mọi model đều quá tải thì acquire() tự chờ đến khi model nghỉ sớm nhất dùng lại được.
                    peaks += 1
                    if peaks > self.peak_retries:
                        return None, (f"máy chủ quá tải liên tục ({self.peak_retries} đợt), bỏ qua: {detail}"), False
                    self.model_peak[slot.model] = time.monotonic() + self.peak_wait
                    log(f"    ⏳ {slot.model}: máy chủ quá tải (đợt {peaks}/{self.peak_retries}) → nghỉ model này "
                        f"{self.peak_wait / 60:.0f} phút | {detail}")
                    if self._advance():
                        log(f"    → chuyển sang {self.cur.label}")
                    continue

                # rate (429 theo phút) hoặc transient
                slot.errs += 1
                label = "giới hạn theo phút (429)" if kind == "rate" else "lỗi tạm thời"
                if slot.errs > self.max_retries:
                    if kind == "rate":
                        log(f"    ⚠ {slot.label}: vẫn bị giới hạn sau {self.max_retries} lần thử, coi như hết quota")
                        self._daily(slot, short)
                        continue
                    slot.errs = 0
                    return None, f"lỗi tạm thời, bỏ qua: {detail}", False
                base = 10 if kind == "rate" else 5
                wait = (retry_after + 1.0) if retry_after else min(base * 2 ** (slot.errs - 1), 120)
                wait += random.uniform(0, 2)

                # Lỗi liên tiếp trên một cặp: nhảy sang cặp kế (nếu còn) thay vì chờ đủ số lần thử lại
                if slot.errs >= self.switch_after and len(self.slots) > 1 and not slot.paid:
                    old = slot
                    if kind == "rate":
                        old.rate_until = time.monotonic() + wait
                    if self._advance():
                        log(f"    ⚠ {old.label}: {label} {old.errs} lần liên tiếp | {detail}")
                        log(f"    → chuyển sang {self.cur.label}")
                        self.sleep(1.0)
                        continue
                log(f"    … {label} ({slot.label}): chờ {wait:.0f}s rồi thử lại "
                    f"({slot.errs}/{self.max_retries}) | {detail}")
                self.sleep(wait)
                continue

            text, finish, block = extract_text(resp)
            slot.errs = 0
            if slot.paid:
                um = getattr(resp, "usage_metadata", None)
                self.paid_reqs += 1
                self.paid_tokens += int(getattr(um, "total_token_count", 0) or 0)
            if text:
                slot.daily_hits = 0  # Google vẫn nhả slot: bỏ đếm khóa cứng
                self.last_label = slot.label
                self.last_source = slot.model + (" (trả phí)" if slot.paid else "")
                if slot.paid:
                    self.paid_pages += len(images)
                if home is not None and home is not slot and self._usable(home, time.monotonic()):
                    self._set_cur(home)  # chỉ trang vướng RECITATION dùng model khác, trang sau quay về model cũ
                truncated = "MAX_TOKENS" in finish.upper()
                return text, ("bị cắt do MAX_TOKENS" if truncated else ""), truncated
            reason = block or finish or "rỗng"
            if "RECITATION" in finish.upper():
                # Đổi sang model khác cho riêng request này; model cũ KHÔNG bị phạt nghỉ
                recited.add(slot.model)
                if home is None:
                    home = slot
                if self._advance(recited):
                    log(f"    ↺ {slot.model}: Gemini từ chối chép (RECITATION) → thử lại bằng {self.cur.label}")
                    continue
                return None, (f"Gemini trả về rỗng ({reason}) trên mọi model còn dùng được "
                              f"({', '.join(sorted(recited))})"), False
            empty_tries += 1
            if empty_tries >= len(TEMPERATURES):
                return None, f"Gemini trả về rỗng ({reason})", False
            log(f"    … phản hồi rỗng ({reason}); thử lại {empty_tries}/{len(TEMPERATURES) - 1}")
            self.sleep(self.delay)

    def paid_note(self) -> str:
        if self.paid is None:
            return ""
        if self.paid_reqs:
            return (f"Key trả phí ({self.paid.model}): {self.paid_pages} trang, {self.paid_reqs} request, "
                    f"{self.paid_tokens:,} token (đối chiếu với bảng giá hiện tại của Google để biết chi phí).")
        return "Key trả phí: chưa phải dùng trong lần chạy này."


# ----------------------------------------------------------------------------
# Gộp nhiều trang trong 1 request: tách theo thẻ <<<PAGE_xxxxx>>>
# ----------------------------------------------------------------------------
_PAGE_TAG = re.compile(r"<<<\s*PAGE_(\d+)\s*>>>")


def parse_batch(raw: str, expected: list[int]) -> dict[int, str] | None:
    """Tách phản hồi nhiều trang. Trả về None nếu thiếu/thừa/trùng thẻ hoặc có trang rỗng
    (khi đó người gọi chạy lại từng trang một)."""
    parts = _PAGE_TAG.split(unfence(raw))
    if len(parts) < 3:
        return None
    nums = [int(x) for x in parts[1::2]]
    bodies = parts[2::2]
    if sorted(nums) != sorted(expected):
        return None
    result: dict[int, str] = {}
    for n, body in zip(nums, bodies):
        t = clean_output(body)
        if not t:
            return None
        result[n] = t
    return result


def transcribe_pages(doc, nums: list[int], args, tr: Transcriber,
                     out: dict[int, tuple[str | None, str, str]]) -> None:
    """Chép các trang `nums`: gộp vào 1 request nếu có từ 2 trang; lỗi định dạng thì chạy lại từng trang.
    Kết quả (văn bản, ghi chú, model đã chép) điền dần vào `out` (nếu bị ngắt giữa chừng thì phần đã xong vẫn được lưu)."""
    imgs: dict[int, bytes] = {}
    try:
        for n in nums:
            try:
                imgs[n] = render_page(doc, n - 1, args.dpi, args.contrast, not args.no_autocontrast,
                                      args.dark_threshold)
            except Exception as e:  # noqa: BLE001  (vd. lỗi render một trang)
                out[n] = (None, f"lỗi render: {one_line(str(e))}", "")
        good = [n for n in nums if n in imgs]

        if len(good) >= 2:
            try:
                raw, note, truncated = tr.run_request([imgs[n] for n in good], tr.batch_text(good))
            except NeedSplit:  # cặp hiện tại là Flash-Lite: chạy từng trang, không cần báo lỗi
                raw, note, truncated = None, "", False
                parsed = None
            else:
                parsed = parse_batch(raw, good) if (raw is not None and not truncated) else None
                if parsed is not None:
                    for n in good:
                        out[n] = (parsed[n], "", tr.last_source)
                    return
                if raw is None:
                    why = note
                elif truncated:
                    why = "chạm MAX_TOKENS"
                else:
                    why = "thiếu hoặc sai thẻ phân tách trang"
                log(f"    ↺ gộp {len(good)} trang không dùng được ({why}) → chạy lại từng trang")

        for n in good:
            raw, note, truncated = tr.run_request([imgs[n]], tr.single_text)
            if raw is None:
                out[n] = (None, note, "")
                continue
            text = clean_output(raw)
            if truncated:
                text += "\n\n[không rõ — trang này có thể bị cắt cụt]"
            out[n] = (text, note, tr.last_source)
    finally:
        imgs.clear()
        gc.collect()


# ----------------------------------------------------------------------------
# Gộp trang -> sách / chương
# ----------------------------------------------------------------------------
_STRUCT = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|\||>|\*\*|<)")


def _continues(prev: str, nxt: str) -> bool:
    """Đoạn văn cuối trang trước có nối sang đầu trang sau không (heuristic thận trọng)."""
    prev_lines = prev.rstrip().splitlines()
    nxt_lines = nxt.lstrip().splitlines()
    if not prev_lines or not nxt_lines:
        return False
    last, first = prev_lines[-1], nxt_lines[0]
    if not last.strip() or not first.strip():
        return False
    if _STRUCT.match(last) or _STRUCT.match(first):
        return False
    if re.search(r"[.!?:;…)\]»”\"']\s*$", last):
        return False
    return first.lstrip()[0].islower()


def join_pages(pages: list[str]) -> str:
    blocks = [pages[0]]
    for t in pages[1:]:
        if _continues(blocks[-1], t):
            blocks[-1] = blocks[-1].rstrip() + " " + t.lstrip()
        else:
            blocks.append(t)
    return "\n\n".join(blocks)


def split_chapters(text: str) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    title = "Mở đầu"
    cur: list[str] = []
    for line in text.splitlines():
        if re.match(r"^#\s+\S", line):
            body = "\n".join(cur).strip()
            if body:
                chunks.append((title, body))
            title = line[2:].strip()
            cur = [line]
        else:
            cur.append(line)
    body = "\n".join(cur).strip()
    if body:
        chunks.append((title, body))
    return chunks


def merge_book(name: str, work: Path, total: int, out_dir: Path,
               split: bool, join: bool) -> dict:
    pages: list[str] = []
    missing: list[int] = []
    review: list[int] = []
    for n in range(1, total + 1):
        pf = work / f"p{n:05d}.md"
        if not pf.exists():
            missing.append(n)
            continue
        t = pf.read_text(encoding="utf-8").strip()
        if not t or t == SENTINEL:
            continue
        if "[không rõ" in t:
            review.append(n)
        pages.append(t)

    outputs: list[Path] = []
    if pages:
        body = join_pages(pages) if join else "\n\n".join(pages)
        base = safe_filename(name)
        if split:
            chunks = split_chapters(body)
            folder = out_dir / base
            folder.mkdir(parents=True, exist_ok=True)
            for old in folder.glob("*.md"):
                old.unlink()
            for i, (title, chunk) in enumerate(chunks, 1):
                path = folder / f"{i:02d} - {safe_filename(title)}.md"
                atomic_write(path, chunk + "\n")
                outputs.append(path)
        else:
            path = out_dir / f"{base}.md"
            atomic_write(path, body + "\n")
            outputs.append(path)
    return {"outputs": outputs, "missing": missing, "review": review}


# ----------------------------------------------------------------------------
# Xử lý một cuốn sách
# ----------------------------------------------------------------------------
def process_book(pdf: Path, args, out_dir: Path, transcriber: Transcriber | None) -> dict:
    name = book_name(pdf)
    log(f"\n=== {name} ===")
    res = {"name": name, "failed": [], "quota_stop": False, "runtime_stop": False, "skipped": False,
           "missing": [], "review": [], "outputs": []}
    work = out_dir / ".pages" / safe_filename(name)

    try:
        doc = fitz.open(str(pdf))
    except Exception as e:  # noqa: BLE001
        log(f"  ✘ Không mở được PDF: {e}")
        res["skipped"] = True
        return res

    with doc:
        if doc.needs_pass:
            log("  ✘ PDF có mật khẩu, bỏ qua.")
            res["skipped"] = True
            return res
        total = doc.page_count
        meta = {"pdf_size": pdf.stat().st_size, "pages": total}
        meta_path = work / "meta.json"

        if not args.test:
            if args.force and work.exists():
                shutil.rmtree(work)
            work.mkdir(parents=True, exist_ok=True)
            if meta_path.exists():
                try:
                    old = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    old = {}
                if old and (old.get("pdf_size") != meta["pdf_size"] or old.get("pages") != total):
                    log("  ⚠ PDF này khác với lần chạy trước (kích thước hoặc số trang). "
                        "Dùng --force để làm lại từ đầu.")
                    res["skipped"] = True
                    return res
            else:
                atomic_write(meta_path, json.dumps(meta))

        src_path = work / "sources.json"
        sources: dict[str, str] = {}
        if not args.test and src_path.exists():
            try:
                sources = json.loads(src_path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                sources = {}
        redo = getattr(args, "redo_set", set())

        if not args.merge_only:
            spec = args.pages or ("1-3" if args.test else "")
            pages = parse_pages(spec, total)
            if args.test:
                todo = pages
                already = 0
            else:
                todo = [n for n in pages
                        if not (work / f"p{n:05d}.md").exists()
                        or sources.get(str(n), "").replace(" (trả phí)", "") in redo]
                already = len(pages) - len(todo)
            ppr = args.pages_per_req
            log(f"  {total} trang | chọn {len(pages)} | đã xong {already} | cần làm {len(todo)}"
                f" | {ppr} trang/request (Flash-Lite: {transcriber.lite_pages})")

            done = 0
            prev_start = 0.0
            i = 0
            while i < len(todo):
                size = max(1, min(ppr, transcriber.cap(transcriber.cur)))
                batch = todo[i:i + size]
                i += size
                out: dict[int, tuple[str | None, str, str]] = {}
                stop = ""
                t0 = time.monotonic()
                try:
                    if transcriber.out_of_time():
                        raise RuntimeLimit()
                    if prev_start:
                        wait = transcriber.delay_now(args.delay) - (time.monotonic() - prev_start)
                        if wait > 0:
                            transcriber.sleep(wait)
                    prev_start = time.monotonic()
                    t0 = prev_start
                    transcribe_pages(doc, batch, args, transcriber, out)
                except QuotaExhausted:
                    stop = "quota"
                except RuntimeLimit:
                    stop = "runtime"
                except FatalError:
                    raise
                except Exception as e:  # noqa: BLE001
                    for n in batch:
                        out.setdefault(n, (None, f"lỗi bất ngờ: {one_line(str(e))}", ""))

                dt = (time.monotonic() - t0) / max(len(out), 1)
                for n in batch:
                    if n not in out:
                        continue
                    text, note, source = out[n]
                    done += 1
                    if text is None:
                        res["failed"].append(n)
                        log(f"  ✘ trang {n:>4}/{total} thất bại: {note}")
                        continue
                    if args.test:
                        log(f"\n----- TRANG {n} ({transcriber.last_label}, {dt:.0f}s/trang) -----\n{text}\n")
                        continue
                    atomic_write(work / f"p{n:05d}.md", text)
                    sources[str(n)] = source
                    tag = " (trang trống)" if text == SENTINEL else ""
                    extra = f" ⚠ {note}" if note else ""
                    log(f"  ✔ trang {n:>4}/{total} [{done}/{len(todo)}] {len(text)} ký tự, {dt:.0f}s/trang{tag}{extra}")

                if not args.test and any(n in out and out[n][0] is not None for n in batch):
                    atomic_write(src_path, json.dumps(sources, ensure_ascii=False))
                if stop == "quota":
                    res["quota_stop"] = True
                    break
                if stop == "runtime":
                    res["runtime_stop"] = True
                    break

        if args.test:
            return res

        merged = merge_book(name, work, total, out_dir, args.split, not args.no_join)
        res["outputs"] = merged["outputs"]
        res["missing"] = merged["missing"]
        res["review"] = merged["review"]
        if sources:
            counts: dict[str, int] = {}
            for n in range(1, total + 1):
                if (work / f"p{n:05d}.md").exists():
                    m = sources.get(str(n)) or "không rõ"
                    counts[m] = counts.get(m, 0) + 1
            if counts:
                log("  Model đã chép các trang: " + ", ".join(f"{m} {c}" for m, c in sorted(counts.items(), key=lambda x: -x[1])))

    if res["outputs"]:
        shown = res["outputs"][:3]
        for p in shown:
            log(f"  → {p}")
        if len(res["outputs"]) > len(shown):
            log(f"  → ... và {len(res['outputs']) - len(shown)} file khác trong {res['outputs'][0].parent}")
    if res["missing"]:
        log(f"  ⚠ CHƯA ĐỦ: còn thiếu {len(res['missing'])} trang ({fmt_ranges(res['missing'])}). "
            "File gộp hiện tại chưa hoàn chỉnh, chạy lại để làm tiếp.")
    if res["failed"]:
        log(f"  ✘ Trang lỗi trong lần chạy này: {fmt_ranges(res['failed'])} (sẽ tự thử lại lần sau)")
    if res["review"]:
        log(f"  ? Nên soát với sách giấy (có [không rõ]): {fmt_ranges(res['review'])}")
    return res


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name) or default)
    except ValueError:
        return default


def parse_args() -> argparse.Namespace:
    env_delay = env_float("REQUEST_DELAY", DEFAULT_DELAY)
    env_timeout = env_float("REQUEST_TIMEOUT", DEFAULT_TIMEOUT)
    ap = argparse.ArgumentParser(description="PDF scan -> Markdown bằng Gemini (checkpoint theo trang).")
    ap.add_argument("input", nargs="?", help="thư mục chứa PDF hoặc 1 file PDF (mặc định: input_pdfs/)")
    ap.add_argument("--out", help="thư mục kết quả (mặc định: output_md/)")
    ap.add_argument("--book", help="chỉ xử lý sách có tên file chứa chuỗi này")
    ap.add_argument("--pages", help="chỉ xử lý các trang này, ví dụ 1-20,25")
    ap.add_argument("--keys", help="nhiều API key cách nhau dấu phẩy (mặc định: GEMINI_API_KEYS / GEMINI_API_KEY)")
    ap.add_argument("--model", default=os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL,
                    help="tên model, có thể nhiều model cách nhau dấu phẩy (dự phòng khi hết quota hoặc lỗi liên tiếp)")
    ap.add_argument("--pages-per-req", type=int, default=DEFAULT_PAGES_PER_REQ, choices=[1, 2, 3],
                    help=f"số trang gộp trong mỗi request, gửi dạng ảnh rời (mặc định {DEFAULT_PAGES_PER_REQ})")
    ap.add_argument("--lite-pages", type=int, default=DEFAULT_LITE_PAGES, choices=[1, 2, 3],
                    help=f"số trang tối đa mỗi request khi chạy Flash-Lite (mặc định {DEFAULT_LITE_PAGES})")
    ap.add_argument("--allow-paid", action="store_true",
                    help="cho phép dùng GEMINI_PAID_API_KEY khi mọi key miễn phí đã hết quota ngày (mặc định TẮT)")
    ap.add_argument("--paid-model", default=os.environ.get("GEMINI_PAID_MODEL") or DEFAULT_PAID_MODEL,
                    help=f"model dùng với key trả phí (mặc định {DEFAULT_PAID_MODEL})")
    ap.add_argument("--paid-max-pages", type=int, default=DEFAULT_PAID_MAX_PAGES,
                    help=f"trần số trang dùng key trả phí trong MỘT lần chạy (mặc định {DEFAULT_PAID_MAX_PAGES})")
    ap.add_argument("--paid-delay", type=float, default=DEFAULT_PAID_DELAY,
                    help=f"giây nghỉ giữa hai request khi dùng key trả phí (mặc định {DEFAULT_PAID_DELAY:g})")
    ap.add_argument("--dark-threshold", type=float, default=DARK_MEAN,
                    help=f"độ sáng trung bình (0-255) dưới mức này thì tăng tương phản mạnh hơn (mặc định {DARK_MEAN}, 0 = tắt)")
    ap.add_argument("--redo-models", default="",
                    help="làm lại các trang do những model này chép (cách nhau dấu phẩy), ví dụ gemini-3.1-flash-lite")
    ap.add_argument("--delay", type=float, default=env_delay,
                    help=f"giây giữa hai request (mặc định {DEFAULT_DELAY:g}, hoặc biến REQUEST_DELAY)")
    ap.add_argument("--timeout", type=float, default=env_timeout,
                    help=f"giây tối đa chờ MỖI lần gọi Gemini (mặc định {DEFAULT_TIMEOUT:g}, hoặc biến REQUEST_TIMEOUT)")
    ap.add_argument("--switch-after", type=int, default=DEFAULT_SWITCH_AFTER,
                    help=f"số lần lỗi liên tiếp thì chuyển sang cặp (key, model) kế (mặc định {DEFAULT_SWITCH_AFTER})")
    ap.add_argument("--cooldown", type=float, default=DEFAULT_COOLDOWN,
                    help=f"giây một cặp nghỉ sau khi báo hết quota ngày (mặc định {DEFAULT_COOLDOWN:g} = 15 phút)")
    ap.add_argument("--peak-wait", type=float, default=DEFAULT_PEAK_WAIT,
                    help=f"giây một model nghỉ khi máy chủ báo quá tải 503/504 (mặc định {DEFAULT_PEAK_WAIT:g} = 5 phút)")
    ap.add_argument("--peak-retries", type=int, default=DEFAULT_PEAK_RETRIES,
                    help=f"số đợt quá tải liên tiếp cho một request trước khi bỏ qua trang (mặc định {DEFAULT_PEAK_RETRIES})")
    ap.add_argument("--max-runtime", type=float, default=0,
                    help="tổng thời gian chạy tối đa (giây); chạm mức này thì dừng êm, gộp file, exit 0 "
                         "(0 = không giới hạn; GitHub Actions dùng 20400)")
    ap.add_argument("--retries", type=int, default=DEFAULT_RETRIES,
                    help="số lần thử lại khi bị 429 theo phút hoặc lỗi mạng (khi không còn cặp nào để chuyển)")
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    ap.add_argument("--contrast", type=float, default=DEFAULT_CONTRAST,
                    help="hệ số ImageEnhance.Contrast (1.0 = giữ nguyên)")
    ap.add_argument("--no-autocontrast", action="store_true", help="tắt bước kéo giãn histogram")
    ap.add_argument("--chu-de", default="", help='chủ đề sách để Gemini đọc đúng thuật ngữ, ví dụ "nội tiết"')
    ap.add_argument("--split", action="store_true", help="chia mỗi sách thành nhiều file theo chương (tiêu đề H1)")
    ap.add_argument("--no-join", action="store_true", help="không nối đoạn văn bị cắt giữa hai trang")
    ap.add_argument("--force", action="store_true", help="làm lại từ đầu, xóa tiến độ cũ của sách")
    ap.add_argument("--merge-only", action="store_true", help="chỉ gộp lại từ các trang đã có, không gọi API")
    ap.add_argument("--test", action="store_true",
                    help="thử sách đầu tiên (mặc định 3 trang đầu), in ra màn hình, không lưu gì")
    ap.add_argument("--list-models", action="store_true", help="liệt kê model dùng được với key rồi thoát")
    return ap.parse_args()


def main() -> int:
    start = time.monotonic()
    load_dotenv(BASE / ".env")
    args = parse_args()
    deadline = start + args.max_runtime if args.max_runtime and args.max_runtime > 0 else None

    if args.list_models:
        client = get_client(get_keys(args.keys)[0], args.timeout)
        log("Model hỗ trợ generateContent với key của bạn:")
        for m in client.models.list():
            actions = getattr(m, "supported_actions", None) or []
            name = getattr(m, "name", "") or ""
            if "generateContent" in actions and "gemini" in name.lower():
                log("  " + name.replace("models/", ""))
        return 0

    out_dir = to_wsl_path(args.out) if args.out else DEFAULT_OUT
    target = to_wsl_path(args.input) if args.input else DEFAULT_IN
    pdfs = find_pdfs(target, args.book)
    if not pdfs:
        log(f"Không thấy file PDF nào ở: {target}"
            + (f" (lọc theo '{args.book}')" if args.book else ""))
        return 2
    if args.test:
        pdfs = pdfs[:1]

    models = [m.strip() for m in args.model.split(",") if m.strip()]
    args.redo_set = {m.strip() for m in args.redo_models.split(",") if m.strip()}
    paid_key = (os.environ.get("GEMINI_PAID_API_KEY") or "").strip().strip("\"'")
    allow_paid = args.allow_paid or (os.environ.get("ALLOW_PAID", "").strip().lower() in ("1", "true", "yes"))
    if allow_paid and not paid_key and not args.merge_only:
        log("⚠ Có --allow-paid nhưng chưa đặt GEMINI_PAID_API_KEY: bỏ qua key trả phí.")
    keys: list[str] = []
    transcriber = None
    if not args.merge_only:
        keys = get_keys(args.keys)
        user_text = "Chép trang sách trong ảnh sang Markdown theo đúng các quy tắc."
        topic = ""
        if args.chu_de.strip():
            topic = (f" Chủ đề sách: {args.chu_de.strip()} "
                     "(chỉ dùng làm ngữ cảnh để đọc đúng thuật ngữ).")
        transcriber = Transcriber(keys, models, SYSTEM_PROMPT, user_text + topic, topic, args.timeout,
                                  args.retries, args.delay, args.switch_after, args.cooldown, deadline,
                                  args.peak_wait, args.peak_retries, args.lite_pages,
                                  paid_key if allow_paid else "", args.paid_model, args.paid_max_pages,
                                  args.paid_delay)

    pairs = f" | {len(keys)} key x {len(models)} model = {len(keys) * len(models)} cặp" if keys else ""
    runtime = f" | tối đa chạy {args.max_runtime / 60:.0f} phút" if deadline else ""
    if args.merge_only or not paid_key:
        paid_txt = ""
    elif allow_paid:
        paid_txt = f" | key trả phí: BẬT ({args.paid_model}, tối đa {args.paid_max_pages} trang)"
    else:
        paid_txt = " | key trả phí: có nhưng TẮT (thêm --allow-paid để bật)"
    runtime += paid_txt
    log(f"{len(pdfs)} sách | model: {', '.join(models)}{pairs} | {args.pages_per_req} trang/request"
        f" | nghỉ {args.delay:g}s/request | tối đa {args.timeout:g}s/lần gọi | chuyển cặp sau {args.switch_after} lỗi"
        f" | {args.dpi} DPI{runtime} | kết quả: {out_dir}")
    if args.test:
        log("Chế độ thử: không lưu tiến độ, không ghi file kết quả.")

    results = []
    try:
        for pdf in pdfs:
            r = process_book(pdf, args, out_dir, transcriber)
            results.append(r)
            if r["quota_stop"]:
                log("\n⚠ Mọi cặp (key, model) đều đã khóa cứng vì hết quota ngày. Tiến độ đã lưu và file đã gộp; "
                    "chạy lại sau để làm tiếp.\n"
                    "  Quota theo ngày thường reset lúc nửa đêm giờ Thái Bình Dương "
                    "(khoảng 14-15h giờ Việt Nam). Thêm key (Project khác) hoặc model dự phòng để chạy được nhiều hơn.")
                if paid_key and not allow_paid:
                    log("  Bạn có GEMINI_PAID_API_KEY: chạy lại với --allow-paid nếu muốn dùng khi hết quota miễn phí.")
                elif transcriber is not None and transcriber.paid is not None and transcriber.paid_pages >= transcriber.paid_max_pages:
                    log(f"  Đã chạm trần {transcriber.paid_max_pages} trang cho key trả phí (--paid-max-pages).")
                break
            if r["runtime_stop"]:
                log(f"\n⏱ Đã chạm giới hạn --max-runtime ({args.max_runtime:g}s). Dừng êm: tiến độ đã lưu và file đã gộp; "
                    "chạy lại để làm tiếp.")
                break
    except FatalError as e:
        msg = str(e)
        log(f"\n✘ Lỗi không thể tự khắc phục: {msg}")
        low = msg.lower()
        if "not found" in low or "404" in low:
            log("  Gợi ý: tên model sai hoặc đã ngừng. Chạy: uv run process_book.py --list-models "
                "rồi dùng --model hoặc đặt GEMINI_MODEL trong .env")
        elif "api key" in low or "403" in low or "401" in low or "permission" in low:
            log("  Gợi ý: kiểm tra lại GEMINI_API_KEYS / GEMINI_API_KEY (tạo ở https://aistudio.google.com/apikey).")
        return 2
    except KeyboardInterrupt:
        log("\nĐã dừng. Các trang đã xong đã được lưu, chạy lại để làm tiếp.")
        return 130
    finally:
        if transcriber is not None and transcriber.paid is not None and transcriber.paid_reqs:
            log("\n" + transcriber.paid_note())

    if args.test:
        return 0
    if any(r["quota_stop"] or r["runtime_stop"] for r in results):
        return 0  # dừng có chủ đích (hết quota ngày / hết giờ): tiến độ đã lưu, không coi là lỗi
    bad = any(r["failed"] or r["missing"] or r["skipped"] for r in results)
    log("\nXong." if not bad else "\nXong, nhưng còn trang chưa hoàn tất (xem cảnh báo ở trên).")
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("\nĐã dừng.")
        sys.exit(130)
