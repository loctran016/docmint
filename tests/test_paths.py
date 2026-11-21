import ast
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
FORBIDDEN_CONFIG_NAMES = {
    "giao_trinh.txt",
    "notebook_id.txt",
    "bien_tap_style.md",
}


def test_static_guard_no_hardcoded_critical_paths():
    files = [ROOT / "menu.py"]
    files.extend((ROOT / "src").rglob("*.py"))

    violations = []
    for path in files:
        if path == ROOT / "src" / "core" / "common.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for arg in ast.walk(node):
                if not isinstance(arg, ast.Constant):
                    continue
                value = arg.value
                if not isinstance(value, str):
                    continue
                if value in FORBIDDEN_CONFIG_NAMES or "ket_qua/" in value:
                    violations.append(f"{path.relative_to(ROOT)}: {value}")

    assert not violations, "Hardcoded critical paths found:\n" + "\n".join(violations)


def test_muc_luc_apply_writes_to_monkeypatched_config(monkeypatch, tmp_path):
    from src.core import common
    import src.notebook.muc_luc as muc_luc

    config_dir = tmp_path / "config"
    workspace_dir = tmp_path / "workspace"
    config_dir.mkdir()
    workspace_dir.mkdir()
    monkeypatch.setattr(common, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(common, "WORKSPACE_DIR", workspace_dir)
    monkeypatch.setattr(common, "GIAO_TRINH_FILE", config_dir / "giao_trinh.txt")

    target = muc_luc.apply_toc("## Chương 1\nBài kiểm thử\n")

    assert target == tmp_path / "config" / "giao_trinh.txt"
    assert target.read_text(encoding="utf-8") == "## Chương 1\nBài kiểm thử\n"
    assert not (ROOT / "giao_trinh.txt").exists()


def test_config_resolution_uses_monkeypatched_config(monkeypatch, tmp_path):
    from src.core import common

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setattr(common, "CONFIG_DIR", config_dir)

    giang = config_dir / common.GIANG_BAI_FILE.name
    giao = config_dir / common.GIAO_TRINH_FILE.name
    giang.write_text("# Không có bài\n", encoding="utf-8")
    giao.write_text("## Chương 1\nBài từ mục lục\n", encoding="utf-8")
    notebook_id = config_dir / common.NOTEBOOK_ID_FILE.name
    notebook_id.write_text("notebook-test-id\n", encoding="utf-8")

    path, items = common.resolve_list(["giang_bai.txt"])
    assert path == giao
    assert items and items[0]["title"] == "Bài từ mục lục"
    assert common.read_notebook_id() == "notebook-test-id"


def test_load_project_env_prefers_repo_over_config(monkeypatch, tmp_path):
    from src.core import common

    repo_root = tmp_path / "repo"
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    repo_env = repo_root / ".env"
    config_env = config_dir / ".env"
    repo_env.write_text("DOCMINT_TEST_VALUE=repo\r\nGEMINI_API_KEY=repo-key\r\n", encoding="utf-8")
    config_env.write_text("DOCMINT_TEST_VALUE=config\r\nGEMINI_API_KEY=config-key\r\n", encoding="utf-8")

    monkeypatch.setattr(common, "REPO_ROOT", repo_root)
    monkeypatch.setattr(common, "CONFIG_DIR", config_dir)
    monkeypatch.setenv("DOCMINT_TEST_VALUE", "")
    monkeypatch.setenv("GEMINI_API_KEY", "shell-key")

    common.load_project_env()

    assert os.environ["DOCMINT_TEST_VALUE"] == "config"
    assert os.environ["GEMINI_API_KEY"] == "config-key"
