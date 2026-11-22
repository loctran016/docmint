import asyncio
import sys
import types

import pytest

from src.llm.exam_preprocessor import (
    QuestionItem,
    configure_formula_mode,
    slugify_vi,
)


def test_slugify_vi_removes_vietnamese_diacritics():
    assert slugify_vi("Nội tiết") == "noi-tiet"
    assert slugify_vi("Đại học Đường/Da liễu") == "dai-hoc-duong-da-lieu"


def test_configure_formula_mode_lists_math_questions_and_caps_output(
    monkeypatch,
    capsys,
):
    questions = [
        QuestionItem(
            id=f"Q{i}_i",
            q_num=str(i),
            stem=(
                "Tính BMI ở một bệnh nhân nặng 70 kg "
                + ("nội dung kiểm tra " * 10)
            ),
        )
        for i in range(1, 18)
    ]

    monkeypatch.setattr("builtins.input", lambda: "")
    mode = configure_formula_mode(questions)
    output = capsys.readouterr().out

    assert mode == "calc_only"
    assert "[Pre-Router] Phát hiện 17/17" in output
    assert "Câu 1:" in output
    assert "Câu 15:" in output
    assert "Câu 16:" not in output
    assert "... và 2 câu khác" in output
    assert "[1] Chỉ câu tính toán" in output
    assert "[2] Toàn bộ câu hỏi" in output
    assert "[3] Chỉ câu lý thuyết" in output
    assert "(Enter=1)" in output


def test_gemini_web_engine_runs_inside_asyncio_run(monkeypatch):
    fake_module = types.ModuleType("gemini_webapi")

    class FakeResponse:
        text = "```\n{\"\u0110\u00e1p\": \"ok\"}\n```"

    class FakeGeminiClient:
        def __init__(self, *args, **kwargs):
            pass

        async def init(self, **kwargs):
            return None

        async def generate_content(self, prompt, **kwargs):
            return FakeResponse()

        async def close(self):
            return None

    fake_module.GeminiClient = FakeGeminiClient
    monkeypatch.setitem(sys.modules, "gemini_webapi", fake_module)

    from src.core.llm_router import GeminiWebEngine

    async def call_from_running_loop():
        engine = GeminiWebEngine(delay=(0, 0))
        try:
            return engine.generate("Hệ thống", "Nội dung")
        finally:
            engine.close()

    result = asyncio.run(call_from_running_loop())
    assert "ok" in result


def test_auto_save_resume_counts_and_missing_batches(tmp_path):
    from src.llm.exam_solver import (
        _atomic_json_write,
        _gemini_notebook_confirmation,
        _json_hash,
        _load_json,
    )

    rag_path = tmp_path / "notebook_rag.json"
    rag = {f"Q{i}": f"fact-{i}" for i in range(1, 31)}
    _atomic_json_write(rag_path, {"rag_by_id": rag})
    loaded = _load_json(rag_path)["rag_by_id"]

    prompt = _gemini_notebook_confirmation(
        done=len(loaded),
        theory_count=60,
        image_count=12,
    )
    assert "Đã trích xuất dữ liệu từ Gemini Notebook cho 30/60" in prompt
    assert "tiếp tục trích xuất 30 câu còn lại" in prompt
    assert "còn lại 12 câu hình ảnh" in prompt
    assert len(loaded) == 30

    subbatches = [{"questions": [{"id": f"Q{i}"}], "require_formula_work": False} for i in range(1, 7)]
    batch_results = {
        _json_hash(subbatches[0]): {"results": []},
        _json_hash(subbatches[1]): {"results": []},
    }
    batch_path = tmp_path / "llm_batches.json"
    _atomic_json_write(batch_path, {"batches": batch_results})
    loaded_batches = _load_json(batch_path)["batches"]
    missing = [
        batch for batch in subbatches
        if _json_hash(batch) not in loaded_batches
    ]
    assert len(loaded_batches) == 2
    assert len(missing) == 4


def test_llm_router_uses_deepseek_before_gemini(monkeypatch):
    from src.core.llm_router import LLMRouter

    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    router = LLMRouter()

    monkeypatch.setattr(
        router,
        "_call_deepseek_json",
        lambda system, user: {"answer": "deepseek"},
    )
    monkeypatch.setattr(
        router,
        "_call_gemini_api_json",
        lambda *args, **kwargs: {"answer": "gemini"},
    )
    result = router.generate_json("system", "user")
    assert result["answer"] == "deepseek"


def test_llm_router_vision_skips_deepseek(monkeypatch):
    from src.core.llm_router import LLMRouter

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    router = LLMRouter()
    called = {"gemini": 0, "web": 0}

    monkeypatch.setattr(
        router,
        "_call_gemini_api_json",
        lambda *args, **kwargs: called.update(gemini=1) or {"answer": "ok"},
    )
    monkeypatch.setattr(
        router,
        "_get_web",
        lambda: types.SimpleNamespace(
            generate=lambda *args, **kwargs: called.update(web=1) or '{"answer":"web"}'
        ),
    )
    result = router.generate_json("system", "user", image_path="/tmp/test.jpg")
    assert result["answer"] == "ok"
    assert called == {"gemini": 1, "web": 0}
