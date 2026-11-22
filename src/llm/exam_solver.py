#!/usr/bin/env python3
"""5-step medical exam solving pipeline for Isolde Full-page Quiz JSON."""
from __future__ import annotations

import argparse
import asyncio
import faulthandler
import hashlib
import json
import os
import re
import shutil
import signal
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

faulthandler.enable()
if hasattr(signal, "SIGUSR1"):
    try:
        faulthandler.register(signal.SIGUSR1)
    except (AttributeError, RuntimeError):
        pass

from src.core import common
from src.core.ai_client import extract_clean_json, parse_list, priority_exam_models
from src.core.llm_router import LLMRouter
from src.core.prompts import render_prompt
from src.llm.exam_preprocessor import (
    QuestionItem,
    configure_formula_mode,
    detect_subject_slug,
    detect_subject_label,
    preprocess_pdf,
    route_and_batch,
    slugify_vi,
)
from src.core.quality_check import (
    clean_exam_strings,
    clean_exam_text,
    normalize_nfc,
    validate_exam_data,
)

DEFAULT_INPUT = common.DE_THI_DIR
DEFAULT_OUTPUT = common.GIAI_DE_DIR
DEFAULT_IMG_DIR = common.EXAM_IMG_DIR
DEFAULT_CACHE_DIR = common.EXAM_CACHE_DIR
GROUP_NAMES = {
    1: "Giải phẫu",
    2: "Giải phẫu bệnh",
    3: "Mô phôi",
    4: "Sinh lý",
    5: "Sinh lý bệnh",
    6: "Dược lý",
    7: "Lâm sàng (Câu dài)",
    8: "Hình ảnh",
}


def prompt_input(msg: str) -> str:
    print(msg, end="", flush=True)
    return input()


def _strict_null(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value or value.upper() in {"N/A", "NA", "NULL"}:
            return None
        return value
    return value


def _normalized_status(value: Any) -> str:
    status = str(value or "").strip().lower()
    return status if status in {"verified", "conflict", "ai_only"} else "ai_only"


def _json_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _valid_batch_cache(entry: Any, subbatch: dict[str, Any]) -> bool:
    if not isinstance(entry, dict) or entry.get("error"):
        return False
    results = entry.get("results")
    if not isinstance(results, list) or not results:
        return False
    expected_ids = {str(q["id"]) for q in subbatch["questions"]}
    got = {str(item.get("id")) for item in results if isinstance(item, dict)}
    if not expected_ids.issubset(got):
        return False
    return all(
        isinstance(item, dict)
        and item.get("answer") is not None
        and str(item.get("answer")).strip() not in {"", "N/A", "NULL"}
        for item in results
        if str(item.get("id")) in expected_ids
    )


def _atomic_json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    data = normalize_nfc(data)
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp_path, path)


def _resolve_cache_path(stem: str, suffix: str) -> Path:
    """Resolve NFC/NFD cache names while preserving an existing cache filename."""
    stem_nfc = unicodedata.normalize("NFC", stem)
    stem_nfd = unicodedata.normalize("NFD", stem)
    target_names = {
        unicodedata.normalize("NFC", f"{stem_nfc}_{suffix}.json"),
        unicodedata.normalize("NFC", f"{stem_nfd}_{suffix}.json"),
    }
    if DEFAULT_CACHE_DIR.is_dir():
        for candidate in DEFAULT_CACHE_DIR.iterdir():
            if candidate.is_file():
                candidate_name = unicodedata.normalize("NFC", candidate.name)
                if candidate_name in target_names:
                    return candidate
    canonical = unicodedata.normalize("NFC", f"{stem}_{suffix}.json")
    return DEFAULT_CACHE_DIR / canonical


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _exam_checkpoint_dir(subject: str, pdf_path: Path) -> Path:
    subject_slug = slugify_vi(subject) or "tong-hop"
    exam_slug = slugify_vi(pdf_path.stem) or "de-thi"
    return common.EXAM_CACHE_DIR / f"{subject_slug}__{exam_slug}"


def _is_quota_or_rate_limit(exc: BaseException) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(token in text for token in (
        "429",
        "quota",
        "rate limit",
        "rate-limit",
        "resource exhausted",
        "too many requests",
    ))


def _gemini_notebook_confirmation(
    done: int,
    theory_count: int,
    image_count: int,
) -> str:
    if done == 0:
        return (
            "Tiếp tục truy xuất dữ liệu từ Gemini Notebook? "
            f"(chỉ truy xuất {theory_count} câu lý thuyết, còn lại "
            f"{image_count} câu hình ảnh) [Y/n]: "
        )
    if 0 < done < theory_count:
        remaining = theory_count - done
        return (
            f"Đã trích xuất dữ liệu từ Gemini Notebook cho {done}/{theory_count} "
            f"câu lý thuyết (còn lại {image_count} câu hình ảnh), "
            f"tiếp tục trích xuất {remaining} câu còn lại? [Y/n]: "
        )
    return (
        f"Đã nạp đủ dữ liệu Gemini Notebook ({theory_count}/{theory_count} "
        "câu lý thuyết) từ bản lưu tự động."
    )


def _options(options: list[str]) -> list[dict[str, str]]:
    result = []
    for option in options:
        match = re.match(r"^\s*([A-D])\s*[.)]\s*(.*)$", option, re.I)
        if match:
            result.append({"key": match.group(1).upper(), "text": match.group(2).strip()})
        else:
            result.append({"key": chr(ord("A") + len(result)), "text": option.strip()})
    return result


def _copy_asset(image_path: str | None, assets_dir: Path) -> str | None:
    if not image_path:
        return None
    source = Path(image_path)
    if not source.exists():
        raise FileNotFoundError(f"Không tìm thấy ảnh câu hỏi: {source}")
    assets_dir.mkdir(parents=True, exist_ok=True)
    target = assets_dir / source.name
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return f"assets/{target.name}"


def _cohort(pdf_path: Path) -> str:
    match = re.search(r"(?<![A-Za-z0-9])(Y\d{2,4})(?!\d)", pdf_path.stem, re.I)
    return match.group(1).upper() if match else ""


def _extract_clean_json_object(raw: str) -> dict[str, Any]:
    try:
        parsed = extract_clean_json(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _resolve_subject(pdf_path: Path, explicit_subject: str) -> tuple[str, bool]:
    if explicit_subject:
        slug = slugify_vi(explicit_subject)
        return slug or "tong-hop", True
    if pdf_path.parent != DEFAULT_INPUT and pdf_path.parent.parent == DEFAULT_INPUT:
        slug = slugify_vi(pdf_path.parent.name)
        if slug:
            return slug, True
    return "", False


async def _step2_classify(
    exam_id: str,
    questions: list[QuestionItem],
    notebook_id: str,
    force: bool,
) -> dict[str, int]:
    cache_path = _resolve_cache_path(exam_id, "step2_grouped")
    if not force and cache_path.is_file():
        data = _load_json(cache_path)
        if isinstance(data, dict) and isinstance(data.get("group_by_id"), dict):
            return {str(k): int(v) for k, v in data["group_by_id"].items()}

    short = [q for q in questions if q.bucket == "short"]
    group_by_id: dict[str, int] = {}
    async with common.notebooklm_client(chat_timeout=300) as client:
        for start in range(0, len(short), 18):
            chunk = short[start:start + 18]
            payload = [
                {"id": q.id, "stem": q.stem, "options": q.options}
                for q in chunk
            ]
            prompt = render_prompt(
                "exam_solver_step2_classify",
                data=json.dumps(payload, ensure_ascii=False),
            )
            result = await common.ask_with_retry(
                client, notebook_id, prompt, max_retry=3, timeout=300
            )
            parsed = _extract_clean_json_object(result)
            for item in parsed.get("groups", []) if isinstance(parsed, dict) else []:
                if not isinstance(item, dict):
                    continue
                try:
                    group = int(item["group_id"])
                except (KeyError, TypeError, ValueError):
                    continue
                if 1 <= group <= 6:
                    group_by_id[str(item["id"])] = group
    for q in short:
        if q.id not in group_by_id:
            group_by_id[q.id] = q.hint_group if q.hint_group in range(1, 7) else 4
    _atomic_json_write(
        cache_path,
        {"exam_id": exam_id, "group_by_id": group_by_id},
    )
    return group_by_id


def _print_distribution(questions: list[QuestionItem], grouped: dict[str, int]) -> None:
    counts = {n: 0 for n in range(1, 9)}
    for q in questions:
        if q.bucket == "short":
            counts[grouped.get(q.id, q.hint_group or 4)] += 1
        elif q.bucket == "long_clinical":
            counts[7] += 1
        elif q.bucket == "image":
            counts[8] += 1
    print("Phân bố câu hỏi:")
    for group_id in range(1, 9):
        print(f"  {group_id}: {GROUP_NAMES[group_id]} = {counts[group_id]}")


async def _step3_rag(
    exam_id: str,
    questions: list[QuestionItem],
    grouped: dict[str, int],
    notebook_id: str,
    force: bool,
    checkpoint_dir: Path | None = None,
) -> dict[str, str]:
    legacy_cache_path = _resolve_cache_path(exam_id, "step3_rag")
    notebook_cache_path = legacy_cache_path
    legacy_checkpoint_path = (
        checkpoint_dir / "notebook_rag.json"
        if checkpoint_dir is not None
        else None
    )
    cache_data = _load_json(notebook_cache_path)
    rag_by_id = {
        str(k): str(v)
        for k, v in cache_data.get("rag_by_id", {}).items()
    } if isinstance(cache_data.get("rag_by_id"), dict) else {}
    theory_ids = {
        q.id for q in questions
        if q.bucket in {"short", "long_clinical"}
    }
    theory_count = len(theory_ids)
    if not rag_by_id and legacy_checkpoint_path is not None:
        checkpoint = _load_json(legacy_checkpoint_path)
        if isinstance(checkpoint.get("rag_by_id"), dict):
            rag_by_id = {
                str(k): str(v)
                for k, v in checkpoint["rag_by_id"].items()
            }
    if force:
        rag_by_id = {}

    done = sum(1 for q_id in theory_ids if q_id in rag_by_id)
    if done == theory_count:
        return rag_by_id

    theory_questions = [
        q for q in questions
        if q.bucket in {"short", "long_clinical"} and q.id not in rag_by_id
    ]
    async with common.notebooklm_client(chat_timeout=300) as client:
        for q in theory_questions:
            payload = [{"id": q.id, "stem": q.stem, "options": q.options}]
            prompt = render_prompt(
                "exam_solver_step3_rag",
                data=json.dumps(payload, ensure_ascii=False),
            )
            while True:
                try:
                    answer = await common.ask_with_retry(
                        client, notebook_id, prompt, max_retry=3, timeout=300
                    )
                    break
                except BaseException as exc:
                    if not _is_quota_or_rate_limit(exc):
                        raise
                    done = sum(1 for q_id in theory_ids if q_id in rag_by_id)
                    print(
                        f"⚠ Chạm giới hạn truy xuất Gemini Notebook tại câu "
                        f"{done}/{theory_count}. Đã tự động lưu tiến độ."
                    )
                    try:
                        choice = prompt_input(
                            "Chọn [1] Chờ 60s rồi thử tiếp | "
                            "[2] Dừng tại đây (lần sau chạy lại sẽ tiếp tục từ câu "
                            f"{done + 1}) [1/2]: "
                        ).strip()
                    except EOFError:
                        choice = "2"
                    if choice == "1":
                        time.sleep(60)
                        continue
                    raise SystemExit(
                        f"Dừng truy xuất Gemini Notebook tại câu {done}/{theory_count}; "
                        "đã tự động lưu tiến độ."
                    )
            parsed = _extract_clean_json_object(answer)
            facts = ""
            for item in parsed.get("rag", []) if isinstance(parsed, dict) else []:
                if isinstance(item, dict) and str(item.get("id")) == q.id:
                    facts = str(item.get("facts") or "").strip()
                    break
            rag_by_id[q.id] = facts
            _atomic_json_write(
                notebook_cache_path,
                {"exam_id": exam_id, "rag_by_id": rag_by_id},
            )
    return rag_by_id


def _validate_results(raw: Any, expected: set[str], require_formula: bool) -> list[dict[str, Any]]:
    if not isinstance(raw, dict) or not isinstance(raw.get("results"), list):
        raise ValueError("LLM không trả về object JSON có trường results")
    results = []
    seen = set()
    for item in raw["results"]:
        if not isinstance(item, dict):
            raise ValueError("Một kết quả LLM không phải object")
        item_id = str(item.get("id", ""))
        try:
            group_id = int(item["group_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Kết quả {item_id or '<không id>'} thiếu group_id") from exc
        if item_id not in expected or item_id in seen or group_id not in range(1, 9):
            raise ValueError(f"Kết quả không hợp lệ: id={item_id!r}, group_id={group_id}")
        answer = str(item.get("answer", "")).strip().upper()
        if answer not in {"A", "B", "C", "D"}:
            raise ValueError(f"Đáp án không hợp lệ cho {item_id}: {answer!r}")
        results.append({
            "id": item_id,
            "group_id": group_id,
            "hint": str(item.get("hint", "")).strip(),
            "formula_work": _strict_null(item.get("formula_work")) if require_formula else None,
            "answer": answer,
            "explanation": str(item.get("explanation", "")).strip(),
        })
        seen.add(item_id)
    if seen != expected:
        raise ValueError(f"LLM bỏ sót câu: {sorted(expected - seen)}")
    return results


def _solve_batch(
    router: LLMRouter,
    batch: dict[str, Any],
    backend: str = "auto",
) -> list[dict[str, Any]]:
    require_formula = bool(batch["require_formula_work"])
    formula_schema = '"str"' if require_formula else "null"
    system = render_prompt("exam_solver_pass1", formula_schema=formula_schema)
    payload = []
    for q in batch["questions"]:
        payload.append({
            "id": q["id"],
            "group_id": q["group_id"],
            "stem": q["stem"],
            "options": q["options"],
            "rag_context": q.get("rag_context", ""),
        })
        if q["group_id"] == 8:
            payload[-1]["image_path"] = q["image_path"]
    raw = router.generate_json(
        system,
        json.dumps({"questions": payload}, ensure_ascii=False),
        image_path=batch.get("image_path"),
        backend=backend,
    )
    return _validate_results(raw, {q["id"] for q in batch["questions"]}, require_formula)


def _audit(result: dict[str, Any], raw_key: str) -> dict[str, Any]:
    raw_key = raw_key.strip().upper()
    result.setdefault("group_id", 8)
    result.setdefault("hint", None)
    result.setdefault("formula_work", None)
    result["status"] = (
        "ai_only" if not raw_key
        else "verified" if result["answer"] == raw_key
        else "conflict"
    )
    return result


def _normalize_exam_question_fields(question: dict[str, Any]) -> dict[str, Any]:
    question = normalize_nfc(question)
    question["textbook_excerpt"] = clean_exam_text(
        _strict_null(question.get("textbook_excerpt")) or ""
    ) or None
    question["stem"] = clean_exam_text(question.get("stem"))
    question["explanation"] = clean_exam_text(question.get("explanation"))
    options = question.get("options")
    if isinstance(options, list):
        for option in options:
            if isinstance(option, dict):
                option["text"] = clean_exam_text(option.get("text"))
    question["student_note"] = clean_exam_text(question.get("student_note"))
    question["note_ref"] = None
    return question


def _group_counts_and_conflicts(questions: list[dict[str, Any]]) -> tuple[dict[str, int], int]:
    group_counts = {str(group_id): 0 for group_id in range(1, 9)}
    conflict_count = 0
    for question in questions:
        try:
            group_id = int(question.get("group_id"))
        except (TypeError, ValueError):
            continue
        if str(group_id) in group_counts:
            group_counts[str(group_id)] += 1
        if _normalized_status(question.get("status")) == "conflict":
            conflict_count += 1
    return group_counts, conflict_count


def _generate_exams_manifest(out_root: Path) -> Path:
    subjects = []
    for subject_dir in sorted((path for path in out_root.iterdir() if path.is_dir()), key=lambda path: path.name):
        bank_path = subject_dir / "bank.json"
        if not bank_path.is_file():
            continue
        try:
            bank = json.loads(bank_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(bank, dict):
            continue

        subject = str(bank.get("subject") or subject_dir.name)
        subject_label = str(
            bank.get("subject_label")
            or subject
        )
        bank_questions = bank.get("questions", [])
        if not isinstance(bank_questions, list):
            bank_questions = []

        exams = []
        bank_exams = bank.get("exams", [])
        if not isinstance(bank_exams, list):
            bank_exams = []
        for exam in bank_exams:
            if not isinstance(exam, dict):
                continue
            exam_id = str(exam.get("exam_id") or "")
            exam_questions = [
                question
                for question in bank_questions
                if isinstance(question, dict) and str(question.get("exam_id") or "") == exam_id
            ]
            group_counts, conflict_count = _group_counts_and_conflicts(exam_questions)
            question_count = len(exam_questions)
            if "question_count" in exam:
                try:
                    question_count = int(exam.get("question_count") or question_count)
                except (TypeError, ValueError):
                    question_count = len(exam_questions)
            try:
                default_time_sec = int(exam.get("default_time_sec") or 3600)
            except (TypeError, ValueError):
                default_time_sec = 3600
            exams.append({
                "exam_id": exam_id,
                "cohort": str(exam.get("cohort") or ""),
                "title": str(exam.get("title") or exam_id),
                "default_time_sec": default_time_sec,
                "question_count": question_count,
                "group_counts": group_counts,
                "conflict_count": conflict_count,
            })

        subjects.append({
            "subject": unicodedata.normalize("NFC", subject),
            "subject_label": subject_label,
            "exams": exams,
        })

    manifest_path = out_root / "exams-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"subjects": subjects}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _export_exam(
    pdf_path: Path,
    out_root: Path,
    subject: str,
    subject_label: str,
    questions: list[QuestionItem],
    results: dict[str, dict[str, Any]],
    rag_by_id: dict[str, str],
) -> Path:
    subject_dir = out_root / subject
    assets_dir = subject_dir / "assets"
    subject_dir.mkdir(parents=True, exist_ok=True)
    exam_id = pdf_path.stem
    exported = []
    used_ids: set[str] = set()
    for q in questions:
        item_id = f"{exam_id}_Q{q.q_num}"
        unique_id = item_id
        suffix = 1
        while unique_id in used_ids:
            unique_id = f"{item_id}_{suffix}"
            suffix += 1
        used_ids.add(unique_id)
        result = results[q.id]
        exported.append({
            "id": unique_id,
            "exam_id": exam_id,
            "cohort": _cohort(pdf_path),
            "num": int(q.q_num) if str(q.q_num).isdigit() else q.q_num,
            "group_id": result["group_id"],
            "group_name": GROUP_NAMES[result["group_id"]],
            "stem": q.stem,
            "options": _options(q.options),
            "answer": result["answer"],
            "status": result["status"],
            "legacy_key": _strict_null(q.raw_key),
            "student_note": _strict_null(q.student_note),
            "hint": result["hint"],
            "formula_work": _strict_null(result["formula_work"]),
            "explanation": result["explanation"],
            "textbook_excerpt": _strict_null(rag_by_id.get(q.id)),
            "note_ref": None,
            "image": _copy_asset(q.image_path, assets_dir),
        })
    payload = {
        "exam_id": unicodedata.normalize("NFC", exam_id),
        "cohort": _cohort(pdf_path),
        "subject": subject,
        "subject_label": unicodedata.normalize("NFC", subject_label),
        "title": unicodedata.normalize("NFC", exam_id),
        "default_time_sec": 3600,
        "question_count": len(exported),
        "questions": exported,
    }
    exam_path = subject_dir / f"{exam_id}.json"
    payload = clean_exam_strings(payload)
    for question in payload["questions"]:
        _normalize_exam_question_fields(question)
    issues = validate_exam_data(payload)
    if issues:
        print("  ⚠ [Gate] JSON đề có cảnh báo bất thường; tạm dừng trước khi ghi file.", flush=True)
        raise ValueError("Gate validation thất bại cho exam JSON; không ghi file")
    exam_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  ✓ Đã xuất file: {exam_path}", flush=True)
    return exam_path


def _merge_bank(subject_dir: Path, subject: str, subject_label: str) -> None:
    exams = []
    questions = []
    seen_exam_ids = set()
    for path in sorted(subject_dir.glob("*.json")):
        if path.name == "bank.json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        exam_id = str(payload.get("exam_id") or "").strip()
        if not exam_id:
            continue
        exam_questions = payload.get("questions", []) or []
        if not isinstance(exam_questions, list):
            exam_questions = []
        for question in exam_questions:
            if isinstance(question, dict):
                _normalize_exam_question_fields(question)
        payload["questions"] = exam_questions
        exam_id = str(payload["exam_id"])
        if exam_id in seen_exam_ids:
            continue
        seen_exam_ids.add(exam_id)
        exams.append({
            "exam_id": exam_id,
            "cohort": payload.get("cohort", ""),
            "title": payload.get("title", exam_id),
            "default_time_sec": payload.get("default_time_sec", 3600),
            "question_count": len(exam_questions),
        })
        questions.extend(_normalize_exam_question_fields(question)
                        for question in exam_questions
                        if isinstance(question, dict))
    bank = {
        "subject": unicodedata.normalize("NFC", subject),
        "subject_label": unicodedata.normalize("NFC", subject_label),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(questions),
        "exams": exams,
        "questions": questions,
    }
    bank_path = subject_dir / "bank.json"
    bank = clean_exam_strings(bank)
    bank_issues = validate_exam_data(bank)
    if bank_issues:
        raise ValueError("Gate validation thất bại cho bank.json; không ghi bank")
    bank_path.write_text(
        json.dumps(bank, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  ✓ Đã xuất file: {bank_path}", flush=True)
    _generate_exams_manifest(subject_dir.parent)


async def solve_exam_async(
    pdf_path: Path,
    out_root: Path,
    subject: str,
    subject_label: str,
    formula_mode: str,
    web_model: str,
    web_gem: str,
    force: bool,
    yes: bool,
    backend: str = "auto",
) -> None:
    exam_id = unicodedata.normalize("NFC", pdf_path.stem)
    questions = preprocess_pdf(pdf_path, DEFAULT_IMG_DIR)
    if not questions:
        raise ValueError(f"Không nhận diện được câu hỏi trong {pdf_path}")

    buckets = route_and_batch(questions, formula_mode)
    notebook_id = common.read_notebook_id()

    grouped = await _step2_classify(exam_id, questions, notebook_id, force)
    for q in questions:
        if q.bucket == "short":
            q.hint_group = grouped.get(q.id, q.hint_group or 4)

    _print_distribution(questions, grouped)
    checkpoint_dir = _exam_checkpoint_dir(subject, pdf_path)
    theory_ids = {
        q.id for q in questions
        if q.bucket in {"short", "long_clinical"}
    }
    image_count = sum(1 for q in questions if q.bucket == "image")
    theory_count = len(theory_ids)
    notebook_cache_path = _resolve_cache_path(exam_id, "step3_rag")
    notebook_cache = _load_json(notebook_cache_path)
    if not notebook_cache and (checkpoint_dir / "notebook_rag.json").is_file():
        notebook_cache = _load_json(checkpoint_dir / "notebook_rag.json")
    if force:
        notebook_cache = {}
    cached_rag = (
        notebook_cache.get("rag_by_id", {})
        if isinstance(notebook_cache.get("rag_by_id"), dict)
        else {}
    )
    done = sum(1 for q_id in theory_ids if q_id in cached_rag)
    remaining = max(0, theory_count - done)

    if done == theory_count:
        print(_gemini_notebook_confirmation(done, theory_count, image_count))
        rag = {str(k): str(v) for k, v in cached_rag.items()}
    else:
        if not yes:
            prompt = _gemini_notebook_confirmation(done, theory_count, image_count)
            try:
                answer = prompt_input(prompt).strip().lower()
            except EOFError:
                print()
                raise SystemExit(
                    "Không có dữ liệu tương tác. Dùng --yes để bỏ gate xác nhận "
                    "Gemini Notebook."
                )
            if answer in {"n", "no", "không", "khong"}:
                raise SystemExit("Đã dừng trước Step 3.")
        rag = await _step3_rag(
            exam_id,
            questions,
            grouped,
            notebook_id,
            force,
            checkpoint_dir,
        )

    router = LLMRouter(web_model=web_model, web_gem=web_gem)
    cache_path = _resolve_cache_path(exam_id, "step4_batches")
    cache = {} if force else _load_json(cache_path)
    batch_results = cache.get("batches", {}) if isinstance(cache.get("batches"), dict) else {}

    subbatches: list[dict[str, Any]] = []
    for bucket in buckets:
        items = bucket["questions"]
        require_formula = bool(bucket["require_formula_work"])
        if bucket["bucket"] == "image":
            by_image: dict[str, list[dict[str, Any]]] = {}
            for item in items:
                image_path = item.get("image_path")
                if image_path:
                    by_image.setdefault(str(image_path), []).append(item)
            subchunks = []
            for image_items in by_image.values():
                subchunks.extend(
                    image_items[i:i + 2] for i in range(0, len(image_items), 2)
                )
        elif bucket["bucket"] == "short":
            subchunks = [items[i:i + 8] for i in range(0, len(items), 8)]
        else:
            subchunks = [items[i:i + 4] for i in range(0, len(items), 4)]

        for chunk in subchunks:
            enriched = []
            for item in chunk:
                q = next((x for x in questions if x.id == item["id"]), None)
                if q is None:
                    continue
                if q.bucket == "image":
                    group_id = 8
                elif q.bucket == "long_clinical":
                    group_id = 7
                else:
                    group_id = grouped.get(q.id, q.hint_group or 4)
                enriched.append({
                    "id": q.id,
                    "group_id": group_id,
                    "stem": q.stem,
                    "options": q.options,
                    "hint_group": q.hint_group,
                    "image_path": q.image_path,
                    "rag_context": "" if q.bucket == "image" else rag.get(q.id, ""),
                })
            if not enriched:
                continue
            if bucket["bucket"] == "image":
                image_path = enriched[0]["image_path"]
                subbatch = {
                    "require_formula_work": False,
                    "questions": enriched,
                    "image_path": image_path,
                }
            else:
                subbatch = {
                    "require_formula_work": require_formula,
                    "questions": enriched,
                }
            subbatches.append(subbatch)

    if not force:
        legacy_cache = _load_json(DEFAULT_CACHE_DIR / f"{exam_id}.json")
        legacy_batches = legacy_cache.get("batches", {})
        if isinstance(legacy_batches, dict):
            for key, value in legacy_batches.items():
                batch_results.setdefault(key, value)
        checkpoint_cache = _load_json(checkpoint_dir / "llm_batches.json")
        checkpoint_batches = checkpoint_cache.get("batches", {})
        if isinstance(checkpoint_batches, dict):
            for key, value in checkpoint_batches.items():
                batch_results.setdefault(key, value)

    restored_keys = [
        key for key in (_json_hash(batch) for batch in subbatches)
        if key in batch_results and _valid_batch_cache(batch_results[key], subbatches[
            next(i for i, candidate in enumerate(subbatches) if _json_hash(candidate) == key)
        ])
    ]
    engines: list[str] = []
    if parse_list(os.getenv("DEEPSEEK_API_KEYS", "") + "," + os.getenv("DEEPSEEK_API_KEY", "")):
        engines.append("DeepSeek API")
    gemini_keys = parse_list(os.getenv("GEMINI_API_KEYS", "") + "," + os.getenv("GEMINI_API_KEY", ""))
    if gemini_keys:
        exam_model = priority_exam_models(
            os.getenv("EXAM_SOLVER_GEMINI_MODEL", os.getenv("GEMINI_MODEL", "")),
            allow_lite=True,
        )[0]
        engines.append(f"Gemini API ({len(gemini_keys)} keys, ưu tiên {exam_model})")
    engines.append("Gemini Web")
    if backend == "web":
        engines = ["Gemini Web"]
    print(f"Engines sẵn sàng: {', '.join(engines)}", flush=True)
    print(
        f"[Bước 4 - Giải đề] Tổng {len(subbatches)} batch "
        f"({len(questions)} câu) | Đã khôi phục từ cache: {len(restored_keys)} batch "
        f"| Cần gọi API: {len(subbatches) - len(restored_keys)} batch.",
        flush=True,
    )

    total_batches = len(subbatches)
    for batch_idx, subbatch in enumerate(subbatches, start=1):
        key = _json_hash(subbatch)
        if key in batch_results and _valid_batch_cache(batch_results[key], subbatch):
            continue
        batch_questions = subbatch["questions"]
        first_id = batch_questions[0]["id"]
        last_id = batch_questions[-1]["id"]
        batch_engine, batch_model = router.describe_next(
            subbatch.get("image_path"),
            backend,
        )
        print(
            f"  → [Batch {batch_idx}/{total_batches}] Đang giải "
            f"{len(batch_questions)} câu (Câu {first_id}–{last_id}) "
            f"bằng {batch_engine} ({batch_model})...",
            flush=True,
        )
        started = time.monotonic()
        while True:
            try:
                results = _solve_batch(router, subbatch, backend=backend)
                batch_results[key] = {"results": results}
                _atomic_json_write(
                    cache_path,
                    {"batches": batch_results},
                )
                elapsed = time.monotonic() - started
                print(
                    f"  ✓ [Batch {batch_idx}/{total_batches}] Hoàn thành trong "
                    f"{elapsed:.1f}s (đã lưu tự động).",
                    flush=True,
                )
                break
            except BaseException as exc:
                kind = "hình ảnh" if subbatch.get("image_path") else "lý thuyết"
                print(
                    f"  ⚠ [Batch {batch_idx}/{total_batches}] Lỗi batch {kind}, "
                    f"đã ghi nhận và tiếp tục: {exc}",
                    flush=True,
                )
                error_results = []
                for q in batch_questions:
                    error_results.append({
                        "id": q["id"],
                        "answer": None,
                        "explanation": f"Lỗi batch {kind}: {exc}",
                        "status": "ai_only",
                    })
                batch_results[key] = {"results": error_results, "error": str(exc)}
                _atomic_json_write(cache_path, {"batches": batch_results})
                break

    all_results = {
        item["id"]: item
        for cached in batch_results.values()
        for item in cached.get("results", [])
        if isinstance(item, dict) and item.get("id")
    }
    for q in questions:
        if q.id not in all_results:
            all_results[q.id] = {
                "id": q.id,
                "answer": None,
                "explanation": "Batch chưa giải được; chưa có kết quả",
                "status": "ai_only",
            }
        all_results[q.id] = _audit(all_results[q.id], q.raw_key or "")
    _export_exam(
        pdf_path,
        out_root,
        subject,
        subject_label,
        questions,
        all_results,
        rag,
    )
    _merge_bank(out_root / subject, subject, subject_label)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Giải đề y khoa theo pipeline 5 bước và xuất JSON Isolde."
    )
    parser.add_argument("--in", dest="input_path", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--subject", default="")
    parser.add_argument("--formula-mode", choices=("calc_only", "all", "off"), default="")
    parser.add_argument("--yes", action="store_true", help="Bỏ gate xác nhận và prompt subject.")
    parser.add_argument("--web-model", default="")
    parser.add_argument("--web-gem", default="")
    parser.add_argument("--force", action="store_true", help="Bỏ qua cache Step 2, 3 và 4.")
    parser.add_argument(
        "--backend",
        choices=("auto", "web"),
        default="auto",
        help="Chọn web để ép Gemini Web; mặc định dùng DeepSeek → Gemini API → Gemini Web.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Hiển thị chi tiết log nội bộ (mặc định chỉ hiển thị trạng thái ngắn gọn).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input_path
    supported = (".pdf", ".md", ".txt", ".docx")
    if input_path.is_file():
        found = [input_path] if input_path.suffix.lower() in supported else []
    else:
        found = sorted(
            (
                p for p in input_path.rglob("*")
                if p.is_file() and p.suffix.lower() in supported
            ),
            key=lambda p: str(p).lower(),
        )
    if not found:
        print(f"Chưa có file đề thi (.pdf, .md, .txt, .docx) trong: {input_path.resolve()}")
        print(f"Hãy bỏ file đề thi vào thư mục: {DEFAULT_INPUT.resolve()}")
        legacy_dir = ROOT_DIR / "de_thi"
        if legacy_dir.is_dir():
            print(f"Phát hiện thư mục đề thi cũ còn sót: {legacy_dir.resolve()}")
            print("Hãy di chuyển đề thi sang workspace/de_thi/ sau refactor.")
        raise SystemExit(1)

    pdfs = [p for p in found if p.suffix.lower() == ".pdf"]
    non_pdf = [p for p in found if p.suffix.lower() != ".pdf"]
    if non_pdf:
        print("Hiện pipeline giải đề chỉ xử lý file PDF.")
        print("Các file không phải PDF đã phát hiện:")
        for path in non_pdf:
            print(f"  - {path.resolve()}")
        print(f"Hãy đặt/copy đề thi dạng PDF vào: {DEFAULT_INPUT.resolve()}")
    if not pdfs:
        raise SystemExit(1)
    if not pdfs:
        raise SystemExit(f"Không tìm thấy PDF trong: {input_path}")

    formula_mode = args.formula_mode
    for pdf_path in pdfs:
        subject, resolved = _resolve_subject(pdf_path, args.subject)
        subject_label = ""
        if not resolved:
            detected = detect_subject_slug(pdf_path)
            if args.yes:
                subject = detected
                subject_label = detect_subject_label(pdf_path, detected)
            else:
                try:
                    answer = prompt_input(
                        f"Nhập tên môn học / subject slug (Enter = {detected}): "
                    ).strip()
                except EOFError:
                    print()
                    print(
                        f"Không có dữ liệu tương tác; dùng subject mặc định: {detected}"
                    )
                    answer = ""
                subject_label = unicodedata.normalize(
                    "NFC",
                    answer or detect_subject_label(pdf_path, detected),
                )
                subject = slugify_vi(answer or subject_label) or detected
        else:
            if args.subject and slugify_vi(args.subject) != args.subject.lower():
                subject_label = unicodedata.normalize("NFC", args.subject)
            else:
                subject_label = detect_subject_label(pdf_path, subject)
        subject = subject or "tong-hop"
        subject_label = unicodedata.normalize(
            "NFC",
            subject_label or detect_subject_label(pdf_path, subject),
        )

        questions = preprocess_pdf(pdf_path, DEFAULT_IMG_DIR)
        if not formula_mode:
            if args.yes:
                mode = "off"
            else:
                mode = configure_formula_mode(questions)
        else:
            mode = formula_mode

        if not args.yes:
            try:
                answer = prompt_input(
                    "Tiếp tục chạy pipeline (bắt đầu gọi API)? [y/N]: "
                ).strip().lower()
            except EOFError:
                print()
                print("Không có dữ liệu tương tác; dừng trước khi gọi API.")
                raise SystemExit(1)
            if answer not in {"y", "yes", "có", "co"}:
                print("Đã dừng trước khi gọi API.")
                raise SystemExit(0)

        asyncio.run(solve_exam_async(
            pdf_path,
            args.out,
            subject,
            subject_label,
            mode,
            args.web_model,
            args.web_gem,
            args.force,
            args.yes,
            args.backend,
        ))


if __name__ == "__main__":
    main()
