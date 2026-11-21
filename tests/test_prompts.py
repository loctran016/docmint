from src.core.prompts import render_prompt


def test_render_prompt_replaces_named_placeholder_and_keeps_json_braces():
    prompt = render_prompt(
        "exam_solver_pass1",
        formula_schema="null",
    )

    assert '"formula_work":null' in prompt
    assert '"results"' in prompt
    assert "Bạn là bác sĩ y khoa Việt Nam chuyên giải đề thi chuẩn hóa" in prompt
    assert '"formula_work":"formula_work"' not in prompt


def test_render_prompt_formula_schema_for_formula_questions():
    prompt = render_prompt(
        "exam_solver_pass1",
        formula_schema='"str"',
    )

    assert '"formula_work":"str"' in prompt
    assert '"formula_work":"formula_work"' not in prompt


def test_render_prompt_reports_missing_placeholder():
    try:
        render_prompt("exam_solver_pass1")
    except ValueError as exc:
        assert "formula_schema" in str(exc)
    else:
        raise AssertionError("Missing placeholder did not raise ValueError")
