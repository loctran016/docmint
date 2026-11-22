import sys
import types

from src.core.ai_client import GeminiExecutor, parse_list, priority_exam_models, priority_process_models


def test_model_priority():
    process = priority_process_models([
        "gemini-3.8-flash",
        "gemini-3.6-flash-lite",
        "gemini-2.5-flash",
    ])
    assert process[0].endswith("flash-lite")

    exam = priority_exam_models(
        "gemini-3.6-flash-lite,gemini-3.8-flash,gemini-2.5-flash",
        allow_lite=True,
    )
    assert exam[0] == "gemini-3.8-flash"
    assert exam[1] == "gemini-3.6-flash"
    assert "gemini-2.5-flash" not in exam
    assert exam[-2:] == ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]


def test_parse_gemini_model_string():
    assert parse_list("gemini-3.6-flash,gemini-3.8-flash") == [
        "gemini-3.6-flash",
        "gemini-3.8-flash",
    ]


def test_gemini_executor_404_rotates_to_next_model(monkeypatch):
    fake_types = types.SimpleNamespace(
        Part=types.SimpleNamespace(
            from_text=lambda text: {"text": text},
            from_bytes=lambda data, mime_type: {"bytes": data, "mime_type": mime_type},
        ),
        SafetySetting=lambda **kwargs: kwargs,
        GenerateContentConfig=lambda **kwargs: kwargs,
        HARM_CATEGORY_HARASSMENT="harassment",
        HARM_CATEGORY_HATE_SPEECH="hate",
        HARM_CATEGORY_SEXUALLY_EXPLICIT="explicit",
        HARM_CATEGORY_DANGEROUS_CONTENT="dangerous",
    )
    fake_genai = types.ModuleType("google.genai")
    fake_genai.types = fake_types
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    class NotFoundError(Exception):
        code = 404

    response = types.SimpleNamespace(
        candidates=[
            types.SimpleNamespace(
                finish_reason="STOP",
                content=types.SimpleNamespace(
                    parts=[types.SimpleNamespace(text='{"answer":"ok"}', thought=False)]
                ),
            )
        ]
    )

    calls = []

    class FakeClient:
        def __init__(self, model):
            self.models = types.SimpleNamespace(generate_content=self.generate)
            self.model = model

        def generate(self, model, contents, config):
            calls.append(model)
            if model == "gemini-3.8-flash":
                raise NotFoundError("404 NOT_FOUND: model unavailable")
            return response

    executor = GeminiExecutor(["key"], ["gemini-3.8-flash", "gemini-3.6-flash"])
    monkeypatch.setattr(executor, "_client", lambda key, model: FakeClient(model))

    text, finish, model = executor.generate("system", "user", structured_json=True)

    assert text == '{"answer":"ok"}'
    assert finish == "STOP"
    assert model == "gemini-3.6-flash"
    assert calls == ["gemini-3.8-flash", "gemini-3.6-flash"]
