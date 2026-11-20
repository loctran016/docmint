# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf"]
# ///
import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
"""
Kiểm tra PDF ngay trên máy (không cần mạng, không cần NotebookLM):
  - tổng số trang, bao nhiêu trang KHÔNG có lớp chữ (cần OCR)
  - dấu trang (bookmark/mục lục nhúng trong PDF) nếu có

Cách chạy:
    uv run 8_kiem_tra_pdf.py                          # tự tìm trong output_ocr/ rồi input_pdfs/
    uv run 8_kiem_tra_pdf.py /đường/dẫn/sach.pdf
    uv run 8_kiem_tra_pdf.py /đường/dẫn/thư_mục        # kiểm tra mọi PDF trong thư mục
    uv run 8_kiem_tra_pdf.py "C:\\Users\\ten\\Sach"      # đường dẫn Windows cũng được
"""
import sys
from pathlib import Path

from pypdf import PdfReader

from src.core import common

MIN_CHARS = 50          # trang có ít hơn số ký tự này coi như không có chữ
OUTLINE_MAX_DEPTH = 2


def ranges(nums):
    """[1,2,3,7,9,10] -> '1-3, 7, 9-10'"""
    if not nums:
        return "(không có)"
    out, start, prev = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        out.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = n
    out.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(out)


def print_outline(reader, items=None, depth=0):
    items = reader.outline if items is None else items
    for it in items:
        if isinstance(it, list):
            if depth < OUTLINE_MAX_DEPTH:
                print_outline(reader, it, depth + 1)
            continue
        try:
            page = reader.get_destination_page_number(it) + 1
        except Exception:  # noqa: BLE001
            page = "?"
        print("   " + "  " * depth + f"- {it.title}  (trang PDF {page})")


def check(path):
    print(f"\n=== {path.name} ===")
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            reader.decrypt("")
        n = len(reader.pages)
    except Exception as e:  # noqa: BLE001
        print(f"  Không mở được file: {type(e).__name__}: {e}")
        return
    empty = []
    for i, page in enumerate(reader.pages, 1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:  # noqa: BLE001
            text = ""
        if len(text) < MIN_CHARS:
            empty.append(i)
        if i % 50 == 0:
            print(f"  ...đã quét {i}/{n} trang", flush=True)

    with_text = n - len(empty)
    pct = 100 * with_text / n if n else 0
    print(f"  Tổng số trang      : {n}")
    print(f"  Trang có chữ       : {with_text} ({pct:.0f}%)")
    print(f"  Trang KHÔNG có chữ : {len(empty)}  -> {ranges(empty)}")
    if not empty:
        print("  Kết luận: PDF có lớp chữ đầy đủ, NotebookLM đọc được.")
    elif pct >= 95:
        print("  Kết luận: gần như đủ chữ; các trang trống có thể là trang trắng hoặc trang ảnh minh họa.")
    else:
        print("  Kết luận: THIẾU lớp chữ ở nhiều trang -> hãy OCR (menu mục OCR) rồi tải bản OCR lên.")

    try:
        has_outline = bool(reader.outline)
    except Exception:  # noqa: BLE001
        has_outline = False
    if has_outline:
        print("  Dấu trang (bookmark) trong PDF:")
        print_outline(reader)
    else:
        print("  PDF không có dấu trang (bookmark).")


def collect(args):
    targets = args or [str(d) for d in (common.DEFAULT_OUTPUT_OCR, common.DEFAULT_INPUT_PDFS)
                       if d.is_dir() and any(d.glob("*.[pP][dD][fF]"))][:1]
    if not targets:
        raise SystemExit("Không thấy PDF nào. Truyền đường dẫn file/thư mục PDF.")
    files = []
    for t in targets:
        p = Path(common.to_wsl_path(t))
        if p.is_dir():
            files += sorted(x for x in p.iterdir() if x.suffix.lower() == ".pdf")
        elif p.exists():
            files.append(p)
        else:
            print(f"Không thấy: {t}")
    if not files:
        raise SystemExit("Không có file PDF để kiểm tra.")
    return files


if __name__ == "__main__":
    for f in collect(sys.argv[1:]):
        check(f)
