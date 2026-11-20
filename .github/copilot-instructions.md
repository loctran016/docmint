# Docmint - Copilot Agent Instructions

## Project Identity

- `docmint` (formerly `notebooklm-toolkit`) is a Python 3.11+ CLI and GitHub Actions toolkit for medical-study workflows.
- Run Python through `uv` from the repository root: `uv run <script>`.
- Use `pathlib.Path` and keep behavior compatible with WSL/Linux and Windows.
- The menu remains a 22-item layout in four sections and must stay intact.

## Refactored Structure

```text
/
|-- menu.py
|-- menu.sh
|-- menu.cmd
|-- README.md
|-- requirements_nguon_gv.txt
|-- pyproject.toml (if present)
|-- .env
|-- .env.example
|-- .env.nguon_gv.example
|-- .gitignore
|-- config/
|   |-- notebook_id.txt
|   |-- giao_trinh.txt
|   |-- giang_bai.txt
|   |-- cau_hoi.txt
|   |-- mindmaps.txt
|   |-- infographics.txt
|   |-- videos.txt
|   |-- bien_tap_style.md
|   `-- medical_terms.txt
|-- src/
|   |-- core/
|   |   |-- common.py
|   |   |-- groq_client.py
|   |   `-- quality_check.py
|   |-- menus/
|   |   |-- menu_nguon_gv.py
|   |   `-- menu_bien_tap.py
|   |-- ingest/
|   |   |-- setup_notebooklm.py
|   |   |-- setup_ocr.py
|   |   |-- ocr_pdfs.py
|   |   |-- check_pdf.py
|   |   |-- process_book.py
|   |   |-- slides_to_md.py
|   |   |-- upload_sources.py
|   |   `-- transcripts/
|   |-- notebook/
|   |   |-- muc_luc.py
|   |   |-- giang_bai.py
|   |   |-- tao_cau_hoi.py
|   |   |-- tao_media.py
|   |   |-- ask_notebook.py
|   |   |-- giang_hang_loat.py
|   |   |-- generate_artifacts.py
|   |   `-- prompts.py
|   |-- llm/
|   |   `-- bien_tap.py
|   `-- sync/
|       `-- cap_nhat_obsidian.py
|-- docs/
|   `-- HUONG_DAN_NGUON_GV.md
|-- workspace/
|   |-- input_pdfs/
|   |-- output_ocr/
|   |-- output_md/
|   |-- ket_qua/
|   |-- transcripts/
|   |-- slides_out/
|   `-- giang_out/
`-- .github/workflows/
```

## Mandatory Path Rules

- `src/core/common.py` defines `ROOT_DIR`, `CONFIG_DIR`, and `WORKSPACE_DIR`.
- `ROOT_DIR = Path(__file__).resolve().parents[2]`.
- Config files must resolve from `config/`, with the repository root as a compatibility fallback.
- Default data paths must resolve inside `workspace/`.
- Every script under `src/` must run from the repository root by both:
  - `uv run src/<area>/<script>.py`
  - `uv run -m src.<area>.<module>`
- Package directories under `src/` contain `__init__.py`.
- Use package imports such as `from src.core import common` and `from src.core import groq_client`.
- Scripts launched directly must insert the repository root into `sys.path` safely.

## Menu and Subprocesses

- Preserve all menu handlers and the 22-item layout.
- Menu subprocess calls use paths under `src/`.
- The main menu launches `src/menus/menu_nguon_gv.py` and `src/menus/menu_bien_tap.py`.
- Editing config files uses `config/...`.
- Notebook and output defaults use `config/...` and `workspace/...`.

## Data Safety

- Never read or edit contents in `output_md/`, `input_pdfs/`, `output_ocr/`, `ket_qua/`, `transcripts/`, `slides_out/`, `giang_out/`, or `.cache/`.
- Move such directories as data only, or treat them as absent.
- `.gitignore` must include `workspace/`, `.cache/`, `.env`, `.menu_settings.json`, and `tessdata/`.

## GitHub Actions

- Update workflow script calls to `src/notebook/...`, `src/ingest/...`, and `src/llm/...`.
- Lesson-list files use `config/giang_bai.txt` or the appropriate `config/*.txt`.
- Generated output and checkpoints use `workspace/...`.
- `.github/scripts/nlm_report.py` must read and write workspace output paths.

## Domain Notes

- PDF-to-Markdown uses incremental pages and resumable state under `workspace/output_md/.pages/`.
- Editorial output stays under `workspace/ket_qua/{giang_bai,raw,polished}/`.
- Source prefixes remain `[SGK]`, `[GV]`, and `[SLIDE]`.
- Obsidian YAML and citation behavior must remain unchanged.

## Data Safety

- Never read, grep, or index `workspace/` (including `workspace/output_md/.pages/`), `.cache/`, or legacy data folders (`output_md/`, `input_pdfs/`, `output_ocr/`, `ket_qua/`, `transcripts/`, `slides_out/`, `giang_out/`).
