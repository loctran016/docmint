#!/usr/bin/env python3
"""5-step medical exam solving pipeline for Isolde Full-page Quiz JSON."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core import common
from src.core.llm_router import LLMRouter
from src.core.prompts import render_prompt
from src.llm.exam_preprocessor import (
    QuestionItem,
    configure_formula_mode,
    detect_subject_slug,
    preprocess_pdf,
    route_and_batch,
)

DEFAULT_INPUT = common.WORKSPACE_DIR / "de_thi"
DEFAULT_OUTPUT = common.WORKSPACE_DIR / "ket_qua" / "giai_de"
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
        from src.core.llm_router import extract_clean_json
        parsed = extract_clean_json(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _resolve_subject(pdf_path: Path, explicit_subject: str) -> tuple[str, bool]:
    if explicit_subject:
        slug = re.sub(r"[^a-z0-9]+", "-", explicit_subject.lower()).strip("-")
        return slug or "tong-hop", True
    if pdf_path.parent != DEFAULT_INPUT and pdf_path.parent.parent == DEFAULT_INPUT:
        slug = re.sub(r"[^a-z0-9]+", "-", pdf_path.parent.name.lower()).strip("-")
        if slug:
            return slug, True
    return "", False


async def _step2_classify(
    exam_id: str,
    questions: list[QuestionItem],
    notebook_id: str,
    force: bool,
) -> dict[str, int]:
    cache_path = DEFAULT_CACHE_DIR / f"{exam_id}_step2_grouped.json"
    if not force and cache_path.is_file():
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("group_by_id"), dict):
            return {str(k): int(v) for k, v in data["group_by_id"].items()}

    short = [q for q in questions if q.bucket == "short"]
    group_by_id: dict[str, int] = {}
    async with common.notebooklm_client(chat_timeout=300) as client:
        for start in range(0, len(short), 18):
            chunk = short[start:start + 18]
            payload = [{"id": q.id, "stem": q.stem, "options": q.options} for q in chunk]
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
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"exam_id": exam_id, "group_by_id": group_by_id}, ensure_ascii=False, indent=2),
        encoding="utf-8",
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
) -> dict[str, str]:
    cache_path = DEFAULT_CACHE_DIR / f"{exam_id}_step3_rag.json"
    if not force and cache_path.is_file():
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("rag_by_id"), dict):
            return {str(k): str(v) for k, v in data["rag_by_id"].items()}

    rag_by_id: dict[str, str] = {}
    batches: list[list[QuestionItem]] = []
    short_by_group: dict[int, list[QuestionItem]] = {}
    for q in questions:
        if q.bucket == "short":
            short_by_group.setdefault(grouped.get(q.id, q.hint_group or 4), []).append(q)
    for group_id in sorted(short_by_group):
        items = short_by_group[group_id]
        batches.extend([items[i:i + 7] for i in range(0, len(items), 7)])
    long_items = [q for q in questions if q.bucket == "long_clinical"]
    batches.extend([long_items[i:i + 3] for i in range(0, len(long_items), 3)])

    async with common.notebooklm_client(chat_timeout=300) as client:
        for chunk in batches:
            payload = [{"id": q.id, "stem": q.stem, "options": q.options} for q in chunk]
            prompt = render_prompt(
                "exam_solver_step3_rag",
                data=json.dumps(payload, ensure_ascii=False),
            )
            answer = await common.ask_with_retry(
                client, notebook_id, prompt, max_retry=3, timeout=300
            )
            parsed = _extract_clean_json_object(answer)
            for item in parsed.get("rag", []) if isinstance(parsed, dict) else []:
                if isinstance(item, dict) and item.get("id"):
                    rag_by_id[str(item["id"])] = str(item.get("facts") or "").strip()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"exam_id": exam_id, "rag_by_id": rag_by_id}, ensure_ascii=False, indent=2),
        encoding="utf-8",
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
    )
    return _validate_results(raw, {q["id"] for q in batch["questions"]}, require_formula)


def _audit(result: dict[str, Any], raw_key: str) -> dict[str, Any]:
    raw_key = raw_key.strip().upper()
    result["status"] = (
        "ai_only" if not raw_key
        else "verified" if result["answer"] == raw_key
        else "conflict"
    )
    return result


def _normalize_exam_question_fields(question: dict[str, Any]) -> dict[str, Any]:
    question["textbook_excerpt"] = _strict_null(question.get("textbook_excerpt"))
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
            or subject.replace("-", " ").title()
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
            "subject": subject,
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
        "exam_id": exam_id,
        "cohort": _cohort(pdf_path),
        "subject": subject,
        "subject_label": subject.replace("-", " ").title(),
        "title": exam_id,
        "default_time_sec": 3600,
        "question_count": len(exported),
        "questions": exported,
    }
    exam_path = subject_dir / f"{exam_id}.json"
    exam_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return exam_path


def _merge_bank(subject_dir: Path, subject: str) -> None:
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
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
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
        "subject": subject,
        "subject_label": subject.replace("-", " ").title(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(questions),
        "exams": exams,
        "questions": questions,
    }
    (subject_dir / "bank.json").write_text(
        json.dumps(bank, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _generate_exams_manifest(subject_dir.parent)


async def solve_exam_async(
    pdf_path: Path,
    out_root: Path,
    subject: str,
    formula_mode: str,
    web_model: str,
    web_gem: str,
    force: bool,
    yes: bool,
) -> None:
    exam_id = pdf_path.stem
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
    if not yes:
        answer = input("Tiếp tục truy xuất dữ liệu từ NotebookLM? [Y/n]: ").strip().lower()
        if answer in {"n", "no", "không", "khong"}:
            raise SystemExit("Đã dừng trước Step 3.")
    rag = await _step3_rag(exam_id, questions, grouped, notebook_id, force)

    router = LLMRouter(web_model=web_model, web_gem=web_gem)
    cache_path = DEFAULT_CACHE_DIR / f"{exam_id}.json"
    cache = {"batches": {}} if force or not cache_path.is_file() else json.loads(
        cache_path.read_text(encoding="utf-8")
    )
    batch_results = cache.get("batches", {})

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
            subchunks = [items[i:i + 15] for i in range(0, len(items), 15)]
        else:
            subchunks = [items[i:i + 3] for i in range(0, len(items), 3)]

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
            key = _json_hash(subbatch)
            if key not in batch_results:
                batch_results[key] = {"results": _solve_batch(router, subbatch)}
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(
                    json.dumps({"batches": batch_results}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

    all_results = {
        item["id"]: item
        for cached in batch_results.values()
        for item in cached["results"]
    }
    for q in questions:
        if q.id not in all_results:
            raise ValueError(f"Thiếu kết quả reasoning cho {q.id}")
        all_results[q.id] = _audit(all_results[q.id], q.raw_key or "")
    _export_exam(pdf_path, out_root, subject, questions, all_results, rag)
    _merge_bank(out_root / subject, subject)


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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input_path
    pdfs = [input_path] if input_path.is_file() else sorted(
        (p for p in input_path.rglob("*.pdf") if p.is_file()),
        key=lambda p: str(p).lower(),
    )
    if not pdfs:
        raise SystemExit(f"Không tìm thấy PDF trong: {input_path}")

    formula_mode = args.formula_mode
    for pdf_path in pdfs:
        subject, resolved = _resolve_subject(pdf_path, args.subject)
        if not resolved:
            detected = detect_subject_slug(pdf_path)
            if args.yes:
                subject = detected
            else:
                answer = input(
                    f"Nhập tên môn học / subject slug (Enter = {detected}): "
                ).strip()
                subject = re.sub(r"[^a-z0-9]+", "-", (answer or detected).lower()).strip("-")
        subject = subject or "tong-hop"

        questions = preprocess_pdf(pdf_path, DEFAULT_IMG_DIR)
        if not formula_mode:
            if args.yes:
                mode = "off"
            else:
                mode = configure_formula_mode(questions)
        else:
            mode = formula_mode

        asyncio.run(solve_exam_async(
            pdf_path,
            args.out,
            subject,
            mode,
            args.web_model,
            args.web_gem,
            args.force,
            args.yes,
        ))


if __name__ == "__main__":
    main()
