import pytest

from src.core.quality_check import slugify_vi
from src.llm.cau_hoi_llm import _ask_settings


LEGACY_SLUG_OPTIONS = {
    "fallback": "bai",
    "max_length": None,
    "normalization": "NFKD",
    "remove_combining_marks": True,
}


@pytest.mark.parametrize(
    ("raw_subject", "expected_slug", "expected_label"),
    [
        ("Nội Tiết", "noi-tiet", "Nội Tiết"),
        ("Đái tháo đường", "dai-thao-duong", "Đái tháo đường"),
        ("Tim mạch", "tim-mach", "Tim mạch"),
        ("noi-tiet", "noi-tiet", "Noi Tiet"),
    ],
)
def test_ask_settings_preserves_unicode_subject_name(
    monkeypatch, raw_subject, expected_slug, expected_label
):
    answers = iter([raw_subject, "", "", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    settings = _ask_settings()

    assert settings["subject"] == expected_slug
    assert settings["subject_label"] == expected_label


@pytest.mark.parametrize(
    ("text", "expected_slug"),
    [
        ("", "bai"),
        ("½a", "1-2a"),
        ("éa", "ea"),
        ("x" * 61, "x" * 61),
    ],
)
def test_shared_slugifier_preserves_question_flow_legacy_ids(text, expected_slug):
    assert slugify_vi(text, **LEGACY_SLUG_OPTIONS) == expected_slug
