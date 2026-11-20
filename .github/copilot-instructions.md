# Docmint — Copilot Agent Instructions

## 1. Project Identity & Runtime

- **Purpose:** `docmint` (formerly `notebooklm-toolkit`) is a Python CLI and GitHub Actions automation toolkit for medical study workflows: scanning/OCRing textbooks, converting PDFs to Markdown via Gemini/Groq, ingesting teacher transcripts and slides into Gemini Notebook (`notebooklm-py`), generating lectures/quizzes/media/flashcards, rewriting prose into textbook style, and syncing to Obsidian[cite: 1].
- **Runtime:** Target **Python 3.11+** executed via **`uv`** (`uv run <script>.py`)[cite: 1]. Always run scripts from the repository root so imports of `common.py` and `groq_client.py` resolve properly[cite: 1].
- **Cross-Platform:** Must run identically on **WSL Ubuntu / Linux (including GitHub Actions)** and **Windows** (`menu.sh` / `menu.cmd` → `uv run menu.py`)[cite: 1]. Use `pathlib.Path` and path conversion helpers in `common.py` (preserving Windows `C:\...` vs WSL `/mnt/c/...`)[cite: 1].

## 2. Context & Token Hygiene (STRICT)

- **NEVER read, grep, or index `output_md/`** (including `output_md/.pages/` and `sources.json`), `input_pdfs/`, `output_ocr/`, `ket_qua/`, `transcripts/`, `slides_out/`, `giang_out/`, or `.cache/`[cite: 1].
- **Git Hygiene:** Keep `.env`, `.menu_settings.json`, and all data/output directories listed above inside `.gitignore` to protect API keys, cookies, and copyrighted medical textbooks[cite: 1].
- **Concise Output:** Return targeted code diffs or complete modified functions without conversational filler.

## 3. Menu Architecture (`menu.py`) vs. Legacy Docs

`menu.py` uses a refactored **22-item layout across 4 sections** (note that `README.md` still references legacy item numbers `[5]`–`[17]`; always follow `menu.py` when editing handlers)[cite: 1]:

- **CÀI ĐẶT & NHẬP LIỆU:**
  - `[1]` View `README.md`[cite: 1]
  - `[2]` `1_setup_notebooklm.py` — Install `notebooklm-py` + Playwright login[cite: 1]
  - `[3]` `2_setup_ocr.py` — Install OCRmyPDF, Tesseract (`vie`/`eng`), Ghostscript[cite: 1]
  - `[4]` `3_ocr_pdfs.py` — Batch OCR PDFs (`input_pdfs/` → `output_ocr/* - OCR.pdf`)[cite: 1]
  - `[5]` `process_book.py` & `8_kiem_tra_pdf.py` — PDF → Markdown via Gemini + PDF text-layer check _(legacy `[15]`)_[cite: 1]
  - `[6]` `menu_nguon_gv.py` — Submenu for teacher sources: transcripts, slides, source-filtered lectures _(legacy `[16]`)_[cite: 1]
- **Gemini Notebook:**
  - `[7]` `6_muc_luc.py` — Extract textbook TOC from NotebookLM into `giao_trinh.txt` _(legacy `[5]`)_[cite: 1]
  - `[8]` `4_giang_bai.py` — Batch generate lectures _(legacy `[6]`)_[cite: 1]
  - `[9]` `5_tao_cau_hoi.py` — Generate questions (`md` or NotebookLM `quiz`) _(legacy `[7]`)_[cite: 1]
  - `[10]`–`[12]` `7_tao_media.py` — Generate `mindmap`, `infographic`, `video` _(legacy `[8]`–`[10]`)_[cite: 1]
  - `[13]` `menu_bien_tap.py` & `bien_tap.py` — Editorial prose rewriter _(legacy `[17]`)_[cite: 1]
- **Gemini Notebook + LLM:**
  - `[14]` Topic-based question generation (planned/active module)
  - `[15]` Detailed exam question solver with explanations (planned/active module)
  - `[16]` Anki & visual flashcard generator (planned/active module)
  - `[17]`, `[18]` Reserved slots (`Đang chờ update`) — keep intact unless explicitly implementing them.
- **ĐỒNG BỘ & TIỆN ÍCH:**
  - `[19]` `9_cap_nhat_obsidian.py` — Update Obsidian hub index note _(legacy `[11]`)_[cite: 1]
  - `[20]` Set active notebook ID in `notebook_id.txt` _(legacy `[12]`)_[cite: 1]
  - `[21]` Check system/env status _(legacy `[13]`)_[cite: 1]
  - `[22]` Open output folder _(legacy `[14]`)_[cite: 1]

## 4. Core Subsystems & Domain Rules

### A. PDF → Markdown (`process_book.py`)

- **Incremental State:** Processes 1 page at a time into `output_md/.pages/<book>/p00001.md` + `sources.json` (tracks per-page model, `_warnings`, `_recitation_groq_fallback`), then merges into `output_md/<book>.md` (or per-`#` chapter files with `--split`)[cite: 1].
- **Brightness & Quota Routing:** Light pages use Flash-Lite (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, 1 page/req, 15 RPM); dark pages (`< --dark-threshold`, default `150`) prioritize `gemini-3.8-flash` / `gemini-3.6-flash` (5 RPM)[cite: 1]. Use API `v1` for stable models and `v1beta` for preview/`gemma-4-31b-it`/`gemini-3-flash`[cite: 1].
- **Paid Key Guard:** `GEMINI_PAID_API_KEY` is disabled by default; only trigger with `--allow-paid` after all free `(key, model)` pairs hit daily quota, capped by `--paid-max-pages` (default `300`)[cite: 1].
- **RECITATION Fallback Chain:** (1) Split multi-page batch to 1 page/req → (2) Single-pass Gemini retry with image perturbation (rotate `-0.4°`, crop `2px`, rotate `+0.8°`) + prompt injecting `[§]` every 4–5 words (strip `[§]` post-response) → (3) Groq Vision (`GROQ_API_KEYS`, default `qwen/qwen3.8-27b`) → (4) Leave uncompleted for next run[cite: 1].
- **Offline Quality Checks:** Flag short pages, 3+ consecutive repeated lines, `>=3` `[không rõ]` tags, Vietnamese syllable phonotactics, `pyspellchecker` typos, and respect `medical_terms.txt`[cite: 1].

### B. Teacher Sources (`input/` & `output/`, `README_nguon_gv.md`)

- **Mandatory Source Prefixes:** `[SGK]` (textbook `.md`), `[GV]` (lecture transcript `.md`), `[SLIDE]` (text-only `*.notebooklm.md`; keep image-embedded `*.md` for Obsidian only)[cite: 1].
- **Source-Level Filtering:** `output/ask_notebook.py` and `output/giang_hang_loat.py` restrict context via `source_ids` matching prefixes (`sach`, `giaovien`, `ca_hai`, `kiemtra_note`) and match `[GV]`/`[SLIDE]` to lesson names (accent-insensitive, stripping `Bài N.`, or explicit `match=...`)[cite: 1].
- **Transcript Pipeline (`input/transcripts/get_medical_transcript.py`):** `yt-dlp` audio → `ffmpeg` mono 16kHz 48kbps ~15-min chunks → Groq Whisper (`groq_stt.py`: `whisper-large-v3` → `whisper-large-v3-turbo` with key rotation) cached in `.cache/transcripts/raw/{video_id}.json` → Gemini medical term cleanup (`build_transcript.py`)[cite: 1].

### C. NotebookLM Batch Extraction & Obsidian (`4_giang_bai.py`–`9_cap_nhat_obsidian.py`)

- **Lesson List Resolution:** Check feature-specific file first (`giang_bai.txt`, `cau_hoi.txt`, `mindmaps.txt`, `infographics.txt`, `videos.txt`), falling back to `giao_trinh.txt` (`## Chương` headers; line syntax: `Tên bài | lưu ý riêng | key=value | cờ`)[cite: 1].
- **Resumability & Safety:** Track completed items via `.state.json` in output dir; stop media generation after 2 consecutive failures[cite: 1].
- **Obsidian Integration (`--obsidian`):** Write directly into vault, inject YAML frontmatter (`nguon`, `chuong`, `bai`, `loai`), rewrite `[1, 2]` citations to `([[Tên sách\|1, 2]])` (escaped pipe inside Markdown tables), and update hub note `<Tên sách>.md` only if it contains the auto-generated marker[cite: 1].

### D. Editorial Rewriter (`bien_tap.py` & `bien_tap_style.md`)

- **Non-Destructive Flow:** Read `ket_qua/giang_bai/*.md` without modifying originals; back up raw files to `ket_qua/raw/` and write outputs to `ket_qua/polished/` + `_bao_cao.md`[cite: 1].
- **Chunking & Numeric Integrity:** Split by `## ` headings and ~700-word chunks (`--max-words`), caching in `.cache/bien_tap/`[cite: 1]. Preserve tables, code blocks, `[[wikilinks]]`, and **every numeric value** from raw text (excluding bullet indices and `[1]` citations)[cite: 1]. If numbers drop, retry once with the missing list; if still missing, fall back to the raw chunk[cite: 1].
- **Provider Fallback:** Gemini (`gemini-3.8-flash`, `gemini-3.6-flash`, etc.) → Groq text (`GROQ_TEXT_MODELS`, default `openai/gpt-oss-120b`) → raw chunk[cite: 1]. Optional `--backend web` (`gemini-webapi` using `GEMINI_SECURE_1PSID` / `GEMINI_SECURE_1PSIDTS`) is for local use only (`temporary=True`, 15–25s delay)[cite: 1].

### E. GitHub Actions Workflows (`.github/workflows/`)

- `notebooklm_batch.yml`: Runs batch lecture/question/media jobs without committing to repo; outputs results to a new Release (`nlm_output.zip` + `run_log.txt`) and persists `.state.json` in rolling release `giang-progress`[cite: 1].
- `giang_bai.yml`: Single-lesson trigger (e.g., from mobile) using `NOTEBOOKLM_AUTH_JSON`[cite: 1].
- `transcribe.yml`: Runs Groq Whisper + Gemini cleanup on audio files attached to a GitHub Release[cite: 1].
