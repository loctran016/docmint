import atexit
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional
from src.core.prompts import render_prompt

try:
  from src.core.common import ROOT_DIR
except ImportError:
  ROOT_DIR = Path(__file__).resolve().parents[2]


def _ensure_env_loaded() -> None:
  env_path = ROOT_DIR / ".env"
  if not env_path.exists():
    return
  try:
    from dotenv import load_dotenv
    load_dotenv(env_path, override=False)
  except ImportError:
    for line in env_path.read_text(encoding="utf-8").splitlines():
      line = line.strip()
      if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def extract_clean_json(raw_text: str) -> dict | list:
  text = raw_text.strip()
  fence_match = re.search(
      r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```",
      text,
      flags=re.DOTALL | re.IGNORECASE,
  )
  if fence_match:
    return json.loads(fence_match.group(1))
  decoder = json.JSONDecoder()
  for idx, char in enumerate(text):
    if char in "{[":
      try:
        obj, _ = decoder.raw_decode(text, idx)
        return obj
      except json.JSONDecodeError:
        continue
  raise ValueError(f"Không tìm thấy JSON hợp lệ trong phản hồi: {text[:200]}...")


class GeminiWebEngine:
  """Gemini web không chính thức qua gemini-webapi cho ảnh và chỉnh sửa web."""

  def __init__(self, model: str = "", gem: str = "", delay=(15.0, 25.0), log=print):
    _ensure_env_loaded()
    try:
      import asyncio
      from gemini_webapi import GeminiClient
    except ImportError as exc:
      raise SystemExit(
          "Thiếu gemini-webapi. Cài bằng: uv run --with gemini-webapi ..."
      ) from exc
    self.loop = asyncio.new_event_loop()
    psid = os.environ.get("GEMINI_SECURE_1PSID")
    psidts = os.environ.get("GEMINI_SECURE_1PSIDTS")
    self.client = GeminiClient(psid, psidts) if psid else GeminiClient()
    self.model = model or None
    self.gem = gem or None
    self.delay = delay
    self._log = log
    self.loop.run_until_complete(
        self.client.init(timeout=60, auto_close=False, close_delay=300, auto_refresh=True)
    )
    self.gem_obj = None
    if self.gem:
      self.loop.run_until_complete(self.client.fetch_gems())
      self.gem_obj = self.client.gems.get(name=self.gem)
    atexit.register(self.close)

  def generate(self, system: str, user: str, image_path: Optional[str] = None) -> str:
    prompt = f"{system}\n\n{user}".strip()
    kwargs = {"temporary": True}
    if self.model:
      kwargs["model"] = self.model
    if self.gem_obj is not None:
      kwargs["gem"] = self.gem_obj
    if image_path:
      if not os.path.exists(image_path):
        raise FileNotFoundError(f"Không tìm thấy file ảnh: {image_path}")
      kwargs["files"] = [str(image_path)]
    response = self.loop.run_until_complete(
        self.client.generate_content(prompt, **kwargs)
    )
    text = (getattr(response, "text", "") or "").strip()
    time.sleep(random.uniform(*self.delay))
    if not text:
      raise RuntimeError("Gemini web trả về rỗng")
    return text

  def close(self) -> None:
    if getattr(self, "loop", None) and not self.loop.is_closed():
      try:
        if hasattr(self.client, "close"):
          self.loop.run_until_complete(self.client.close())
      except Exception:
        pass
      finally:
        self.loop.close()


class LLMRouter:
  """Ảnh -> Gemini Web; văn bản -> DeepSeek API. Không dùng google-genai."""

  def __init__(self, web_model: str = "", web_gem: str = "", log=print):
    _ensure_env_loaded()
    self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    self.web_model = web_model
    self.web_gem = web_gem
    self._log = log
    self._web_engine: Optional[GeminiWebEngine] = None

  def _get_web(self) -> GeminiWebEngine:
    if self._web_engine is None:
      self._web_engine = GeminiWebEngine(
          model=self.web_model, gem=self.web_gem, log=self._log
      )
    return self._web_engine

  def _call_deepseek_json(self, system: str, user: str) -> dict | list:
    if "json" not in system.lower() and "json" not in user.lower():
      system = f"{system}\n{render_prompt('llm_router_json_suffix')}"
    payload = json.dumps({
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_key}",
        },
    )
    try:
      with urllib.request.urlopen(request, timeout=120) as response:
        body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
      detail = exc.read().decode("utf-8", errors="ignore")[:200]
      raise RuntimeError(f"DeepSeek HTTP {exc.code}: {detail}") from exc
    content = body["choices"][0]["message"]["content"]
    return extract_clean_json(content)

  def generate_json(
      self, system: str, user: str, image_path: Optional[str] = None
  ) -> dict | list:
    if image_path:
      raw = self._get_web().generate(system, user, image_path=image_path)
      return extract_clean_json(raw)
    if not self.deepseek_key:
      raise SystemExit("Thiếu DEEPSEEK_API_KEY trong môi trường hoặc .env")
    return self._call_deepseek_json(system, user)
