# Docmint - Hướng dẫn dành cho Copilot Agent

## Nhận diện dự án

- `docmint` (tên cũ: `notebooklm-toolkit`) là bộ công cụ CLI bằng Python 3.11+ và GitHub Actions cho quy trình nghiên cứu y khoa.
- Chạy Python bằng `uv` từ thư mục gốc của repository: `uv run <lệnh>`.
- Dùng `pathlib.Path` và giữ tương thích với WSL/Linux và Windows.
- Menu phải giữ nguyên bố cục 22 mục trong 4 nhóm.

## Cấu trúc đã refactor

```text
/
|-- menu.py
|-- menu.sh
|-- menu.cmd
|-- README.md
|-- requirements_nguon_gv.txt
|-- pyproject.toml (nếu có)
|-- .env
|-- .env.example
|-- .env.nguon_gv.example
|-- .gitignore
|-- config/
|   |-- notebook_id.txt
|   |-- prompts/
|   |   |-- artifact_extra.md
|   |   |-- artifact_instructions.md
|   |   |-- bien_tap_core_rules.md
|   |   |-- bien_tap_fallback_system.md
|   |   |-- bien_tap_retry_note.md
|   |   |-- bien_tap_summary.md
|   |   |-- bien_tap_user.md
|   |   |-- exam_solver_pass1.md
|   |   |-- exam_solver_step2_classify.md
|   |   |-- exam_solver_step3_rag.md
|   |   |-- giang_bai.md
|   |   |-- llm_router_json_suffix.md
|   |   |-- media_infographic.md
|   |   |-- media_mindmap.md
|   |   |-- media_video.md
|   |   |-- muc_luc.md
|   |   |-- notebook_ca_hai.md
|   |   |-- notebook_common.md
|   |   |-- notebook_format_md.md
|   |   |-- notebook_giaovien.md
|   |   |-- notebook_note_check.md
|   |   |-- notebook_sach.md
|   |   |-- process_book_batch.md
|   |   |-- process_book_inject.md
|   |   |-- process_book_ocr.md
|   |   |-- process_topic.md
|   |   |-- quiz_instruction.md
|   |   |-- slides_to_markdown.md
|   |   |-- tao_cau_hoi.md
|   |   |-- transcript_clean.md
|   |   |-- whisper_context_en.md
|   |   |-- whisper_context_vi.md
|   |   |-- whisper_initial_en.md
|   |   `-- whisper_initial_vi.md
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
|   |   |-- ai_client.py
|   |   |-- common.py
|   |   |-- groq_client.py
|   |   |-- llm_router.py
|   |   |-- pdf_utils.py
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
|   |-- HUONG_DAN_NGUON_GV.md
|   `-- HUONG_DAN_PROMPT.md
|-- workspace/
|   |-- input_pdfs/
|   |-- output_ocr/
|   |-- output_md/
|   |-- ket_qua/
|   |-- transcripts/
|   |-- slides_out/
|   `-- giang_out/
|-- .github/
|   |-- copilot-instructions.md
|   |-- prompts/
|   |   `-- audit-prompt.prompt.md
|   |-- scripts/
|   |   `-- nlm_report.py
|   `-- workflows/
|       |-- giang_bai.yml
|       |-- notebooklm_batch.yml
|       |-- ocr_books.yml
|       |-- transcribe.yml
|       `-- transcribe_faster_whisper.yml
`-- tests/
```

## Quy tắc đường dẫn bắt buộc

- `src/core/common.py` định nghĩa `ROOT_DIR`, `CONFIG_DIR` và `WORKSPACE_DIR`.
- `ROOT_DIR = Path(__file__).resolve().parents[2]`.
- Các file cấu hình phải được resolve trong `config/`, đồng thời giữ thư mục gốc repository làm đường dẫn tương thích dự phòng.
- Đường dẫn dữ liệu mặc định phải nằm trong `workspace/`.
- Mọi script dưới `src/` phải chạy được từ thư mục gốc repository bằng cả hai lệnh:
  - `uv run src/<area>/<script>.py`
  - `uv run -m src.<area>.<module>`
- Mỗi thư mục package dưới `src/` phải có `__init__.py`.
- Dùng import package như `from src.core import common`, `from src.core import groq_client` và `from src.core.ai_client import GeminiExecutor`.
- Script chạy trực tiếp phải chèn thư mục gốc repository vào `sys.path` an toàn.

## Menu và subprocess

- Giữ nguyên mọi menu handler và bố cục 22 mục trong 4 nhóm.
- Lời gọi subprocess của menu phải dùng đường dẫn dưới `src/`.
- Menu chính chạy `src/menus/menu_nguon_gv.py` và `src/menus/menu_bien_tap.py`.
- Chỉnh file cấu hình bằng `config/...`.
- Mặc định Notebook và output dùng `config/...` và `workspace/...`.

## Quy tắc bắt buộc

- **Xử lý PDF:** Mọi tính năng đọc, trích xuất hoặc upload PDF mới hoặc refactor phải import và dùng bộ hàm chung trong `src/core/pdf_utils.py` (hoặc `common.py`). Cấm viết lại logic mở/đọc PDF riêng bằng `fitz.open`, `PdfReader` hoặc API tương đương.
- **Luồng CLI tương tác:** Mọi mục menu CLI sau khi chạy xong, dù thành công hay lỗi, đều phải gọi `wait_for_menu()` để trả luồng về vòng lặp menu chính và không tự thoát terminal. Ngoại lệ bắt buộc: `src/ingest/process_book.py`.
- **Script CI/GitHub Actions:** Script tự động như `process_book.py` phải hoàn toàn non-interactive, không chứa `input()` và phải giữ exit code phù hợp với GitHub Actions.

## An toàn dữ liệu

- ĐƯỢC ĐỌC nội dung `workspace/`, `.cache/` và các thư mục dữ liệu cũ (`output_md/`, `input_pdfs/`, `output_ocr/`, `ket_qua/`, `transcripts/`, `slides_out/`, `giang_out/`) để kiểm tra.
- Khi đọc dữ liệu, chỉ đọc phần cần thiết và tránh grep hoặc lập chỉ mục hàng loạt các file lớn.
- KHÔNG ĐƯỢC sửa, biến đổi, di chuyển hoặc xoá file trong các thư mục trên khi người dùng chưa yêu cầu.
- Nếu thật sự cần thay đổi file trong các thư mục này:
  1. Dừng lại và báo người dùng nêu rõ file nào, thay đổi gì và vì sao.
  2. Chờ người dùng đồng ý.
  3. Sao lưu bản gốc trước khi sửa.
  4. Ghi một dòng vào `docs/DATA_CHANGES.md` gồm ngày giờ, đường dẫn, hành động, lý do và vị trí bản sao lưu; file log nằm NGOÀI `workspace/`.
  5. Nhắc lại trong phần tóm tắt cuối câu trả lời để người dùng xem xét.
- `.gitignore` phải gồm `workspace/`, `.cache/`, `.env`, `.menu_settings.json` và `tessdata/`.
- Các thư mục `workspace/`, `.cache/` và thư mục dữ liệu legacy nằm trong `.gitignore`, nên git không theo dõi hoặc cung cấp bản hoàn tác cho chúng. Vì vậy, không được giả định có thể khôi phục bằng `git restore` hoặc `git checkout`.

## Quy ước code

- Hàm nội bộ dùng tiền tố `_`.
- Code mới hoặc refactor ghi JSON bằng cơ chế ghi nguyên tử: ghi trước vào file `.tmp`, sau đó dùng `os.replace()` để thay file đích. Hiện `_atomic_json_write` nằm trong `src/llm/exam_solver.py`; khi refactor, chuyển hàm này vào `src/core/common.py` để dùng chung.
- Chuỗi hiển thị cho người dùng phải dùng tiếng Việt.
- Không dùng `except BaseException` trong code mới hoặc refactor; chỉ bắt ngoại lệ cụ thể hoặc ít nhất `Exception` với lý do xử lý rõ ràng.
- Code cũ hiện còn vi phạm quy tắc này sẽ được sửa dần trong công việc liên quan. Không tự sửa rộng ra ngoài phạm vi nhiệm vụ.

## GitHub Actions

- Cập nhật lời gọi script workflow tới `src/notebook/...`, `src/ingest/...` và `src/llm/...`.
- File danh sách bài học dùng `config/giang_bai.txt` hoặc file `config/*.txt` phù hợp.
- Output được sinh ra và checkpoint dùng `workspace/...`.
- `.github/scripts/nlm_report.py` phải đọc và ghi các đường dẫn output trong workspace.

## Quy tắc miền nghiệp vụ

- PDF-to-Markdown dùng trang tăng dần và trạng thái resumable dưới `workspace/output_md/.pages/`.
- Output biên tập nằm trong `workspace/ket_qua/{giang_bai,raw,polished}/`.
- Tiền tố nguồn giữ nguyên `[SGK]`, `[GV]` và `[SLIDE]`.
- Hành vi YAML và citation của Obsidian phải giữ nguyên.

## Kiến trúc prompt

- Nguồn chuẩn của prompt là `config/prompts/*.md`.
- Loader là `src/core/prompts.py`; gọi prompt bằng `render_prompt(name, **kwargs)`.
- Không thêm system prompt, user prompt template, instruction định dạng hoặc multi-line LLM instruction cố định trong Python.
- Giá trị động dùng `$variable_name` hoặc `${variable_name}`; không dùng Python `.format()` cho prompt chứa JSON `{}` thô.
- `render_prompt()` cache Markdown đã nạp, kiểm tra placeholder, ném `FileNotFoundError` khi thiếu file và ném `ValueError` khi thiếu biến.
- Giữ nguyên JSON schema và instruction y khoa trong file Markdown trừ khi nhiệm vụ yêu cầu thay đổi trực tiếp.
- Giữ provider routing và control flow. `GeminiExecutor` trong `src/core/ai_client.py` là executor cho Gemini API. Groq chỉ dùng trong các fallback hoặc luồng hiện có.
- Giữ `_step2_grouped.json`, `_step3_rag.json`, `_step4_batches.json`, batch size, retry và audit `verified/conflict/ai_only`.
- Sau khi thay đổi prompt, chạy `uv run python -m compileall -q src`, smoke import prompt và test liên quan.
- Đọc [hướng dẫn prompt](../docs/HUONG_DAN_PROMPT.md) trước khi thêm hoặc đổi tên prompt.

## Provider Exam Solver và pipeline 5 bước

- Provider cho text: DeepSeek → Gemini API → Gemini Web.
- Provider cho ảnh: Gemini API → Gemini Web.
- `--backend web` ép Gemini Web cho cả text lẫn ảnh.
- `GeminiExecutor` trong `src/core/ai_client.py` thực thi Gemini API cho text, JSON và vision.
- Gemini Web dùng `GeminiWebEngine` trong `src/core/llm_router.py` qua `gemini-webapi`.
- Các tham số CLI hiện có:
  - `--in`: đường dẫn PDF/file hoặc thư mục đầu vào.
  - `--out`: thư mục xuất kết quả.
  - `--subject`: subject slug hoặc tên môn.
  - `--formula-mode`: `calc_only`, `all` hoặc `off`.
  - `--yes`: bỏ gate xác nhận và prompt subject.
  - `--web-model`: model Gemini Web.
  - `--web-gem`: Gem Gemini Web.
  - `--force`: bỏ qua cache Step 2, 3 và 4.
  - `--backend`: `auto` hoặc `web`; `web` ép Gemini Web cho cả text và ảnh.
  - `--verbose`: hiển thị chi tiết log nội bộ.
- Resolve subject trước Step 1 bằng `--subject`, thư mục cha `workspace/de_thi/<subject>/` hoặc prompt lấy subject slug từ title trang đầu.
- CLI input mặc định là `workspace/de_thi/`.
- Step 1: Parse PDF bằng PyMuPDF qua bộ preprocess/routing hiện có, rồi chia luồng Image (nhóm 8), Long/Clinical (nhóm 7 hoặc stem >=30 từ/case lâm sàng) và Short (hint_group 1..6).
- Step 2: Chỉ phân loại môn cho câu Short theo nhóm 1–6; không giải đáp án. Gom tối đa 18 câu Short vào một tin nhắn NotebookLM, mỗi câu gồm `id`, `stem` và `options`. Kết quả ghi cache `_step2_grouped.json`; câu không được NotebookLM phân loại sẽ dùng dự phòng `hint_group`, hoặc nhóm 4 nếu không có hint hợp lệ.
- Giữa Step 2 và Step 3: in phân bố nhóm 1–8 bằng `_print_distribution()`. Khi chưa đủ cache cho Step 3, code hỏi xác nhận bằng chuỗi:
  - khi chưa trích xuất câu nào: `"Tiếp tục truy xuất dữ liệu từ Gemini Notebook? (chỉ truy xuất {theory_count} câu lý thuyết, còn lại {image_count} câu hình ảnh) [Y/n]: "`;
  - code khởi đầu chuỗi bằng `"Tiếp tục truy xuất dữ liệu từ Gemini Notebook? [Y/n]"` ở logic xác nhận nhưng cũng có thể thêm số liệu tiến độ hoặc số câu còn lại.
  - `--yes` bỏ qua gate xác nhận này.
- NotebookLM: dùng `NotebookLMClient.from_storage()` thông qua `common.notebooklm_client()` và `common.read_notebook_id()`; không tạo luồng auth NotebookLM khác.
- Step 3: Hỏi NotebookLM từng câu lý thuyết thuộc Short + Long/Clinical để lấy kiến thức từ giáo trình, dùng `rag_by_id` trong cache `_step3_rag.json`. Không RAG cho câu ảnh.
- Khi chạm quota/rate limit ở Step 3, code in trạng thái đã lưu tiến độ rồi hỏi input:
  - `[1] Chờ 60s rồi thử tiếp`;
  - `[2] Dừng tại đây`.
- Khi chạy với `--yes`, Step 3 vẫn chưa bỏ qua prompt quota này: code vẫn gọi `prompt_input()` để hỏi lựa chọn chờ hoặc dừng. Nếu không có dữ liệu tương tác/EOF, code chọn dừng.
- Step 4: Giải theo batch Short 8 câu, Long 4 câu và câu ảnh tối đa 2 câu cùng một ảnh. Cache theo hash batch trong `_step4_batches.json`, `_json_hash(batch)` và `_valid_batch_cache`.
- Step 5: Audit Python bằng cách so sánh `answer` với `raw_key` thành `verified`/`conflict`/`ai_only`; cổng `validate_exam_data` phải chạy trước khi xuất dữ liệu. Xuất `<exam_id>.json`, `bank.json` và `exams-manifest.json` dưới thư mục môn trong `workspace/ket_qua/giai_de/`, kèm assets câu ảnh.
- Cổng xuất đề và bank không ghi file khi validation thất bại.
- Không chạy lại script migration hoặc validation lên JSON hiện có trong `workspace/ket_qua/giai_de/`.
- “Batch 18” chỉ áp dụng cho Step 2 để gom tối đa 18 câu Short vào một tin nhắn NotebookLM; không phải batch giải đáp án ở Step 4.
