"""benh_an_sv — lõi chạy bộ skill bệnh án sinh viên (phần I–VI) bằng DeepSeek.

Vị trí đề xuất trong docmint: src/llm/benh_an_sv.py
Gói skill/checklist (giải nén benh-an-skills.zip) đề xuất đặt ở: config/benh_an_sv/
    config/benh_an_sv/skills/<ten-skill>/SKILL.md
    config/benh_an_sv/checklists/{INDEX,CAUSES,dau-nguc,kho-tho,...}.md

Luồng:
    đọc bệnh án (PDF text-layer từ Word / .txt / .md) -> làm sạch nhẹ
    -> chọn checklist theo LÝ DO NHẬP VIỆN (người dùng chỉ định triệu chứng, hoặc tách mục "Lý do nhập viện"
       rồi nhờ DeepSeek chọn một hay nhiều checklist; kết quả luôn được kiểm tra lại với INDEX.md)
    -> bước 1 benh-an-trich-xuat  (I–V)
    -> bước 2 benh-an-ma-tran-nguyen-nhan  (giả thuyết H-U / H-D)
    -> bước 3 benh-an-kham-lam-sang  (VI)
    -> ghi file kết quả + 04_gui_claude.md (gói dán thẳng sang Claude để kiểm tra chéo)

Module này KHÔNG có menu/hỏi đáp tương tác; phần đó do lớp menu gọi run_pipeline().
Hai chỗ có thể thay bằng code sẵn có của docmint (xem tham số của run_pipeline):
    pdf_pages_fn : (Path) -> list[str]   # text từng trang của PDF
    llm          : (system, user, *, effort) -> str
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Protocol

log = logging.getLogger(__name__)

__all__ = [
    "BenhAnError",
    "ScannedPdfError",
    "Config",
    "PipelineResult",
    "read_case_text",
    "load_index",
    "run_pipeline",
    "make_deepseek_llm",
]

# (khoá bước/tên file kết quả, tên thư mục skill)
STAGES: tuple[tuple[str, str], ...] = (
    ("01_trich_xuat", "benh-an-trich-xuat"),
    ("02_ma_tran", "benh-an-ma-tran-nguyen-nhan"),
    ("03_kham", "benh-an-kham-lam-sang"),
)


class BenhAnError(RuntimeError):
    """Lỗi chung của pipeline bệnh án sinh viên."""


class ScannedPdfError(BenhAnError):
    """PDF không có text layer (bản scan) — cần chạy OCR trước."""


# ------------------------------------------------------------------ cấu hình


@dataclass
class Config:
    skills_dir: Path = Path("config/benh_an_sv")
    model: str = field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"))
    effort: str = "max"  # mức suy luận cao nhất của DeepSeek: "high" hoặc "max"
    selector_effort: str = "high"  # bước chọn checklist không cần "max"
    max_tokens: int = 32000
    timeout_s: int = 900
    max_retries: int = 4
    max_case_chars: int = 120_000
    min_chars_per_page: int = 40  # dưới ngưỡng này coi là trang không có text
    resume: bool = True  # bước nào đã có file kết quả thì dùng lại


class LLMFn(Protocol):
    def __call__(self, system: str, user: str, *, effort: str) -> str: ...


PdfPagesFn = Callable[[Path], "list[str]"]
ProgressFn = Callable[[str], None]


@dataclass
class PipelineResult:
    out_dir: Path
    files: dict[str, Path]
    selected_checklists: list[str]
    missing_checklists: list[str]
    reused_stages: list[str]


# ------------------------------------------------------------------ DeepSeek


def make_deepseek_llm(cfg: Config) -> LLMFn:
    """Client DeepSeek mặc định (API tương thích OpenAI). Thay bằng client sẵn có nếu docmint đã có."""
    from openai import OpenAI

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise BenhAnError("Thiếu biến môi trường DEEPSEEK_API_KEY.")
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        timeout=cfg.timeout_s,
    )

    def call(system: str, user: str, *, effort: str) -> str:
        last_err: Optional[Exception] = None
        for attempt in range(1, cfg.max_retries + 1):
            try:
                resp = client.chat.completions.create(
                    model=cfg.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=cfg.max_tokens,
                    # Thinking mode không nhận temperature; đưa tham số qua extra_body để
                    # không phụ thuộc phiên bản SDK.
                    extra_body={"thinking": {"type": "enabled"}, "reasoning_effort": effort},
                )
                choice = resp.choices[0]
                text = (choice.message.content or "").strip()
                if not text:
                    raise BenhAnError("DeepSeek trả về nội dung rỗng.")
                if choice.finish_reason == "length":
                    log.warning("Kết quả bị cắt do max_tokens=%s.", cfg.max_tokens)
                    text += "\n\n[CẢNH BÁO: kết quả bị cắt do chạm giới hạn max_tokens]"
                return text
            except Exception as exc:  # noqa: BLE001 - cần bắt rộng để retry
                last_err = exc
                status = getattr(exc, "status_code", None)
                if status in (400, 401, 402, 403, 404):  # lỗi cấu hình/số dư: retry vô ích
                    raise BenhAnError(f"DeepSeek từ chối yêu cầu (HTTP {status}): {exc}") from exc
                wait = min(60, 3 * 2**attempt)
                log.warning("DeepSeek lỗi (lần %s/%s): %s — chờ %ss", attempt, cfg.max_retries, exc, wait)
                time.sleep(wait)
        raise BenhAnError(f"DeepSeek lỗi sau {cfg.max_retries} lần thử: {last_err}") from last_err

    return call


# ------------------------------------------------------------------ đọc bệnh án

_PUA = re.compile(r"[\ue000-\uf8ff]")  # ký tự private-use (bullet Symbol/Wingdings khi Word xuất PDF)


def _default_pdf_pages(path: Path) -> list[str]:
    import pymupdf as fitz  # PyMuPDF

    with fitz.open(str(path)) as doc:
        return [page.get_text("text", sort=True) for page in doc]


def _normalize_page(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = re.sub(r"^[ \t]*[\ue000-\uf8ff][ \t]*", "- ", text, flags=re.MULTILINE)
    text = _PUA.sub("", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _norm_line(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip().lower())


def clean_pages(pages: list[str]) -> tuple[list[str], list[str]]:
    """Chuẩn hoá ký tự và bỏ header/footer lặp (dòng ngắn xuất hiện ở >= 60% số trang).

    Trả về (các trang đã làm sạch, danh sách dòng đã bỏ để người dùng kiểm tra).
    """
    pages = [_normalize_page(p) for p in pages]
    removed: list[str] = []
    if len(pages) >= 3:
        counter: Counter[str] = Counter()
        for page in pages:
            counter.update({_norm_line(ln) for ln in page.splitlines() if ln.strip()})
        threshold = max(3, int(len(pages) * 0.6))
        repeated = {k for k, v in counter.items() if v >= threshold and len(k) <= 80}
        if repeated:
            cleaned: list[str] = []
            for page in pages:
                kept = []
                for ln in page.splitlines():
                    if _norm_line(ln) in repeated:
                        removed.append(ln.strip())
                    else:
                        kept.append(ln)
                cleaned.append("\n".join(kept).strip())
            pages = cleaned
    return pages, sorted(set(removed))


def read_case_text(
    path: Path | str,
    cfg: Optional[Config] = None,
    pdf_pages_fn: Optional[PdfPagesFn] = None,
) -> tuple[str, dict]:
    """Đọc bệnh án sinh viên -> (văn bản sạch, thông tin phụ cho meta.json)."""
    cfg = cfg or Config()
    path = Path(path)
    if not path.is_file():
        raise BenhAnError(f"Không tìm thấy file bệnh án: {path}")

    suffix = path.suffix.lower()
    info: dict = {"source": path.name}
    if suffix in {".txt", ".md"}:
        text = _normalize_page(path.read_text(encoding="utf-8"))
        info["pages"] = 1
    elif suffix == ".pdf":
        pages = (pdf_pages_fn or _default_pdf_pages)(path)
        if not pages:
            raise BenhAnError("PDF không có trang nào.")
        no_text = [i for i, p in enumerate(pages, 1) if len(p.strip()) < cfg.min_chars_per_page]
        if len(no_text) > len(pages) / 2:
            raise ScannedPdfError(
                f"PDF gần như không có text layer ({len(no_text)}/{len(pages)} trang trống). "
                "Có thể là bản scan: hãy OCR trước rồi chạy lại."
            )
        pages, removed = clean_pages(pages)
        text = "\n\n".join(f"[Trang {i}]\n{p}" for i, p in enumerate(pages, 1) if p.strip())
        info.update({"pages": len(pages), "pages_without_text": no_text, "removed_repeated_lines": removed})
    else:
        raise BenhAnError(f"Định dạng không hỗ trợ: {suffix} (chỉ .pdf, .txt, .md)")

    if len(text) > cfg.max_case_chars:
        raise BenhAnError(
            f"Bệnh án quá dài ({len(text):,} ký tự > {cfg.max_case_chars:,}). "
            "Đây có vẻ là hồ sơ bệnh viện nhiều trang, không phải bệnh án sinh viên."
        )
    info["chars"] = len(text)
    return text, info


# ------------------------------------------------------------------ checklist


@dataclass(frozen=True)
class ChecklistEntry:
    name: str
    file: str


def _read(path: Path) -> str:
    if not path.is_file():
        raise BenhAnError(f"Thiếu file trong gói skill: {path}")
    return path.read_text(encoding="utf-8")


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def load_index(cfg: Config) -> list[ChecklistEntry]:
    """Đọc checklists/INDEX.md -> danh sách (tên triệu chứng, file)."""
    text = _read(cfg.skills_dir / "checklists" / "INDEX.md")
    entries: list[ChecklistEntry] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[1].endswith(".md") and not cells[1].startswith("_"):
            entries.append(ChecklistEntry(cells[0], cells[1]))
    if not entries:
        raise BenhAnError("INDEX.md không có checklist nào.")
    return entries


def resolve_symptoms(names: list[str], index: list[ChecklistEntry]) -> list[ChecklistEntry]:
    """Khớp tên người dùng nhập (không phân biệt dấu/hoa thường, hoặc tên file) với INDEX."""
    chosen: list[ChecklistEntry] = []
    for raw in names:
        key = _fold(raw)
        hit = next(
            (e for e in index if _fold(e.name) == key or _fold(e.file) == key or _fold(Path(e.file).stem) == key),
            None,
        )
        if hit is None:
            have = ", ".join(e.name for e in index)
            raise BenhAnError(f"Chưa có checklist cho '{raw}'. Hiện có: {have}")
        if hit not in chosen:
            chosen.append(hit)
    return chosen


# ---- lý do nhập viện -> checklist

_RE_LDNV = re.compile(r"^\W*(?:ii\b)?\W*l[iy] do (?:(?:nhap|vao) vien|kham)\b")
_RE_HET_MUC = re.compile(r"^\W*(?:iii\b|benh su\b|3\W*benh su\b)")
_RE_TRANG = re.compile(r"^\[Trang \d+\]$")


def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", _fold(s))


def extract_chief_complaint(case_text: str) -> Optional[str]:
    """Tách mục "Lý do nhập viện": từ dòng tiêu đề tới tiêu đề mục III / "Bệnh sử". Không thấy thì trả None."""
    lines = case_text.splitlines()
    for i, line in enumerate(lines):
        if not _RE_LDNV.match(_fold(line)):
            continue
        parts: list[str] = []
        if ":" in line:  # "II. Lý do nhập viện: đau ngực" — nội dung nằm cùng dòng tiêu đề
            parts.append(line.split(":", 1)[1].strip())
        for nxt in lines[i + 1 : i + 31]:
            if _RE_HET_MUC.match(_fold(nxt)):
                break
            if _RE_TRANG.match(nxt.strip()):
                continue
            parts.append(nxt.strip())
        text = " ".join(p for p in parts if p).strip()
        if text:
            return text[:1500]
    return None


_EXTRACT_SYSTEM = (
    "Từ bệnh án sinh viên dưới đây, hãy trích NGUYÊN VĂN (không sửa, không tóm tắt) phần lý do nhập viện "
    "(than phiền chính của bệnh nhân). Chỉ trả về JSON, không giải thích, đúng dạng: "
    '{"ly_do_nhap_vien": "..."}. Nếu không có thì để chuỗi rỗng.'
)


def llm_extract_chief_complaint(case_text: str, llm: LLMFn, cfg: Config) -> Optional[str]:
    """Dự phòng khi không tách được bằng tiêu đề. Kết quả phải là đoạn có thật trong bệnh án, nếu không thì bỏ."""
    raw = llm(_EXTRACT_SYSTEM, case_text[:8000], effort=cfg.selector_effort)
    value = str(_parse_json(raw).get("ly_do_nhap_vien", "")).strip()
    if not value or _collapse(value) not in _collapse(case_text):
        return None
    return value


_SELECTOR_SYSTEM = (
    "Bạn chọn checklist triệu chứng cho một bệnh án sinh viên, CHỈ dựa vào LÝ DO NHẬP VIỆN được cung cấp. "
    "Xác định mọi triệu chứng/than phiền trong lý do nhập viện (có thể có nhiều) rồi chọn các checklist "
    "tương ứng trong danh mục; không suy đoán triệu chứng nằm ngoài lý do nhập viện. "
    "Chỉ trả về JSON, không giải thích, đúng dạng: "
    '{"files": ["ten-file.md"], "trieu_chung_chua_co_checklist": ["..."]}. '
    '"files" chỉ gồm tên file có trong danh mục; triệu chứng trong lý do nhập viện mà danh mục không có '
    "thì đưa vào mảng còn lại, không chọn checklist gần giống."
)


def _parse_json(raw: str) -> dict:
    raw = re.sub(r"```(?:json)?", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def auto_select_checklists(
    chief_complaint: str, index: list[ChecklistEntry], llm: LLMFn, cfg: Config
) -> tuple[list[ChecklistEntry], list[str]]:
    """Chọn một hay nhiều checklist theo lý do nhập viện -> (checklist, triệu chứng chưa có checklist)."""
    catalog = "\n".join(f"- {e.file}: {e.name}" for e in index)
    user = f"DANH MỤC CHECKLIST:\n{catalog}\n\nLÝ DO NHẬP VIỆN:\n{chief_complaint}"
    data = _parse_json(llm(_SELECTOR_SYSTEM, user, effort=cfg.selector_effort))
    by_file = {e.file: e for e in index}
    chosen = [by_file[f] for f in data.get("files", []) if f in by_file]
    missing = [str(x) for x in data.get("trieu_chung_chua_co_checklist", [])]
    if not chosen:  # dự phòng: khớp tên triệu chứng trong lý do nhập viện (không dấu)
        folded = _fold(chief_complaint)
        chosen = [e for e in index if _fold(e.name) in folded]
    if not chosen:
        detail = f" Triệu chứng chưa có checklist: {', '.join(missing)}." if missing else ""
        raise BenhAnError(
            "Lý do nhập viện không khớp checklist nào." + detail +
            f" Hãy chỉ định triệu chứng thủ công (hiện có: {', '.join(e.name for e in index)})."
        )
    return chosen, missing


# ------------------------------------------------------------------ prompt

GLOBAL_RULES = """Bạn hỗ trợ sinh viên Y phân tích BỆNH ÁN SINH VIÊN (đã ẩn danh, dùng cho học tập).
Quy tắc chung, ưu tiên cao nhất, áp dụng cho mọi skill bên dưới:
- Trả lời bằng tiếng Việt.
- Chỉ dùng dữ kiện có trong <BENH_AN> hoặc trong kết quả bước trước. Không bịa triệu chứng, dấu hiệu, tiền căn, số đo.
- Chỉ chọn mục từ các <CHECKLIST> và mã nguyên nhân từ <CAUSES>; nội dung ngoài danh sách phải gắn đúng nhãn mà skill quy định.
- Không có dữ kiện thì ghi "CHƯA KHAI THÁC" (phần khám: "CHƯA GHI NHẬN"). Im lặng không có nghĩa là KHÔNG.
- Không đưa chẩn đoán xác định.
- Các checklist liên quan ĐÃ được chọn sẵn trong <CHECKLIST>: bỏ qua việc đọc INDEX.md hay chọn checklist; vẫn gộp mục trùng theo cột "Gộp với".
- Chỉ xuất kết quả theo định dạng skill yêu cầu, không thêm lời dẫn."""


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL)


def _tag(name: str, content: str, **attrs: str) -> str:
    attr = "".join(f' {k}="{v}"' for k, v in attrs.items())
    return f"<{name}{attr}>\n{content.strip()}\n</{name}>"


def _stage_user(
    key: str,
    *,
    case_text: str,
    prev: dict[str, str],
    causes: str,
    checklists: dict[str, str],
    missing: list[str],
) -> str:
    parts = [_tag("CAUSES", causes)]
    parts += [_tag("CHECKLIST", text, file=fname) for fname, text in checklists.items()]

    if key == "01_trich_xuat":
        if missing:
            parts.append(_tag("TRIEU_CHUNG_CHUA_CO_CHECKLIST", "\n".join(f"- {m}" for m in missing)))
        parts.append(_tag("BENH_AN", case_text))
        task = "Thực hiện skill cho phần I–V của bệnh án trên."
    elif key == "02_ma_tran":
        parts.append(_tag("KET_QUA_TRICH_XUAT", prev["01_trich_xuat"]))
        task = (
            "Thực hiện skill: lập ma trận nguyên nhân × triệu chứng và sinh giả thuyết H-U / H-D, "
            "chỉ dựa trên <KET_QUA_TRICH_XUAT>, <CHECKLIST> và <CAUSES>."
        )
    else:
        parts.append(_tag("GIA_THUYET", prev["02_ma_tran"]))
        parts.append(_tag("BENH_AN", case_text))
        task = (
            "Thực hiện skill cho phần VI. Kết quả khám lâm sàng (nếu có) lấy từ <BENH_AN>; "
            "dấu hiệu nào bệnh án không ghi thì ghi CHƯA GHI NHẬN."
        )
    parts.append(task)
    return "\n\n".join(parts)


CLAUDE_REVIEW_PROMPT = """Đây là một bệnh án sinh viên đã ẩn danh, bộ checklist, và kết quả phân tích từng bước do DeepSeek làm.
Hãy kiểm tra và suy luận tiếp:
1. Dữ kiện nào DeepSeek nêu mà bệnh án không có? (dẫn trích)
2. Mục nào ghi KHÔNG trong khi bệnh án chỉ im lặng?
3. Giả thuyết H-U / H-D có bỏ sót hoặc ép gộp không? Thẻ/dấu hiệu khám nào sai so với kiến thức chuẩn?
4. Sau khi sửa lỗi, viết tiếp các phần VII–XIII (tóm tắt, đặt vấn đề, chẩn đoán sơ bộ và phân biệt, biện luận lâm sàng, đề nghị CLS, biện luận CLS, chẩn đoán xác định) nếu dữ kiện đủ; nếu chưa đủ thì nói rõ thiếu gì.
Chỉ ra từng lỗi kèm trích dẫn nguyên văn từ bệnh án. Trả lời bằng tiếng Việt."""


def build_claude_bundle(case_text: str, outputs: dict[str, str], checklists: dict[str, str], causes: str) -> str:
    parts = [CLAUDE_REVIEW_PROMPT, _tag("BENH_AN", case_text)]
    labels = {
        "01_trich_xuat": "DS_I_V_TRICH_XUAT",
        "02_ma_tran": "DS_MA_TRAN_GIA_THUYET",
        "03_kham": "DS_VI_KHAM_LAM_SANG",
    }
    for key, label in labels.items():
        if key in outputs:
            parts.append(_tag(label, outputs[key]))
    parts.append(_tag("CAUSES", causes))
    parts += [_tag("CHECKLIST", text, file=fname) for fname, text in checklists.items()]
    return "\n\n".join(parts) + "\n"


# ------------------------------------------------------------------ pipeline


def run_pipeline(
    case_path: Path | str,
    out_root: Path | str,
    *,
    symptoms: Optional[list[str]] = None,
    cfg: Optional[Config] = None,
    llm: Optional[LLMFn] = None,
    pdf_pages_fn: Optional[PdfPagesFn] = None,
    on_progress: Optional[ProgressFn] = None,
    force: bool = False,
    chief_complaint: Optional[str] = None,
) -> PipelineResult:
    """Chạy 3 bước cho một bệnh án.

    symptoms: tên triệu chứng người dùng chỉ định (vd ["Đau ngực", "Khó thở"]); None = tự chọn theo lý do nhập viện.
    chief_complaint: lý do nhập viện do người dùng nhập (ưu tiên hơn việc tự tách từ bệnh án); chỉ dùng khi tự chọn.
    force: chạy lại từ đầu, bỏ qua kết quả đã có. Khi một bước phải chạy lại, các bước sau cũng chạy lại.
    """
    cfg = cfg or Config()
    say = on_progress or log.info
    case_path = Path(case_path)

    case_text, case_info = read_case_text(case_path, cfg, pdf_pages_fn)
    say(f"Đã đọc bệnh án: {case_info['chars']:,} ký tự, {case_info['pages']} trang.")

    out_dir = Path(out_root) / case_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "00_benh_an_sach.txt").write_text(case_text, encoding="utf-8")

    llm_holder: list[LLMFn] = []

    def get_llm() -> LLMFn:  # tạo client trễ: chạy lại toàn bộ từ cache thì không cần API key
        if not llm_holder:
            llm_holder.append(llm or make_deepseek_llm(cfg))
        return llm_holder[0]

    index = load_index(cfg)
    meta_path = out_dir / "meta.json"
    old_meta: dict = {}
    if cfg.resume and not force and meta_path.is_file():
        try:
            old_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            old_meta = {}

    missing: list[str] = []
    used_cc: Optional[str] = None
    if symptoms:
        selected = resolve_symptoms(symptoms, index)
    elif old_meta.get("selected_checklists"):
        by_file = {e.file: e for e in index}
        selected = [by_file[f] for f in old_meta["selected_checklists"] if f in by_file]
        missing = old_meta.get("missing_checklists", [])
        used_cc = old_meta.get("chief_complaint")
    else:
        used_cc = (chief_complaint or "").strip() or extract_chief_complaint(case_text)
        if not used_cc:
            say("Không thấy mục lý do nhập viện theo tiêu đề, nhờ DeepSeek trích nguyên văn...")
            used_cc = llm_extract_chief_complaint(case_text, get_llm(), cfg)
        if not used_cc:
            raise BenhAnError(
                "Không xác định được lý do nhập viện. Hãy nhập lý do nhập viện hoặc chỉ định triệu chứng thủ công."
            )
        say(f"Lý do nhập viện: {used_cc[:200]}")
        say("Đang chọn checklist theo lý do nhập viện...")
        selected, missing = auto_select_checklists(used_cc, index, get_llm(), cfg)
    say("Checklist: " + ", ".join(e.name for e in selected))
    if missing:
        say("Chưa có checklist cho: " + ", ".join(missing))

    root = cfg.skills_dir
    causes = _read(root / "checklists" / "CAUSES.md")
    checklists = {e.file: _read(root / "checklists" / e.file) for e in selected}
    skills = {folder: _strip_frontmatter(_read(root / "skills" / folder / "SKILL.md")) for _, folder in STAGES}

    outputs: dict[str, str] = {}
    files: dict[str, Path] = {}
    reused: list[str] = []
    dirty = force or bool(symptoms and symptoms_changed(symptoms, old_meta, index))

    for key, folder in STAGES:
        path = out_dir / f"{key}.md"
        if cfg.resume and not dirty and path.is_file():
            outputs[key] = path.read_text(encoding="utf-8")
            reused.append(key)
            say(f"[{key}] dùng lại kết quả có sẵn.")
        else:
            say(f"[{key}] đang chạy ({cfg.model}, effort={cfg.effort})...")
            started = time.monotonic()
            system = GLOBAL_RULES + "\n\n# SKILL\n" + skills[folder]
            user = _stage_user(
                key, case_text=case_text, prev=outputs, causes=causes, checklists=checklists, missing=missing
            )
            outputs[key] = get_llm()(system, user, effort=cfg.effort)
            path.write_text(outputs[key], encoding="utf-8")
            dirty = True  # các bước sau phụ thuộc bước này
            say(f"[{key}] xong sau {time.monotonic() - started:.0f}s.")
        files[key] = path

    bundle_path = out_dir / "04_gui_claude.md"
    bundle_path.write_text(build_claude_bundle(case_text, outputs, checklists, causes), encoding="utf-8")
    files["04_gui_claude"] = bundle_path

    meta = {
        "case": case_info,
        "model": cfg.model,
        "effort": cfg.effort,
        "chief_complaint": used_cc,
        "selected_checklists": [e.file for e in selected],
        "missing_checklists": missing,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    say(f"Xong. Kết quả ở: {out_dir}")

    return PipelineResult(
        out_dir=out_dir,
        files=files,
        selected_checklists=[e.file for e in selected],
        missing_checklists=missing,
        reused_stages=reused,
    )


def symptoms_changed(symptoms: list[str], old_meta: dict, index: list[ChecklistEntry]) -> bool:
    """True nếu danh sách checklist người dùng chỉ định khác lần chạy trước (phải chạy lại)."""
    old = set(old_meta.get("selected_checklists", []))
    new = {e.file for e in resolve_symptoms(symptoms, index)}
    return bool(old) and old != new


# ------------------------------------------------------------------ chạy thử nhanh (không dùng cho menu)


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Chạy pipeline bệnh án sinh viên (I–VI) bằng DeepSeek.")
    parser.add_argument("case", help="PDF/.txt/.md bệnh án sinh viên")
    parser.add_argument("--out", default="workspace/benh_an_sv", help="thư mục gốc chứa kết quả")
    parser.add_argument("--symptoms", default="", help='vd "Đau ngực,Khó thở"; bỏ trống = tự chọn')
    parser.add_argument("--ly-do", default="", help="lý do nhập viện nhập tay (bỏ trống = tự tách từ bệnh án)")
    parser.add_argument("--effort", default="max", choices=["high", "max"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="  %(message)s")
    names = [s.strip() for s in args.symptoms.split(",") if s.strip()] or None
    try:
        result = run_pipeline(
            args.case,
            args.out,
            symptoms=names,
            cfg=Config(effort=args.effort),
            force=args.force,
            chief_complaint=args.ly_do or None,
        )
    except ScannedPdfError as exc:
        print(f"\n  PDF có vẻ là bản scan, chưa có lớp chữ: {exc}\n  Hãy OCR trước (mục [4]) rồi chọn file đã OCR.")
        return 2
    except BenhAnError as exc:
        print(f"\n  Không thể phân tích bệnh án: {exc}")
        return 1

    print("\n  Các file kết quả:")
    for p in result.files.values():
        print(f"    - {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
