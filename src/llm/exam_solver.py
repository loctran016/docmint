#!/usr/bin/env python3
"""Solve medical exams and export Isolde Full-page Quiz JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.common import ROOT_DIR, WORKSPACE_DIR
from src.core.llm_router import LLMRouter
from src.llm.exam_preprocessor import (
    QuestionItem,
    configure_formula_mode,
    preprocess_pdf,
    route_and_batch,
)

DEFAULT_INPUT = WORKSPACE_DIR / "de_thi"
DEFAULT_OUTPUT = WORKSPACE_DIR / "ket_qua" / "giai_de"
DEFAULT_IMG_DIR = ROOT_DIR / ".cache" / "exam_imgs"
DEFAULT_CACHE_DIR = ROOT_DIR / ".cache" / "exam_solver"
GROUP_NAMES = {
    1: "Giải phẫu / Mô phôi / GPB",
    2: "Sinh lý / Sinh lý bệnh / Vi sinh",
    3: "Dược lý",
    4: "Lâm sàng & Cận lâm sàng",
    5: "Câu hỏi hình ảnh",
}
GROUP_LABELS = GROUP_NAMES
SUBJECT_LABELS = {
    "tong-hop": "Tổng hợp",
    "tieu-hoa": "Tiêu hóa",
    "dinh-duong": "Dinh dưỡng",
}


def _json_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _question_payload(question: dict[str, Any]) -> dict[str, Any]:
    return {
        key: question[key]
        for key in ("id", "stem", "options", "hint_group", "image_path")
        if key in question
    }


def _image_batches(batch: dict[str, Any]) -> list[dict[str, Any]]:
    if batch["bucket"] != "image_pipeline":
        return [batch]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for question in batch["questions"]:
        image_path = question.get("image_path")
        if not image_path:
            raise ValueError(f"Câu hình ảnh {question.get('id')} không có image_path")
        grouped.setdefault(image_path, []).append(question)
    return [
        {**batch, "questions": questions, "image_path": image_path}
        for image_path, questions in grouped.items()
    ]


def _validate_results(
    raw: Any, expected_ids: set[str], require_formula: bool
) -> list[dict[str, Any]]:
    if not isinstance(raw, dict) or not isinstance(raw.get("results"), list):
        raise ValueError("LLM không trả về object JSON có trường results")
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw["results"]:
        if not isinstance(item, dict):
            raise ValueError("Một kết quả LLM không phải object")
        item_id = str(item.get("id", ""))
        try:
            group = int(item["final_group"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Kết quả {item_id or '<không id>'} thiếu final_group") from exc
        if item_id not in expected_ids or item_id in seen or group not in GROUP_NAMES:
            raise ValueError(f"Kết quả không hợp lệ: id={item_id!r}, final_group={group}")
        answer = str(item.get("answer", "")).strip().upper()
        if answer not in {"A", "B", "C", "D"}:
            raise ValueError(f"Đáp án không hợp lệ cho {item_id}: {answer!r}")
        seen.add(item_id)
        results.append({
            "id": item_id,
            "final_group": group,
            "hint": str(item.get("hint", "")).strip(),
            "formula_work": (
                str(item.get("formula_work", "")).strip() if require_formula else None
            ),
            "answer": answer,
            "explanation": str(item.get("explanation", "")).strip(),
        })
    if seen != expected_ids:
        raise ValueError(f"LLM bỏ sót câu: {sorted(expected_ids - seen)}")
    return results


def _solve_batch(router: LLMRouter, batch: dict[str, Any]) -> list[dict[str, Any]]:
    require_formula = bool(batch["require_formula_work"])
    formula_schema = '"formula_work":"str"' if require_formula else '"formula_work":null'
    system = f"""Bạn là bác sĩ giải đề thi y khoa Việt Nam.
Trả về JSON hợp lệ đúng schema:
{{"results":[{{"id":"str","final_group":1,"hint":"str","formula_work":{formula_schema},"answer":"A","explanation":"str"}}]}}
final_group chỉ được là 1..5: 1={GROUP_LABELS[1]}, 2={GROUP_LABELS[2]}, 3={GROUP_LABELS[3]}, 4={GROUP_LABELS[4]}, 5={GROUP_LABELS[5]}.
answer phải là chữ cái A/B/C/D. hint là một câu gợi ý khái niệm, không tiết lộ đáp án.
Giải thích ngắn gọn theo kiến thức giáo trình.
{"Chỉ điền formula_work cho câu thật sự cần tính toán." if require_formula else "formula_work phải luôn là null."}"""
    user = json.dumps(
        {"questions": [_question_payload(q) for q in batch["questions"]]},
        ensure_ascii=False,
    )
    raw = router.generate_json(system, user, image_path=batch.get("image_path"))
    return _validate_results(raw, {q["id"] for q in batch["questions"]}, require_formula)


def _audit_one(result: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    raw_key = str(meta.get("raw_key") or "").strip().upper()
    result["status"] = (
        "ai_only" if not raw_key
        else "verified" if result["answer"] == raw_key
        else "conflict"
    )
    return result


def _cohort(pdf_path: Path) -> str:
    match = re.search(r"(?<![A-Za-z0-9])(Y\d{2,4})(?!\d)", pdf_path.stem, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _options(options: list[str]) -> list[dict[str, str]]:
    result = []
    for option in options:
        match = re.match(r"^\s*([A-D])\s*[.)]\s*(.*)$", option, re.IGNORECASE)
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


def _export_question(
    exam_id: str,
    cohort: str,
    question: QuestionItem,
    result: dict[str, Any],
    assets_dir: Path,
) -> dict[str, Any]:
    image = _copy_asset(question.image_path, assets_dir)
    return {
        "id": f"{exam_id}_Q{question.q_num}",
        "exam_id": exam_id,
        "cohort": cohort,
        "num": int(question.q_num) if str(question.q_num).isdigit() else question.q_num,
        "group_id": result["final_group"],
        "group_name": GROUP_NAMES[result["final_group"]],
        "stem": question.stem,
        "options": _options(question.options),
        "answer": result["answer"],
        "status": result["status"],
        "legacy_key": question.raw_key,
        "student_note": question.student_note,
        "hint": result["hint"],
        "formula_work": result["formula_work"],
        "explanation": result["explanation"],
        "image": image,
    }


def _export_exam(
    pdf_path: Path,
    out_root: Path,
    subject: str,
    questions: list[QuestionItem],
    results: dict[str, dict[str, Any]],
) -> Path:
    subject_dir = out_root / subject
    assets_dir = subject_dir / "assets"
    exam_id = pdf_path.stem
    cohort = _cohort(pdf_path)
    exported_questions = [
        _export_question(exam_id, cohort, question, results[question.id], assets_dir)
        for question in questions
    ]
    payload = {
        "exam_id": exam_id,
        "cohort": cohort,
        "subject": subject,
        "subject_label": SUBJECT_LABELS.get(subject, subject.replace("-", " ").title()),
        "title": pdf_path.stem,
        "default_time_sec": 3600,
        "questions": exported_questions,
    }
    subject_dir.mkdir(parents=True, exist_ok=True)
    exam_path = subject_dir / f"{exam_id}.json"
    exam_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return exam_path


def _merge_bank(subject_dir: Path, subject: str) -> None:
    exams = []
    for path in sorted(subject_dir.glob("*.json")):
        if path.name == "bank.json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        exams.append({
            "exam_id": payload["exam_id"],
            "cohort": payload["cohort"],
            "title": payload["title"],
            "default_time_sec": payload["default_time_sec"],
            "question_count": len(payload["questions"]),
        })
    questions = []
    for exam in exams:
        payload = json.loads((subject_dir / f"{exam['exam_id']}.json").read_text(encoding="utf-8"))
        questions.extend(payload["questions"])
    bank = {
        "subject": subject,
        "subject_label": SUBJECT_LABELS.get(subject, subject.replace("-", " ").title()),
        "exams": exams,
        "questions": questions,
    }
    (subject_dir / "bank.json").write_text(
        json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def solve_exam(
    pdf_path: Path,
    out_root: Path,
    subject: str,
    formula_mode: str,
    web_model: str,
    web_gem: str,
    force: bool,
) -> None:
    questions = preprocess_pdf(pdf_path, DEFAULT_IMG_DIR)
    if not questions:
        raise ValueError(f"Không nhận diện được câu hỏi trong {pdf_path}")
    batches = route_and_batch(questions, formula_mode)
    router = LLMRouter(web_model=web_model, web_gem=web_gem)
    cache_path = DEFAULT_CACHE_DIR / f"{pdf_path.stem}.json"
    cache = {"batches": {}} if force or not cache_path.exists() else json.loads(cache_path.read_text(encoding="utf-8"))
    batch_results: dict[str, dict[str, Any]] = cache.get("batches", {})
    for batch in batches:
        for sub_batch in _image_batches(batch):
            key = _json_hash({
                "questions": sub_batch["questions"],
                "require_formula_work": sub_batch["require_formula_work"],
            })
            if key not in batch_results:
                batch_results[key] = {"results": _solve_batch(router, sub_batch)}
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    all_results = {
        item["id"]: item
        for cached in batch_results.values()
        for item in cached["results"]
    }
    for question in questions:
        question.legacy_key = question.raw_key
        question.student_note = question.student_note or ""
        result = all_results[question.id]
        result.setdefault("hint", "")
        result.setdefault("formula_work", None)
        result.setdefault("explanation", "")
        all_results[question.id] = _audit_one(
            result,
            {"raw_key": question.legacy_key, "student_note": question.student_note},
        )
    _export_exam(pdf_path, out_root, subject, questions, all_results)
    _merge_bank(out_root / subject, subject)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Giải đề y khoa và xuất JSON cho Isolde Full-page Quiz.")
    parser.add_argument("--in", dest="input_path", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--subject", default="tong-hop")
    parser.add_argument("--formula-mode", choices=("", "calc_only", "all", "off"), default="")
    parser.add_argument("--web-model", default="")
    parser.add_argument("--web-gem", default="")
    parser.add_argument("--force", action="store_true", help="Bỏ qua cache batch hiện có.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input_path
    pdfs = [input_path] if input_path.is_file() else sorted(input_path.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"Không tìm thấy PDF trong: {input_path}")
    formula_mode = args.formula_mode
    for pdf_path in pdfs:
        questions = preprocess_pdf(pdf_path, DEFAULT_IMG_DIR)
        if not formula_mode:
            formula_mode = configure_formula_mode(questions)
        solve_exam(pdf_path, args.out, args.subject, formula_mode, args.web_model, args.web_gem, args.force)


if __name__ == "__main__":
    main()
