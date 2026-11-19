"""
Groq Whisper (endpoint OpenAI-compatible /audio/transcriptions) bằng urllib, không cần cài SDK.

    GROQ_API_KEYS=key1,key2        nhiều key cách nhau dấu phẩy; 429 ở key này thì sang key kế
    GROQ_STT_MODELS=a,b            tuỳ chọn; mặc định whisper-large-v3 rồi whisper-large-v3-turbo

Mỗi lần gọi gửi MỘT file audio (mp3 nhỏ hơn 25MB) và nhận lại verbose_json có `segments` (start, end, text).
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"
DEFAULT_MODELS = ["whisper-large-v3", "whisper-large-v3-turbo"]
USER_AGENT = "docmint/1.0"  # User-Agent mặc định của urllib bị Cloudflare phía Groq chặn (lỗi 1010)


class GroqSTTError(Exception):
    """Không thể chép audio (hết quota phải chờ quá lâu, key bị từ chối, file không hợp lệ...)."""


def parse_list(raw: str | None) -> list[str]:
    out: list[str] = []
    for k in re.split(r"[,;\s]+", raw or ""):
        k = k.strip().strip("\"'")
        if k and k not in out:
            out.append(k)
    return out


def build_multipart(fields: list[tuple[str, str]], filename: str, content: bytes,
                    ctype: str = "audio/mpeg") -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for k, v in fields:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode("utf-8"))
    parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                  f"Content-Type: {ctype}\r\n\r\n").encode("utf-8"))
    parts.append(content)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def retry_seconds(retry_after_header: str | None, message: str) -> float | None:
    """Số giây cần chờ: ưu tiên header retry-after, không có thì đọc câu 'try again in 7m12.5s' trong thông báo."""
    if retry_after_header:
        try:
            return float(retry_after_header)
        except ValueError:
            pass
    m = re.search(r"try again in\s+(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+(?:\.\d+)?)s)?", message or "", re.I)
    if m and any(m.groups()):
        h, mi, s = (float(x) if x else 0.0 for x in m.groups())
        return h * 3600 + mi * 60 + s
    return None


class GroqSTT:
    def __init__(self, keys: list[str], models: list[str] | None = None, timeout: float = 300.0,
                 endpoint: str = ENDPOINT, sleep=time.sleep, monotonic=time.monotonic, log=print):
        self.keys = keys
        self.models = models or list(DEFAULT_MODELS)
        self.timeout = timeout
        self.endpoint = endpoint
        self._sleep = sleep
        self._now = monotonic
        self._log = log
        self.cool: dict[tuple[str, str], float] = {}
        self.bad: set[str] = set()
        self.requests = 0

    def available(self) -> bool:
        return any(k not in self.bad for k in self.keys) and bool(self.models)

    def _post(self, key: str, body: bytes, ctype: str) -> tuple[int, dict, str | None]:
        req = urllib.request.Request(self.endpoint, data=body, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": ctype, "User-Agent": USER_AGENT})
        self.requests += 1
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.status, json.loads(r.read().decode("utf-8")), None
        except urllib.error.HTTPError as e:
            try:
                obj = json.loads(e.read().decode("utf-8"))
            except Exception:  # noqa: BLE001
                obj = {}
            return e.code, obj, e.headers.get("retry-after")
        except Exception as e:  # noqa: BLE001  (mạng, timeout, JSON hỏng)
            return 0, {"error": {"message": f"{type(e).__name__}: {e}"}}, None

    def transcribe_file(self, path: str | Path, language: str = "vi", prompt: str = "",
                        max_wait: float = 1800.0) -> dict:
        """Trả về {"text", "segments": [{"start","end","text"}], "model"}. Ném GroqSTTError nếu không chép được."""
        path = Path(path)
        content = path.read_bytes()
        waited = 0.0
        note = "không có key hoặc model nào dùng được"
        while True:
            soonest = None
            for model in self.models:
                fields = [("model", model), ("language", language), ("temperature", "0"),
                          ("response_format", "verbose_json"), ("timestamp_granularities[]", "segment")]
                if prompt:
                    fields.append(("prompt", prompt))
                body, ctype = build_multipart(fields, path.name, content)
                for key in self.keys:
                    if key in self.bad:
                        continue
                    until = self.cool.get((key, model), 0.0)
                    if until > self._now():
                        soonest = until if soonest is None else min(soonest, until)
                        continue
                    for attempt in range(2):  # lỗi mạng hoặc 5xx: thử lại một lần trên cùng key
                        status, obj, retry_hdr = self._post(key, body, ctype)
                        if status != 0 and status < 500:
                            break
                        if attempt == 0:
                            self._sleep(5)
                    msg = ((obj.get("error") or {}).get("message", "")) if isinstance(obj, dict) else ""
                    if status == 200:
                        segs = [{"start": float(s.get("start", 0)), "end": float(s.get("end", 0)),
                                 "text": (s.get("text") or "").strip()}
                                for s in (obj.get("segments") or []) if (s.get("text") or "").strip()]
                        text = (obj.get("text") or "").strip()
                        if not segs and text:
                            segs = [{"start": 0.0, "end": 0.0, "text": text}]
                        return {"text": text or " ".join(s["text"] for s in segs), "segments": segs, "model": model}
                    if status == 429:
                        wait = retry_seconds(retry_hdr, msg) or 60.0
                        self.cool[(key, model)] = self._now() + wait
                        soonest = self.cool[(key, model)] if soonest is None else min(soonest, self.cool[(key, model)])
                        note = f"{model}: 429 giới hạn, chờ khoảng {wait:.0f}s"
                        continue
                    if status in (401, 403):
                        self.bad.add(key)
                        note = f"key bị từ chối ({status}) {msg[:80]}"
                        continue
                    if status in (400, 413, 404):
                        raise GroqSTTError(f"{model}: lỗi {status} {msg[:200]}")
                    note = f"{model}: lỗi {status} {msg[:120]}"
            if not any(k not in self.bad for k in self.keys):
                raise GroqSTTError(f"mọi key Groq đều bị từ chối: {note}")
            if soonest is None:
                raise GroqSTTError(note)
            wait = min(max(soonest - self._now(), 1.0), 120.0)
            if waited + wait > max_wait:
                raise GroqSTTError(f"Groq đang giới hạn, phải chờ quá {max_wait:.0f}s ({note}). Chạy lại sau, "
                                   "các đoạn đã xong được giữ trong .cache.")
            self._log(f"    ⏳ Groq đang giới hạn ({note}); chờ {wait:.0f}s")
            self._sleep(wait)
            waited += wait
