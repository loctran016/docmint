from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
  sys.path.insert(0, str(ROOT_DIR))

from dataclasses import dataclass, field
import os
import re
from typing import Optional
import fitz  # PyMuPDF

from src.core.common import CONFIG_DIR, ROOT_DIR, WORKSPACE_DIR

DEFAULT_IMG_DIR = ROOT_DIR / ".cache" / "exam_imgs"

# --- REGEX PATTERNS ---
SECTION_MAP = {
    r"giải phẫu(?!\s*bệnh)": 1,
    r"mô phôi(?:\s*[-–]\s*(?:gpb|giải phẫu bệnh))?|giải phẫu bệnh": 1,
    r"sinh lý(?:\s*[-–]\s*vi sinh)?(?!\s*bệnh)": 2,
    r"sinh lý bệnh|vi sinh|ký sinh": 2,
    r"dược lý|thuốc": 3,
    r"cận lâm sàng|lâm sàng": 4,
}

SHARED_CTX_RE = re.compile(
    r"^(\d+)\s*câu\s*tiếp\s*theo\s*[:\-]\s*(.+)", re.IGNORECASE
)
SHARED_IMG_RE = re.compile(
    r"^Hình\s*chung\s*câu\s*([\d,\s\-và]+)\s*[:\-]?", re.IGNORECASE
)
Q_START_RE = re.compile(r"^(?:Câu\s*)?(\d+)\s*[:.,]\s*(.+)", re.IGNORECASE)
OPT_START_RE = re.compile(r"^([A-D])\s*[.)]\s*(.*)", re.IGNORECASE)

HEADER_FOOTER_RE = re.compile(
    r"^(?:Lưu hành nội bộ|Câu lạc bộ Bồ Câu Xanh.*|Tủ Sách Khoa Y|"
    r"S\.E\.E\. CLUB.*|Tổng hợp.*|From\s*:.*)$",
    re.IGNORECASE,
)
NOISE_SPLIT_RE = re.compile(
    r"(https?://|Giới thiệu về đoạn trích|Lưu hành nội bộ)",
    re.IGNORECASE,
)
ENGLISH_SNIPPET_RE = re.compile(r"^(?:[A-Za-z0-9(),.;:'\"/\-]+\s+){12,}")

IMAGE_HINT_RE = re.compile(
    r"(hình\s*(?:dưới|bên|sau|trên|\d)|siêu âm|sơ đồ|biểu đồ|"
    r"x[\s\-]?quang|\bct\b|\bmri\b|tiêu bản|mũi tên)",
    re.IGNORECASE,
)

# Bắt ý định tính toán thực sự (kể cả cặp cân nặng + chiều cao để tính BMI)
MATH_INTENT_RE = re.compile(
    r"(tính\b|bao nhiêu\s*(?:g|gam|kg|kcal|ml|lít|%|nhịp|lần|tuần|tháng)|"
    r"chuyển hóa cơ bản|\bbmi\b|nhịp tim tối đa|tổng năng lượng|"
    r"chiếm bao nhiêu|tỷ lệ|xác suất|kiểu gen|tần số alen|"
    r"(?:cân nặng|nặng)\s*\d+(?:[.,]\d+)?\s*kg.*(?:chiều cao|cao)\s*\d|"
    r"(?:chiều cao|cao)\s*\d+(?:[.,]\d+)?\s*m.*(?:cân nặng|nặng)\s*\d)",
    re.IGNORECASE,
)

CLINICAL_RE = re.compile(
    r"(bệnh nhân|\bbn\b|\b(?:nam|nữ|ông|bà|cô|anh|chú|bác|cụ|trẻ|bé)\b\s*,?\s*\d*\s*tuổi|"
    r"vào viện|nhập viện|khám thấy|tiền căn|xét nghiệm|hồi sức|xử trí|chẩn"
    r" đoán)",
    re.IGNORECASE,
)


@dataclass
class QuestionItem:
  id: str
  q_num: str
  stem: str
  options: list[str] = field(default_factory=list)
  raw_key: Optional[str] = None
  student_note: str = ""
  hint_group: Optional[int] = None
  has_image: bool = False
  image_path: Optional[str] = None
  bucket: str = "direct_recall"
  page_idx: int = 0
  page_has_img: bool = False


def save_page_snapshot(
    doc: fitz.Document, page_idx: int, out_dir: str | Path, q_id: str
) -> str:
  """Render ảnh trang PDF cho câu hỏi có hình ảnh (image_pipeline)."""
  out_path = Path(out_dir)
  out_path.mkdir(parents=True, exist_ok=True)
  img_file = out_path / f"{q_id}_p{page_idx + 1}.png"
  if not img_file.exists():
    pix = doc[page_idx].get_pixmap(dpi=150)
    pix.save(str(img_file))
  return str(img_file)


def _is_watermark(span: dict) -> bool:
  size = span.get("size", 11)
  color = span.get("color", 0)
  r, g, b = (color >> 16) & 255, (color >> 8) & 255, color & 255
  is_faint_gray = (r > 175 and g > 175 and b > 175) and not (
      r == 255 and g == 255 and b == 255
  )
  return size > 22 or is_faint_gray


def _is_highlighted_color(color_int: int) -> bool:
  r, g, b = (color_int >> 16) & 255, (color_int >> 8) & 255, color_int & 255
  return max(r, g, b) - min(r, g, b) > 45 and max(r, g, b) > 100


def _extract_clean_lines(doc: fitz.Document) -> list[dict]:
  extracted = []
  for page_idx, page in enumerate(doc):
    has_page_img = len(page.get_images(full=True)) > 0
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
      if b["type"] != 0:
        continue
      for line in b["lines"]:
        parts, has_color = [], False
        for span in line["spans"]:
          if _is_watermark(span):
            continue
          txt = span["text"]
          if txt.strip():
            parts.append(txt)
            if _is_highlighted_color(span.get("color", 0)):
              has_color = True
        full_line = "".join(parts).strip()
        if full_line:
          extracted.append({
              "text": full_line,
              "colored": has_color,
              "page": page_idx,
              "page_has_img": has_page_img,
          })
  return extracted


def _finalize_question(
    q: QuestionItem,
    doc: Optional[fitz.Document],
    img_out_dir: str | Path,
    shared_img_map: dict[str, int],
) -> None:
  """Chốt nhận diện hình ảnh trên toàn bộ stem đã ghép đủ và xuất ảnh trang PDF."""
  q.stem = re.sub(r"\s+", " ", q.stem).strip()
  q.options = [re.sub(r"\s+", " ", opt).strip() for opt in q.options]

  if q.q_num in shared_img_map:
    q.has_image = True
    q.page_idx = shared_img_map[q.q_num]
  elif q.page_has_img and IMAGE_HINT_RE.search(q.stem):
    q.has_image = True

  if q.has_image and doc is not None and not q.image_path:
    q.image_path = save_page_snapshot(doc, q.page_idx, img_out_dir, q.id)


def parse_questions(
    lines: list[dict],
    doc: Optional[fitz.Document] = None,
    img_out_dir: str | Path = DEFAULT_IMG_DIR,
) -> list[QuestionItem]:
  questions: list[QuestionItem] = []
  curr_q: Optional[QuestionItem] = None
  curr_group: Optional[int] = None
  shared_ctx: str = ""
  shared_remaining: int = 0
  shared_img_map: dict[str, int] = {}

  for row in lines:
    text = NOISE_SPLIT_RE.split(row["text"])[0].strip()
    if (
        not text
        or text.isdigit()
        or HEADER_FOOTER_RE.match(text)
        or ENGLISH_SNIPPET_RE.match(text)
    ):
      continue

    # 1. Tiêu đề phân môn (GIẢI PHẪU, SINH LÝ, DƯỢC LÝ...)
    clean_sec = text.rstrip(":").strip()
    if len(clean_sec.split()) <= 6:
      matched_sec = False
      for pat, grp_id in SECTION_MAP.items():
        if re.fullmatch(pat, clean_sec, re.IGNORECASE):
          curr_group = grp_id
          matched_sec = True
          break
      if matched_sec:
        continue

    # 2. Dòng dẫn hình chung ("Hình chung câu 102, 103:")
    m_simg = SHARED_IMG_RE.match(text)
    if m_simg:
      for num in re.findall(r"\d+", m_simg.group(1)):
        shared_img_map[num] = row["page"]
      continue

    # 3. Chùm câu hỏi ("4 câu tiếp theo: ...")
    m_shared = SHARED_CTX_RE.match(text)
    if m_shared:
      shared_remaining = int(m_shared.group(1))
      shared_ctx = m_shared.group(2).strip()
      continue

    # 4. Bắt đầu câu hỏi mới
    m_q = Q_START_RE.match(text)
    if m_q:
      if curr_q:
        _finalize_question(curr_q, doc, img_out_dir, shared_img_map)
        questions.append(curr_q)
      q_num, stem_part = m_q.group(1), m_q.group(2).strip()
      if shared_remaining > 0:
        stem_part = f"[{shared_ctx}] {stem_part}"
        shared_remaining -= 1
      curr_q = QuestionItem(
          id=f"Q{q_num}_{len(questions) + 1}",
          q_num=q_num,
          stem=stem_part,
          hint_group=curr_group,
          page_idx=row["page"],
          page_has_img=row["page_has_img"],
      )
      continue

    if not curr_q:
      continue

    # 5. Bắt đầu đáp án A/B/C/D
    m_opt = OPT_START_RE.match(text)
    if m_opt:
      letter, opt_body = m_opt.group(1).upper(), m_opt.group(2).strip()
      # Chỉ tách note ghi tay khi vế sau ' - ' là câu giải thích dài (>= 4 từ)
      if " - " in opt_body:
        main_opt, note = opt_body.split(" - ", 1)
        if len(note.split()) >= 4:
          opt_body = main_opt.strip()
          curr_q.student_note = f"{curr_q.student_note}; {note.strip()}".strip(
              "; "
          )
      curr_q.options.append(f"{letter}. {opt_body}")
      if row["colored"] and not curr_q.raw_key:
        curr_q.raw_key = letter
    else:
      if curr_q.options:
        curr_q.options[-1] = f"{curr_q.options[-1]} {text}".strip()
        if row["colored"] and not curr_q.raw_key:
          curr_q.raw_key = curr_q.options[-1][0]
      else:
        curr_q.stem = f"{curr_q.stem} {text}".strip()

  if curr_q:
    _finalize_question(curr_q, doc, img_out_dir, shared_img_map)
    questions.append(curr_q)
  return questions


def preprocess_pdf(
    pdf_path: str | Path, img_out_dir: str | Path = DEFAULT_IMG_DIR
) -> list[QuestionItem]:
  """Hàm chính đọc file PDF đề thi, trích xuất câu hỏi và xuất ảnh trang nếu có."""
  doc = fitz.open(str(pdf_path))
  try:
    lines = _extract_clean_lines(doc)
    return parse_questions(lines, doc=doc, img_out_dir=img_out_dir)
  finally:
    doc.close()


def configure_formula_mode(questions: list[QuestionItem]) -> str:
  total = len(questions)
  calc_count = sum(1 for q in questions if MATH_INTENT_RE.search(q.stem))
  ratio = (calc_count / total * 100) if total else 0.0
  default_choice = "1" if calc_count > 0 else "3"

  print(
      f"[Pre-Router] Phát hiện {calc_count}/{total} câu ({ratio:.1f}%) có phép"
      " tính."
  )
  print(
      "Chế độ formula_work: [1] Chỉ câu tính toán | [2] Toàn bộ | [3] Tắt"
      f" (Enter={default_choice}): ",
      end="",
  )
  choice = input().strip() or default_choice
  return {"1": "calc_only", "2": "all", "3": "off"}.get(choice, "calc_only")


def route_and_batch(
    questions: list[QuestionItem], formula_mode: str
) -> list[dict]:
  buckets: dict[str, list[QuestionItem]] = {
      "image_pipeline": [],
      "calculation_step": [],
      "clinical_deep": [],
      "direct_recall": [],
  }

  for q in questions:
    if q.has_image:
      q.bucket = "image_pipeline"
      q.hint_group = 5
    elif MATH_INTENT_RE.search(q.stem):
      q.bucket = "calculation_step"
    elif len(q.stem.split()) >= 30 or CLINICAL_RE.search(q.stem):
      q.bucket = "clinical_deep"
      q.hint_group = q.hint_group or 4
    else:
      q.bucket = "direct_recall"
    buckets[q.bucket].append(q)

  batch_sizes = {
      "image_pipeline": 2,
      "calculation_step": 6,
      "clinical_deep": 6,
      "direct_recall": 18,
  }
  batches = []

  for b_name, items in buckets.items():
    size = batch_sizes[b_name]
    use_formula = (formula_mode == "all") or (
        formula_mode == "calc_only" and b_name == "calculation_step"
    )
    for i in range(0, len(items), size):
      chunk = items[i : i + size]
      payload_items = [
          {
              "id": x.id,
              "stem": x.stem,
              "options": x.options,
              "hint_group": x.hint_group,
              "image_path": x.image_path,
          }
          for x in chunk
      ]
      batches.append({
          "bucket": b_name,
          "require_formula_work": use_formula,
          "questions": payload_items,
          "audit_meta": {
              x.id: {"raw_key": x.raw_key, "student_note": x.student_note}
              for x in chunk
          },
      })
  return batches
