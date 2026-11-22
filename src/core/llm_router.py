import atexit
import asyncio
import json
import hashlib
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
import base64
import mimetypes
import shutil
from pathlib import Path
from typing import Any, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
  sys.path.insert(0, str(ROOT_DIR))

from src.core import common
from src.core.ai_client import (
    GeminiExecutor,
    extract_clean_json,
    parse_list,
    priority_exam_models,
)
from src.core.prompts import render_prompt


def _ensure_env_loaded() -> None:
  common.load_project_env()


class GeminiWebEngine:
  """Gemini web không chính thức qua gemini-webapi cho ảnh và chỉnh sửa web."""

  def __init__(self, model: str = "", gem: str = "", delay=(15.0, 25.0), log=print):
    _ensure_env_loaded()
    self._invalidate_cookie_cache_if_changed()
    try:
      from gemini_webapi import GeminiClient
    except ImportError as exc:
      raise SystemExit(
          "Thiếu gemini-webapi. Cài bằng: uv run --with gemini-webapi ..."
      ) from exc
    self.loop = asyncio.new_event_loop()
    self._bg_loop = self.loop
    self._ready = threading.Event()
    self._loop_thread = threading.Thread(
        target=self._run_loop, name="gemini-webapi-loop", daemon=True
    )
    self._loop_thread.start()
    if not self._ready.wait(timeout=5):
      self._shutdown_background_loop()
      raise RuntimeError("Gemini Web: event loop chưa sẵn sàng sau 5 giây")
    psid = os.environ.get("GEMINI_SECURE_1PSID")
    psidts = os.environ.get("GEMINI_SECURE_1PSIDTS")
    try:
      try:
        self.client = GeminiClient(psid, psidts, timeout=25, auto_refresh=False) if psid else GeminiClient(timeout=25, auto_refresh=False)
      except TypeError:
        self.client = GeminiClient(psid, psidts, timeout=25) if psid else GeminiClient(timeout=25)
    except Exception as exc:
      self._shutdown_background_loop()
      raise RuntimeError(f"Không khởi tạo được Gemini Web: {exc}") from exc
    self.model = model or None
    self.gem = gem or None
    self.delay = delay
    self._log = log
    init_coro = self.client.init(
        timeout=25, auto_close=False, close_delay=300, auto_refresh=False
    )
    try:
      self._run(init_coro)
    except BaseException:
      self._close_unawaited(init_coro)
      self._shutdown_background_loop()
      if "UNAUTHENTICATED" in str(sys.exc_info()[1]).upper():
        self._clear_gemini_cookie_cache()
        raise RuntimeError(
            "Gemini Web bị UNAUTHENTICATED. Cập nhật GEMINI_SECURE_1PSID "
            "và GEMINI_SECURE_1PSIDTS trong file .env, sau đó chạy lại."
        )
      raise
    self.gem_obj = None
    if self.gem:
      gems_coro = self.client.fetch_gems()
      try:
        self._run(gems_coro)
      except BaseException:
        self._close_unawaited(gems_coro)
        self._shutdown_background_loop()
        raise
      self.gem_obj = self.client.gems.get(name=self.gem)
    atexit.register(self.close)

  def _run_loop(self) -> None:
    asyncio.set_event_loop(self._bg_loop)
    self._ready.set()
    self._bg_loop.run_forever()

  def _run(self, coro):
    try:
      future = asyncio.run_coroutine_threadsafe(coro, self._bg_loop)
      return future.result(timeout=25)
    except TimeoutError as exc:
      try:
        future.cancel()
      except BaseException:
        pass
      raise RuntimeError("Gemini Web timeout sau 25 giây") from exc
    except BaseException:
      self._close_unawaited(coro)
      raise

  def _clear_gemini_cookie_cache(self) -> None:
    candidates = (
        Path.home() / ".gemini_webapi",
        Path.home() / ".cache" / "gemini_webapi",
        Path.home() / ".cache" / "gemini-webapi",
        Path.home() / ".config" / "gemini_webapi",
    )
    for path in candidates:
      if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
      elif path.is_file():
        path.unlink(missing_ok=True)

  def _invalidate_cookie_cache_if_changed(self) -> None:
    psid = os.environ.get("GEMINI_SECURE_1PSID", "")
    psidts = os.environ.get("GEMINI_SECURE_1PSIDTS", "")
    marker_dir = Path.home() / ".cache" / "docmint"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker = marker_dir / "gemini_cookies.sha256"
    fingerprint = hashlib.sha256(f"{psid}\n{psidts}".encode("utf-8")).hexdigest()
    previous = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
    if previous != fingerprint:
      self._clear_gemini_cookie_cache()
    marker.write_text(fingerprint, encoding="utf-8")

  @staticmethod
  def _close_unawaited(coro) -> None:
    close = getattr(coro, "close", None)
    if close and getattr(coro, "cr_frame", None) is not None:
      close()

  def _shutdown_background_loop(self) -> None:
    if getattr(self, "_loop_thread", None) and self._loop_thread.is_alive():
      self._bg_loop.call_soon_threadsafe(self._bg_loop.stop)
      self._loop_thread.join(timeout=5)
    if not self._bg_loop.is_closed():
      self._bg_loop.close()

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
    response = self._run(self.client.generate_content(prompt, **kwargs))
    text = (getattr(response, "text", "") or "").strip()
    if not text:
      raise RuntimeError("Gemini web trả về rỗng")
    return text

  def close(self) -> None:
    if getattr(self, "_bg_loop", None) and not self._bg_loop.is_closed():
      try:
        if hasattr(self.client, "close"):
          try:
            self._run(self.client.close())
          except BaseException:
            pass
      except Exception:
        pass
      finally:
        if self._loop_thread.is_alive():
          self._bg_loop.call_soon_threadsafe(self._bg_loop.stop)
          self._loop_thread.join(timeout=5)
        if not self._bg_loop.is_closed():
          self._bg_loop.close()


class LLMRouter:
  """Định tuyến API/text và vision với fallback rõ ràng."""

  def __init__(self, web_model: str = "", web_gem: str = "", log=print):
    _ensure_env_loaded()
    self.deepseek_keys = parse_list(
        (os.getenv("DEEPSEEK_API_KEYS", "") + "," + os.getenv("DEEPSEEK_API_KEY", ""))
    )
    self.gemini_keys = parse_list(
        (os.getenv("GEMINI_API_KEYS", "") + "," + os.getenv("GEMINI_API_KEY", ""))
    )
    self.web_model = web_model
    self.web_gem = web_gem
    self._log = log
    self._web_engine: Optional[GeminiWebEngine] = None
    self._web_disabled_reason: str | None = None
    self.last_engine = ""
    self.last_model = ""

  def _get_web(self) -> GeminiWebEngine:
    if self._web_disabled_reason:
      raise RuntimeError(self._web_disabled_reason)
    if self._web_engine is None:
      self._web_engine = GeminiWebEngine(
          model=self.web_model, gem=self.web_gem, log=self._log
      )
    return self._web_engine

  def describe_next(self, image_path: Optional[str] = None, backend: str = "auto") -> tuple[str, str]:
    if backend == "web":
      return "Gemini Web", self.web_model or "gemini-web"
    if image_path:
      if self.gemini_keys:
        raw = os.getenv("EXAM_SOLVER_GEMINI_MODEL", os.getenv("GEMINI_MODEL", ""))
        return "Gemini API", priority_exam_models(raw, allow_lite=True)[0]
      return "Gemini Web", self.web_model or "gemini-web"
    if self.deepseek_keys:
      return "DeepSeek API", os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip() or "deepseek-chat"
    if self.gemini_keys:
      raw = os.getenv("EXAM_SOLVER_GEMINI_MODEL", os.getenv("GEMINI_MODEL", ""))
      return "Gemini API", priority_exam_models(raw, allow_lite=True)[0]
    return "Gemini Web", self.web_model or "gemini-web"

  def _call_deepseek_json(self, system: str, user: str) -> dict | list:
    if "json" not in system.lower() and "json" not in user.lower():
      system = f"{system}\n{render_prompt('llm_router_json_suffix')}"
    last_error: BaseException | None = None
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip() or "deepseek-chat"
    for key in self.deepseek_keys:
      payload_obj = {
          "model": model,
          "messages": [
              {"role": "system", "content": system},
              {"role": "user", "content": user},
          ],
          "temperature": 0.2,
      }
      payload_obj["response_format"] = {"type": "json_object"}
      request = urllib.request.Request(
          "https://api.deepseek.com/chat/completions",
          data=json.dumps(payload_obj).encode("utf-8"),
          headers={
              "Content-Type": "application/json",
              "Authorization": "Bearer " + key,
          },
      )
      try:
        with urllib.request.urlopen(request, timeout=90) as response:
          body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return extract_clean_json(content)
      except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as exc:
        last_error = exc
        if isinstance(exc, urllib.error.HTTPError):
          detail = exc.read().decode("utf-8", errors="ignore")[:200]
          last_error = RuntimeError(f"DeepSeek HTTP {exc.code}: {detail}")
        self._log(f"⚠ DeepSeek API lỗi: {last_error}. Thử key/API tiếp theo...")
    if last_error:
      raise last_error
    raise RuntimeError("Thiếu DEEPSEEK_API_KEY hoặc DEEPSEEK_API_KEYS")

  def _call_gemini_api_json(
      self,
      system: str,
      user: str,
      image_path: Optional[str] = None,
  ) -> dict | list:
    raw_models = os.getenv(
        "EXAM_SOLVER_GEMINI_MODEL",
        os.getenv("GEMINI_MODEL", ""),
    )
    models = priority_exam_models(
        raw_models,
        allow_lite=True,
    )
    executor = GeminiExecutor(self.gemini_keys, models)
    text, _, model = executor.generate(
        system,
        user,
        image_path=image_path,
        structured_json=True,
    )
    self.last_engine = "Gemini API"
    self.last_model = model
    return extract_clean_json(text)

  def generate_json(
      self,
      system: str,
      user: str,
      image_path: Optional[str] = None,
      backend: str = "auto",
  ) -> dict | list:
    if backend == "web":
      self.last_engine = "Gemini Web"
      self.last_model = self.web_model or "gemini-web"
      raw = self._get_web().generate(system, user, image_path=image_path)
      return extract_clean_json(raw)
    if image_path:
      try:
        self.last_engine = "Gemini API"
        raw_models = os.getenv("EXAM_SOLVER_GEMINI_MODEL", os.getenv("GEMINI_MODEL", ""))
        self.last_model = priority_exam_models(
            raw_models,
            allow_lite=True,
        )[0]
        return self._call_gemini_api_json(system, user, image_path=image_path)
      except BaseException as api_exc:
        self._log(f"⚠ Gemini API vision lỗi: {api_exc}. Fallback sang Gemini Web...")
        try:
          raw = self._get_web().generate(system, user, image_path=image_path)
          self.last_engine = "Gemini Web"
          self.last_model = self.web_model or "gemini-web"
          return extract_clean_json(raw)
        except BaseException as web_exc:
          web_text = str(web_exc)
          if "timeout" in web_text.lower() or "UNAUTHENTICATED" in web_text.upper():
            self._web_disabled_reason = (
                "Gemini Web đã bị tạm khóa trong phiên này. Cập nhật GEMINI_SECURE_1PSID "
                "và GEMINI_SECURE_1PSIDTS trong file .env."
            )
            self._log(f"⚠ {self._web_disabled_reason}")
          raise RuntimeError(
              f"Gemini API và Gemini Web đều lỗi. API: {api_exc}; Web: {web_exc}"
          ) from web_exc
    if self.deepseek_keys:
      try:
        self.last_engine = "DeepSeek API"
        self.last_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip() or "deepseek-chat"
        return self._call_deepseek_json(system, user)
      except BaseException as deepseek_exc:
        self._log(f"⚠ DeepSeek API không khả dụng: {deepseek_exc}. Fallback sang Gemini API...")
    if self.gemini_keys:
      try:
        raw_models = os.getenv("EXAM_SOLVER_GEMINI_MODEL", os.getenv("GEMINI_MODEL", ""))
        self.last_engine = "Gemini API"
        self.last_model = priority_exam_models(
            raw_models,
            allow_lite=True,
        )[0]
        return self._call_gemini_api_json(system, user)
      except BaseException as gemini_exc:
        self._log(f"⚠ Gemini API không khả dụng: {gemini_exc}. Fallback cuối: Gemini Web...")
        try:
          raw = self._get_web().generate(system, user)
          self.last_engine = "Gemini Web"
          self.last_model = self.web_model or "gemini-web"
          return extract_clean_json(raw)
        except BaseException as web_exc:
          web_text = str(web_exc)
          if "timeout" in web_text.lower() or "UNAUTHENTICATED" in web_text.upper():
            self._web_disabled_reason = (
                "Gemini Web đã bị tạm khóa trong phiên này. Cập nhật GEMINI_SECURE_1PSID "
                "và GEMINI_SECURE_1PSIDTS trong file .env."
            )
            self._log(f"⚠ {self._web_disabled_reason}")
          raise RuntimeError(
              f"Gemini API và Gemini Web đều lỗi. API: {gemini_exc}; Web: {web_exc}"
          ) from web_exc
    if self._web_disabled_reason:
      raise RuntimeError(self._web_disabled_reason)
    raise RuntimeError("Thiếu DEEPSEEK_API_KEYS/DEEPSEEK_API_KEY và GEMINI_API_KEYS/GEMINI_API_KEY")
