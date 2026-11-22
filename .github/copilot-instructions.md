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
|   |-- prompts/
|   |   |-- bien_tap_core_rules.md
|   |   |-- exam_solver_step2_classify.md
|   |   `-- exam_solver_step3_rag.md
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
|   |   |-- llm_router.py
|   |   |-- prompts.py
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
|   |   |-- bien_tap.py
|   |   |-- exam_preprocessor.py
|   |   `-- exam_solver.py
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

## Quy tắc bắt buộc cho lần sửa sau

- **Xử lý PDF:** Mọi tính năng đọc, trích xuất hoặc upload PDF mới/refactor phải import và sử dụng bộ hàm chung trong `src/core/pdf_utils.py` (hoặc `common.py`); cấm tự viết lại logic mở/đọc PDF riêng lẻ bằng `fitz.open`, `PdfReader`, hoặc API tương đương.
- **Luồng CLI tương tác:** Mọi mục menu CLI sau khi chạy xong, dù thành công hay lỗi, đều phải gọi `wait_for_menu()` để trả luồng về vòng lặp menu chính và không tự thoát terminal. Ngoại lệ bắt buộc: `src/ingest/process_book.py`.
- **Script CI/GitHub Actions:** Các script tự động như `process_book.py` phải hoàn toàn non-interactive, không chứa `input()` và phải giữ exit code phục vụ GitHub Actions.
- **Dữ liệu workspace:** Được sử dụng thoải mái để kiểm tra, nhưng không được thay đổi, biến đổi hoặc xóa các file trong `workspace/` khi người dùng không yêu cầu.

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

## Prompt Architecture

- Prompt source of truth: `config/prompts/*.md`.
- Loader: `src/core/prompts.py`; call prompts with `render_prompt(name, **kwargs)`.
- Do not add hardcoded system prompts, user prompt templates, formatting instructions, or multi-line LLM instructions in Python.
- Dynamic values use `$variable_name` or `${variable_name}`; never use Python `.format()` for prompts containing raw JSON `{}`.
- `render_prompt()` caches loaded Markdown, validates placeholders, raises `FileNotFoundError` for missing files, and raises `ValueError` for missing variables.
- Keep JSON schemas and medical instructions in the Markdown file intact unless the task explicitly requires changing them.
- Preserve provider routing and control flow. Use DeepSeek for text, Gemini Web for exam images, NotebookLM for Step 2/3 RAG, and Groq only in existing fallback paths.
- Preserve `_step2_grouped.json`, `_step3_rag.json`, batch sizes, retries, and `verified/conflict/ai_only` auditing.
- After changing a prompt, run `uv run python -m compileall -q src`, prompt smoke imports, and relevant tests.
- Read [the prompt guide](../docs/HUONG_DAN_PROMPT.md) before adding or renaming prompts.

## Exam Solver Providers and 5-Step Pipeline

- For exam text solving, use `DEEPSEEK_API_KEY` through `src/core/llm_router.py`; do not silently fall back to Gemini for text.
- Use the existing `notebooklm-py` `NotebookLMClient.from_storage()` session and `config/notebook_id.txt` loader for both Step 2 grouping and Step 3 RAG. Reuse `src.core.common.notebooklm_client()`/`read_notebook_id()` rather than creating another auth flow.
- For image questions, use `GeminiWebEngine` through `gemini-webapi` and attached `image_path`. Do not use `google-genai` for the exam solver or image/web editing provider.
- Step 1 parses with PyMuPDF and routes to three streams: Image (`8`), Long/Clinical (`7`, stem >=30 words or clinical case), and Short (`hint_group` 1..6).
- Step 2 sends only Short questions to NotebookLM in batches of 15–20 and writes `.cache/exam_solver/<exam_id>_step2_grouped.json`.
- Between Steps 2 and 3, print distribution for groups 1–8 and confirm `Tiếp tục truy xuất dữ liệu từ NotebookLM? [Y/n]: `, or skip with `--yes`.
- Step 3 is separate RAG extraction: Short 5–8 items per confirmed group, Long 2–3 items, no text RAG for Image. Write `_step3_rag.json`.
- Step 4 solves Short/Long with DeepSeek in batches of 12–15/2–3 and images with Gemini Web in batches of 1–2.
- Step 5 performs Python-only `answer` vs `raw_key` audit (`verified`/`conflict`/`ai_only`) and writes Isolde JSON under `workspace/ket_qua/giai_de/<subject>/` plus `bank.json` and `assets/`.
- Resolve subject before Step 1 with `--subject`, the parent `workspace/de_thi/<subject>/` folder, or page-1 title slug prompting. CLI input defaults to `workspace/de_thi/`.
- Do not re-run migration or validation scripts against existing JSON in `workspace/ket_qua/giai_de/`.

## Data Safety

- Never read, grep, or index `workspace/` (including `workspace/output_md/.pages/`), `.cache/`, or legacy data folders (`output_md/`, `input_pdfs/`, `output_ocr/`, `ket_qua/`, `transcripts/`, `slides_out/`, `giang_out/`).
