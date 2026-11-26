#!/usr/bin/env python3
"""Kiểm tra file kiến thức triệu chứng (knowledge/*.md).

Kiểm tra:
  1. Mỗi "Trích nguyên văn" có thật trong file chương sách (so khớp sau khi gộp khoảng trắng, không phân biệt hoa/thường,
     CÓ phân biệt dấu). Mỗi trích dẫn nằm trong “ ”; nhiều trích dẫn trong một ô thì đặt liền nhau: “a” “b”.
  2. Mã nguyên nhân (cột "Mã nguyên nhân", hoặc tiêu đề khối "## MÃ — tên") tồn tại trong checklists/CAUSES.md.
  3. Với bảng có cột "Loại" và "Nguồn dữ kiện": giá trị hợp lệ (Loại: G C L IN LY CPL; Nguồn: BS TC K CLS).
  4. ID dòng (bắt đầu bằng KN-) không trùng; ID kết thúc bằng @MÃ phải khớp khối nguyên nhân đang đứng.

Chạy:  python tools/kiem_tra_kien_thuc.py knowledge/dau-nguc.md --nguon knowledge/sources/dau-nguc_bai1.txt
Chỉ dùng thư viện chuẩn. Thoát mã 1 nếu có lỗi.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

CODE_RE = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*")
HEAD_RE = re.compile(r"^##\s+([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*)\s+[—-]\s+")
LOAI = {"G", "C", "L", "IN", "LY", "CPL"}
NGUON_DL = {"BS", "TC", "K", "CLS"}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip().casefold()


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def load_codes(path: Path) -> set[str]:
    codes: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("|"):
            first = cells(line)[0]
            if CODE_RE.fullmatch(first):
                codes.add(first)
    return codes


def strip_quotes(s: str) -> str:
    return s.strip().strip('"\u201c\u201d').strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("knowledge", type=Path)
    ap.add_argument("--nguon", type=Path, required=True, help="file text chương sách")
    ap.add_argument("--causes", type=Path, default=Path("checklists/CAUSES.md"))
    args = ap.parse_args()

    source = norm(args.nguon.read_text(encoding="utf-8"))
    codes = load_codes(args.causes)
    errors: list[str] = []
    seen: set[str] = set()
    rows = quotes = 0
    header: list[str] = []
    cause: str | None = None
    by_type: Counter[str] = Counter()
    by_cause: Counter[str] = Counter()

    for lineno, line in enumerate(args.knowledge.read_text(encoding="utf-8").splitlines(), 1):
        m = HEAD_RE.match(line)
        if m:
            cause = m.group(1)
            if cause not in codes:
                errors.append(f"dòng {lineno}: khối nguyên nhân dùng mã không có trong CAUSES.md: {cause}")
            continue
        if line.startswith("## "):
            cause = None
            continue
        if not line.startswith("|"):
            continue
        row = cells(line)
        if row and row[0] == "ID":
            header = row
            continue
        if not row or not row[0].startswith("KN-"):
            continue
        rows += 1
        rid = row[0]
        if rid in seen:
            errors.append(f"dòng {lineno}: ID trùng {rid}")
        seen.add(rid)
        if "Trích nguyên văn" not in header or len(row) != len(header):
            errors.append(f"dòng {lineno} ({rid}): số cột không khớp tiêu đề")
            continue

        quote_cell = row[header.index("Trích nguyên văn")]
        parts = [p.strip() for p in re.findall(r"\u201c([^\u201d]*)\u201d", quote_cell)]
        if not parts and quote_cell.strip():
            parts = [strip_quotes(quote_cell)]
        if not parts:
            errors.append(f"dòng {lineno} ({rid}): thiếu trích nguyên văn")
        for part in parts:
            quotes += 1
            if norm(part) not in source:
                errors.append(f"dòng {lineno} ({rid}): KHÔNG thấy trong sách: {part[:90]}")

        if "Mã nguyên nhân" in header:
            code_cell = row[header.index("Mã nguyên nhân")]
            if code_cell not in ("", "—", "-"):
                for token in (t.strip() for t in code_cell.split(",")):
                    code = token.lstrip("+-~=").strip()
                    if code and code not in codes:
                        errors.append(f"dòng {lineno} ({rid}): mã không có trong CAUSES.md: {code}")

        if "Loại" in header:
            loai = row[header.index("Loại")]
            by_type[loai] += 1
            if loai not in LOAI:
                errors.append(f"dòng {lineno} ({rid}): Loại không hợp lệ: {loai}")
            if "Nguồn dữ kiện" in header and row[header.index("Nguồn dữ kiện")] not in NGUON_DL:
                errors.append(f"dòng {lineno} ({rid}): Nguồn dữ kiện không hợp lệ: {row[header.index('Nguồn dữ kiện')]}")
            if "@" in rid:
                suffix = rid.rsplit("@", 1)[1]
                if cause is not None and suffix != cause:
                    errors.append(f"dòng {lineno} ({rid}): ID không khớp khối nguyên nhân {cause}")
            if cause:
                by_cause[cause] += 1

    print(f"Đã kiểm tra {rows} dòng, {quotes} trích dẫn, {len(codes)} mã nguyên nhân hợp lệ.")
    if by_type:
        print("Theo Loại: " + ", ".join(f"{k}={v}" for k, v in sorted(by_type.items())))
        print("Theo nguyên nhân: " + ", ".join(f"{k}={v}" for k, v in by_cause.items()))
    if errors:
        print(f"{len(errors)} lỗi:")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: mọi trích dẫn có trong sách, mọi mã và giá trị hợp lệ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
