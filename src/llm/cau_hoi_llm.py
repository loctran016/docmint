#!/usr/bin/env python3
"""Mục 14 - Tạo câu hỏi (inpage) bằng LLM.

1) Từ bài giảng (output của giang_bai): sinh câu hỏi JSON theo từng mục của bài.
2) Từ chủ đề mới: hỏi NotebookLM lấy tư liệu, rồi sinh câu hỏi JSON như mục 1.

Đầu ra: workspace/ket_qua/cau_hoi_llm/<subject>/<exam_id>.json
(khớp types/quiz.ts, thêm inpage=true và note_path).

Chạy: uv run src/llm/cau_hoi_llm.py  hoặc  uv run -m src.llm.cau_hoi_llm
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
import random
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

try:
    import readline  # noqa: F401  (giúp input() sửa dòng đúng theo UTF-8)
except ImportError:
    pass

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.core import common  # noqa: E402
from src.core.prompts import render_prompt  # noqa: E402
from src.core.quality_check import slugify_vi  # noqa: E402

# ───────────────────────── Cấu hình ─────────────────────────

OUT_ROOT = common.WORKSPACE_DIR / "ket_qua" / "cau_hoi_llm"
CACHE_ROOT = common.ROOT_DIR / ".cache" / "cau_hoi_llm"

# Thư mục chứa bài giảng (ưu tiên bản đã biên tập). Copilot cần đối chiếu với thực tế.
LESSON_DIR_CANDIDATES = (
    common.WORKSPACE_DIR / "ket_qua" / "polished",
    common.WORKSPACE_DIR / "ket_qua" / "raw",
    common.WORKSPACE_DIR / "ket_qua" / "giang_bai",
    common.WORKSPACE_DIR / "giang_out",
)

GROUPS = {
    1: "Giải phẫu",
    2: "Giải phẫu bệnh",
    3: "Mô phôi",
    4: "Sinh lý",
    5: "Sinh lý bệnh",
    6: "Dược lý",
    7: "Lâm sàng (Câu dài)",
    8: "Hình ảnh",
}

DEFAULT_GROUP = 4
DEFAULT_SO_CAU = 20
OPTION_COUNT = 4
OPTION_KEYS = "ABCD"
MAX_QUESTIONS_PER_CHUNK = 10
MIN_CHARS_CHUNK = 700
MAX_CHARS_CHUNK = 9000
MAX_RETRY = 3
RETRY_SLEEP = 3.0
CALL_SLEEP = 1.0  # nghỉ giữa các lần gọi để đỡ chạm quota gói free
SEC_PER_QUESTION = 60
DUP_RATIO = 0.85
NO_SOURCE = "KHÔNG_CÓ_NGUỒN"
SOURCE_INPAGE = True  # cả hai luồng đều thuộc nhóm "Ôn theo bài" (inpage=true)

SKIP_HEADING_RE = re.compile(
    r"^(tóm tắt( nhanh)?|câu hỏi tự (kiểm tra|luyện)|bài (học )?tiếp theo|tài liệu tham khảo)\b",
    re.I,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
BANNED_OPTION_RE = re.compile(
    r"tất cả (các )?(ý|đáp án|câu|phương án)|không có (đáp án|ý|phương án) nào|"
    r"cả\s+[A-D]\s*(và|,)\s*[A-D]|\bnone of the above\b|\ball of the above\b",
    re.I,
)
LETTER_REF_RE = re.compile(r"\b(đáp án|lựa chọn|phương án|ý|câu|chọn)\s+[A-D]\b", re.I)
CITATION_RE = re.compile(r"\s*\[\d+(?:\s*[,\-–]\s*\d+)*\]")


# ───────────────────────── Adapter (Copilot nối với code có sẵn) ─────────────────────────


def _llm_complete(prompt: str) -> str:
    """Gọi router; ưu tiên Gemini 3.x Flash, dùng DeepSeek khi Gemini lỗi."""
    from src.core import llm_router

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRY + 1):
        router = llm_router.LLMRouter(log=print)
        try:
            result = router._call_gemini_api_json("", prompt)
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"  ⚠ Gemini API lỗi (lần {attempt}/{MAX_RETRY}): {exc}")
            if attempt < MAX_RETRY:
                time.sleep(RETRY_SLEEP * attempt)

    router = llm_router.LLMRouter(log=print)
    try:
        result = router._call_deepseek_json("", prompt)
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Gemini API và DeepSeek đều lỗi. Gemini: {last_error}; DeepSeek: {exc}") from exc


async def _ask_notebooklm_async(question: str) -> str:
    notebook_id = common.read_notebook_id()
    async with common.notebooklm_client(chat_timeout=300) as client:
        return await common.ask_with_retry(
            client, notebook_id, question, max_retry=MAX_RETRY, timeout=300
        ) or ""


def _ask_notebooklm(question: str) -> str:
    """ADAPTER: gửi câu hỏi lên NotebookLM (notebook trong config/notebook_id.txt), trả về câu trả lời.

    Copilot nên thay bằng hàm sẵn có của ask_notebook.py / giang_bai.py nếu chúng đã làm việc này.
    """
    return CITATION_RE.sub("", asyncio.run(_ask_notebooklm_async(question))).strip()


def _publish_to_system(paths: list[Path]) -> bool:
    """Mục 15 không hiện có bước xuất/pub; không thay đổi dữ liệu ngoài output cục bộ."""
    print("⚠ Mục 15 hiện không có handler đăng/đưa dữ liệu lên hệ thống ngoài.")
    return False


def _wait() -> None:
    fn = getattr(common, "wait_for_menu", None)
    if callable(fn):
        fn()
    else:
        input("\nNhấn Enter để quay lại menu...")


def _fix_surrogates(text: str) -> str:
    if not re.search(r"[\ud800-\udfff]", text):
        return text
    try:
        return text.encode("utf-8", "surrogateescape").decode("utf-8")
    except UnicodeDecodeError:
        text = re.sub(r"[\ud800-\udfff]", "", text)
        return unicodedata.normalize("NFC", text)


# ───────────────────────── Tiện ích văn bản ─────────────────────────


def norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[*_`#>]", "", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _s(value: object) -> str:
    return re.sub(r"\s+", " ", value).strip() if isinstance(value, str) else ""


def _hash(*parts: object) -> str:
    return hashlib.md5("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:8]


def read_lesson(path: Path) -> tuple[str, str]:
    raw = path.read_text(encoding="utf-8")
    title = None
    m = FRONTMATTER_RE.match(raw)
    if m:
        tm = re.search(r'^title:\s*"?(.*?)"?\s*$', m.group(1), re.M)
        if tm:
            title = tm.group(1).strip()
        raw = raw[m.end():]
    if not title:
        hm = re.search(r"^#\s+(.+)$", raw, re.M)
        title = hm.group(1).strip() if hm else path.stem
    return title, raw


def clean_body(body: str) -> str:
    """Bỏ phần tóm tắt, câu hỏi tự kiểm tra, lời dẫn cuối bài và dòng kẻ ngang."""
    out: list[str] = []
    skip_level: int | None = None
    for line in body.splitlines():
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip(" *#")
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if skip_level is None and SKIP_HEADING_RE.match(text):
                skip_level = level
                continue
        if skip_level is not None:
            continue
        stripped = line.strip()
        if stripped == "---" or stripped.startswith("📖"):
            continue
        out.append(line)
    return "\n".join(out)


def _split_by_level(lines: list[str], level: int) -> list[dict]:
    sections: list[dict] = []
    current: dict | None = None
    for line in lines:
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) == level:
            current = {"heading": m.group(2).strip(" *#"), "lines": [line]}
            sections.append(current)
        elif current is not None:
            current["lines"].append(line)
    return [{"heading": s["heading"], "text": "\n".join(s["lines"]).strip()} for s in sections]


def _split_oversized(section: dict) -> list[dict]:
    text = section["text"]
    if len(text) <= MAX_CHARS_CHUNK:
        return [section]
    parts: list[str] = []
    buf: list[str] = []
    size = 0
    for line in text.splitlines():
        buf.append(line)
        size += len(line) + 1
        at_break = not line.strip() or line.startswith("#")
        if (size >= MAX_CHARS_CHUNK and at_break) or size >= MAX_CHARS_CHUNK * 1.3:
            parts.append("\n".join(buf).strip())
            buf, size = [], 0
    if "".join(buf).strip():
        parts.append("\n".join(buf).strip())
    out = []
    for i, part in enumerate(parts, 1):
        if i > 1:
            part = f"## {section['heading']} (tiếp {i})\n{part}"
        out.append({"heading": section["heading"], "text": part})
    return out


def split_into_chunks(body: str, fallback_title: str) -> list[dict]:
    lines = body.splitlines()
    sections = _split_by_level(lines, 2) or _split_by_level(lines, 3)
    if not sections:
        text = body.strip()
        sections = [{"heading": fallback_title, "text": text}] if text else []
    parts: list[dict] = []
    for s in sections:
        parts.extend(_split_oversized(s))
    merged: list[dict] = []
    carry: dict | None = None
    for p in parts:
        if carry:
            p = {"heading": carry["heading"], "text": carry["text"] + "\n\n" + p["text"]}
            carry = None
        if len(p["text"]) < MIN_CHARS_CHUNK:
            carry = p
            continue
        merged.append(p)
    if carry:
        if merged:
            merged[-1]["text"] += "\n\n" + carry["text"]
        else:
            merged.append(carry)
    return merged


def allocate(chunks: list[dict], total: int) -> list[int]:
    weights = [max(len(c["text"]), 1) for c in chunks]
    s = sum(weights)
    return [min(MAX_QUESTIONS_PER_CHUNK, max(1, round(total * w / s))) for w in weights]


# ───────────────────────── Phân tích và kiểm tra JSON ─────────────────────────


def parse_json_array(raw: str) -> list[dict]:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end <= start:
            raise ValueError("Không tìm thấy mảng JSON trong phản hồi")
        data = json.loads(text[start:end + 1])
    if isinstance(data, dict):
        for key in ("questions", "cau_hoi", "items"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            raise ValueError("JSON là object nhưng không có danh sách câu hỏi")
    if not isinstance(data, list):
        raise ValueError("JSON không phải mảng")
    return [d for d in data if isinstance(d, dict)]


def _is_grounded(excerpt: str, text: str) -> bool:
    e = norm(excerpt).strip(" .…\"'“”‘’")
    if len(e) < 12:
        return False
    t = norm(text)
    if e in t:
        return True
    m = SequenceMatcher(None, t, e, autojunk=False).find_longest_match(0, len(t), 0, len(e))
    return m.size >= 0.8 * len(e)


def validate_item(raw: dict, chunk_text: str, accepted_norm: list[str]) -> tuple[dict | None, str]:
    stem = _s(raw.get("stem") or raw.get("question") or raw.get("cau_hoi"))
    if len(stem) < 15:
        return None, "stem_ngan"

    opts = raw.get("options")
    if not isinstance(opts, list) or len(opts) != OPTION_COUNT:
        return None, "so_lua_chon"
    texts: list[str] = []
    keys: list[str] = []
    for idx, o in enumerate(opts):
        if isinstance(o, dict):
            t, k = _s(o.get("text")), _s(o.get("key")).upper()
        else:
            t, k = _s(o), ""
        t = re.sub(r"^[A-Da-d][\.\):]\s+", "", t)
        texts.append(t)
        keys.append(k or OPTION_KEYS[idx])
    if len(set(keys)) != OPTION_COUNT:
        keys = list(OPTION_KEYS)
    if any(not t for t in texts):
        return None, "lua_chon_rong"
    if len({norm(t) for t in texts}) != OPTION_COUNT:
        return None, "lua_chon_trung"
    if any(BANNED_OPTION_RE.search(t) for t in texts):
        return None, "lua_chon_cam"

    ans = _s(raw.get("answer") or raw.get("dap_an")).upper()
    if ans in keys:
        answer_idx = keys.index(ans)
    else:
        hits = [i for i, t in enumerate(texts) if norm(t) == norm(ans)]
        if len(hits) != 1:
            return None, "dap_an"
        answer_idx = hits[0]

    explanation = _s(raw.get("explanation") or raw.get("giai_thich"))
    hint = _s(raw.get("hint") or raw.get("goi_y"))
    if len(explanation) < 20:
        return None, "giai_thich"
    if LETTER_REF_RE.search(explanation) or LETTER_REF_RE.search(hint):
        return None, "nhac_chu_cai"

    excerpt = _s(raw.get("excerpt") or raw.get("trich_dan"))
    if not excerpt or not _is_grounded(excerpt, chunk_text):
        return None, "khong_bam_nguon"

    ns = norm(stem)
    for prev in accepted_norm:
        if ns == prev or SequenceMatcher(None, ns, prev).ratio() > DUP_RATIO:
            return None, "trung_cau"

    return {
        "stem": stem,
        "options": texts,
        "answer_idx": answer_idx,
        "hint": hint,
        "explanation": explanation,
        "excerpt": excerpt,
        "norm_stem": ns,
    }, "ok"


def _validate_all(items: list[dict], chunk_text: str, accepted_norm: list[str], limit: int) -> tuple[list[dict], list[str]]:
    seen = list(accepted_norm)
    valid: list[dict] = []
    rejects: list[str] = []
    for raw in items:
        item, reason = validate_item(raw, chunk_text, seen)
        if item is None:
            rejects.append(reason)
            continue
        if len(valid) < limit:
            valid.append(item)
            seen.append(item["norm_stem"])
    return valid, rejects


# ───────────────────────── Sinh câu hỏi cho một đoạn ─────────────────────────


def _da_co_text(accepted: list[dict]) -> str:
    if not accepted:
        return "Chưa có."
    return "\n".join(f"- {a['stem']}" for a in accepted[-12:])


def _generate_for_chunk(
    chunk: dict, n: int, title: str, accepted: list[dict], cache_file: Path
) -> tuple[list[dict], list[str], bool]:
    accepted_norm = [a["norm_stem"] for a in accepted]

    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            valid, rejects = _validate_all(cached, chunk["text"], accepted_norm, n)
            if valid:
                return valid, rejects, True
        except (OSError, json.JSONDecodeError):
            pass

    best_valid: list[dict] = []
    best_rejects: list[str] = []
    best_raw: list[dict] = []
    for attempt in range(1, MAX_RETRY + 1):
        prompt = render_prompt(
            "cau_hoi_bai_giang",
            so_cau=n,
            tieu_de_bai=title,
            da_co=_da_co_text(accepted),
            noi_dung=chunk["text"],
        )
        try:
            raw_items = parse_json_array(_llm_complete(prompt))
        except NotImplementedError:
            raise
        except Exception as exc:  # noqa: BLE001
            print(f"    ! lần {attempt}: {exc}")
            time.sleep(RETRY_SLEEP * attempt)
            continue
        valid, rejects = _validate_all(raw_items, chunk["text"], accepted_norm, n)
        if len(valid) > len(best_valid):
            best_valid, best_rejects, best_raw = valid, rejects, raw_items
        if len(valid) >= max(1, math.ceil(n * 0.7)):
            break
        time.sleep(CALL_SLEEP)

    if best_raw:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(best_raw, ensure_ascii=False, indent=2), encoding="utf-8")
    return best_valid, best_rejects, False


# ───────────────────────── Dựng JSON đầu ra ─────────────────────────


def finalize_questions(items: list[dict], exam_id: str, group_id: int) -> list[dict]:
    out: list[dict] = []
    for num, it in enumerate(items, 1):
        rng = random.Random(f"{exam_id}:{num}")
        order = list(range(OPTION_COUNT))
        rng.shuffle(order)
        texts = [it["options"][j] for j in order]
        answer_key = OPTION_KEYS[order.index(it["answer_idx"])]
        out.append({
            "id": f"{exam_id}_Q{num:02d}",
            "exam_id": exam_id,
            "cohort": "",
            "num": num,
            "group_id": group_id,
            "group_name": GROUPS[group_id],
            "stem": it["stem"],
            "options": [{"key": OPTION_KEYS[i], "text": t} for i, t in enumerate(texts)],
            "answer": answer_key,
            "status": "ai_only",
            "legacy_key": None,
            "student_note": None,
            "hint": it["hint"],
            "formula_work": None,
            "textbook_excerpt": it["excerpt"],
            "explanation": it["explanation"],
            "note_ref": it["heading"],
            "image": None,
        })
    return out


def build_bank(
    *, exam_id: str, title: str, subject: str, subject_label: str, group_id: int,
    questions: list[dict], note_path: str | None, source: str,
) -> dict:
    return {
        "exam_id": exam_id,
        "cohort": "",
        "subject": subject,
        "subject_label": subject_label,
        "title": title,
        "default_time_sec": len(questions) * SEC_PER_QUESTION,
        "question_count": len(questions),
        "inpage": SOURCE_INPAGE,
        "note_path": note_path,
        "source": source,
        "questions": questions,
    }


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _merge_subject_bank(subject_dir: Path, subject: str, subject_label: str) -> None:
    exams: list[dict] = []
    questions: list[dict] = []
    seen: set[str] = set()
    for path in sorted(subject_dir.glob("*.json")):
        if path.name in {"bank.json", "exams-manifest.json"}:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        exam_id = str(payload.get("exam_id") or "").strip()
        if not exam_id or exam_id in seen:
            continue
        seen.add(exam_id)
        exam_questions = payload.get("questions")
        if not isinstance(exam_questions, list):
            exam_questions = []
        exams.append({
            "exam_id": exam_id,
            "cohort": str(payload.get("cohort") or ""),
            "title": str(payload.get("title") or exam_id),
            "default_time_sec": int(payload.get("default_time_sec") or len(exam_questions) * SEC_PER_QUESTION),
            "question_count": len(exam_questions),
        })
        questions.extend(q for q in exam_questions if isinstance(q, dict))

    bank = {
        "subject": unicodedata.normalize("NFC", subject),
        "subject_label": unicodedata.normalize("NFC", subject_label),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_questions": len(questions),
        "exams": exams,
        "questions": questions,
    }
    _write_json(subject_dir / "bank.json", bank)

    subjects = []
    for directory in sorted((p for p in OUT_ROOT.iterdir() if p.is_dir()), key=lambda p: p.name):
        bank_path = directory / "bank.json"
        if not bank_path.is_file():
            continue
        try:
            subject_bank = json.loads(bank_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        manifest_exams = []
        for exam in subject_bank.get("exams", []) if isinstance(subject_bank.get("exams"), list) else []:
            exam_id = str(exam.get("exam_id") or "")
            exam_questions = [
                q for q in subject_bank.get("questions", [])
                if isinstance(q, dict) and str(q.get("exam_id") or "") == exam_id
            ]
            group_counts = {str(g): 0 for g in range(1, 9)}
            conflict_count = 0
            for question in exam_questions:
                try:
                    group_id = int(question.get("group_id"))
                except (TypeError, ValueError):
                    continue
                if str(group_id) in group_counts:
                    group_counts[str(group_id)] += 1
                if question.get("status") == "conflict":
                    conflict_count += 1
            manifest_exams.append({
                "exam_id": exam_id,
                "cohort": str(exam.get("cohort") or ""),
                "title": str(exam.get("title") or exam_id),
                "default_time_sec": int(exam.get("default_time_sec") or 3600),
                "question_count": len(exam_questions),
                "group_counts": group_counts,
                "conflict_count": conflict_count,
            })
        subjects.append({
            "subject": unicodedata.normalize("NFC", str(subject_bank.get("subject") or directory.name)),
            "subject_label": str(subject_bank.get("subject_label") or directory.name),
            "exams": manifest_exams,
        })
    _write_json(
        OUT_ROOT / "exams-manifest.json",
        {"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "subjects": subjects},
    )


def generate_lesson(
    title: str, body: str, *, subject: str, subject_label: str, group_id: int,
    so_cau: int, note_path: str | None, source: str, overwrite: bool = False,
) -> Path:
    exam_id = slugify_vi(
        title,
        fallback="bai",
        max_length=None,
        normalization="NFKD",
        remove_combining_marks=True,
    )
    out_path = OUT_ROOT / subject / f"{exam_id}.json"
    if out_path.exists() and not overwrite:
        print(f"  ↷ Bỏ qua (đã có): {out_path.name}")
        return out_path

    chunks = split_into_chunks(clean_body(body), title)
    if not chunks:
        raise ValueError("Bài không có nội dung để tạo câu hỏi")
    counts = allocate(chunks, so_cau)

    accepted: list[dict] = []
    audit_chunks: list[dict] = []
    for i, (chunk, n) in enumerate(zip(chunks, counts), 1):
        cache_file = CACHE_ROOT / exam_id / f"chunk_{i:02d}_{_hash(n, chunk['text'])}.json"
        valid, rejects, cached = _generate_for_chunk(chunk, n, title, accepted, cache_file)
        for v in valid:
            v["heading"] = chunk["heading"]
        accepted.extend(valid)
        audit_chunks.append({
            "heading": chunk["heading"], "chars": len(chunk["text"]), "requested": n,
            "accepted": len(valid), "from_cache": cached,
            "rejected": {r: rejects.count(r) for r in sorted(set(rejects))},
        })
        print(f"  [{i}/{len(chunks)}] {chunk['heading'][:50]}: {len(valid)}/{n} câu{' (cache)' if cached else ''}")
        if not cached:
            time.sleep(CALL_SLEEP)

    if not accepted:
        raise RuntimeError("Không tạo được câu hỏi hợp lệ nào")

    questions = finalize_questions(accepted, exam_id, group_id)
    bank = build_bank(
        exam_id=exam_id, title=title, subject=subject, subject_label=subject_label,
        group_id=group_id, questions=questions, note_path=note_path, source=source,
    )
    _write_json(out_path, bank)
    _merge_subject_bank(out_path.parent, subject, subject_label)
    _write_json(OUT_ROOT / "_audit" / subject / f"{exam_id}.json", {
        "exam_id": exam_id, "requested": so_cau, "accepted": len(questions), "chunks": audit_chunks,
    })
    print(f"  ✔ {out_path.name}: {len(questions)}/{so_cau} câu")
    return out_path


# ───────────────────────── Giao diện dòng lệnh ─────────────────────────


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        value = _fix_surrogates(input(f"{prompt}{suffix}: ")).strip()
    except EOFError:
        print()
        return default
    return value or default


def _default_subject_display_name(raw_subject: str) -> str:
    raw_subject = unicodedata.normalize("NFC", raw_subject.strip())
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", raw_subject):
        return raw_subject.replace("-", " ").title()
    return raw_subject


def parse_selection(text: str, n: int) -> list[int]:
    text = text.strip().lower()
    if text in ("", "all", "a", "tất cả", "tat ca"):
        return list(range(n))
    picked: set[int] = set()
    for part in text.replace(" ", "").split(","):
        if "-" in part:
            a, _, b = part.partition("-")
            if a.isdigit() and b.isdigit():
                picked.update(range(int(a) - 1, int(b)))
        elif part.isdigit():
            picked.add(int(part) - 1)
    return sorted(i for i in picked if 0 <= i < n)


def _ask_settings() -> dict:
    while True:
        raw_subject = _ask("Môn (slug, vd noi-tiet)")
        subject = slugify_vi(raw_subject)
        if subject:
            break
    label = _ask(
        "Tên hiển thị của môn",
        _default_subject_display_name(raw_subject),
    )
    print("Nhóm môn của câu hỏi:")
    for gid, name in GROUPS.items():
        print(f"  {gid}. {name}")
    raw_gid = _ask("Chọn nhóm 1-8", str(DEFAULT_GROUP))
    group_id = int(raw_gid) if raw_gid.isdigit() and int(raw_gid) in GROUPS else DEFAULT_GROUP
    raw_n = _ask("Số câu mục tiêu mỗi bài", str(DEFAULT_SO_CAU))
    so_cau = int(raw_n) if raw_n.isdigit() and int(raw_n) > 0 else DEFAULT_SO_CAU
    return {"subject": subject, "subject_label": label, "group_id": group_id, "so_cau": so_cau}


def _choose_lesson_dir() -> Path | None:
    cands = [d for d in LESSON_DIR_CANDIDATES if d.is_dir() and any(d.rglob("*.md"))]
    if cands:
        print("Thư mục bài giảng:")
        for i, d in enumerate(cands, 1):
            print(f"  {i}. {d.relative_to(common.ROOT_DIR)} ({len(list(d.rglob('*.md')))} file)")
    raw = _ask("Chọn số hoặc nhập đường dẫn", "1" if cands else "")
    if raw.isdigit() and cands and 1 <= int(raw) <= len(cands):
        return cands[int(raw) - 1]
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = common.ROOT_DIR / path
    return path if path.is_dir() else None


def run_from_lessons() -> int:
    lesson_dir = _choose_lesson_dir()
    if lesson_dir is None:
        print("✖ Không tìm thấy thư mục bài giảng.")
        return 1
    files = [p for p in sorted(lesson_dir.rglob("*.md")) if not p.name.startswith(("_", "."))]
    if not files:
        print("✖ Thư mục không có file .md.")
        return 1

    settings = _ask_settings()
    titles = [read_lesson(p)[0] for p in files]
    print("\nDanh sách bài (✔ = đã có câu hỏi):")
    for i, (p, t) in enumerate(zip(files, titles), 1):
        title_slug = slugify_vi(
            t,
            fallback="bai",
            max_length=None,
            normalization="NFKD",
            remove_combining_marks=True,
        )
        mark = "✔" if (OUT_ROOT / settings["subject"] / f"{title_slug}.json").exists() else " "
        print(f"  {i:>2}. [{mark}] {t}")
    picked = parse_selection(_ask("Chọn bài (vd 1,3-5 hoặc all)", "all"), len(files))
    if not picked:
        print("✖ Chưa chọn bài nào.")
        return 1
    overwrite = _ask("Ghi đè bài đã có? [y/N]", "n").lower().startswith("y")

    written: list[Path] = []
    failed = 0
    for idx in picked:
        path = files[idx]
        title, body = read_lesson(path)
        print(f"\n▶ {title}")
        try:
            relative = path.relative_to(lesson_dir).with_suffix("")
            note_path = "/".join(
                slugify_vi(
                    part,
                    fallback="bai",
                    max_length=None,
                    normalization="NFKD",
                    remove_combining_marks=True,
                )
                for part in relative.parts
            )
            written.append(generate_lesson(
                title, body, note_path=note_path, source="giang_bai", overwrite=overwrite, **settings,
            ))
        except NotImplementedError:
            raise
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  ✖ {exc}")
    return _finish(written, failed)


def _outline_from_notebooklm(chu_de: str) -> list[str]:
    answer = _ask_notebooklm(render_prompt("nlm_dan_y_chu_de", chu_de=chu_de))
    if NO_SOURCE in answer:
        return []
    items = []
    for line in answer.splitlines():
        m = re.match(r"^\s*(?:[-*•]|\d+[\.\)])\s+(.*\S)", line)
        if m:
            items.append(m.group(1).strip(" *"))
    return items[:8]


def run_from_topic() -> int:
    chu_de = unicodedata.normalize("NFC", _ask("Vui lòng nhập chủ đề mới"))
    if not chu_de:
        print("✖ Chưa nhập chủ đề.")
        return 1
    settings = _ask_settings()
    overwrite = _ask("Ghi đè nếu đã có? [y/N]", "n").lower().startswith("y")

    exam_id = slugify_vi(
        chu_de,
        fallback="bai",
        max_length=None,
        normalization="NFKD",
        remove_combining_marks=True,
    )
    if (OUT_ROOT / settings["subject"] / f"{exam_id}.json").exists() and not overwrite:
        print(f"↷ Đã có câu hỏi cho chủ đề này: {exam_id}.json")
        return 0

    print("\n▶ Hỏi NotebookLM: lập dàn ý chủ đề...")
    outline = _outline_from_notebooklm(chu_de) or [chu_de]
    sections: list[str] = []
    for muc in outline:
        print(f"  • {muc}")
        digest = _ask_notebooklm(render_prompt("nlm_tom_luoc_muc", chu_de=chu_de, muc_con=muc))
        if NO_SOURCE in digest or len(digest) < 50:
            print("    (nguồn không có, bỏ qua)")
            continue
        sections.append(f"## {muc}\n\n{digest.strip()}")
        time.sleep(CALL_SLEEP)
    if not sections:
        print("✖ NotebookLM không có tư liệu cho chủ đề này.")
        return 1

    body = f"# {chu_de}\n\n" + "\n\n".join(sections) + "\n"
    source_file = OUT_ROOT / "_nguon" / settings["subject"] / f"{exam_id}.md"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text(body, encoding="utf-8")
    print(f"  ✔ Đã lưu tư liệu: {source_file.relative_to(common.ROOT_DIR)}")

    written: list[Path] = []
    failed = 0
    print(f"\n▶ {chu_de}")
    try:
        written.append(generate_lesson(
            chu_de, body, note_path=None, source="notebooklm", overwrite=overwrite, **settings,
        ))
    except NotImplementedError:
        raise
    except Exception as exc:  # noqa: BLE001
        failed += 1
        print(f"  ✖ {exc}")
    return _finish(written, failed)


def _finish(written: list[Path], failed: int) -> int:
    print(f"\nXong: {len(written)} bài, {failed} lỗi.")
    for p in written:
        print(f"  - {p.relative_to(common.ROOT_DIR)}")
    if written and _ask("Đưa lên hệ thống ngay (như mục 15)? [Y/n]", "y").lower().startswith("y"):
        _publish_to_system(written)
    return 1 if failed else 0


MENU_TEXT = """\
=== 14. Tạo câu hỏi bằng LLM ===
  1. Tạo câu hỏi cho bài giảng (lấy từ output của giang_bai)
  2. Vui lòng nhập chủ đề mới (lấy tư liệu từ NotebookLM)
"""


def main() -> int:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    code = 0
    try:
        print(MENU_TEXT)
        choice = _ask("Chọn [1/2] (Enter để thoát)")
        if choice == "1":
            code = run_from_lessons()
        elif choice == "2":
            code = run_from_topic()
        else:
            print("Đã thoát.")
    except KeyboardInterrupt:
        print("\nĐã hủy.")
        code = 130
    except NotImplementedError as exc:
        print(f"✖ {exc}")
        code = 1
    except Exception as exc:  # noqa: BLE001
        print(f"✖ Lỗi: {exc}")
        code = 1
    finally:
        _wait()
    return code


if __name__ == "__main__":
    sys.exit(main())
