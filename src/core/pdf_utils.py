"""Các hàm dùng chung để mở, kiểm tra, trích xuất và chia nhỏ PDF."""
from __future__ import annotations

import os
import tempfile
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pymupdf as fitz


class PDFError(Exception):
    """Lỗi PDF có thể hiển thị cho người dùng."""


@dataclass(frozen=True)
class PDFInfo:
    path: Path
    exists: bool
    size_bytes: int = 0
    page_count: int = 0
    encrypted: bool = False
    text_chars: int = 0
    pages_with_text: int = 0
    error: str = ""

    @property
    def needs_ocr(self) -> bool:
        if self.error or not self.page_count:
            return False
        return self.pages_with_text == 0 or (
            self.text_chars / max(1, self.page_count) < 50
        )

    @property
    def too_large(self) -> bool:
        return self.size_bytes > 50 * 1024 * 1024

    @property
    def too_many_pages(self) -> bool:
        return self.page_count > 500

    @property
    def should_chunk(self) -> bool:
        return self.too_large or self.too_many_pages


def validate_pdf(path: str | Path) -> PDFInfo:
    """Kiểm tra file PDF mà không để lỗi làm crash luồng."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        return PDFInfo(pdf_path, False, error="file không tồn tại")
    if not pdf_path.is_file():
        return PDFInfo(pdf_path, False, error="đường dẫn không phải file")
    if pdf_path.suffix.lower() != ".pdf":
        return PDFInfo(pdf_path, True, pdf_path.stat().st_size, error="định dạng không phải PDF")
    try:
        size = pdf_path.stat().st_size
        if size == 0:
            return PDFInfo(pdf_path, True, size, error="file rỗng")
        with open_pdf(pdf_path) as doc:
            if len(doc) == 0:
                return PDFInfo(pdf_path, True, size, error="PDF không có trang")
            encrypted = bool(doc.needs_pass)
            text_chars = 0
            pages_with_text = 0
            for page in doc:
                text = page.get_text("text") or ""
                if text.strip():
                    text_chars += len(text)
                    pages_with_text += 1
            return PDFInfo(
                pdf_path,
                True,
                size,
                len(doc),
                encrypted,
                text_chars,
                pages_with_text,
            )
    except PDFError as exc:
        return PDFInfo(pdf_path, True, pdf_path.stat().st_size, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return PDFInfo(pdf_path, True, pdf_path.stat().st_size, error=f"{type(exc).__name__}: {exc}")


@contextmanager
def open_pdf(path: str | Path) -> Iterator[fitz.Document]:
    """Mở PDF, đồng bộ xử lý file thiếu/rỗng/hỏng/mật khẩu."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise PDFError(f"File không tồn tại: {pdf_path}")
    if not pdf_path.is_file():
        raise PDFError(f"Đường dẫn không phải file: {pdf_path}")
    if pdf_path.stat().st_size == 0:
        raise PDFError(f"File rỗng: {pdf_path}")
    doc = None
    try:
        doc = fitz.open(str(pdf_path))
        if doc.needs_pass:
            raise PDFError(f"PDF đang được mã hóa/mật khẩu: {pdf_path}")
        if len(doc) == 0:
            raise PDFError(f"PDF không có trang: {pdf_path}")
        yield doc
    except PDFError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PDFError(f"Không đọc được cấu trúc/stream PDF: {type(exc).__name__}: {exc}") from exc
    finally:
        if doc is not None:
            doc.close()


def inspect_pdf(path: str | Path) -> PDFInfo:
    return validate_pdf(path)


def extract_pdf_text(path: str | Path) -> str:
    with open_pdf(path) as doc:
        return unicodedata.normalize(
            "NFC",
            "\n".join(page.get_text("text") or "" for page in doc),
        )


def render_pdf_pages(
    path: str | Path,
    out_dir: str | Path,
    *,
    dpi: int = 150,
    first_page: int | None = None,
    last_page: int | None = None,
    prefix: str | None = None,
) -> list[Path]:
    """Render trang thành PNG để OCR hoặc gửi Vision/Gemini."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = prefix or Path(path).stem
    start = 0 if first_page is None else max(0, first_page - 1)
    rendered: list[Path] = []
    with open_pdf(path) as doc:
        end = len(doc) if last_page is None else min(len(doc), last_page)
        for page_idx in range(start, end):
            pix = doc[page_idx].get_pixmap(dpi=dpi)
            img = out / f"{stem}_p{page_idx + 1}.png"
            pix.save(str(img))
            rendered.append(img)
    return rendered


def split_pdf_chunks(
    path: str | Path,
    *,
    pages_per_chunk: int = 50,
    out_dir: str | Path | None = None,
) -> list[Path]:
    """Chia PDF thành các phần an toàn trước khi đẩy qua LLM."""
    if pages_per_chunk < 1:
        raise PDFError("pages_per_chunk phải >= 1")
    source = Path(path)
    temp_dir = Path(out_dir) if out_dir is not None else Path(tempfile.mkdtemp(prefix="docmint-pdf-"))
    temp_dir.mkdir(parents=True, exist_ok=True)
    chunks: list[Path] = []
    with open_pdf(source) as doc:
        for start in range(0, len(doc), pages_per_chunk):
            chunk = fitz.open()
            chunk.insert_pdf(doc, from_page=start, to_page=min(start + pages_per_chunk - 1, len(doc) - 1))
            out = temp_dir / f"{source.stem}_pages_{start + 1}-{min(start + pages_per_chunk, len(doc))}.pdf"
            chunk.save(str(out))
            chunk.close()
            chunks.append(out)
    return chunks


def log_pdf_error(path: str | Path, exc: PDFError | Exception | str) -> str:
    message = str(exc)
    print(f"[PDF] {Path(path).name}: {message}", flush=True)
    return message
