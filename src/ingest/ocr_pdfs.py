# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
"""
OCR hàng loạt: PDF scan (chỉ là ảnh) -> PDF có lớp chữ để NotebookLM đọc được.

Cách dùng:
    uv run 3_ocr_pdfs.py                          # đọc thư mục input_pdfs/, ghi ra output_ocr/
    uv run 3_ocr_pdfs.py /đường/dẫn/thư_mục       # thư mục bất kỳ chứa các file PDF
    uv run 3_ocr_pdfs.py "C:\\Users\\ten\\Sach"     # đường dẫn Windows (dùng được cả trên WSL)
    uv run 3_ocr_pdfs.py thư_mục_vào thư_mục_ra
    uv run 3_ocr_pdfs.py --langs vie --jobs 1

Kết quả: output_ocr/<tên file sách> - OCR.pdf
Chỉ quét các file .pdf nằm trực tiếp trong thư mục. File đã có kết quả sẽ được bỏ qua.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from src.core import common
from src.core.pdf_utils import inspect_pdf, log_pdf_error


def ocr_command():
    exe = shutil.which("ocrmypdf")
    if exe:
        return [exe]
    uv = shutil.which("uv")
    if uv:
        # uv tự tải ocrmypdf (cần Tesseract và Ghostscript đã cài sẵn, xem bước cài đặt OCR)
        return [uv, "run", "--no-project", "--with", "ocrmypdf", "python", "-m", "ocrmypdf"]
    raise SystemExit("Không tìm thấy ocrmypdf hoặc uv. Hãy chạy bước 'Cài & set-up OCR' trước.")


def main():
    ap = argparse.ArgumentParser(description="OCR hàng loạt PDF")
    ap.add_argument("input_dir", nargs="?")
    ap.add_argument("output_dir", nargs="?")
    ap.add_argument("--langs", default=os.environ.get("OCR_LANGS", "vie+eng"),
                    help="ngôn ngữ OCR (mặc định vie+eng)")
    ap.add_argument("--jobs", type=int,
                    default=int(os.environ.get("OCR_JOBS", min(os.cpu_count() or 2, 4))),
                    help="số luồng (mặc định tối đa 4)")
    args = ap.parse_args()

    in_dir, in_default = common.resolve_dir("ocr_pdfs_input", common.INPUT_PDFS_DIR, args.input_dir)
    out_dir, out_default = common.resolve_dir("ocr_pdfs_output", common.OUTPUT_OCR_DIR, args.output_dir)
    common.announce_default_dirs([
        ("ocr_pdfs_input", in_default, in_dir),
        ("ocr_pdfs_output", out_default, out_dir),
    ])

    # --- kiểm tra công cụ
    tess = common.find_tesseract()
    if not tess:
        raise SystemExit("Chưa cài Tesseract. Hãy chạy bước 'Cài & set-up OCR' trước.")
    if not common.find_ghostscript():
        raise SystemExit("Chưa cài Ghostscript (OCRmyPDF cần nó). Hãy chạy bước 'Cài & set-up OCR'.")
    have = common.tesseract_langs(tess)
    missing = [lang for lang in args.langs.split("+") if lang not in have]
    if missing:
        raise SystemExit(f"Tesseract thiếu gói ngôn ngữ: {', '.join(missing)}. "
                         "Hãy chạy bước 'Cài & set-up OCR'.")
    if not in_dir.is_dir():
        raise SystemExit(f"Không thấy thư mục: {in_dir}\n"
                         "Hãy tạo thư mục input_pdfs rồi chép PDF vào, hoặc truyền đường dẫn thư mục khác.")

    pdfs = sorted(p for p in in_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
    if not pdfs:
        raise SystemExit(f"Không thấy file PDF nào trong: {in_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ocr_command()
    env = common.tesseract_env()
    print(f"Thư mục vào : {in_dir}")
    print(f"Thư mục ra  : {out_dir}")
    print(f"Ngôn ngữ OCR: {args.langs} | Số luồng: {args.jobs}\n")

    ok = skip = 0
    failed = []
    for pdf in pdfs:
        info = inspect_pdf(pdf)
        if info.error:
            print(f"[lỗi] PDF không hợp lệ: {pdf.name}: {info.error}")
            failed.append(pdf.name)
            continue
        base = pdf.stem
        if base.endswith(" - OCR"):
            continue
        out = out_dir / f"{base} - OCR.pdf"
        if out.exists() and out.stat().st_size > 0:
            print(f"[bỏ qua] đã có: {out}")
            skip += 1
            continue
        print(f"[OCR] {pdf.name}  (sách dày có thể mất nhiều phút)")
        # --skip-text: trang nào đã có chữ thì giữ nguyên, chỉ OCR các trang ảnh
        full = cmd + ["-l", args.langs, "--skip-text", "--output-type", "pdf",
                      "--optimize", "1", "--jobs", str(args.jobs), str(pdf), str(out)]
        try:
            code = subprocess.run(full, env=env).returncode
        except KeyboardInterrupt:
            if out.exists():
                out.unlink()
            raise SystemExit("\nĐã dừng. Chạy lại, các file đã xong sẽ được bỏ qua.")
        if code == 0 and out.exists():
            ok += 1
            print(f"[xong] {out}\n")
        else:
            print(f"[lỗi] không OCR được: {pdf.name} (mã {code})\n")
            if out.exists():
                out.unlink()
            failed.append(pdf.name)

    print("==== TỔNG KẾT ====")
    print(f"OCR xong: {ok} | Bỏ qua (đã có): {skip} | Lỗi: {len(failed)}")
    for n in failed:
        print("  - lỗi:", n)
    print(f"\nKết quả trong: {out_dir}")
    print("Bước tiếp theo: xóa source cũ trên NotebookLM, tải các file '- OCR.pdf' lên,")
    print("chờ xử lý xong rồi hỏi thử một câu về trang đầu sách để chắc chắn nó đọc được.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
