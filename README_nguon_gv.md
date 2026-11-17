# Gói "Nguồn giáo viên": transcript, slide, tải nguồn, giảng theo nguồn

Gói này đã được ghép vào toolkit (bổ sung, không ghi đè file nào của toolkit). Mục tiêu: mỗi môn học là một notebook NotebookLM riêng, nạp ba loại nguồn, rồi giảng bài / kiểm tra note **chỉ dựa trên nguồn đã chọn**.

> **Tình trạng kiểm tra:** code được rà cú pháp và tên hàm tĩnh, **chưa chạy thật** (không có key Gemini, tài khoản NotebookLM, GitHub Actions). Bạn chạy thử từng bước ở mục 5 rồi báo lỗi để cùng sửa.

## 1. Luồng tổng

```
INPUT (chuẩn bị nguồn)                              OUTPUT (khai thác từ notebook)
────────────────────────────────────────            ───────────────────────────────────
[SGK]   Sách → Markdown (process_book.py, đã có)    Giảng bài: sách / giáo viên / cả hai
[GV]    Video bài giảng → transcript .md            Kiểm tra note của bạn
[SLIDE] Slide (.pptx/.pdf) → .md có mô tả sơ đồ     Quiz, flashcards, mindmap, infographic
Tài liệu ngoài (y văn, Ninja Nerd...): tự học, không tự động hoá
```

Vì sao như vậy:
- NotebookLM đọc chữ tốt, đọc sơ đồ kém, nên mọi nguồn đều thành **Markdown thuần chữ**. Ảnh slide chỉ để bạn đọc trong Obsidian.
- **Quy ước tên nguồn là chìa khoá** nối input với output. Bước tải đặt tên có tiền tố; bước giảng chọn nguồn **thật sự** bằng `source_ids` theo tiền tố, nên "chỉ sách" hay "chỉ giáo viên" bị giới hạn ở tầng nguồn chứ không chỉ nhờ prompt.
- Transcript có 2 tầng: tầng 1 lấy phụ đề YouTube ngay trên máy (nhẹ, nhanh); tầng 2 chạy Whisper trên GitHub Actions, chỉ khi video không có phụ đề (máy không có GPU).

## 2. Quy ước tên nguồn (bắt buộc nhất quán)

| Tiền tố | Nội dung | Ví dụ |
|---|---|---|
| `[SGK]` | Sách giáo khoa Markdown | `[SGK] Sinh lý học - Tiêu hoá` |
| `[GV]` | Transcript bài giảng | `[GV] Sinh lý gan` |
| `[SLIDE]` | Slide bản `*.notebooklm.md` | `[SLIDE] Sinh lý gan` |

`[GV]` và `[SLIDE]` được ghép với bài theo **tên**: nguồn `[GV] Sinh lý gan` khớp bài "Bài 5. Sinh lý gan" (so sánh không dấu, bỏ phần "Bài N."). Tên nguồn nên chứa tên bài. Muốn chỉ định tay, thêm `match=chuỗi` vào dòng của bài trong danh sách.

## 3. Các file trong gói

```
.github/workflows/transcribe.yml       Whisper trên Actions (transcript tầng 2)
.github/workflows/giang_bai.yml        giảng bài / kiểm tra note từ Actions (tuỳ chọn, bấm từ iPhone)
input/transcripts/transcript_utils.py  hàm dùng chung cho hai tầng
input/transcripts/build_transcript.py  chạy trên Actions
input/transcripts/get_medical_transcript.py  chạy trên máy cá nhân
input/slides/slides_to_md.py           slide → Markdown bằng Gemini
input/upload_sources.py                tải .md lên notebook, đặt tên theo quy ước
output/prompts.py                      prompt tách riêng
output/ask_notebook.py                 hỏi một bài / kiểm tra note, chọn nguồn theo tiền tố
output/giang_hang_loat.py              giảng hàng loạt từ giao_trinh.txt / giang_bai.txt
output/generate_artifacts.py           quiz, flashcards, mindmap, infographic theo nguồn
menu_nguon_gv.py                       menu phụ gom các việc trên
requirements_nguon_gv.txt, .env.nguon_gv.example, README_nguon_gv.md
```

Các file này đã nằm sẵn trong thư mục gốc toolkit (cùng cấp với `common.py`, `menu.py`). Các script chạy **từ thư mục gốc**, ví dụ `uv run output/ask_notebook.py ...`. Tên file `requirements_nguon_gv.txt`, `.env.nguon_gv.example`, `README_nguon_gv.md` được đặt khác tên mặc định để không đè `README.md` / `.env.example` có sẵn.

`giang_hang_loat.py` và `upload_sources.py` dùng `common.py` của toolkit (đọc `giao_trinh.txt`, ID notebook, lưu `.md`, kiểu Obsidian).

## 4. Cài đặt

Mỗi script khai báo thư viện ở đầu file, nên chỉ cần `uv` (đã có trong toolkit) và chạy bằng `uv run đường/dẫn.py`. Muốn dùng pip: `pip install -r requirements_nguon_gv.txt`.

Công cụ hệ thống (không phải Python):

```bash
sudo apt install libreoffice-impress     # chỉ khi slide là .pptx/.ppt
# GitHub CLI (gh) + đăng nhập, chỉ khi dùng Whisper trên Actions:
gh auth login
```

Khoá Gemini: menu phụ mục `[8]`, hoặc tạo file `.env` ở thư mục gốc:

```
GEMINI_API_KEY=khóa_của_bạn
GEMINI_MODEL=gemini-3.8-flash,gemini-3.6-flash
```

Notebook: dùng `notebook_id.txt` của toolkit (menu chính mục Đặt ID notebook), hoặc `-n <id>`, hoặc biến `NOTEBOOKLM_NOTEBOOK`. Mỗi môn một notebook: đổi ID khi chuyển môn.

### Menu chính

Đã gắn sẵn mục **[16]** trong `menu.py` (bản đã có mục [15]). Cũng có thể chạy riêng: `uv run menu_nguon_gv.py`.

### `.gitignore`

Thêm các dòng sau (hoặc dùng menu `[15]` → `[12]`, rồi bổ sung):

```
.env
/transcripts/
transcript_out/
slides_out/
giang_out/
```

## 5. Chạy thử theo thứ tự này

**A. Transcript (máy cá nhân, không cần key)**

```bash
uv run input/transcripts/get_medical_transcript.py --url "https://youtu.be/..." --lang vi
```
Có phụ đề → `transcripts/<tên video>.md`. Không có → hỏi có chuyển sang Actions + Whisper không (cần `gh` và workflow đã được đẩy lên repo; xem mục 6).

**B. Slide**

```bash
uv run input/slides/slides_to_md.py "Sinh ly gan.pptx"        # hoặc .pdf
```
Ra `slides_out/<tên>/<tên>.md` (có ảnh, cho Obsidian) và `<tên>.notebooklm.md` (chỉ chữ, để tải lên NotebookLM). Bị ngắt thì chạy lại sẽ làm tiếp. Hãy thử trước với file nhỏ vài slide.

**C. Tải nguồn lên (xem trước bằng --dry-run)**

```bash
uv run input/upload_sources.py --prefix GV transcripts/ --dry-run
uv run input/upload_sources.py --prefix GV transcripts/
uv run input/upload_sources.py --prefix SLIDE slides_out/            # chỉ lấy *.notebooklm.md
uv run input/upload_sources.py --prefix SGK output_md/               # sách đã chuyển bằng process_book.py
uv run input/upload_sources.py --prefix SLIDE --merge-as "Sinh lý gan" slides_out/Gan1 slides_out/Gan2
```
Nguồn trùng tên được bỏ qua. Script đọc hạn mức nguồn từ tài khoản và cảnh báo khi sắp đầy (không ghi cứng con số).

**D. Giảng bài**

```bash
uv run output/ask_notebook.py ca_hai "Sinh lý gan"                 # một bài, in ra màn hình
uv run output/ask_notebook.py giaovien "Sinh lý gan" -o bai.md
uv run output/ask_notebook.py kiemtra_note "Sinh lý gan" --note note.txt
uv run output/giang_hang_loat.py ca_hai --test                      # hàng loạt: thử bài đầu
uv run output/giang_hang_loat.py ca_hai --obsidian --book "Sinh lý"
```
- Danh sách bài: `giang_bai.txt`, nếu trống thì `giao_trinh.txt` (định dạng của toolkit).
- Chế độ: `sach` (chỉ [SGK]), `giaovien` ([GV] + [SLIDE]), `ca_hai`, `kiemtra_note`.
- Hỏi mà không truyền `conversation_id` thì **nối** vào cuộc trò chuyện hiện tại. `--new` (một bài) / `--new-each` (hàng loạt) **xoá lịch sử chat, không khôi phục được**; mặc định tắt.
- Kết quả hàng loạt: `ket_qua/giang_bai_nguon/<chế độ>/NN - <tiêu đề>.md`.

**E. Quiz, flashcards, mindmap, infographic (một bài)**

```bash
uv run output/generate_artifacts.py quiz "Sinh lý gan" --source ca_hai --quantity more --difficulty medium
uv run output/generate_artifacts.py mindmap "Sinh lý gan" --source giaovien
```
Kết quả trong `ket_qua/artifacts_nguon/<loại>/`. Script tải đúng artifact vừa tạo (theo `artifact_id`). Hạn mức tạo nội dung tuỳ gói tài khoản.

**Menu phụ:** `uv run menu_nguon_gv.py` gom các bước A đến E (hỏi từng thông tin, có chế độ `--dry-run`/`--test`).

## 6. GitHub Actions

1. Đẩy `.github/workflows/*.yml` lên repo GitHub của bạn, bật Actions.
2. **transcribe.yml** (Whisper): không cần secret. Chạy từ máy bằng `get_medical_transcript.py` (cần `gh auth login`), hoặc bấm tay trong tab Actions. Kết quả là artifact `medical-transcript`.
   - Nếu YouTube chặn IP của GitHub ("Sign in to confirm you're not a bot"): tạo secret `YT_COOKIES` chứa nội dung file `cookies.txt` (định dạng Netscape) từ trình duyệt của bạn. Workflow tự dùng nếu có.
3. **giang_bai.yml** (giảng bài từ iPhone, tuỳ chọn): tạo secret `NOTEBOOKLM_AUTH_JSON` = nội dung `storage_state.json` (đăng nhập bằng `notebooklm login`), và secret `NOTEBOOKLM_NOTEBOOK` (hoặc điền ID khi bấm chạy). Workflow kiểm tra đăng nhập trước khi chạy rồi tải kết quả về dạng artifact `giang-bai`. Cookie hết hạn thì cập nhật secret, khoảng 1 đến 2 tuần một lần. Nên dùng tài khoản Google riêng cho việc này.

## 7. Điểm chưa kiểm chứng

- **Tên model Gemini:** mặc định `gemini-3.8-flash,gemini-3.6-flash` theo trang model của Google tại thời điểm viết; có thể đã đổi. Dùng `uv run process_book.py --list-models`, rồi sửa `GEMINI_MODEL` trong `.env` cho khớp `process_book.py`. Script slide tự bỏ qua model không tồn tại hoặc hết quota ngày.
- **YouTube chặn Actions:** hay xảy ra; cách xử lý dự phòng là cookie qua secret `YT_COOKIES` (cũng chưa được thử thật).
- **Whisper:** tên model Hugging Face (`deepdml/faster-whisper-large-v3-turbo-ct2`) và các tham số của `BatchedInferencePipeline` chưa được thử; trên CPU Actions có thể rất lâu với video dài.
- **Tìm lần chạy vừa kích hoạt:** `get_medical_transcript.py` so sánh danh sách run trước và sau khi kích hoạt thay vì lấy run mới nhất; vẫn có thể nhầm nếu bạn bấm nhiều lần cùng lúc.
- **Slide ẩn:** LibreOffice bỏ qua slide ẩn; code cũng bỏ slide ẩn khi lấy ghi chú. Nên thử trên một file thật; nếu số ghi chú khác số slide thì script bỏ qua ghi chú và báo.
- **Infographic:** tên tham số của `generate_infographic` (`orientation`...) không có trong tài liệu thư viện; script chỉ truyền tham số có thật trong hàm, nên có thể bỏ qua tuỳ chọn mà không báo lỗi.
- **Ghép bài với nguồn [GV]/[SLIDE] theo tên** là suy đoán dựa trên tên bài; nếu không khớp, dùng `match=` hoặc `--match`.
- **Giới hạn kích thước từng nguồn** của NotebookLM chưa kiểm chứng; script không khẳng định con số nào.
- Bản ghi phụ đề tự động có thể sai thuật ngữ y khoa; NotebookLM chỉ dựa vào chữ đã có, nên cần soát các bài quan trọng.

## 8. Debug

| Triệu chứng | Cách xử lý |
|---|---|
| `Không có nguồn READY nào có tiền tố [...]` | Tên nguồn chưa đúng quy ước hoặc nguồn chưa xử lý xong. Xem danh sách nguồn trong NotebookLM, dùng `upload_sources.py` để tải lại với `--prefix`. |
| Giảng `giaovien` báo không tìm thấy nguồn [GV]/[SLIDE] khớp | Tên nguồn không chứa tên bài. Đổi tên nguồn, hoặc thêm `match=chuỗi` vào dòng bài, hoặc `--match`. |
| `Chưa có ID notebook` | Ghi ID vào `notebook_id.txt` (menu chính [12]) hoặc dùng `-n`. |
| Slide: `Thiếu LibreOffice` | `sudo apt install libreoffice-impress`. |
| Slide: `Không còn model nào dùng được` | Sửa `GEMINI_MODEL` theo `--list-models`, hoặc đợi quota ngày reset (checkpoint đã lưu, chạy lại là tiếp tục). |
| Transcript: `Không thấy yt-dlp` | Chạy bằng `uv run ...` (tự cài) hoặc `pip install yt-dlp`. |
| Transcript: không kích hoạt được workflow | Workflow chưa được đẩy lên repo, chưa `gh auth login`, hoặc đang đứng sai thư mục repo. |
| Actions: giảng bài báo phiên đăng nhập hết hạn | Cập nhật secret `NOTEBOOKLM_AUTH_JSON`. |
| `generate_*` lỗi / hết hạn mức | Hạn mức tạo nội dung tuỳ gói tài khoản. Chạy lại sau. |
| Câu trả lời lẫn nội dung bài trước | Hỏi nối vào cuộc trò chuyện cũ. Dùng `--new`/`--new-each` (xoá lịch sử chat, không khôi phục được). |
| `menu_nguon_gv.py` báo thiếu hàm trong `menu` | `menu.py` của bạn là bản cũ; dùng bản có mục [15] (đã có `has_key`, `md_set_key`). |

Khi báo lỗi, gửi: tên bước đang làm (ví dụ "C. upload slide"), dòng lệnh đã chạy, và **nguyên văn** thông báo lỗi (cả traceback).
