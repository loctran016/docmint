# Hướng dẫn quản lý Prompt trong Docmint

Tài liệu này dành cho người phát triển muốn đọc, thay đổi hoặc thêm prompt cho Gemini, Groq, DeepSeek và NotebookLM.

## 1. Nguyên tắc

- Prompt nằm trong `config/prompts/*.md`, không viết prompt dài hoặc instruction cố định trong Python.
- Python chỉ giữ logic, tên prompt, dữ liệu đầu vào và cách gọi provider.
- Chỉ sửa prompt khi mục đích là thay đổi hành vi của model.
- Không dùng `.format()` với prompt có JSON schema hoặc nhiều dấu `{}`.
- Dùng biến kiểu `$variable_name` hoặc `${variable_name}`.
- Giữ nguyên nghĩa y khoa, thuật ngữ, quy tắc và định dạng trong prompt.
- Chạy kiểm tra sau mỗi lần đổi prompt.

## 2. Cấu trúc

```text
config/
  prompts/
    bien_tap_core_rules.md
    bien_tap_summary.md
    exam_solver_step2_classify.md
    exam_solver_step3_rag.md
    exam_solver_pass1.md
    ...
src/
  core/
    prompts.py
```

`src/core/prompts.py` là lớp load chung:

```python
from src.core.prompts import render_prompt

text = render_prompt(
    "exam_solver_step2_classify",
    data=json.dumps(payload, ensure_ascii=False),
)
```

`render_prompt()` sẽ:

1. Tìm file trong `config/prompts/`.
2. Tự thêm phần `.md` nếu tên chưa có đuôi.
3. Nạp file một lần nhờ `lru_cache`.
4. Kiểm tra tất cả biến template.
5. Báo `ValueError` rõ ràng nếu thiếu biến.
6. Báo `FileNotFoundError` nếu prompt không tồn tại.

Đường dẫn được tính tương đối từ `src/core/prompts.py`, vì vậy hoạt động ở máy Linux/WSL/Windows và trong GitHub Actions.

## 3. Cách đặt tên prompt

Tên file nên mô tả vai trò, luồng và provider khi cần:

| Tên | Vai trò |
|---|---|
| `bien_tap_core_rules.md` | Quy tắc bắt buộc cho biên tập |
| `exam_solver_step2_classify.md` | NotebookLM phân loại câu ngắn |
| `exam_solver_step3_rag.md` | NotebookLM trích xuất RAG |
| `exam_solver_pass1.md` | DeepSeek/Gemini giải đề pass đầu |
| `process_book_ocr.md` | Gemini OCR trang sách |
| `slides_to_markdown.md` | Gemini chuyển slide sang Markdown |
| `notebook_common.md` | Quy tắc chung cho hỏi NotebookLM |

Ưu tiên tên dễ tìm qua Git, ví dụ `exam_solver_pass2_verify.md` thay vì `prompt2.md`.

## 4. Cách viết placeholder

Trong file Markdown:

```markdown
Bạn là bác sĩ y khoa.

Đề bài:
$question_text

Ngữ cảnh RAG:
$rag_context

Trả JSON:
{"answer":"A","explanation":"..."}
```

Trong Python:

```python
render_prompt(
    "exam_example",
    question_text=question,
    rag_context=rag,
)
```

Quy ước:

- Tên biến chỉ dùng chữ, số và dấu `_`, bắt đầu bằng chữ hoặc `_`.
- Dùng `$data` cho giá trị đơn giản.
- Dùng `${variable_name}` nếu biến đứng sát chữ hoặc ký hiệu.
- Dữ liệu động phải là tham số; không nối chuỗi prompt lớn bằng `.format()`.
- JSON schema có dấu `{}` được giữ nguyên trong Markdown.
- Không truyền secret hoặc dữ liệu cá nhân vào prompt.

Nếu gọi thiếu:

```python
render_prompt("exam_example", question_text="...")
```

sẽ nhận:

```text
ValueError: Thiếu biến khi render prompt 'exam_example': rag_context
```

## 5. Quy trình sửa một prompt

1. Tìm prompt cần đổi bằng `rg "exam_solver_step2"` trong `src/` hoặc tên vai trò trong `config/prompts/`.
2. Mở file `config/prompts/<role>.md`.
3. Sửa trực tiếp nội dung Markdown.
4. Không sửa tên biến nếu call site chưa được cập nhật.
5. Nếu thêm biến, thêm `variable=value` trong call site.
6. Chạy compile/import và test.
7. Chạy thử pipeline ở mức nhỏ; không xử lý workspace hoặc `.cache/` ngoài phạm vi task.

Ví dụ thêm ngữ cảnh vào prompt OCR:

```markdown
Chủ đề: $topic

Nội dung trang cần chép:
$page_text
```

```python
render_prompt(
    "process_book_custom",
    topic=topic,
    page_text=page_text,
)
```

## 6. Thêm prompt mới

1. Tạo `config/prompts/<vai_tro>.md`.
2. Viết placeholder `$variable_name`.
3. Import `render_prompt` tại module gọi LLM.
4. Thay chuỗi prompt hoặc constant trong Python bằng `render_prompt(...)`.
5. Truyền đủ biến.
6. Gắn prompt vào đúng provider và luồng hiện có.

Ví dụ module mới:

```python
from src.core.prompts import render_prompt

prompt = render_prompt(
    "pre_router_classify",
    question_text=question_text,
)
```

Không tạo prompt mới nếu prompt hiện có đã mô tả đúng vai trò. Ưu tiên dùng lại hoặc tách phần hệ thống/chuyên môn khỏi phần dữ liệu động.

## 7. Giữ control flow

Khi đổi prompt:

- Giữ nguyên batch size, retry, timeout và cache checkpoint.
- Giữ nguyên `_step2_grouped.json` và `_step3_rag.json`.
- Giữ nguyên luồng 2 pass audit `verified/conflict/ai_only`.
- Giữ nguyên provider: text dùng DeepSeek qua `LLMRouter`, ảnh dùng Gemini Web.
- Không thay đổi JSON output contract nếu model không yêu cầu thay đổi.

Nếu prompt yêu cầu JSON mới, cập nhật đồng thời:

- prompt Markdown;
- `_validate_results()` hoặc parser liên quan;
- test cho output hợp lệ và output sai;
- tài liệu mapping trong file này.

## 8. Mapping module → prompt

### Biên tập

- `src/llm/bien_tap.py`
  - `bien_tap_core_rules.md`
  - `bien_tap_summary.md`
  - `bien_tap_user.md`
  - `bien_tap_retry_note.md`
  - `bien_tap_fallback_system.md`

### Exam solver

- `src/llm/exam_solver.py`
  - `exam_solver_step2_classify.md`: `$data`
  - `exam_solver_step3_rag.md`: `$data`
  - `exam_solver_pass1.md`: `$formula_schema`

### LLM Router

- `src/core/llm_router.py`
  - `llm_router_json_suffix.md`

### NotebookLM

- `src/notebook/prompts.py`
  - `notebook_common.md`
  - `notebook_sach.md`: `$lesson`
  - `notebook_giaovien.md`: `$lesson`
  - `notebook_ca_hai.md`: `$lesson`
  - `notebook_format_md.md`
  - `notebook_note_check.md`: `$lesson`, `$note`
- `src/notebook/giang_bai.py`
  - `giang_bai.md`: `$bai`, `$luu_y`, `$ket_bai`
- `src/notebook/tao_cau_hoi.py`
  - `tao_cau_hoi.md`: `$bai`, `$tn`, `$tl_dong`, `$kho`, `$luu_y`, `$tl_format`, `$tl_goi_y`
  - `quiz_instruction.md`: `$lesson`, `$note`
- `src/notebook/muc_luc.py`
  - `muc_luc.md`
- `src/notebook/generate_artifacts.py`
  - `artifact_instructions.md`: `$lesson`
  - `artifact_extra.md`: `$base`, `$extra`
- `src/notebook/tao_media.py`
  - `media_mindmap.md`: `$bai`, `$luu_y`
  - `media_infographic.md`: `$bai`, `$luu_y`
  - `media_video.md`: `$bai`, `$luu_y`

### OCR, slide và transcript

- `src/ingest/process_book.py`
  - `process_book_ocr.md`
  - `process_book_inject.md`
  - `process_book_batch.md`: `$page_count`, `$page_numbers`, `$tags`, `$topic`
  - `process_topic.md`: `$topic`
- `src/ingest/slides_to_md.py`
  - `slides_to_markdown.md`
- `src/ingest/transcripts/build_transcript.py`
  - `transcript_clean.md`
  - `whisper_initial_vi.md`
  - `whisper_initial_en.md`
- `src/ingest/transcripts/get_medical_transcript.py`
  - `whisper_context_vi.md`
  - `whisper_context_en.md`

## 9. Kiểm tra

Compile nguồn:

```bash
uv run python -m compileall -q src
```

Load một prompt:

```bash
uv run python -c "from src.core.prompts import render_prompt; print(render_prompt('bien_tap_core_rules')[:80])"
```

Kiểm tra placeholder động:

```bash
uv run python -c "from src.core.prompts import render_prompt; print(render_prompt('exam_solver_step2_classify', data='[]')[:80])"
```

Test:

```bash
uv run --with pytest pytest -q tests/test_paths.py tests/test_prompts.py
```

## 10. Xử lý lỗi thường gặp

### `FileNotFoundError`

- Kiểm tra tên file trong `config/prompts/`.
- Tên prompt không được chứa `/` hoặc `\`.
- Tên có thể viết không có `.md`; loader sẽ thêm `.md`.

### `ValueError: Thiếu biến`

- So khớp placeholder trong `.md` với keyword argument trong `render_prompt(...)`.
- Kiểm tra tên chính xác, phân biệt `_` và khoảng trắng.

### Prompt không cập nhật

- `render_prompt()` dùng cache theo process.
- Khởi chạy lại Python/CLI sau khi đổi file.
- Nếu test trong cùng process sau khi ghi file, khởi chạy lại process để nạp lại cache.

### Prompt bị thay nội dung LaTeX/JSON

- Không dùng `.format()` hoặc f-string thay prompt.
- Dùng `$variable_name`.
- Giữ dấu `$`, `{}`, `[]` trong Markdown; loader chỉ thay placeholder nhận dạng `$name` hoặc `${name}`.
