#!/usr/bin/env python3
"""
Tạo ghi chú release + file zip kết quả cho workflow NotebookLM (giảng bài, câu hỏi, mindmap...).
Đọc log của src/notebook/giang_bai.py, src/notebook/tao_cau_hoi.py và src/notebook/tao_media.py.
Chỉ dùng thư viện chuẩn.

Ghi `new_files=<số file mới>` vào $GITHUB_OUTPUT (nếu có).
"""
from __future__ import annotations

import argparse
import os
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

LABELS = {"giang": "Giảng bài", "hoi": "Câu hỏi", "mindmap": "Mindmap",
          "infographic": "Infographic", "video": "Video"}


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n} B"


def human_time(sec: int) -> str:
    h, rem = divmod(max(sec, 0), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h} giờ {m} phút"
    if m:
        return f"{m} phút {s} giây"
    return f"{s} giây"


def parse_log(text: str) -> dict:
    """Lấy từ log: danh sách bài làm xong / bỏ qua / không tìm thấy / lỗi và dòng tổng kết."""
    info = {"list_line": "", "done": [], "skipped": [], "not_found": [], "failed": [],
            "summary": "", "stopped": ""}
    cur = ""
    section = ""
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("Danh sách đang dùng:"):
            info["list_line"] = s
        m = re.match(r"^\[(\d+)/(\d+)\]\s+(?:Bỏ qua \(đã có file\):\s*)?(.*)$", s)
        if m:
            cur = m.group(3)
            if "Bỏ qua (đã có file)" in s:
                info["skipped"].append(cur)
            continue
        if s.startswith("-> Đã lưu") and cur:
            if cur not in info["done"]:
                info["done"].append(cur)
        if s.startswith("Dừng vì"):
            info["stopped"] = s
        if s.startswith("Xong:") and "|" in s:
            info["summary"] = s
        if s.startswith("Không tìm thấy trong nguồn") or s.startswith("Bài lỗi") or s.startswith("Lỗi ("):
            section = "not_found" if s.startswith("Không tìm thấy") else "failed"
            continue
        if section and s.startswith("- "):
            info[section].append(s[2:].strip())
        elif section and not s.startswith("-"):
            section = ""
    return info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="run_log.txt")
    ap.add_argument("--feature", default="giang")
    ap.add_argument("--mode", default="run")
    ap.add_argument("--code", default="0")
    ap.add_argument("--elapsed", type=int, default=0)
    ap.add_argument("--notebook", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--out", required=True, help="thư mục kết quả của chức năng, ví dụ ket_qua/giang_bai")
    ap.add_argument("--marker", default=".nlm_start", help="file mốc: chỉ lấy file mới hơn mốc này")
    ap.add_argument("--zip", default="nlm_output.zip")
    ap.add_argument("--notes", default="release_notes.md")
    args = ap.parse_args()

    log_path = Path(args.log)
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    info = parse_log(text)

    out = Path(args.out)
    marker = Path(args.marker)
    since = marker.stat().st_mtime if marker.exists() else 0.0
    new_files: list[Path] = []
    if out.is_dir():
        for p in sorted(out.rglob("*")):
            if p.is_file() and p.name != ".state.json" and p.stat().st_mtime > since:
                new_files.append(p)

    if new_files:
        with zipfile.ZipFile(args.zip, "w", zipfile.ZIP_DEFLATED) as z:
            for p in new_files:
                z.write(p, p.relative_to(out).as_posix())

    label = LABELS.get(args.feature, args.feature)
    now = datetime.now(timezone(timedelta(hours=7)))
    lines = [f"# {label} (NotebookLM) — {now:%d/%m/%Y %H:%M} (giờ Việt Nam)", ""]
    meta = f"**Chế độ:** `{args.mode}` | **Thời gian chạy:** {human_time(args.elapsed)}"
    if args.notebook:
        meta += f" | **Notebook:** `{args.notebook}…`"
    if args.run_url:
        meta += f" | [Xem log trên Actions]({args.run_url})"
    lines.append(meta)
    if info["list_line"]:
        lines += ["", f"{info['list_line']}"]
    if info["summary"]:
        lines += ["", "## Tổng kết", f"- {info['summary']}"]

    lines += ["", f"## File mới ({len(new_files)})"]
    if new_files:
        for p in new_files[:60]:
            lines.append(f"- `{p.relative_to(out).as_posix()}` ({human_size(p.stat().st_size)})")
        if len(new_files) > 60:
            lines.append(f"- … và {len(new_files) - 60} file khác")
    else:
        lines.append("- Không có file mới trong lần chạy này.")
    if info["skipped"]:
        lines += ["", f"## Bỏ qua vì đã có file ({len(info['skipped'])})"]
        lines += [f"- {t}" for t in info["skipped"][:30]]
        if len(info["skipped"]) > 30:
            lines.append(f"- … và {len(info['skipped']) - 30} bài khác")
    if info["not_found"]:
        lines += ["", f"## NotebookLM báo không tìm thấy trong nguồn ({len(info['not_found'])})",
                  "Kiểm tra tên bài có khớp mục lục và nguồn đã đủ trang chưa."]
        lines += [f"- {t}" for t in info["not_found"]]
    if info["failed"]:
        lines += ["", f"## Lỗi ({len(info['failed'])}), chạy lại sẽ tự thử lại"]
        lines += [f"- {t}" for t in info["failed"]]
    if info["stopped"]:
        lines += ["", f"> {info['stopped']}"]
    if args.code not in ("0", ""):
        lines += ["", f"> Script thoát với mã {args.code} (xem log đầy đủ)."]
    lines += ["", "File đính kèm: `nlm_output.zip` (chỉ các file mới của lần chạy này) và `run_log.txt` (log đầy đủ)."]

    Path(args.notes).write_text("\n".join(lines) + "\n", encoding="utf-8")
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"new_files={len(new_files)}\n")
    print(f"Đã tạo {args.notes} (file mới: {len(new_files)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
