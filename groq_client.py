"""
Groq Vision (OpenAI-compatible) bằng urllib, không cần cài SDK.
Dùng làm dự phòng khi Gemini từ chối chép một trang vì RECITATION: Groq không có bộ lọc này.

    GROQ_API_KEYS=key1,key2        (nhiều key cách nhau dấu phẩy; hết 429 ở key này thì sang key kế)
    GROQ_MODELS=modelA,modelB      (tuỳ chọn; mặc định llama-4-maverick rồi llama-4-scout)
"""
from __future__ import annotations

import base64
import io
import json
import re
import time
import urllib.error
import urllib.request

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODELS = ["meta-llama/llama-4-maverick-17b-128e-instruct",
                  "meta-llama/llama-4-scout-17b-16e-instruct"]
MAX_B64 = 3_500_000  # Groq giới hạn ảnh base64 khoảng 4MB mỗi request
USER_AGENT = "docmint/1.0"  # User-Agent mặc định của urllib bị Cloudflare phía Groq chặn (lỗi 1010)


def parse_list(raw: str | None) -> list[str]:
    out: list[str] = []
    for k in re.split(r"[,;\s]+", raw or ""):
        k = k.strip().strip("\"'")
        if k and k not in out:
            out.append(k)
    return out


def fit_image(jpeg: bytes, limit: int = MAX_B64) -> bytes:
    """Giữ ảnh gốc nếu đủ nhỏ; nếu base64 vượt giới hạn thì giảm chất lượng, rồi giảm kích thước."""
    if len(jpeg) * 4 // 3 + 4 <= limit:
        return jpeg
    from PIL import Image  # PIL đã có sẵn trong môi trường của process_book.py
    img = Image.open(io.BytesIO(jpeg))
    img.load()
    quality, scale = 85, 1.0
    for _ in range(8):
        work = img if scale == 1.0 else img.resize((int(img.width * scale), int(img.height * scale)))
        buf = io.BytesIO()
        work.save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()
        if len(data) * 4 // 3 + 4 <= limit:
            return data
        quality = max(60, quality - 10)
        scale *= 0.85
    return data


class GroqPool:
    def __init__(self, keys: list[str], models: list[str] | None = None, timeout: float = 120.0,
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
        self.pages = 0
        self.requests = 0

    def available(self) -> bool:
        return any(k not in self.bad for k in self.keys) and bool(self.models)

    def _post(self, key: str, payload: dict) -> tuple[int, dict, float | None]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=data, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": USER_AGENT})
        self.requests += 1
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.status, json.loads(r.read().decode("utf-8")), None
        except urllib.error.HTTPError as e:
            retry = None
            try:
                retry = float(e.headers.get("retry-after")) if e.headers.get("retry-after") else None
            except (TypeError, ValueError):
                retry = None
            try:
                body = json.loads(e.read().decode("utf-8"))
            except Exception:  # noqa: BLE001
                body = {}
            return e.code, body, retry
        except Exception as e:  # noqa: BLE001  (mạng, timeout, JSON hỏng)
            return 0, {"error": {"message": f"{type(e).__name__}: {e}"}}, None

    def transcribe(self, jpeg: bytes, system_prompt: str, user_text: str,
                   max_tokens: int = 8192) -> tuple[str | None, str, str]:
        """Trả về (văn bản hoặc None, model đã dùng, ghi chú lỗi)."""
        b64 = base64.b64encode(fit_image(jpeg)).decode("ascii")
        note = "không có key/model nào dùng được"
        for pass_no in range(2):
            soonest = None
            for model in self.models:
                payload = {
                    "model": model, "temperature": 0.1, "max_tokens": max_tokens,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": [
                            {"type": "text", "text": user_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                        ]},
                    ],
                }
                for key in self.keys:
                    if key in self.bad:
                        continue
                    wait_until = self.cool.get((key, model), 0.0)
                    if wait_until > self._now():
                        soonest = wait_until if soonest is None else min(soonest, wait_until)
                        continue
                    for attempt in range(2):  # lỗi mạng/5xx: thử lại một lần trên cùng key
                        status, body, retry = self._post(key, payload)
                        if status != 0 and status < 500:
                            break
                        if attempt == 0:
                            self._sleep(5)
                    msg = (body.get("error") or {}).get("message", "") if isinstance(body, dict) else ""
                    if status == 200:
                        try:
                            choice = body["choices"][0]
                            text = (choice["message"].get("content") or "").strip()
                        except Exception:  # noqa: BLE001
                            text = ""
                        if text:
                            self.pages += 1
                            if choice.get("finish_reason") == "length":
                                text += "\n\n[không rõ — trang này có thể bị cắt cụt]"
                            return text, model, ""
                        note = f"{model}: phản hồi rỗng"
                        continue
                    if status == 429:
                        self.cool[(key, model)] = self._now() + (retry if retry else 30.0)
                        note = f"{model}: 429 giới hạn"
                        continue
                    if status in (401, 403):
                        self.bad.add(key)
                        note = f"key bị từ chối ({status}) {msg[:80]}"
                        continue
                    note = f"{model}: lỗi {status} {msg[:120]}"
                    if status in (400, 404, 413):
                        break  # lỗi của model/payload: sang model kế
            if pass_no == 0 and soonest is not None and not any(
                    k not in self.bad and self.cool.get((k, m), 0.0) <= self._now()
                    for k in self.keys for m in self.models):
                self._sleep(min(max(soonest - self._now(), 1.0), 60.0))
                continue
            break
        return None, "", note
