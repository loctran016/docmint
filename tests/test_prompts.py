from src.core.prompts import render_prompt


def test_render_prompt_replaces_named_placeholder_and_keeps_json_braces():
    prompt = render_prompt(
        "exam_solver_pass1",
        formula_schema='"formula_work":null',
    )

    assert '"formula_work":null' in prompt
    assert '"results"' in prompt
    assert "Bạn là bác sĩ giải đề y khoa Việt Nam" in prompt


def test_render_prompt_reports_missing_placeholder():
    try:
        render_prompt("exam_solver_pass1")
    except ValueError as exc:
        assert "formula_schema" in str(exc)
    else:
        raise AssertionError("Missing placeholder did not raise ValueError")
