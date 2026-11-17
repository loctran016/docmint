#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["notebooklm-py"]
# ///
"""
Sinh quiz, flashcards, mindmap, infographic cho MỘT bài, chỉ từ các nguồn đã chọn
([SGK]/[GV]/[SLIDE], cùng cách chọn nguồn với ask_notebook.py).

Dùng (từ thư mục gốc repo):
    uv run output/generate_artifacts.py quiz "Sinh lý gan" --source ca_hai
    uv run output/generate_artifacts.py flashcards "Sinh lý gan" --source sach --quantity more
    uv run output/generate_artifacts.py mindmap "Sinh lý gan" --source giaovien
    uv run output/generate_artifacts.py infographic "Sinh lý gan" --source ca_hai

Kết quả: <đầu ra gốc>/artifacts_nguon/<loại>/<tên bài> (<loại>).<đuôi>
Mỗi lần sinh tải đúng artifact vừa tạo (theo artifact_id), không lấy nhầm bản cũ.
Hạn mức tạo nội dung tuỳ gói tài khoản; hết hạn mức thì lệnh báo lỗi.
"""
import argparse
import asyncio
import inspect
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for _p in (str(HERE), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import common  # của toolkit

import notebooklm
from notebooklm import NotebookLMClient, QuizDifficulty, QuizQuantity, SourceStatus

from ask_notebook import GROUPS, match_lesson_sources, resolve_notebook

QUANTITY = {"fewer": QuizQuantity.FEWER, "standard": QuizQuantity.STANDARD, "more": QuizQuantity.MORE}
DIFFICULTY = {"easy": QuizDifficulty.EASY, "medium": QuizDifficulty.MEDIUM, "hard": QuizDifficulty.HARD}
INSTRUCTION_PARAMS = ("instructions", "prompt", "custom_prompt")


def build_instructions(lesson, extra):
    text = (f'Chỉ dùng các nguồn đã chọn, tuyệt đối không thêm kiến thức ngoài nguồn. '
            f'Nội dung chỉ về bài "{lesson}". Viết bằng tiếng Việt.')
    return f"{text} {extra}".strip() if extra else text


async def wait_done(client, nb, task_id, timeout):
    final = await client.artifacts.wait_for_completion(nb, task_id, timeout=timeout)
    if not final.is_complete:
        raise RuntimeError(f"Tạo không thành công (trạng thái: {final.status}, lỗi: {final.error})")
    return final


async def make_quiz_or_cards(client, nb, ids, lesson, args, out_dir, kind):
    arts = client.artifacts
    gen = arts.generate_quiz if kind == "quiz" else arts.generate_flashcards
    dl = arts.download_quiz if kind == "quiz" else arts.download_flashcards
    status = await gen(
        nb,
        source_ids=ids,
        instructions=build_instructions(lesson, args.extra),
        quantity=QUANTITY[args.quantity],
        difficulty=DIFFICULTY[args.difficulty],
        language="vi",
        include_images=False,
    )
    await wait_done(client, nb, status.task_id, args.timeout)
    ext = {"markdown": "md", "json": "json", "html": "html"}[args.format]
    path = out_dir / f"{common.safe_filename(lesson)} ({kind}).{ext}"
    await dl(nb, str(path), artifact_id=status.task_id, output_format=args.format)
    return path


async def make_mindmap(client, nb, ids, lesson, args, out_dir):
    kind = (notebooklm.MindMapKind.INTERACTIVE if args.mm_kind == "interactive"
            else notebooklm.MindMapKind.NOTE_BACKED)
    mm = await client.mind_maps.generate(
        nb, ids, kind=kind, language="vi",
        instructions=build_instructions(lesson, args.extra),
        wait=True, failure_policy="raise",
    )
    path = out_dir / f"{common.safe_filename(lesson)} (mindmap).json"
    await client.artifacts.download_mind_map(nb, str(path), mm.id)
    return path


async def make_infographic(client, nb, ids, lesson, args, out_dir):
    arts = client.artifacts
    gen = arts.generate_infographic
    params = inspect.signature(gen).parameters
    kwargs = {}
    if "source_ids" in params:
        kwargs["source_ids"] = ids
    else:
        print("  CẢNH BÁO: hàm tạo infographic không nhận source_ids, sẽ dùng mọi nguồn của notebook.")
    for name in INSTRUCTION_PARAMS:
        if name in params:
            kwargs[name] = build_instructions(lesson, args.extra)
            break
    if "language" in params:
        kwargs["language"] = "vi"
    orient = getattr(notebooklm, "InfographicOrientation", None)
    if orient is not None and "orientation" in params and hasattr(orient, args.orientation.upper()):
        kwargs["orientation"] = getattr(orient, args.orientation.upper())
    status = await gen(nb, **kwargs)
    await wait_done(client, nb, status.task_id, args.timeout)
    path = out_dir / f"{common.safe_filename(lesson)} (infographic).png"
    await arts.download_infographic(nb, str(path), artifact_id=status.task_id)
    return path


def parse_args():
    ap = argparse.ArgumentParser(description="Sinh quiz/flashcards/mindmap/infographic theo nguồn")
    ap.add_argument("kind", choices=["quiz", "flashcards", "mindmap", "infographic"])
    ap.add_argument("lesson", help="tên bài")
    ap.add_argument("-n", "--notebook", help="ID hoặc URL notebook")
    ap.add_argument("--source", choices=["sach", "giaovien", "ca_hai"], default="ca_hai",
                    help="nguồn dùng để sinh (mặc định ca_hai)")
    ap.add_argument("--match", help="chỉ lấy [GV]/[SLIDE] có chuỗi này trong tên")
    ap.add_argument("--quantity", choices=list(QUANTITY), default="standard", help="quiz/flashcards")
    ap.add_argument("--difficulty", choices=list(DIFFICULTY), default="medium", help="quiz/flashcards")
    ap.add_argument("--format", choices=["markdown", "json", "html"], default="markdown",
                    help="định dạng tải về cho quiz/flashcards")
    ap.add_argument("--mm-kind", choices=["interactive", "note-backed"], default="interactive")
    ap.add_argument("--orientation", choices=["landscape", "portrait", "square"], default="portrait")
    ap.add_argument("--extra", default="", help="yêu cầu thêm gắn vào hướng dẫn")
    ap.add_argument("--timeout", type=float, default=1200, help="giây chờ tạo xong (mặc định 1200)")
    ap.add_argument("--out-root", help="thư mục đầu ra gốc (mặc định ket_qua)")
    return ap.parse_args()


async def main():
    args = parse_args()
    nb = resolve_notebook(args.notebook)
    out_dir = common.get_out_root(args.out_root) / "artifacts_nguon" / args.kind
    out_dir.mkdir(parents=True, exist_ok=True)

    async with NotebookLMClient.from_storage() as client:
        sources = await client.sources.list(nb, statuses={SourceStatus.READY})
        chosen, found = match_lesson_sources(sources, GROUPS[args.source], args.lesson, args.match)
        if not chosen:
            sys.exit("Không có nguồn READY phù hợp. Kiểm tra tên nguồn/tên bài, hoặc dùng --match.")
        print("Nguồn được chọn:")
        for s in chosen:
            print(f"  - {s.title}")
        ids = [s.id for s in chosen]

        print(f"Đang tạo {args.kind} cho '{args.lesson}' (có thể mất vài phút)...")
        if args.kind in ("quiz", "flashcards"):
            path = await make_quiz_or_cards(client, nb, ids, args.lesson, args, out_dir, args.kind)
        elif args.kind == "mindmap":
            path = await make_mindmap(client, nb, ids, args.lesson, args, out_dir)
        else:
            path = await make_infographic(client, nb, ids, args.lesson, args, out_dir)
        print(f"Đã lưu: {path}")


if __name__ == "__main__":
    asyncio.run(main())
