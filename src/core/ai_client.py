"""Shared AI client helpers for Gemini API calls and response parsing."""
from __future__ import annotations

import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any

from src.core import common


def load_project_env() -> list[Path]:
    return common.load_project_env()


def parse_list(raw: str | list[str] | None) -> list[str]:
    """Split comma/semicolon/whitespace lists without forwarding a whole string as one model/key."""
    if isinstance(raw, list):
        raw = " ".join(str(item) for item in raw)
    out: list[str] = []
    for item in re.split(r"[,;\s]+", raw or ""):
        item = item.strip().strip("\"'")
        if item and item not in out:
            out.append(item)
    return out


def needs_beta(model: str) -> bool:
    m = (model or "").lower()
    return "preview" in m or m.startswith("gemma") or m in {
        "gemini-3-flash",
        "gemini-2.5-flash-lite",
    }


def choose_api_version(model: str) -> str:
    return "v1beta" if needs_beta(model) else "v1"


def classify_gemini_error(exc: BaseException) -> str:
    code = getattr(exc, "code", None)
    text = f"{type(exc).__name__}: {exc}".upper()
    if code == 400 or "HTTP 400" in text or "INVALID_ARGUMENT" in text:
        return "BAD_ARGUMENT"
    if code in (401, 403) or "401" in text or "403" in text or "API KEY" in text:
        return "BAD_KEY"
    if code == 404 or "404" in text or "NOT_FOUND" in text:
        return "MODEL_NOT_FOUND"
    if code == 429 or "429" in text or "RESOURCE_EXHAUSTED" in text or "RATE LIMIT" in text:
        return "RATE_LIMIT"
    if code in (503, 504) or "503" in text or "504" in text or "UNAVAILABLE" in text or "DEADLINE_EXCEEDED" in text:
        return "OVERLOADED"
    if "RECITATION" in text:
        return "RECITATION"
    return "UNKNOWN"


def extract_clean_json(raw_text: str) -> dict | list:
    text = (raw_text or "").strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        return json.loads(fence.group(1))
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char in "{[":
            try:
                obj, _ = decoder.raw_decode(text, index)
                return obj
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Không tìm thấy JSON hợp lệ trong phản hồi: {text[:200]}...")


def priority_process_models(models: list[str]) -> list[str]:
    lite = [m for m in models if "flash-lite" in m.lower()]
    other = [m for m in models if "flash-lite" not in m.lower()]
    return lite + other


def priority_exam_models(
    raw: str | list[str] | None,
    *,
    allow_lite: bool = False,
) -> list[str]:
    configured = [
        m for m in parse_list(raw)
        if not m.lower().startswith("gemini-2.5-flash")
    ]
    standard = [
        m for m in configured
        if "flash" in m.lower() and "lite" not in m.lower()
    ]
    # Exam solving is pinned to the newest flash family first, while old
    # gemini-2.5-flash names are never added back as implicit fallbacks.
    ordered: list[str] = []
    for model in ("gemini-3.8-flash", "gemini-3.6-flash"):
        ordered.append(model)
    for model in standard:
        if model not in ordered:
            ordered.append(model)

    if allow_lite:
        for model in ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite"):
            ordered.append(model)

    return ordered


class GeminiExecutor:
    """Small google-genai executor shared by text, JSON and vision callers."""

    def __init__(self, keys: list[str], models: list[str], timeout: float = 90.0, thinking: str = ""):
        load_project_env()
        self.keys = parse_list(keys)
        self.models = parse_list(models)
        self.timeout = timeout
        self.thinking = thinking
        self._clients: dict[tuple[str, str], Any] = {}

    def _client(self, key: str, model: str):
        from google import genai
        from google.genai import types

        version = choose_api_version(model)
        cache_key = (key, version)
        if cache_key not in self._clients:
            self._clients[cache_key] = genai.Client(
                api_key=key,
                http_options=types.HttpOptions(
                    timeout=int(self.timeout * 1000),
                    api_version=version,
                ),
            )
        return self._clients[cache_key]

    def generate(
        self,
        system: str,
        user: str,
        *,
        image_path: str | None = None,
        structured_json: bool = False,
    ) -> tuple[str, str, str]:
        from google.genai import types

        last_error: BaseException | None = None
        bad_models: set[str] = set()
        for model in self.models:
            if model in bad_models:
                continue
            for key in self.keys:
                if model in bad_models:
                    break
                try:
                    contents: list[Any] = []
                    if image_path:
                        path = Path(image_path)
                        if not path.is_file():
                            raise FileNotFoundError(f"Không tìm thấy file ảnh: {path}")
                        mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
                        contents = [
                            types.Part.from_text(text=f"{system}\n\n{user}".strip()),
                            types.Part.from_bytes(data=path.read_bytes(), mime_type=mime),
                        ]
                    else:
                        contents = [types.Part.from_text(text=f"{system}\n\n{user}".strip())]

                    config_kwargs: dict[str, Any] = {
                        "temperature": 0.2,
                        "safety_settings": [
                            types.SafetySetting(category=c, threshold="BLOCK_NONE")
                            for c in (
                                "HARM_CATEGORY_HARASSMENT",
                                "HARM_CATEGORY_HATE_SPEECH",
                                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                "HARM_CATEGORY_DANGEROUS_CONTENT",
                            )
                        ],
                    }
                    if structured_json:
                        config_kwargs["response_mime_type"] = "application/json"
                    if system and not image_path:
                        config_kwargs["system_instruction"] = system
                        contents = [types.Part.from_text(text=user)]
                    if self.thinking:
                        try:
                            config_kwargs["thinking_config"] = types.ThinkingConfig(
                                thinking_level=self.thinking
                            )
                        except (AttributeError, TypeError, ValueError):
                            pass

                    response = self._client(key, model).models.generate_content(
                        model=model,
                        contents=contents,
                        config=types.GenerateContentConfig(**config_kwargs),
                    )
                    candidates = getattr(response, "candidates", None) or []
                    finish = ""
                    text = ""
                    if candidates:
                        candidate = candidates[0]
                        finish = str(getattr(candidate, "finish_reason", "") or "")
                        parts = getattr(getattr(candidate, "content", None), "parts", None) or []
                        text = "".join(
                            getattr(part, "text", "") or ""
                            for part in parts
                            if getattr(part, "text", None) and not getattr(part, "thought", False)
                        ).strip()
                    if not text:
                        raise RuntimeError(f"Gemini API trả về rỗng ({finish or 'rỗng'})")
                    return text, finish, model
                except BaseException as exc:
                    last_error = exc
                    error_class = classify_gemini_error(exc)
                    error_text = f"{type(exc).__name__}: {exc}".lower()
                    unsupported_model = (
                        "unexpected model name format" in error_text
                        or "model" in error_text and "not supported" in error_text
                        or "unsupported model" in error_text
                    )
                    if error_class == "MODEL_NOT_FOUND" or (
                        error_class == "BAD_ARGUMENT" and unsupported_model
                    ):
                        bad_models.add(model)
                    continue
        if last_error:
            raise last_error
        raise RuntimeError("Thiếu GEMINI_API_KEYS hoặc GEMINI_API_KEY")
