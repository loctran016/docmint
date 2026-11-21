#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-genai", "python-dotenv"]
# ///
"""
Lớp biên tập văn phong (menu [17]): viết lại bài giảng thô từ NotebookLM thành văn phong sách giáo khoa,
tách biệt khỏi bước hút dữ liệu của NotebookLM.

    ket_qua/giang_bai/*.md  (thô)  --copy-->  ket_qua/raw/   (bản thô, không bao giờ bị ghi đè)
                                  --biên tập-->  ket_qua/polished/  (bản đã biên tập)

Để KHÔNG sót ý:
  - Cắt theo từng mục `## ` rồi cắt tiếp thành phần ~700 từ; mỗi lần gọi chỉ biên tập một phần.
  - Kiểm tra số liệu: mọi con số trong bản thô phải còn trong bản biên tập; thiếu thì thử lại một lần rồi giữ bản thô
    của phần đó và ghi vào báo cáo.
  - Prompt cố định (bien_tap_style.md + quy tắc cấm tóm tắt) gửi qua system_instruction.
  - Gemini từ chối (RECITATION) hoặc rỗng: thử Groq (GROQ_API_KEYS, model GROQ_TEXT_MODELS), không được thì giữ bản thô.
Kết quả từng phần được cache (.cache/bien_tap/) nên chạy dở có thể chạy lại tiếp; đổi file khung văn phong thì tự làm lại.

Dùng:
    uv run bien_tap.py --test                      # thử 2 phần đầu của file đầu tiên, in ra màn hình, không lưu
    uv run bien_tap.py                             # biên tập cả thư mục ket_qua/giang_bai
    uv run bien_tap.py --match "NÔN" --force       # chọn file theo tên, bỏ cache
    uv run --with gemini-webapi bien_tap.py --backend web   # (tuỳ chọn) Gemini web bằng cookie, xem README

Biến môi trường: GEMINI_API_KEYS (hoặc GEMINI_API_KEY); BIEN_TAP_MODEL hoặc GEMINI_MODEL (nhiều model cách nhau dấu phẩy);
REQUEST_DELAY; GROQ_API_KEYS, GROQ_TEXT_MODELS (dự phòng RECITATION); backend web: GEMINI_SECURE_1PSID, GEMINI_SECURE_1PSIDTS.
"""
from __future__ import annotations
import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time
from pathlib import Path

from src.core import common
from src.core.prompts import render_prompt

BASE = common.CONFIG_DIR
DEFAULT_MODELS = "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite"
MAX_WORDS = 700

CORE_RULES = render_prompt("bien_tap_core_rules")
SUMMARY_RULE = render_prompt("bien_tap_summary", n="{n}")


# ---------------------------------------------------------------------------
# Tách văn bản
# ---------------------------------------------------------------------------
def split_document(text: str) -> tuple[list[str], list[tuple[str | None, str]]]:
    """Trả về (phần đầu giữ nguyên: frontmatter + tiêu đề H1, [(dòng '## ...' hoặc None, nội dung)])."""
    lines = text.replace("\r\n", "\n").splitlines()
    header: list[str] = []
    i = 0
    if lines and lines[0].strip() == "---":
        j = next((k for k in range(1, len(lines)) if lines[k].strip() == "---"), None)
        if j is not None:
            header, i = lines[: j + 1], j + 1
    while i < len(lines) and not lines[i].strip():
        header.append(lines[i]); i += 1
    if i < len(lines) and re.match(r"^# \S", lines[i]):
        header.append(lines[i]); i += 1
    sections: list[tuple[str | None, str]] = []
    head, cur, fence = None, [], False
    for line in lines[i:]:
        if line.strip().startswith("```"):
            fence = not fence
        if not fence and re.match(r"^## \S", line):
            if head is not None or "".join(cur).strip():
                sections.append((head, "\n".join(cur).strip("\n")))
            head, cur = line, []
        else:
            cur.append(line)
    if head is not None or "".join(cur).strip():
        sections.append((head, "\n".join(cur).strip("\n")))
    return header, sections


def blocks(body: str) -> list[str]:
    out, cur, fence = [], [], False
    for line in body.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
        if not line.strip() and not fence:
            if cur:
                out.append("\n".join(cur)); cur = []
        else:
            cur.append(line)
    if cur:
        out.append("\n".join(cur))
    return out


def split_parts(body: str, max_words: int = MAX_WORDS) -> list[str]:
    parts, cur, n = [], [], 0
    for b in blocks(body):
        w = len(b.split())
        if cur and n + w > max_words:
            parts.append("\n\n".join(cur)); cur, n = [], 0
        cur.append(b); n += w
    if cur:
        parts.append("\n\n".join(cur))
    return parts


# ---------------------------------------------------------------------------
# Kiểm tra số liệu
# ---------------------------------------------------------------------------
_CITE = re.compile(r"\[\d+(?:\s*[,\-–]\s*\d+)*\]")
_LISTNUM = re.compile(r"^\s*\d+[.)]\s+", re.M)
_NUM = re.compile(r"\d+(?:[.,]\d+)?")


def numbers(text: str) -> set[str]:
    text = _LISTNUM.sub("", _CITE.sub(" ", text))
    return {n.replace(",", ".") for n in _NUM.findall(text)}


def missing_numbers(raw: str, edited: str) -> list[str]:
    return sorted(numbers(raw) - numbers(edited), key=lambda x: (len(x), x))


# ---------------------------------------------------------------------------
# Backend API chính thức (Gemini API key, xoay key x model)
# ---------------------------------------------------------------------------
def parse_list(raw) -> list[str]:
    out: list[str] = []
    for k in re.split(r"[,;\s]+", raw or ""):
        k = k.strip().strip("\"'")
        if k and k not in out:
            out.append(k)
    return out


def needs_beta(model: str) -> bool:
    m = model.lower()
    return "preview" in m or m.startswith("gemma") or m in ("gemini-3-flash", "gemini-2.5-flash-lite")


class ApiEditor:
    def __init__(self, keys, models, thinking="medium", delay=6.0, timeout=240.0, sleep=time.sleep, log=print):
        self.keys, self.models = list(keys), list(models)
        self.thinking, self.delay, self.timeout = thinking, delay, timeout
        self._sleep, self._log = sleep, log
        self._clients: dict = {}
        self.bad_keys: set[str] = set()
        self.bad_models: set[str] = set()
        self.no_thinking: set[str] = set()
        self.no_system: set[str] = set()
        self.start = 0
        self.last_model = ""

    def _client(self, key, model):
        from google import genai
        from google.genai import types
        ver = "v1beta" if needs_beta(model) else "v1"
        if (key, ver) not in self._clients:
            self._clients[(key, ver)] = genai.Client(
                api_key=key, http_options=types.HttpOptions(timeout=int(self.timeout * 1000), api_version=ver))
        return self._clients[(key, ver)]

    def _call(self, key, model, system, user):
        from google.genai import types
        cfg = dict(temperature=0.3, max_output_tokens=16384, safety_settings=[
            types.SafetySetting(category=c, threshold="BLOCK_NONE") for c in (
                "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")])
        if model in self.no_system:
            contents = [system + "\n\n" + user]
        else:
            contents = [user]
            cfg["system_instruction"] = system
        if self.thinking and model not in self.no_thinking and "thinking_level" in types.ThinkingConfig.model_fields:
            cfg["thinking_config"] = types.ThinkingConfig(thinking_level=self.thinking)
        resp = self._client(key, model).models.generate_content(
            model=model, contents=contents, config=types.GenerateContentConfig(**cfg))
        text, finish = "", ""
        try:
            c = (resp.candidates or [None])[0]
            finish = str(getattr(c, "finish_reason", "") or "")
            parts = getattr(getattr(c, "content", None), "parts", None) or []
            text = "".join((p.text or "") for p in parts if getattr(p, "text", None) and not getattr(p, "thought", False))
        except Exception:  # noqa: BLE001
            pass
        return text.strip(), finish

    def edit(self, system: str, user: str) -> tuple[str | None, str]:
        """(văn bản hoặc None, ghi chú). Ghi chú bắt đầu bằng 'RECITATION' nếu bị bộ lọc bản quyền chặn."""
        note = "không có cặp key/model nào dùng được"
        for round_no in range(4):
            pairs = [(k, m) for m in self.models for k in self.keys
                     if k not in self.bad_keys and m not in self.bad_models]
            if not pairs:
                return None, note
            for i in range(len(pairs)):
                key, model = pairs[(self.start + i) % len(pairs)]
                try:
                    text, finish = self._call(key, model, system, user)
                except Exception as e:  # noqa: BLE001
                    code = getattr(e, "code", None)
                    msg = re.sub(r"\s+", " ", str(e))[:160]
                    low = msg.lower()
                    if code == 400 and "thinking" in low and model not in self.no_thinking:
                        self.no_thinking.add(model); self._log(f"    ⚠ {model}: không nhận thinking_level → bỏ tham số này"); continue
                    if code == 400 and "instruction" in low and model not in self.no_system:
                        self.no_system.add(model); self._log(f"    ⚠ {model}: không nhận system_instruction → gộp vào lời nhắn"); continue
                    if code in (401, 403) or "api key" in low:
                        self.bad_keys.add(key); note = f"key bị từ chối: {msg}"
                    elif code == 404:
                        self.bad_models.add(model); note = f"model {model} không dùng được: {msg}"
                    else:
                        note = f"{model}: {msg}"
                    continue
                if "RECITATION" in finish.upper():
                    return None, f"RECITATION ({model})"
                if text and "MAX_TOKENS" not in finish.upper():
                    self.start = (self.start + i) % len(pairs)
                    self.last_model = model
                    self._sleep(self.delay)
                    return text, ""
                if not text:
                    return None, f"{model} trả về rỗng ({finish or 'rỗng'})"
                note = f"{model}: đầu ra bị cắt (MAX_TOKENS)"
            if round_no < 3:
                self._log(f"    ⏳ Gemini chưa dùng được ({note}); chờ {20 * (round_no + 1)}s rồi thử lại")
                self._sleep(20 * (round_no + 1))
        return None, note


# ---------------------------------------------------------------------------
# Backend web (tuỳ chọn): gemini-webapi + cookie, dùng gói Google AI Pro
# ---------------------------------------------------------------------------
class WebEditor:
    """Compatibility wrapper around the shared Gemini Web engine."""

    def __init__(
        self, model="", gem="", delay=(15.0, 25.0), sleep=time.sleep, log=print
    ):
        from src.core.llm_router import GeminiWebEngine

        self.engine = GeminiWebEngine(model=model, gem=gem, delay=delay, log=log)
        self.last_model = self.engine.last_model

    def edit(self, system: str, user: str) -> tuple[str | None, str]:
        try:
            text = self.engine.generate(system, user)
            return text, ""
        except Exception as e:  # noqa: BLE001
            return None, f"Gemini web lỗi: {re.sub(chr(10), ' ', str(e))[:160]}"


# ---------------------------------------------------------------------------
# Biên tập một file
# ---------------------------------------------------------------------------
def sha(*parts: str) -> str:
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


def strip_heading(text: str, head: str | None) -> str:
    lines = text.strip().splitlines()
    if lines and re.match(r"^##\s", lines[0]):
        lines = lines[1:]
    return "\n".join(lines).strip()


def edit_part(editor, groq, system: str, head: str | None, part: str, k: int, n: int, sec_no: int,
              last: bool, summary: bool, log) -> tuple[str, str, str]:
    """Trả về (văn bản, nguồn, cờ). cờ rỗng nếu ổn; 'giữ bản thô: ...' nếu phải dùng bản thô."""
    title = (head or "").lstrip("# ").strip() or "(phần mở đầu)"
    note = render_prompt("bien_tap_summary", n=sec_no) if (last and summary and head) else ""
    user = render_prompt("bien_tap_user", title=title, k=k, n=n, note=note, part=part)
    text, why = editor.edit(system, user)
    source = editor.last_model
    if text is None and why.startswith("RECITATION") and groq is not None and groq.available():
        log("    ↺ Gemini từ chối (RECITATION) → thử Groq")
        gtext, gmodel, gnote = groq.chat_text(system, user, groq_text_models())
        if gtext:
            text, source, why = gtext, "groq/" + gmodel.split("/")[-1], ""
        else:
            why = f"{why}; Groq: {gnote}"
    if text is None:
        return part, "gốc", f"giữ bản thô: {why}"
    text = strip_heading(text, head)
    miss = missing_numbers(part, text)
    if miss:
        log(f"    ⚠ thiếu số liệu {miss[:6]} → thử lại một lần")
        retry_user = user + "\n\n" + render_prompt(
            "bien_tap_retry_note", missing=", ".join(miss)
        )
        t2, why2 = editor.edit(system, retry_user)
        if t2 is not None:
            t2 = strip_heading(t2, head)
            if not missing_numbers(part, t2):
                return t2, editor.last_model, ""
            miss = missing_numbers(part, t2)
        return part, "gốc", f"giữ bản thô: thiếu số liệu {miss[:8]}"
    return text, source, ""


def groq_text_models() -> list[str] | None:
    return parse_list(os.environ.get("GROQ_TEXT_MODELS")) or None


def polish_file(path: Path, args, editor, groq, system: str, log=print) -> dict:
    text = path.read_text(encoding="utf-8")
    header, sections = split_document(text)
    cache_path = common.REPO_ROOT / ".cache" / "bien_tap" / (re.sub(r"[^\w.-]+", "_", path.stem) + ".json")
    cache: dict = {}
    if cache_path.exists() and not args.force:
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}
    stats = {"file": path.name, "parts": 0, "edited": 0, "cached": 0, "kept_raw": [], "groq": 0}
    out_sections: list[str] = []
    sec_no = 0
    limit = 2 if args.test else None
    for head, body in sections:
        if head is not None:
            sec_no += 1
        parts = split_parts(body, args.max_words) if body.strip() else []
        done: list[str] = []
        for k, part in enumerate(parts, 1):
            if limit is not None and stats["parts"] >= limit:
                done.append(part); continue
            stats["parts"] += 1
            key = sha(system, str(head), part, str(args.summary), str(k == len(parts)))
            if key in cache and not args.test:
                res, source, flag = cache[key]["text"], cache[key]["source"], cache[key]["flag"]
                stats["cached"] += 1
            else:
                log(f"  [{stats['parts']}] {(head or 'mở đầu').lstrip('# ')[:50]} (phần {k}/{len(parts)}, {len(part.split())} từ)")
                res, source, flag = edit_part(editor, groq, system, head, part, k, len(parts), sec_no,
                                              k == len(parts), args.summary, log)
                cache[key] = {"text": res, "source": source, "flag": flag}
                if not args.test:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            if flag:
                stats["kept_raw"].append(f"{(head or 'mở đầu').lstrip('# ')} (phần {k}): {flag}")
            else:
                stats["edited"] += 1
            if source.startswith("groq/"):
                stats["groq"] += 1
            done.append(res)
        body_out = "\n\n".join(done)
        out_sections.append(((head + "\n\n") if head else "") + body_out)
    result = "\n".join(header).rstrip("\n") + "\n\n" + "\n\n".join(s for s in out_sections if s.strip()) + "\n"
    stats["text"] = result
    return stats


def make_editor(args, log=print):
    if args.backend == "web":
        return WebEditor(model=args.model, gem=args.gem, log=log)
    keys = parse_list(os.environ.get("GEMINI_API_KEYS")) or parse_list(os.environ.get("GEMINI_API_KEY"))
    if not keys:
        raise SystemExit("Chưa có GEMINI_API_KEYS hoặc GEMINI_API_KEY trong .env (tạo ở https://aistudio.google.com/apikey).")
    models = parse_list(args.model or os.environ.get("BIEN_TAP_MODEL") or os.environ.get("GEMINI_MODEL") or DEFAULT_MODELS)
    try:
        delay = float(os.environ.get("REQUEST_DELAY") or 6)
    except ValueError:
        delay = 6.0
    return ApiEditor(keys, models, thinking=args.thinking, delay=delay, log=log)


def make_groq(log=print):
    try:
        from src.core import groq_client
    except ImportError:
        return None
    keys = groq_client.parse_list(os.environ.get("GROQ_API_KEYS"))
    return groq_client.GroqPool(keys, timeout=180, log=log) if keys else None


def parse_args(argv=None):
    root = common.get_out_root()
    ap = argparse.ArgumentParser(description="Biên tập văn phong bài giảng thô từ NotebookLM")
    ap.add_argument("--in", dest="inp", default=str(Path(root) / "giang_bai"), help="file hoặc thư mục .md thô")
    ap.add_argument("--raw-dir", default=str(Path(root) / "raw"), help="nơi giữ bản thô (không bị ghi đè)")
    ap.add_argument("--out", default=str(Path(root) / "polished"), help="thư mục kết quả")
    ap.add_argument("--style", default=str(common.CONFIG_DIR / common.BIEN_TAP_STYLE_FILE.name),
                    help="file khung văn phong (system prompt)")
    ap.add_argument("--backend", choices=["api", "web"], default="api")
    ap.add_argument("--model", default="", help="model (api: nhiều model cách nhau dấu phẩy; web: tên model Gemini web)")
    ap.add_argument("--gem", default="", help="(web) tên Gem đã tạo trên gemini.google.com")
    ap.add_argument("--thinking", default="medium", choices=["", "minimal", "low", "medium", "high"],
                    help="mức suy luận (api); để trống = không gửi tham số")
    ap.add_argument("--max-words", type=int, default=MAX_WORDS)
    ap.add_argument("--match", default="", help="chỉ file có tên chứa chuỗi này")
    ap.add_argument("--force", action="store_true", help="bỏ cache và làm lại")
    ap.add_argument("--test", action="store_true", help="thử 2 phần đầu của file đầu tiên, in ra, không lưu")
    ap.add_argument("--no-summary", dest="summary", action="store_false", help="không thêm dòng Tóm ý cuối mục")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    common.load_project_env()
    args = parse_args(argv)
    src = Path(args.inp)
    files = [src] if src.is_file() else sorted(src.glob("*.md")) if src.is_dir() else []
    files = [f for f in files if args.match.lower() in f.name.lower() and not f.name.startswith("_")]
    if not files:
        print(f"Không thấy file .md nào ở {src}" + (f" (lọc '{args.match}')" if args.match else ""))
        return 2
    if args.test:
        files = files[:1]
    try:
        style = Path(args.style).read_text(encoding="utf-8").strip()
    except OSError:
        print(f"Không đọc được {args.style}; dùng khung văn phong tối thiểu.")
        style = render_prompt("bien_tap_fallback_system")
    system = style + CORE_RULES
    editor = make_editor(args)
    groq = make_groq()
    out_dir, raw_dir = Path(args.out), Path(args.raw_dir)
    print(f"{len(files)} file | backend: {args.backend} | model: {getattr(editor, 'models', args.model or 'mặc định')}"
          f" | Groq dự phòng: {'có' if groq else 'không'}" + (" | CHẾ ĐỘ THỬ" if args.test else ""))
    report, bad = [], 0
    for f in files:
        print(f"\n=== {f.name} ===")
        if not args.test and raw_dir.resolve() != f.parent.resolve():
            raw_dir.mkdir(parents=True, exist_ok=True)
            if not (raw_dir / f.name).exists():
                shutil.copy2(f, raw_dir / f.name)
        st = polish_file(f, args, editor, groq, system)
        if args.test:
            print("\n----- KẾT QUẢ THỬ -----\n" + st["text"])
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f.name).write_text(st["text"], encoding="utf-8")
        line = f"{f.name}: {st['edited']}/{st['parts']} phần đã biên tập" + (f" ({st['cached']} từ cache)" if st["cached"] else "")
        if st["groq"]:
            line += f", {st['groq']} phần do Groq"
        print("  " + line)
        report.append("- " + line)
        for k in st["kept_raw"]:
            bad += 1
            print(f"  ⚠ {k}")
            report.append(f"  - ⚠ {k}")
    if not args.test:
        (out_dir / "_bao_cao.md").write_text("# Báo cáo biên tập\n\n" + "\n".join(report) + "\n", encoding="utf-8")
    print(f"\nXong. {'Có ' + str(bad) + ' phần giữ bản thô (xem cảnh báo ở trên)' if bad else 'Mọi phần đều đã biên tập'}."
          + ("" if args.test else f" Kết quả: {out_dir}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
