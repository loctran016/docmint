"""Centralized loading and rendering for Docmint prompt templates."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re


ROOT_DIR = Path(__file__).resolve().parents[2]
PROMPTS_DIR = ROOT_DIR / "config" / "prompts"


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    """Load one prompt Markdown file from config/prompts."""
    if not name or "/" in name or "\\" in name or Path(name).suffix not in {"", ".md"}:
        raise ValueError(f"Tên prompt không hợp lệ: {name!r}")
    filename = name if name.endswith(".md") else f"{name}.md"
    path = PROMPTS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy prompt: {path}")
    return path.read_text(encoding="utf-8").strip()


def render_prompt(name: str, **kwargs: object) -> str:
    """Render a cached prompt and validate every $placeholder."""
    template_text = load_prompt(name)
    placeholder_pattern = re.compile(r"\$(?:([A-Za-z_][A-Za-z0-9_]*)|\{([A-Za-z_][A-Za-z0-9_]*)\})")
    placeholders = {
        match.group(1) or match.group(2)
        for match in placeholder_pattern.finditer(template_text)
    }
    missing = sorted(placeholders - set(kwargs))
    if missing:
        raise ValueError(
            f"Thiếu biến khi render prompt {name!r}: {', '.join(missing)}"
        )
    def replace(match: re.Match[str]) -> str:
        key = match.group(1) or match.group(2)
        return str(kwargs[key])
    return placeholder_pattern.sub(replace, template_text)
