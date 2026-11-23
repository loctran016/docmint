# /// script
# requires-python = ">=3.10"
# dependencies = ["notebooklm-py"]
# ///
import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
"""
Tạo Mindmap, Infographic hoặc Video bằng NotebookLM cho từng bài, rồi tải về.

Danh sách bài (đọc file riêng trước, nếu chưa có bài nào thì dùng giao_trinh.txt):
    mindmap      -> mindmaps.txt
    infographic  -> infographics.txt
    video        -> videos.txt

Cách chạy (từ thư mục toolkit):
    uv run 7_tao_media.py video --test            # chỉ làm bài đầu tiên (vẫn lưu file)
    uv run 7_tao_media.py video                   # làm toàn bộ danh sách
    uv run 7_tao_media.py infographic --only 2,4
    uv run 7_tao_media.py mindmap --mm-kind note-backed
    uv run 7_tao_media.py video --api-info        # xem tham số thật của các hàm trong thư viện

Tùy chọn riêng cho từng bài viết ngay trong file danh sách dạng key=value, ví dụ
    Bài 2. Carbohydrate | tập trung sơ đồ chuyển hóa | style=whiteboard
Key nào trùng tên tham số của hàm generate_<loại> trong thư viện thì được truyền vào
(xem tên tham số bằng --api-info). Cũng có thể áp dụng cho mọi bài bằng --opt key=value.

Kết quả: <đầu ra gốc>/mindmap | infographic | video
"""
import argparse
import asyncio
import enum
import inspect
import json
import random
import re
import typing
from pathlib import Path

from notebooklm import NotebookLMClient

from src.core import common
from src.core.prompts import render_prompt

MAX_CONSECUTIVE_FAIL = 2          # lỗi liên tiếp quá số này thì dừng (thường là hết hạn mức)
INSTRUCTION_PARAMS = ("instructions", "prompt", "custom_prompt", "description", "focus", "topic")
IGNORED_KEYS = {"tn", "tl", "kho"}   # key dành cho chức năng tạo câu hỏi

KINDS = {
    "mindmap": {
        "label": "Mindmap", "feature_files": [common.MINDMAPS_FILE.name], "out_name": "mindmap",
        "ext": "json", "timeout": 600, "tag": "mindmap",
        "prompt": "media_mindmap",
    },
    "infographic": {
        "label": "Infographic", "feature_files": [common.INFOGRAPHICS_FILE.name], "out_name": "infographic",
        "ext": "png", "timeout": 900, "tag": "infographic",
        "prompt": "media_infographic",
    },
    "video": {
        "label": "Video", "feature_files": [common.VIDEOS_FILE.name], "out_name": "video",
        "ext": "mp4", "timeout": 1800, "tag": "video",
        "prompt": "media_video",
    },
}


# ------------------------------------------------------------- hỗ trợ tham số
def build_prompt(spec, item):
    luu_y = f" Lưu ý riêng cho bài này (hãy ưu tiên làm theo): {item['note']}" if item["note"] else ""
    return render_prompt(spec["prompt"], bai=item["title"], luu_y=luu_y)


def coerce(fn, name, value):
    """Đổi chuỗi 'whiteboard' thành thành viên Enum mà tham số đó yêu cầu (nếu có)."""
    try:
        ann = typing.get_type_hints(fn).get(name)
    except Exception:  # noqa: BLE001
        ann = None
    if ann is None:
        p = inspect.signature(fn).parameters.get(name)
        ann = p.annotation if p is not None else None
    cands = [a for a in typing.get_args(ann) if a is not type(None)] or [ann]
    norm = re.sub(r"[\s\-]+", "_", str(value).strip().lower())
    for c in cands:
        if inspect.isclass(c) and issubclass(c, enum.Enum):
            for m in c:
                if m.name.lower() == norm or re.sub(r"[\s\-]+", "_", str(m.value).lower()) == norm:
                    return m
            raise ValueError(f"'{value}' không hợp lệ cho {name}. Giá trị hợp lệ: "
                             + ", ".join(m.name.lower() for m in c))
        if c is int:
            return int(value)
    return value


def find_gen(client, kind):
    if kind == "mindmap":
        return getattr(client.mind_maps, "generate", None)
    return getattr(client.artifacts, f"generate_{kind}", None)


def find_dl(client, kind):
    name = "download_mind_map" if kind == "mindmap" else f"download_{kind}"
    return getattr(client.artifacts, name, None)


def print_api_info(client):
    arts = client.artifacts
    for name in ("generate_video", "download_video", "generate_infographic",
                 "download_infographic", "download_mind_map", "wait_for_completion"):
        fn = getattr(arts, name, None)
        print(f"artifacts.{name}", inspect.signature(fn) if fn else "(KHÔNG CÓ)")
    fn = getattr(client.mind_maps, "generate", None)
    print("mind_maps.generate", inspect.signature(fn) if fn else "(KHÔNG CÓ)")
    print("Các hàm generate/download có trên client.artifacts:",
          [n for n in dir(arts) if n.startswith(("generate", "download"))])


# -------------------------------------------------------- mindmap JSON -> markdown
LABEL_KEYS = ("name", "label", "title", "text", "topic", "content", "heading")
CHILD_KEYS = ("children", "nodes", "items", "branches", "subtopics", "topics")


def _label(node):
    for k in LABEL_KEYS:
        v = node.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().replace("\n", " ")
    return None


def _walk(node, depth, out):
    if isinstance(node, list):
        for c in node:
            _walk(c, depth, out)
        return
    if isinstance(node, str):
        out.append("  " * depth + "- " + node.strip())
        return
    if not isinstance(node, dict):
        return
    lab = _label(node)
    d = depth
    if lab:
        out.append("  " * depth + "- " + lab)
        d = depth + 1
    for k in CHILD_KEYS:
        if isinstance(node.get(k), list):
            for c in node[k]:
                _walk(c, d, out)
            break


def mindmap_markdown(data, title):
    """Đoán cấu trúc cây trong JSON để tạo dàn ý Markdown (heuristic). Trả None nếu không đoán được."""
    root = data
    if isinstance(data, dict):
        for k in ("root", "mind_map", "mindmap", "tree", "data"):
            if isinstance(data.get(k), (dict, list)):
                root = data[k]
                break
    out = []
    _walk(root, 0, out)
    if len(out) < 2:
        return None
    return f"# Mindmap: {title}\n\n" + "\n".join(out) + "\n"


# --------------------------------------------------------------- tạo một mục
async def make_one(client, nb_id, kind, spec, gen, dl, params, idx, item, args, out_dir, global_opts):
    title = item["title"]
    kwargs = {}
    instr_name = next((n for n in INSTRUCTION_PARAMS if n in params), None)
    if instr_name:
        kwargs[instr_name] = build_prompt(spec, item)

    if kind == "mindmap" and "kind" in params:
        try:
            kwargs["kind"] = coerce(gen, "kind", args.mm_kind)
        except ValueError as e:
            print(f"  Cảnh báo (--mm-kind): {e}")

    for key, val in {**global_opts, **item["opts"]}.items():
        if key in IGNORED_KEYS:
            continue
        if key not in params:
            print(f"  Cảnh báo: hàm không có tham số '{key}', bỏ qua (xem --api-info).")
            continue
        try:
            kwargs[key] = coerce(gen, key, val)
        except ValueError as e:
            print(f"  Cảnh báo: {e}")

    res = await asyncio.wait_for(gen(nb_id, **kwargs), timeout=spec["timeout"]) \
        if kind == "mindmap" else None
    if kind != "mindmap":
        status = await gen(nb_id, **kwargs)
        await asyncio.wait_for(client.artifacts.wait_for_completion(nb_id, status.task_id),
                               timeout=spec["timeout"])

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{idx:02d} - {common.safe_filename(title)} ({spec['label']}).{spec['ext']}"
    if kind == "mindmap":
        await dl(nb_id, str(path), res.id)
    else:
        await dl(nb_id, str(path))
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("Đã tạo nhưng file tải về không có nội dung")
    return path


def parse_args():
    ap = argparse.ArgumentParser(description="Tạo mindmap / infographic / video bằng NotebookLM")
    ap.add_argument("kind", choices=list(KINDS), help="loại cần tạo")
    common.add_common_args(ap, delay_default="10,20")
    ap.add_argument("--mm-kind", default="interactive", choices=["interactive", "note-backed"],
                    help="loại mindmap (chỉ dùng cho mindmap)")
    ap.add_argument("--opt", action="append", default=[], metavar="KEY=VALUE",
                    help="tham số truyền cho hàm tạo, áp dụng cho mọi bài (có thể lặp lại)")
    ap.add_argument("--api-info", action="store_true",
                    help="in tham số của các hàm tạo/tải rồi thoát")
    return ap.parse_args()


async def main():
    args = parse_args()
    kind = args.kind
    spec = KINDS[kind]

    if args.api_info:
        async with NotebookLMClient.from_storage() as client:
            print_api_info(client)
        return

    nb_id = common.read_notebook_id(args.notebook_id)
    list_path, items = common.resolve_list(spec["feature_files"], args.file)
    print(f"Danh sách đang dùng: {list_path} ({len(items)} bài)")

    default_out = common.get_out_root() / spec["out_name"]
    if args.out_root:
        out_dir, out_default = common.get_out_root(args.out_root) / spec["out_name"], False
    else:
        out_dir, out_default = common.resolve_dir("tao_media_output", default_out)
    common.announce_default_dirs([("tao_media_output", out_default)])
    only = common.parse_only(args.only)
    if args.test and not only:
        only = {1}
    delay = common.parse_delay(args.delay)
    state = common.State(out_dir / ".state.json")

    global_opts = {}
    for raw in args.opt:
        k, _, v = raw.partition("=")
        if k.strip() and v.strip():
            global_opts[k.strip().lower()] = v.strip()

    done, skipped, failed = [], [], []
    consecutive = 0

    async with NotebookLMClient.from_storage() as client:
        gen, dl = find_gen(client, kind), find_dl(client, kind)
        if gen is None or dl is None:
            print_api_info(client)
            raise SystemExit(f"Thư viện bản này không có hàm tạo/tải cho '{kind}'. "
                             "Hãy cập nhật notebooklm-py hoặc xem tên hàm ở danh sách trên.")
        params = inspect.signature(gen).parameters

        if not any(n in params for n in INSTRUCTION_PARAMS):
            print(f"CẢNH BÁO: hàm tạo {kind} không nhận hướng dẫn riêng, nên không thể tạo riêng từng bài.")
            print("          Sẽ chỉ tạo MỘT bản cho toàn bộ nguồn.")
            items = [{"title": "Toàn bộ nguồn", "note": "", "opts": {}, "flags": set(), "chapter": ""}]

        for idx, item in enumerate(items, 1):
            title = item["title"]
            if only and idx not in only:
                continue
            old = state.get_file(title)
            if old and not args.force:
                print(f"[{idx}/{len(items)}] Bỏ qua (đã có file): {title}")
                skipped.append(title)
                continue

            print(f"[{idx}/{len(items)}] {spec['label']}: {title}  (có thể mất vài phút)")
            try:
                path = await make_one(client, nb_id, kind, spec, gen, dl, params,
                                      idx, item, args, out_dir, global_opts)
            except Exception as e:  # noqa: BLE001
                print(f"  Lỗi: {type(e).__name__}: {e}")
                failed.append(title)
                consecutive += 1
                if consecutive >= MAX_CONSECUTIVE_FAIL:
                    print(f"\nDừng vì {consecutive} lỗi liên tiếp (thường do hết hạn mức tạo nội dung "
                          "hoặc phiên đăng nhập hết hạn). Chạy lại sau, bài đã xong sẽ được bỏ qua.")
                    break
                continue
            consecutive = 0
            state.set_file(title, path)
            done.append(title)
            print(f"  -> Đã lưu: {path}")

            if kind == "mindmap":
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    md = mindmap_markdown(data, title)
                except Exception:  # noqa: BLE001
                    md = None
                if md:
                    md_path = common.save_markdown(
                        out_dir, idx, f"Mindmap: {title}", md,
                        frontmatter=args.frontmatter, tags=[spec["tag"]],
                        old_file=state.get_file(f"{title}::md"),
                        obs=common.make_obs(args, item, "Mindmap"))
                    state.set_file(f"{title}::md", md_path)
                    print(f"  -> Dàn ý Markdown: {md_path}")
                else:
                    print("  (không đoán được cấu trúc cây để tạo dàn ý Markdown, vẫn có file JSON)")

            await asyncio.sleep(random.uniform(*delay))

    if args.obsidian:
        hub = common.update_hub(root, common.get_book(args.book))
        if hub:
            print(f"Note mục lục Obsidian: {hub}")
    print("\n==== TỔNG KẾT ====")
    print(f"Xong: {len(done)} | Bỏ qua: {len(skipped)} | Lỗi: {len(failed)}")
    if failed:
        print("Bài lỗi (chạy lại sẽ tự thử lại):")
        for t in failed:
            print("  -", t)
    print("Thư mục kết quả:", out_dir)


if __name__ == "__main__":
    asyncio.run(main())
