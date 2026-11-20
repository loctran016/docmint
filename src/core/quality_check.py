"""
Kiểm tra chất lượng OFFLINE (không dùng AI) cho các trang Markdown do process_book.py tạo ra.

1) Bất thường cấu trúc: trang quá ngắn, lặp dòng liên tiếp >= 3 lần, nhiều thẻ [không rõ].
2) Chính tả song ngữ Anh - Việt:
   - Tiếng Việt: kiểm tra từng âm tiết theo quy tắc ngữ âm (phụ âm đầu + vần + dấu thanh), không cần từ điển.
     Bắt tốt lỗi mất dấu / sai dấu / dính ký tự rác do OCR (ví dụ "hoc" thay cho "học", "tiêt" thay cho "tiết").
   - Tiếng Anh: từ điển của pyspellchecker (nếu có cài).
   - Thuật ngữ y khoa: file medical_terms.txt (mỗi dòng một từ, # là ghi chú) để không báo nhầm.
Chỉ trả kết quả để in ra log; không tự sửa file và không gọi API.
"""
from __future__ import annotations

import re
import statistics
import unicodedata
from pathlib import Path

SENTINEL = "<<TRANG_TRONG>>"

try:  # tuỳ chọn: thiếu thì bỏ qua phần tiếng Anh
    from spellchecker import SpellChecker  # type: ignore
except Exception:  # noqa: BLE001
    SpellChecker = None  # type: ignore

# ---------------------------------------------------------------------------
# Âm tiết tiếng Việt
# ---------------------------------------------------------------------------
_TONES = {"\u0300": "huyen", "\u0309": "hoi", "\u0303": "nga", "\u0301": "sac", "\u0323": "nang"}
_ONSETS = ["ngh", "gh", "gi", "ng", "nh", "ph", "th", "tr", "ch", "kh", "qu",
           "b", "c", "d", "đ", "g", "h", "k", "l", "m", "n", "p", "r", "s", "t", "v", "x"]
_CODAS = ["ng", "nh", "ch", "c", "m", "n", "p", "t"]
_NUCLEI = {
    "iêu", "yêu", "uyê", "uôi", "ươi", "ươu", "oai", "oay", "oeo", "uây", "uya", "uyu",
    "ai", "ao", "au", "ay", "âu", "ây", "eo", "êu", "ia", "iê", "yê", "iu", "oa", "oă", "oe", "oi",
    "ôi", "ơi", "ua", "uâ", "uê", "ui", "uô", "uơ", "uy", "ưa", "ưi", "ươ", "ưu",
    "a", "ă", "â", "e", "ê", "i", "y", "o", "ô", "ơ", "u", "ư",
}
_CH_NH_OK = {"a", "ê", "i", "y", "oa", "uê", "uy"}
_NO_C_NG = {"i", "ê", "y", "ơ"}  # "ic", "êc", "yc", "ơc", "ing", "êng", "yng", "ơng" không tồn tại
_OPEN_ONLY = {"ia", "ua", "ưa", "uơ"}      # chỉ đứng cuối âm tiết (kia, mua, mưa, thuở)
_NEED_CODA = {"iê", "yê", "uô", "ươ", "uyê"}  # luôn có phụ âm cuối (tiên, uống, ương)


def _split_tone(word: str):
    nfd = unicodedata.normalize("NFD", word)
    tones = [c for c in nfd if c in _TONES]
    if len(tones) > 1:
        return None, ""
    base = unicodedata.normalize("NFC", "".join(c for c in nfd if c not in _TONES))
    return base, (_TONES[tones[0]] if tones else "")


def _vn_ok(base: str, tone: str) -> bool:
    if not base or not base.isalpha():
        return False
    for onset in [""] + [o for o in _ONSETS if base.startswith(o)]:
        rest = base[len(onset):]
        for coda in [""] + [c for c in _CODAS if rest.endswith(c)]:
            nucleus = rest[: len(rest) - len(coda)] if coda else rest
            if nucleus not in _NUCLEI:
                continue
            if coda and nucleus in _OPEN_ONLY:
                continue
            if not coda and nucleus in _NEED_CODA:
                continue
            if coda in ("c", "ch", "p", "t") and tone not in ("sac", "nang"):
                continue
            if coda in ("ch", "nh") and nucleus not in _CH_NH_OK:
                continue
            if coda in ("c", "ng") and nucleus in _NO_C_NG:
                continue
            if onset in ("ngh", "gh") and not nucleus.startswith(("e", "ê", "i", "y")):
                continue
            return True
    return False


def is_vn_syllable(word: str) -> bool:
    """Từ có phải một âm tiết tiếng Việt hợp lệ (không xét vị trí đặt dấu, chấp nhận cả hóa/hoá)."""
    base, tone = _split_tone(word.lower())
    return base is not None and _vn_ok(base, tone)


def vn_missing_tone(word: str) -> bool:
    """Từ không hợp lệ nhưng sẽ hợp lệ nếu thêm dấu sắc: nhiều khả năng OCR làm mất dấu (hoc -> học)."""
    base, tone = _split_tone(word.lower())
    return base is not None and tone in ("", "huyen", "hoi", "nga") and _vn_ok(base, "sac")


# ---------------------------------------------------------------------------
# Từ vựng y khoa người dùng
# ---------------------------------------------------------------------------
def load_vocab(path: Path | str | None) -> set[str]:
    vocab: set[str] = set()
    if not path:
        return vocab
    p = Path(path)
    try:
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                for part in re.split(r"[\s,;]+", line):
                    if part:
                        vocab.add(unicodedata.normalize("NFC", part).lower())
    except OSError:
        pass
    return vocab


# Đuôi thuật ngữ y khoa Anh/Latinh hay gặp: coi là hợp lệ để giảm báo nhầm
_MED_SUFFIX = ("itis", "osis", "emia", "aemia", "pathy", "ectomy", "otomy", "ostomy", "plasty", "scopy",
               "oma", "penia", "cyte", "cytes", "genic", "lysis", "algia", "uria", "rrhea", "rrhage", "plasia",
               "trophy", "megaly", "ptosis", "sclerosis", "gram", "graphy")

_URL = re.compile(r"https?://\S+|www\.\S+")
_LATEX = re.compile(r"\$\$.*?\$\$|\$[^$\n]+\$", re.S)
_CODE = re.compile(r"`[^`\n]*`")
_TAGS = re.compile(r"<<[^>\n]*>>|\[không rõ[^\]]*\]")
_TOKEN = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*", re.U)

_spell_cache: dict[str, object] = {}


def _spell():
    if SpellChecker is None:
        return None
    if "en" not in _spell_cache:
        try:
            _spell_cache["en"] = SpellChecker(language="en")
        except Exception:  # noqa: BLE001
            _spell_cache["en"] = None
    return _spell_cache["en"]


def _clean(text: str) -> str:
    for rx in (_LATEX, _CODE, _URL, _TAGS):
        text = rx.sub(" ", text)
    return text


def _check_part(part: str, initial: bool, vocab: set[str], spell) -> str | None:
    """Trả về mô tả nếu từ đáng ngờ, None nếu ổn."""
    if len(part) < 3:
        return None
    if part.isupper():  # viết tắt: GHRH, UKPDS
        return None
    if any(c.isupper() for c in part[1:]):  # mRNA, pH, tên riêng viết liền kiểu camel
        return None
    if part[0].isupper() and not initial:  # tên riêng giữa câu: Graves, Basedow
        return None
    low = unicodedata.normalize("NFC", part).lower()
    if low in vocab:
        return None
    if is_vn_syllable(low):
        return None
    if spell is not None:
        try:
            if spell.known([low]):
                return None
        except Exception:  # noqa: BLE001
            pass
    if low.endswith(_MED_SUFFIX):
        return None
    if vn_missing_tone(low):
        return f"{low} (thiếu dấu?)"
    has_vn_mark = any(ord(c) > 127 for c in low)
    if has_vn_mark:
        return low[:40]  # có dấu nhưng không thành âm tiết hợp lệ: sai dấu hoặc dính ký tự
    if spell is not None and len(low) <= 24:
        try:
            fix = spell.correction(low)
        except Exception:  # noqa: BLE001
            fix = None
        if fix and fix != low:
            return f"{low[:40]}→{fix}"
    return low[:40]


def spell_page(text: str, vocab: set[str], use_spell: bool = True) -> list[str]:
    spell = _spell() if use_spell else None
    text = _clean(text)
    found: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        line = re.sub(r"^[\s>#*\-+|0-9.)]+", "", line)  # bỏ ký hiệu đầu dòng markdown
        prev_end_sentence = True
        for m in _TOKEN.finditer(line):
            s, e = m.span()
            before = line[s - 1] if s > 0 else " "
            after = line[e] if e < len(line) else " "
            initial = prev_end_sentence
            gap = line[: s].rstrip()
            prev_end_sentence = False
            if before.isdigit() or after.isdigit() or before == "_" or after == "_":
                continue
            tok = m.group(0)
            if "-" in tok or "'" in tok or "’" in tok:
                if unicodedata.normalize("NFC", tok).lower() in vocab:
                    continue
                parts = re.split(r"[-'’]", tok)
            else:
                parts = [tok]
            for part in parts:
                why = _check_part(part, initial, vocab, spell)
                if why and why not in seen:
                    seen.add(why)
                    found.append(why)
            # câu mới sau . ! ? :
            if re.match(r"\s*[.!?:]", line[e:]):
                prev_end_sentence = True
    return found


# ---------------------------------------------------------------------------
# Phân tích các trang
# ---------------------------------------------------------------------------
def _has_repeat(text: str, n: int = 3) -> bool:
    prev, run = None, 0
    for line in text.splitlines():
        s = re.sub(r"\s+", " ", line).strip()
        if not s:
            continue
        if s == prev:
            run += 1
            if run >= n:
                return True
        else:
            prev, run = s, 1
    return False


def analyze(pages: dict[int, str], vocab: set[str] | None = None, max_unclear: int = 3,
            spell: bool = True) -> dict:
    vocab = vocab or set()
    real = {n: t.strip() for n, t in pages.items() if t.strip() and t.strip() != SENTINEL}
    lengths = [len(t) for t in real.values()]
    median = statistics.median(lengths) if lengths else 0
    short_cut = max(60, 0.15 * median) if median >= 300 else 0
    res: dict = {"checked": len(real), "short": [], "repeat": [], "unclear": [], "spell": {},
                 "spell_available": (not spell) or (_spell() is not None)}
    for n in sorted(real):
        t = real[n]
        if short_cut and len(t) < short_cut:
            res["short"].append(n)
        if _has_repeat(t):
            res["repeat"].append(n)
        if t.count("[không rõ") >= max_unclear:
            res["unclear"].append(n)
        bad = spell_page(t, vocab, use_spell=spell)
        if bad:
            res["spell"][str(n)] = bad
    return res


def _rng(nums: list[int]) -> str:
    nums = sorted(nums)
    parts, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            parts.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = n
    if start is not None:
        parts.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(parts)


def format_report(res: dict, max_pages: int = 30, max_tokens: int = 6, brief: bool = False) -> list[str]:
    lines = [f"  🔎 Kiểm tra chất lượng (offline, không dùng AI) trên {res['checked']} trang:"]
    issues = False
    if res["short"]:
        issues = True
        lines.append(f"    - Trang ngắn bất thường ({len(res['short'])}): {_rng(res['short'])}")
    if res["repeat"]:
        issues = True
        lines.append(f"    - Lặp dòng liên tiếp từ 3 lần ({len(res['repeat'])}): {_rng(res['repeat'])}")
    if res["unclear"]:
        issues = True
        lines.append(f"    - Nhiều thẻ [không rõ] ({len(res['unclear'])}): {_rng(res['unclear'])}")
    sp = res["spell"]
    if sp:
        issues = True
        limit = 10 if brief else max_pages
        lines.append(f"    - Nghi sai chính tả/dấu ở {len(sp)} trang (kèm gợi ý nếu có):")
        for n in sorted(sp, key=int)[:limit]:
            toks = sp[n]
            more = f" … (+{len(toks) - max_tokens})" if len(toks) > max_tokens else ""
            lines.append(f"        trang {n}: " + ", ".join(f'"{t}"' for t in toks[:max_tokens]) + more)
        if len(sp) > limit:
            lines.append(f"        … và {len(sp) - limit} trang khác (xem mục _warnings trong sources.json)")
    if not res.get("spell_available", True):
        lines.append("    (chưa cài pyspellchecker: bỏ qua kiểm tra từ tiếng Anh)")
    if not issues:
        lines.append("    Không thấy bất thường.")
    return lines
