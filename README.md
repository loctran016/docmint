# Bộ công cụ NotebookLM: OCR sách, đọc mục lục, giảng bài, câu hỏi, mindmap, infographic, video, Obsidian

Chạy được trên **WSL Ubuntu** và **Windows** (và macOS ở mức cơ bản). Mọi thứ điều khiển từ một menu đánh số, hoặc chạy từng script riêng.

> **Đã kiểm tra gì, chưa kiểm tra gì.** Toàn bộ logic được chạy thử trên Linux bằng thư viện giả (không gọi NotebookLM thật, không chạy trên Windows thật). Vì vậy các bước đầu tiên của từng chức năng luôn nên chạy thử một bài trước.
> `notebooklm-py` là thư viện **không chính thức**, dùng API nội bộ của Google nên có thể hỏng khi Google thay đổi. Theo trang PyPI của nó, NotebookLM đã được đổi tên thành **Gemini Notebook** (7/2026), cùng một dịch vụ và thư viện vẫn chạy như cũ.

## Mục lục

0. [Bắt đầu nhanh](#0-bắt-đầu-nhanh)
1. [Cấu trúc thư mục và các file danh sách](#1-cấu-trúc-thư-mục-và-các-file-danh-sách)
2. [Cài notebooklm-py](#2-cài-notebooklm-py)
3. [Cài OCR (WSL và Windows)](#3-cài-ocr-wsl-và-windows)
4. [OCR cả thư mục PDF](#4-ocr-cả-thư-mục-pdf)
5. [Kiểm tra sách: đọc mục lục](#5-kiểm-tra-sách-đọc-mục-lục)
6. [Giảng bài](#6-giảng-bài)
7. [Tạo câu hỏi](#7-tạo-câu-hỏi)
8. [Mindmap, Infographic, Video](#8-mindmap-infographic-video)
9. [Obsidian: đồng bộ vào vault](#9-obsidian-đồng-bộ-vào-vault)
10. [Debug: lỗi thường gặp](#10-debug-lỗi-thường-gặp)
11. [Phụ lục: lệnh chạy từng script](#11-phụ-lục-lệnh-chạy-từng-script)
12. [PDF → Markdown bằng Gemini (mục [15])](#12-pdf--markdown-bằng-gemini-menu-mục-15)
13. [Nguồn giáo viên: transcript, slide, giảng theo nguồn (mục [16])](#13-nguồn-giáo-viên-menu-mục-16)
14. [Giảng bài / câu hỏi tự động trên GitHub Actions](#14-giảng-bài--câu-hỏi-tự-động-trên-github-actions)

---

## 0. Bắt đầu nhanh

Cần duy nhất một thứ: **uv** (trình quản lý Python, tự tải Python khi cần, nên không phải cài Python riêng).

### WSL / Linux

```bash
cp /mnt/c/Users/TEN_WINDOWS/Downloads/notebooklm-toolkit.zip ~/
python3 -m zipfile -e ~/notebooklm-toolkit.zip ~/
cd ~/notebooklm-toolkit
bash menu.sh
```

`menu.sh` hỏi cài uv nếu máy chưa có. Gọi menu bằng một từ ngắn (zsh): `echo "alias nlm='bash ~/notebooklm-toolkit/menu.sh'" >> ~/.zshrc && source ~/.zshrc`.

### Windows

1. Giải nén `notebooklm-toolkit.zip` vào một thư mục (ví dụ `C:\notebooklm-toolkit`). Nên để ở ổ Windows, không để trong `\\wsl$\...`.
2. **Nhấp đúp `menu.cmd`.** Nếu máy chưa có uv, nó cài bằng `winget install astral-sh.uv`; khi xong hãy **đóng cửa sổ và nhấp đúp lại**.
3. Dùng Windows Terminal để hiển thị khung và tiếng Việt đẹp nhất. Mở PowerShell tại thư mục toolkit rồi chạy `uv run menu.py` cũng được.

> `menu.py` là menu chính trên mọi hệ điều hành. `menu.cmd` (Windows) và `menu.sh` (WSL/Linux/macOS) chỉ là lối tắt kiểm tra uv rồi chạy `uv run menu.py`; chạy thẳng `uv run menu.py` cũng như nhau.

> **WSL và Windows là hai môi trường tách biệt**: mỗi nơi có phiên đăng nhập NotebookLM riêng (lưu trong thư mục home của nơi đó) và cài OCR riêng. Dùng một nơi là đủ; nếu dùng cả hai, hãy dùng hai bản chép riêng của toolkit để tránh lẫn kết quả.

### Menu

```
┌────────────────────────────────────────────────────────────────┐
│                     BỘ CÔNG CỤ NOTEBOOKLM                      │
│                   Ubuntu 24.04 LTS (WSL)                       │
├────────────────────────────────────────────────────────────────┤
│  Notebook ID: 623ed002… | Obsidian: TẮT                        │
│  uv: có | OCR: có | đăng nhập: có | Gemini: có                 │
├────────────────────────────────────────────────────────────────┤
│ [1] Hướng dẫn (README.md)                                      │
│ [2] Cài & set-up notebooklm-py                                 │
│ [3] Cài & set-up OCR                                           │
│ [4] OCR PDFs (cả thư mục)                                      │
│ [15] PDF → Markdown bằng Gemini (process_book.py)              │
│ [16] Nguồn giáo viên: transcript, slide, giảng theo nguồn      │
│                        ────────────────                        │
│ [5] Kiểm tra sách: đọc mục lục Chương/Bài                      │
│ [6] Giảng bài NotebookLM                                       │
│ [7] Tạo câu hỏi NotebookLM                                     │
│ [8] Tạo Mindmap                                                │
│ [9] Tạo Infographic                                            │
│ [10] Tạo Video                                                 │
│                        ────────────────                        │
│ [11] Obsidian: đồng bộ vào vault                               │
│ [12] Đặt ID notebook                                           │
│ [13] Kiểm tra trạng thái                                       │
│ [14] Mở thư mục                                                │
│                        ────────────────                        │
│ [0] Thoát                                                      │
└────────────────────────────────────────────────────────────────┘
```

**Thứ tự dùng lần đầu:** `[2]` → `[3]` → `[12]` → `[4]` (PDF đã OCR chỉ để đọc cho rõ) → `[15]` (PDF → Markdown bằng Gemini, **đây là nguồn tải lên NotebookLM**) → `[5]` → `[6]`…`[10]`.

Muốn thêm transcript bài giảng của giáo viên và slide làm nguồn, rồi giảng theo từng loại nguồn: dùng `[16]` (xem mục 13).

Menu nhớ các công tắc bạn chọn (file ẩn `.menu_settings.json`). Ctrl+C dừng tác vụ đang chạy nhưng không thoát menu.

---

## 1. Cấu trúc thư mục và các file danh sách

```
notebooklm-toolkit/
├── README.md
├── menu.py / menu.sh / menu.cmd   menu (menu.sh cho WSL/Linux, menu.cmd cho Windows)
├── 1_setup_notebooklm.py          cài notebooklm-py, đăng nhập Google
├── 2_setup_ocr.py                 cài OCR
├── 3_ocr_pdfs.py                  OCR cả thư mục PDF
├── process_book.py                PDF scan → Markdown bằng Gemini (menu [15])
├── 4_giang_bai.py                 giảng bài
├── 5_tao_cau_hoi.py               tạo câu hỏi
├── 6_muc_luc.py                   đọc mục lục sách
├── 7_tao_media.py                 mindmap / infographic / video
├── 8_kiem_tra_pdf.py              kiểm tra lớp chữ của PDF
├── 9_cap_nhat_obsidian.py         cập nhật note mục lục Obsidian
├── common.py                      hàm dùng chung (đừng xóa)
├── menu_nguon_gv.py               menu phụ nguồn giáo viên (menu [16])
├── input/                         chuẩn bị nguồn: transcripts/, slides/, upload_sources.py
├── output/                        khai thác nguồn: ask_notebook.py, giang_hang_loat.py, generate_artifacts.py, prompts.py
├── .github/workflows/             transcribe.yml (Whisper), giang_bai.yml (giảng 1 bài từ iPhone), notebooklm_batch.yml (giảng bài / câu hỏi hàng loạt)
├── .github/scripts/               nlm_report.py (tóm tắt kết quả cho Release)
├── requirements_nguon_gv.txt  .env.nguon_gv.example  README_nguon_gv.md
├── notebook_id.txt                ID notebook
├── giao_trinh.txt                 DANH SÁCH CHUNG: chương và bài của sách
├── giang_bai.txt  cau_hoi.txt  mindmaps.txt  infographics.txt  videos.txt
│                                  danh sách RIÊNG của từng chức năng (tùy chọn)
├── input_pdfs/  output_ocr/       (tự tạo) PDF gốc, PDF đã OCR
├── output_md/                     (tự tạo) Markdown do Gemini chuyển, nguồn tải lên NotebookLM
├── tessdata/                      (tự tạo trên Windows) gói ngôn ngữ OCR tải về
└── ket_qua/                       (tự tạo) kết quả, có thể đổi sang vault Obsidian
    ├── muc_luc/  giang_bai/  cau_hoi/  mindmap/  infographic/  video/
```

### Quy tắc đọc danh sách: file riêng trước, danh sách chung sau

Mỗi chức năng **nhìn vào file riêng của nó trước**. Nếu file đó chưa có bài nào (chỉ có chú thích), nó dùng `giao_trinh.txt`.

| Chức năng | File riêng (đọc trước) | Rồi mới đến |
|---|---|---|
| Giảng bài | `giang_bai.txt` | `giao_trinh.txt` |
| Câu hỏi | `cau_hoi.txt` (hoặc tên cũ `cauhoi.txt`) | `giao_trinh.txt` |
| Mindmap | `mindmaps.txt` | `giao_trinh.txt` |
| Infographic | `infographics.txt` | `giao_trinh.txt` |
| Video | `videos.txt` | `giao_trinh.txt` |

Ví dụ: muốn làm video chỉ cho 3 bài thì ghi 3 bài đó vào `videos.txt`; các chức năng khác vẫn dùng toàn bộ `giao_trinh.txt`. (`giao_trinh.txt` thay cho `bai.txt` cũ. Nếu bạn còn `bai.txt`, đổi tên thành `giao_trinh.txt`; script vẫn đọc được tên cũ.)

### Cách viết một dòng

```
Tên bài | lưu ý riêng | tùy chọn | cờ
```

- **Tên bài**: chép đúng như mục lục sách, vì NotebookLM tìm bài theo tên.
- **Lưu ý riêng**: chữ thường, đưa thẳng vào prompt của bài đó.
- **Tùy chọn** dạng `key=value`: `tn=15 | tl=3 | kho=kho` (câu hỏi); `style=whiteboard`, `orientation=portrait` (video, infographic, xem mục 8).
- **Cờ** (giảng bài): `tomtat`, `khongtomtat`, `cauhoi`, `khongcauhoi`.
- Các phần sau tên bài đặt theo thứ tự nào cũng được.

### Chương trong danh sách

Dòng `## Tên chương` (hoặc `# Chương 1 ...`, `# Phần II ...`) đánh dấu tên chương; các bài bên dưới thuộc chương đó. Chương được dùng để nhóm bài trong Obsidian. Các dòng khác bắt đầu bằng `#` là chú thích, dòng trống bị bỏ qua.

```
## CHƯƠNG 1: GIỚI THIỆU VỀ KHOA HỌC DINH DƯỠNG
Bài 1. Dinh dưỡng và sức khỏe
Liên hệ thực tế 1: Dinh dưỡng lâm sàng | tóm gọn, không cần giảng sâu | khongcauhoi

## CHƯƠNG 2: CÁC DƯỠNG CHẤT TRONG DINH DƯỠNG
Bài 2. Carbohydrate, lipid, protid | giảng kỹ phần chuyển hóa
```

Không cần gõ tay: mục [5] của menu tự đọc mục lục từ NotebookLM và ghi vào đúng định dạng này (mục 5).

---

## 2. Cài notebooklm-py

Menu `[2]`, hoặc:

```bash
uv run 1_setup_notebooklm.py            # thêm --dry-run để chỉ xem các lệnh sẽ chạy
```

Script làm: (WSL/Linux) cài `curl` và `libatomic1` bằng apt → cài Chromium cho Playwright → mở cửa sổ đăng nhập Google → kiểm tra phiên đăng nhập (phải thấy `"status": "ok"`). Trên Windows bỏ bước apt.

- WSL: khi hỏi mật khẩu `sudo`, gõ mật khẩu Ubuntu (không hiện ký tự khi gõ).
- Cửa sổ Chromium hiện ra: đăng nhập Google, vào tới trang NotebookLM, rồi quay lại terminal làm theo hướng dẫn (thường là nhấn Enter).

**Lấy ID notebook:** menu `[12]` có mục liệt kê notebook (`notebooklm list`) và mục dán ID hoặc cả URL. ID là đoạn cuối URL `https://notebooklm.google.com/notebook/<ID>`. Cũng có thể sửa tay file `notebook_id.txt`.

---

## 3. Cài OCR (WSL và Windows)

Menu `[3]`, hoặc `uv run 2_setup_ocr.py` (thêm `--dry-run` để chỉ xem lệnh).

### WSL / Linux (Debian, Ubuntu)

Script chạy `apt-get install ocrmypdf tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng ghostscript` (hỏi mật khẩu sudo) rồi kiểm tra.

### Windows (chạy trực tiếp, không cần WSL)

Theo tài liệu của OCRmyPDF, **OCR chạy được trực tiếp trên Windows**, cần ba thành phần 64-bit: Python, Tesseract, Ghostscript. Tài liệu cũng nói OCRmyPDF tự tìm Tesseract và Ghostscript trong Registry và thư mục Program Files. Script cài đặt làm như sau:

| Thành phần | Cách cài | Ghi chú |
|---|---|---|
| Python | **không cần cài riêng** | `uv` tự tải. OCRmyPDF được `uv` kéo về khi chạy OCR. |
| Tesseract | `winget install -e --id UB-Mannheim.TesseractOCR` | Windows có thể hỏi quyền quản trị (UAC), chọn Yes. Nếu không có winget, thử Chocolatey. |
| Ghostscript | `winget install -e --id ArtifexSoftware.GhostScript` | Bản mới của Ghostscript **không còn hỗ trợ cài tự động**. Nếu lệnh lỗi, tải bản 64-bit từ trang chính thức ghostscript.com và cài tay, rồi chạy lại bước này. |
| Tiếng Việt | script tải `vie.traineddata` và `eng.traineddata` về thư mục `tessdata/` của toolkit | Nguồn: kho `tesseract-ocr/tessdata_fast` trên GitHub. OCR sẽ tự dùng thư mục này (đặt `TESSDATA_PREFIX`). Nếu tải lỗi, tải tay hai file đó rồi chép vào `tessdata/`. |

Cuối bước cài, script in đường dẫn Tesseract, Ghostscript và danh sách ngôn ngữ để bạn kiểm tra.

> Không dùng Python bản Microsoft Store với OCRmyPDF (tài liệu của nó khuyên dùng Python từ python.org hoặc Chocolatey). Python do `uv` tải không phải bản Store, nhưng tôi chưa kiểm chứng riêng trường hợp này; nếu OCRmyPDF báo lỗi lạ thì cài Python từ python.org rồi chạy lại.

### macOS

Script chỉ in lệnh cần chạy: `brew install ocrmypdf tesseract-lang`.

---

## 4. OCR cả thư mục PDF

Menu `[4]`, hoặc:

```bash
uv run 3_ocr_pdfs.py                              # input_pdfs/ -> output_ocr/
uv run 3_ocr_pdfs.py /đường/dẫn/thư_mục           # thư mục bất kỳ
uv run 3_ocr_pdfs.py "C:\Users\ten\Sach"          # đường dẫn Windows (dùng được cả trên WSL)
uv run 3_ocr_pdfs.py thư_mục_vào thư_mục_ra
uv run 3_ocr_pdfs.py --langs vie --jobs 1         # chỉ tiếng Việt, giảm tải máy
```

- **Kết quả**: `output_ocr/<tên file sách> - OCR.pdf`. Chỉ quét các `.pdf` nằm trực tiếp trong thư mục (không quét thư mục con).
- File đã có kết quả được **bỏ qua**, nên chạy lại thoải mái sau khi bị ngắt. File lỗi được liệt kê cuối buổi.
- Trang nào đã có chữ được giữ nguyên (`--skip-text`), chỉ OCR trang ảnh.
- Sách dày có thể mất từ vài phút đến vài chục phút.
- Trong menu, chọn thư mục rỗng thì menu mở sẵn `input_pdfs/` trong Explorer để bạn chép PDF vào.

**Sau khi OCR xong:** xóa source cũ trên NotebookLM, tải các file `- OCR.pdf` lên, chờ xử lý xong, rồi dùng mục [5] để kiểm tra NotebookLM đã đọc được sách chưa. Tôi chưa kiểm chứng giới hạn dung lượng/số từ mỗi source hiện nay; nếu NotebookLM từ chối file quá lớn thì tách sách theo chương rồi tải từng phần lên.

---

## 5. Kiểm tra sách: đọc mục lục

Menu `[5]`. Có hai việc: nhờ NotebookLM đọc mục lục, và kiểm tra lớp chữ của PDF ngay trên máy.

### 5.1. Đọc mục lục từ NotebookLM

```bash
uv run 6_muc_luc.py            # in ra màn hình và lưu file
uv run 6_muc_luc.py --apply    # như trên và GHI vào giao_trinh.txt (bản cũ sao lưu thành giao_trinh.txt.bak)
```

NotebookLM đọc mục lục và trả về **Chương/Phần → Bài** (kèm số trang). Script in ra màn hình:

```
 MỤC LỤC ĐỌC ĐƯỢC: 3 chương/phần, 5 bài
 CHƯƠNG 1: GIỚI THIỆU VỀ KHOA HỌC DINH DƯỠNG
    - Bài 1. Dinh dưỡng và sức khỏe   (tr. 1)
    ...
 Kiểm tra nguồn (NotebookLM tự báo, chỉ để tham khảo): thấy nội dung từ trang 1 đến trang 202
------- SAO CHÉP TỪ ĐÂY (dán vào giao_trinh.txt) -------
```

và lưu `ket_qua/muc_luc/muc_luc.txt` (dán thẳng vào `giao_trinh.txt`, chương dạng `## ...`) cùng `muc_luc.md` (bản dễ đọc, có số trang).

**Cách dùng để kiểm tra PDF:**
- Nếu mục lục đọc ra đúng và đủ: NotebookLM đọc được trang mục lục.
- Dòng "Kiểm tra nguồn" là NotebookLM **tự báo** khoảng trang nó thấy. Đây chỉ là tham khảo, không phải bằng chứng chắc chắn. Trước đây chính câu báo này đã lộ ra việc nguồn chỉ có trang 154 đến 202.
- Nếu không đọc được mục lục, script in câu trả lời gốc và gợi ý OCR lại.
- Mục lục có thể đọc đủ mà thân bài vẫn thiếu trang, nên vẫn cần chạy thử `Giảng bài` một bài ở giữa sách.

### 5.2. Kiểm tra lớp chữ của PDF trên máy

```bash
uv run 8_kiem_tra_pdf.py                       # tự tìm trong output_ocr/ rồi input_pdfs/
uv run 8_kiem_tra_pdf.py /đường/dẫn/sach.pdf   # một file hoặc cả thư mục
```

In tổng số trang, số trang **không có chữ** (kèm khoảng trang, ví dụ `5-7, 9-10`), kết luận có cần OCR không, và dấu trang (bookmark) nhúng trong PDF nếu có. Không cần mạng.

---

## 6. Giảng bài

Menu `[6]`, hoặc:

```bash
uv run 4_giang_bai.py --test          # thử bài đầu tiên, in ra màn hình, không lưu
uv run 4_giang_bai.py                 # chạy toàn bộ
uv run 4_giang_bai.py --only 2,5-7    # chỉ bài thứ 2 và 5 đến 7 trong danh sách
uv run 4_giang_bai.py --force         # làm lại cả bài đã có file
```

Danh sách: `giang_bai.txt`, nếu chưa có bài thì `giao_trinh.txt`. Mỗi bài là một prompt riêng, bám sát bố cục bài trong sách (H1/H2/H3 theo đúng số mục), kết bằng "Tóm tắt nhanh" và "Câu hỏi tự kiểm tra". Cờ `tomtat`/`khongtomtat`/`cauhoi`/`khongcauhoi` trên từng dòng bật tắt hai phần cuối; mặc định đổi ở đầu `4_giang_bai.py` hoặc bằng `--no-tomtat`, `--no-cauhoi`.

Nếu NotebookLM trả lời **"Không tìm thấy bài này trong nguồn"**, script không lưu file mà liệt kê bài đó ở phần tổng kết (xem mục 10).

**Tùy chọn chung cho 4, 5 và 7** (menu có công tắc tương ứng):

| Tùy chọn | Tác dụng |
|---|---|
| `--test` | chỉ làm một bài (giảng bài, câu hỏi: in ra không lưu; mindmap/infographic/video: vẫn lưu) |
| `--only 1,3-5` | chỉ làm các bài theo số thứ tự trong danh sách |
| `--force` | làm lại cả bài đã có file |
| `--strip-cite` | xóa số trích dẫn `[1]`, `[2, 3]` khỏi file |
| `--frontmatter` | thêm YAML (title, tags, created) đầu file |
| `--obsidian` | chế độ Obsidian đầy đủ (mục 9) |
| `--out-root THƯ_MỤC` | đổi thư mục đầu ra gốc |
| `--delay 3,6` | nghỉ ngẫu nhiên giữa các bài (giây) |

Chạy lại sau khi bị ngắt: script nhớ bài nào đã xong (file ẩn `.state.json` trong thư mục đầu ra) nên chỉ làm tiếp các bài còn lại.

---

## 7. Tạo câu hỏi

Menu `[7]`, hoặc:

```bash
uv run 5_tao_cau_hoi.py --test            # thử bài đầu tiên
uv run 5_tao_cau_hoi.py                   # chế độ md (mặc định)
uv run 5_tao_cau_hoi.py --mode quiz       # dùng tính năng Quiz của NotebookLM
uv run 5_tao_cau_hoi.py --mode both       # cả hai
uv run 5_tao_cau_hoi.py --quiz-info       # xem tham số thật của hàm tạo Quiz
```

Danh sách: `cau_hoi.txt`, nếu chưa có bài thì `giao_trinh.txt`. Tùy chọn từng bài: `tn=` (số câu trắc nghiệm), `tl=` (số câu tự luận, `0` = không có), `kho=de|vua|kho`. Mặc định (đổi ở đầu `5_tao_cau_hoi.py`): 10 trắc nghiệm, 2 tự luận, độ khó vừa.

- **`md`**: NotebookLM viết đề Markdown: H1 tiêu đề, H2 "Phần I. Trắc nghiệm", H2 "Phần II. Tự luận", H2 "Đáp án và giải thích" ở cuối. Trong Obsidian có thể gập mục Đáp án lại để tự làm bài. Đây là chế độ ổn định nhất.
- **`quiz`**: tạo Quiz bằng tính năng riêng của NotebookLM và tải về `markdown` (mặc định), `json` hoặc `html` (`--quiz-format`).

**Chưa kiểm chứng ở chế độ quiz:** thư viện có hàm tạo/tải Quiz, nhưng tôi chưa biết nó có nhận hướng dẫn "chỉ hỏi về bài này" không (script cảnh báo nếu không), và khi notebook có nhiều Quiz thì `download_quiz` có tải đúng cái vừa tạo không (script tải ngay sau khi tạo; hãy mở thử vài file). `tn` và `kho` không áp dụng cho chế độ quiz.

---

## 8. Mindmap, Infographic, Video

Menu `[8]`, `[9]`, `[10]`, hoặc:

```bash
uv run 7_tao_media.py mindmap
uv run 7_tao_media.py infographic --only 2,4
uv run 7_tao_media.py video --test            # tạo thử bài đầu tiên (vẫn lưu file)
uv run 7_tao_media.py mindmap --mm-kind note-backed
uv run 7_tao_media.py video --api-info        # xem tham số thật của các hàm trong thư viện
```

| Loại | Danh sách đọc trước | Kết quả | Prompt |
|---|---|---|---|
| Mindmap | `mindmaps.txt` | `.json` (+ `.md` dàn ý nếu đọc được cấu trúc) | sơ đồ tư duy về {BÀI}, nhánh chính theo mục của bài |
| Infographic | `infographics.txt` | `.png` | infographic về {BÀI}, ý chính theo thứ tự mục, số liệu, bảng so sánh |
| Video | `videos.txt` | `.mp4` | video bài giảng về {BÀI}: mở đầu, các mục chính kèm ví dụ, tóm tắt |

Cả ba prompt đều yêu cầu tiếng Việt và chỉ dùng nội dung của bài đó. Muốn đổi lời lẽ prompt, sửa phần `KINDS` ở đầu `7_tao_media.py`.

- **Mindmap**: `--mm-kind interactive` (mặc định, bản tương tác mới) hoặc `note-backed` (bản JSON gắn với ghi chú). Dàn ý `.md` được tạo bằng cách **đoán** cấu trúc cây trong JSON; nếu đoán không ra, bạn vẫn có file JSON.
- **Tùy chọn từng bài** viết `key=value` trong dòng danh sách, ví dụ `Bài 2. ... | style=whiteboard`. Key nào trùng tên tham số của hàm tạo trong thư viện thì được truyền vào (kể cả đổi chuỗi sang giá trị Enum). Không trùng thì có cảnh báo. Xem tên tham số bằng `--api-info`. Cũng áp dụng cho mọi bài bằng `--opt key=value`.
- **Hạn mức**: video và infographic tốn nhiều thời gian (vài phút mỗi bài) và có hạn mức theo gói tài khoản. Script **dừng sau 2 lỗi liên tiếp** (thường là hết hạn mức hoặc phiên đăng nhập hết hạn); chạy lại sau, bài đã xong sẽ được bỏ qua. Nên liệt kê riêng các bài thật cần vào `videos.txt`.
- **Chưa kiểm chứng:** README của thư viện chỉ ghi ví dụ cho mindmap, âm thanh và quiz; tên hàm `generate_video`, `generate_infographic`, `download_video`, `download_infographic` là suy ra từ cách đặt tên của chúng. Script báo lỗi và in danh sách hàm thật nếu tên không khớp. Nếu hàm tạo không nhận hướng dẫn riêng, script chỉ tạo **một bản cho toàn bộ nguồn** thay vì tạo từng bài.

---

## 9. Obsidian: đồng bộ vào vault

Menu `[11]`. Bật chế độ Obsidian (hoặc thêm `--obsidian` khi chạy script) để **mọi thứ biến thành một mạng lưới liên kết** thay vì các file rời:

| Tính năng | Chi tiết |
|---|---|
| **Đầu ra thẳng vào vault** | Đặt thư mục đầu ra (`--out-root`) là một thư mục trong vault, ví dụ `~/vault/Dinh duong` hoặc `C:\Users\ten\Vault\Dinh duong`. Mọi file (bài giảng, đề, mindmap, infographic, video) rơi thẳng vào vault, không cần chép. |
| **Frontmatter** | `title`, `tags`, `created`, và các thuộc tính liên kết: `nguon: "[[Sách]]"`, `chuong: "[[Sách#CHƯƠNG...]]"`, `bai`, `loai`. |
| **Trích dẫn thành wikilink** | `[1, 2]` → `([[Tên sách\|1, 2]])`, trỏ về note sách. Trong bảng Markdown, dấu `\|` được tự thoát để không vỡ bảng. `--strip-cite` vẫn xóa hẳn trích dẫn nếu bạn muốn. |
| **Liên kết ngược** | Cuối mỗi note: `Liên kết: [[Sách]] · [[Sách#Chương]]`. |
| **Note mục lục (hub)** | File `<Tên sách>.md` liệt kê Chương > Bài, mỗi bài kèm link tới bài giảng, đề, Quiz, mindmap, infographic, video đã tạo. Trong Graph view, các note quây quanh sách. Cập nhật tự động sau mỗi lần chạy, hoặc chạy `uv run 9_cap_nhat_obsidian.py`. |

Menu `[11]` cho: bật/tắt chế độ, đặt thư mục đầu ra (kéo thả đường dẫn Windows cũng được), đặt tên note sách, cập nhật note mục lục, mở thư mục đầu ra.

**Cần biết:**
- Link trích dẫn trỏ về **note sách**, không phải đúng đoạn trang đó. NotebookLM chỉ cho số trích dẫn, và tôi không có cách xác định chính xác trang tương ứng. Đồ thị vẫn nối đúng quan hệ "note này dựa trên sách này".
- Note mục lục có dấu hiệu tự động trong file; nếu bạn đã có note trùng tên mà không có dấu hiệu đó, script **không ghi đè** mà báo để bạn đổi tên note sách.
- File ẩn `.state.json` trong thư mục đầu ra dùng để nhớ tiến độ; Obsidian bỏ qua file ẩn. Xóa file đó (hoặc dùng `--force`) nếu muốn làm lại tất cả.
- Tên file đã bỏ các ký tự Obsidian không cho dùng (`# ^ [ ] | : / \ ? * " < >`).
- Trong vault, link tới ảnh và video có phần mở rộng (`[[... (Video).mp4|Video]]`); Obsidian mở được chúng nếu định dạng được hỗ trợ.

---

## 10. Debug: lỗi thường gặp

### Cài đặt

| Triệu chứng | Nguyên nhân và cách xử lý |
|---|---|
| WSL: `sudo: 3 incorrect password attempts`, `apt` không chạy | Mật khẩu `sudo` là mật khẩu **Ubuntu** bạn đặt lúc cài WSL, không nhất thiết trùng Windows; gõ không hiện ký tự. Quên mật khẩu: trong PowerShell chạy `wsl -u root`, rồi `passwd TEN_USER_UBUNTU`, đặt mật khẩu mới, `exit`. |
| WSL: `error while loading shared libraries: libatomic.so.1` | Thiếu thư viện hệ thống (thường do bước apt bị lỗi). `sudo apt-get install -y libatomic1` rồi chạy lại bước cài. |
| `uv: command not found` ngay sau khi cài | WSL/Linux: `source $HOME/.local/bin/env` hoặc mở lại terminal. Windows: đóng rồi mở lại cửa sổ (PATH chỉ cập nhật ở cửa sổ mới). |
| Windows: `winget` không có | Cập nhật "App Installer" từ Microsoft Store, hoặc cài uv bằng PowerShell theo hướng dẫn trên trang của uv. |
| `TypeError: onExit is not a function` khi cài Chromium trên Linux | README của thư viện chỉ tới mục Linux trong `docs/troubleshooting.md` của repo `teng-lin/notebooklm-py`. |
| Không mở được cửa sổ trình duyệt khi `login` (WSL) | Cần WSLg (Windows 11) và `echo $DISPLAY` phải in giá trị như `:0`. Nếu không có, xem ngay dưới. |

**Không mở được trình duyệt trong WSL:** cách này dựa trên việc thư viện lưu phiên đăng nhập trong thư mục `.notebooklm` ở home, điều tôi chưa kiểm chứng. Đăng nhập trên Windows (mục 0, bản Windows), rồi trong WSL chép: `cp -r /mnt/c/Users/TEN_WINDOWS/.notebooklm ~/` và kiểm tra: `uv tool run --from "notebooklm-py[browser]" notebooklm auth check --test --json`. Thư viện còn có cách đăng nhập khác (nhập cookie từ trình duyệt đã đăng nhập, master token), xem phần Authentication trong tài liệu của nó.

### OCR

| Triệu chứng | Cách xử lý |
|---|---|
| "Tesseract thiếu gói ngôn ngữ: vie" | Chạy lại bước cài OCR. WSL: `sudo apt-get install -y tesseract-ocr-vie`. Windows: kiểm tra thư mục `tessdata/` có `vie.traineddata` và `eng.traineddata` (tải tay từ kho `tesseract-ocr/tessdata_fast` nếu cần). |
| "Chưa cài Ghostscript" (Windows) | Cài tay bản 64-bit từ ghostscript.com (winget có thể không cài được bản mới), rồi chạy `[13] Kiểm tra trạng thái`. |
| Windows: winget cài Tesseract xong mà script vẫn báo chưa có | Đóng và mở lại menu. Script tìm trong `Program Files\Tesseract-OCR` và `%LOCALAPPDATA%`; nếu bạn cài ở chỗ khác, thêm thư mục đó vào PATH. |
| Lỗi lạ dù đã cài đủ (Windows) | Tài liệu OCRmyPDF: dùng bản 64-bit của cả Python, Tesseract, Ghostscript, đừng trộn 32-bit với 64-bit. |
| Máy treo hoặc hết RAM khi OCR sách dày | `uv run 3_ocr_pdfs.py --jobs 1`. |
| `[lỗi] không OCR được` một file | File hỏng, bị mã hóa hoặc có mật khẩu. Mở bằng trình đọc PDF, lưu lại thành bản mới rồi OCR lại. |
| Chữ sau OCR sai dấu | Ảnh scan kém. Kiểm tra vài trang (`uv run 8_kiem_tra_pdf.py`, mở PDF và bôi đen chữ). |

### Chạy script

| Triệu chứng | Nguyên nhân và cách xử lý |
|---|---|
| Script chạy mà **không in gì**, hoặc `SyntaxError ... cd ~/...` | File `.py` bị rỗng hoặc lẫn lệnh terminal khi tạo thủ công bằng `cat > ... << EOF`. Dùng đúng file trong zip. Kiểm tra: `wc -l 4_giang_bai.py` (phải vài trăm dòng, không phải 0). |
| `Chưa có ID notebook` | Dán ID vào `notebook_id.txt` (không để dấu `#` ở đầu dòng ID) hoặc dùng menu `[12]`. |
| `Chưa có bài nào để làm` | Cả file riêng lẫn `giao_trinh.txt` chỉ có chú thích. Điền ít nhất một bài, hoặc dùng `[5]` để đọc mục lục. |
| NotebookLM trả lời **"Không tìm thấy bài này trong nguồn"**, hoặc nói nguồn chỉ có một số trang (ví dụ chỉ trang 154 đến 202) | PDF là bản scan chưa có lớp chữ, hoặc tên bài không khớp sách. Xem "Khi NotebookLM không thấy các trang đầu" bên dưới. |
| Bài giảng "trông hợp lý" nhưng không đúng sườn sách | NotebookLM không thấy bài đó nên ghép từ bài khác. Prompt đã bắt nó từ chối thay vì ghép nên lỗi này thường hiện ra thành "không tìm thấy"; nếu vẫn gặp, so tiêu đề với mục lục sách. |
| `Lỗi (lần 1/3): ...` rồi tự thử lại | Có thể do mạng, phiên đăng nhập hết hạn hoặc giới hạn tốc độ. Đợi rồi chạy lại. Lỗi xác thực: `uv tool run --from "notebooklm-py[browser]" notebooklm login`. |
| Hết thời gian chờ (timeout) | Câu trả lời hoặc video quá lâu. Tăng `TIMEOUT` ở đầu file `.py` (hoặc `timeout` trong `KINDS` của `7_tao_media.py`). |
| `Thư viện bản này không có hàm tạo/tải cho 'video'` | Tên hàm khác dự đoán. Script in danh sách hàm `generate_*`/`download_*` thật; cập nhật thư viện (`uv cache clean notebooklm-py`) hoặc báo cho tôi danh sách đó. |
| `Cảnh báo: hàm không có tham số 'style'` | Tên tham số khác. Chạy `--api-info`, dùng đúng tên. |
| "Dừng vì 2 lỗi liên tiếp" khi tạo video/infographic | Thường là hết hạn mức tạo nội dung hoặc đăng nhập hết hạn. Chạy lại sau. |
| `DeprecationWarning: Awaiting NotebookLMClient.from_storage(...)` | Bản script cũ. Bản trong bộ này đã dùng cú pháp mới. |
| Số trích dẫn `[1]`, `[2, 3]` dính trong file | Dùng `--strip-cite` (hoặc chế độ Obsidian để biến thành wikilink). Xóa sau bằng regex: `\s?\[\d+(?:\s*[,\-–]\s*\d+)*\]`. |
| Bài sau bị lẫn nội dung bài trước | Mỗi prompt đã có câu "bỏ qua các câu hỏi trước". Nếu vẫn lẫn, xóa lịch sử chat của notebook trên web rồi chạy lại với `--force`. |
| Cảnh báo "note của bạn (không có dấu hiệu tự động), không ghi đè" | Đã có note trùng tên note sách. Đổi tên note sách ở menu `[11]` hoặc đổi tên note cũ. |

#### Khi NotebookLM không thấy các trang đầu sách

Xem trước (preview) của nguồn hiển thị **hình ảnh** trang, nên bạn thấy chữ rõ không có nghĩa NotebookLM đã trích được chữ.

1. Menu `[5]` → `[4]` (hoặc `uv run 8_kiem_tra_pdf.py sach.pdf`) cho biết bao nhiêu trang không có chữ.
2. Nếu nhiều trang không có chữ: OCR (mục 4), rồi **xóa source cũ và tải bản OCR lên**.
3. Nếu bản OCR đủ chữ mà NotebookLM vẫn thiếu trang: file có thể quá lớn. Tách sách theo chương, tải từng phần lên cùng một notebook.

### Menu

| Triệu chứng | Cách xử lý |
|---|---|
| Khung menu lệch hoặc ký tự `┌ ─ │` hiện lạ | Font terminal không có ký tự vẽ khung. Dùng Windows Terminal với font Cascadia Mono, Consolas hoặc Nerd Font. |
| "Sửa danh sách" báo không thấy trình soạn thảo | WSL: `sudo apt-get install -y nano` hoặc đặt `EDITOR=vim`. Windows mở Notepad; sửa xong **lưu và đóng**, rồi nhấn Enter trong menu. |
| Mở thư mục mà Explorer không hiện | WSL: kiểm tra `explorer.exe .` chạy được. Windows: kiểm tra đường dẫn thư mục đầu ra có tồn tại. |
| Menu hiện `OCR: chưa` dù đã cài | Vào `[13] Kiểm tra trạng thái` để làm mới (nó kiểm tra Tesseract, Ghostscript, tiếng Việt). |
| Muốn xóa các công tắc đã nhớ | Xóa file ẩn `.menu_settings.json`. |

---

## 11. Phụ lục: lệnh chạy từng script

Ở thư mục toolkit (WSL, Windows PowerShell đều dùng được):

```bash
uv run 1_setup_notebooklm.py                  # cài notebooklm-py + đăng nhập
uv run 2_setup_ocr.py                         # cài OCR
uv run 3_ocr_pdfs.py [thư_mục_vào] [thư_mục_ra]
uv run 6_muc_luc.py [--apply]                 # đọc mục lục
uv run 8_kiem_tra_pdf.py [file|thư_mục]       # kiểm tra lớp chữ PDF
uv run 4_giang_bai.py [--test|--only 1,3-5|--force|--obsidian|--strip-cite]
uv run 5_tao_cau_hoi.py [--mode md|quiz|both|--test|--obsidian]
uv run 7_tao_media.py mindmap|infographic|video [--test|--only 1,3|--api-info|--opt key=value]
uv run 9_cap_nhat_obsidian.py [--out-root THƯ_MỤC] [--book "Tên sách"]
```

Quy trình đầy đủ không dùng menu:

```bash
uv run 1_setup_notebooklm.py && uv run 2_setup_ocr.py
uv run 3_ocr_pdfs.py /đường/dẫn/Sach                 # rồi tải output_ocr/*- OCR.pdf lên NotebookLM
echo "ID_NOTEBOOK" > notebook_id.txt
uv run 6_muc_luc.py --apply                          # mục lục -> giao_trinh.txt
uv run 4_giang_bai.py --test && uv run 4_giang_bai.py --obsidian
uv run 5_tao_cau_hoi.py --obsidian
uv run 7_tao_media.py mindmap --obsidian
```

---

## 12. PDF → Markdown bằng Gemini (menu mục [15])

`process_book.py` đọc PDF scan từng trang bằng Gemini (qua Google AI Studio) và chép lại thành Markdown: đoạn văn, tiêu đề `#`/`##`/`###` theo cấp bậc của sách, bảng, sơ đồ thành danh sách lồng nhau (mũi tên thành `-->`), số liệu giữ nguyên, chữ không đọc được ghi `[không rõ]`. Kết quả là văn bản sạch để tải lên NotebookLM làm nguồn, thay cho PDF scan.

> **Chưa kiểm chứng:** script này được viết ở một cuộc trò chuyện khác và **chưa được chạy thử** (cả bản gốc lẫn phần tích hợp vào menu). Hãy luôn chạy thử vài trang trước khi chạy cả cuốn.

### Dùng lần đầu

1. Menu `[15]` → `[7]`: dán `GEMINI_API_KEY` (tạo miễn phí tại https://aistudio.google.com/apikey). Khi dán không hiện ký tự. Key được ghi vào file `.env` và `.env` tự được thêm vào `.gitignore`.
2. `[15]` → `[9]`: liệt kê model dùng được với key của bạn. Nếu tên model mặc định bị báo không tồn tại, dùng `[8]` để đặt tên đúng.
3. `[15]` → `[12]`: thêm `.env` và các thư mục dữ liệu (`input_pdfs/`, `output_ocr/`, `output_md/`, `ket_qua/`...) vào `.gitignore` nếu repo của bạn công khai. Đó là nội dung sách có bản quyền, không nên đưa lên GitHub.
4. `[15]` → `[1]`: chạy thử. Nhập số trang có bảng hoặc sơ đồ (ví dụ `12`) để soát chất lượng. Kết quả in ra màn hình, không lưu gì.
5. `[15]` → `[2]`: chạy toàn bộ.

Chạy trực tiếp không qua menu:

```bash
uv run process_book.py --list-models
uv run process_book.py --test --pages 12            # thử riêng trang 12
uv run process_book.py                              # mọi PDF trong input_pdfs/
uv run process_book.py "đường/dẫn/thư_mục_hoặc_file.pdf"
uv run process_book.py --split                      # chia mỗi sách thành nhiều file theo chương (H1)
uv run process_book.py --pages 1-20,25 --book "dinh duong"
```

### Cách hoạt động

- Mỗi lần chỉ xử lý **một trang**: render ảnh xám, tăng tương phản, gửi Gemini, lưu ngay thành `output_md/.pages/<sách>/p00001.md`. Bị ngắt hoặc hết quota thì chạy lại sẽ **làm tiếp từ trang chưa xong**.
- Cuối cùng các trang được gộp thành `output_md/<sách>.md`. Đoạn văn bị cắt giữa hai trang được nối lại bằng một heuristic thận trọng (`--no-join` để tắt). Với `--split`, mỗi sách ra một thư mục, mỗi chương (mỗi tiêu đề `#`) một file.
- Lỗi 429 được chia hai loại: hết quota **theo phút** (chờ rồi thử lại) và hết quota **theo ngày** (dừng sạch, tiến độ vẫn được lưu, tự chuyển sang model dự phòng nếu bạn đặt nhiều model). Quota ngày thường reset lúc nửa đêm giờ Thái Bình Dương (khoảng 14 đến 15 giờ Việt Nam).
- Nếu Gemini trả về rỗng thì thử lại với nhiệt độ cao dần; vẫn rỗng thì trang đó được đánh dấu lỗi, không ghi file và **tự làm lại ở lần chạy sau**.
- Cuối mỗi sách, script liệt kê: trang còn thiếu (`CHƯA ĐỦ`), trang lỗi, và các trang có `[không rõ]` nên soát với sách giấy.

### Các công tắc trong menu `[15]`

| Mục | Tác dụng |
|---|---|
| `[1]` | Chạy thử vài trang, không lưu gì |
| `[2]` | Chuyển toàn bộ PDF |
| `[3]` | Chọn sách theo tên và/hoặc khoảng trang (`1-20,25`) |
| `[4]` | Làm lại từ đầu, bỏ tiến độ cũ (`--force`) |
| `[5]` | Chỉ gộp lại từ các trang đã có, không gọi API (`--merge-only`, không cần key) |
| `[6]` | Chia file theo chương (`--split`) |
| `[8]` | Đặt model; có thể ghi nhiều model cách nhau dấu phẩy, ví dụ `gemini-3.8-flash,gemini-3.6-flash` |
| `[10]`, `[11]` | Mở / đặt thư mục đầu ra (có thể là thư mục trong vault Obsidian) |

PDF đầu vào có thể là bản gốc trong `input_pdfs/` hoặc bản đã làm sạch trong `output_ocr/`. Tên file kiểu `... - OCR.pdf` được tự bỏ hậu tố khi đặt tên sách.

### Dùng kết quả với NotebookLM

- Tải các file `.md` lên NotebookLM làm nguồn thay cho PDF scan. Vì đã là văn bản thật, bạn không còn gặp tình huống NotebookLM chỉ thấy một phần trang.
- Với `--split`, mỗi chương là một file riêng: tải từng file thành một source để NotebookLM tập trung đúng phạm vi (mục tiêu "mỗi bài một prompt"). Chỉ tải lên khi sách không còn dòng `CHƯA ĐỦ`; file gộp khi còn thiếu trang là **bản chưa hoàn chỉnh**.
- Mục lục (`[5]` ở menu chính) và các chức năng giảng bài, câu hỏi... dùng như cũ sau khi bạn đã tải nguồn lên.

### Debug

| Triệu chứng | Cách xử lý |
|---|---|
| `Chưa có GEMINI_API_KEY` | Menu `[15]` → `[7]`, hoặc tạo file `.env` cùng thư mục với một dòng `GEMINI_API_KEY=khóa_của_bạn`. |
| Lỗi 404 / "model not found" | Tên model đã đổi hoặc bị ngừng. `[15]` → `[9]` để xem tên hiện có, `[8]` để đặt. Script bỏ qua model không tồn tại và dùng model kế tiếp trong danh sách (nếu bạn đặt nhiều model). |
| Lỗi 401/403, "API key not valid" | Key sai hoặc bị thu hồi. Tạo key mới và đặt lại ở `[7]`. |
| "hết quota (thường là quota ngày)" rồi dừng | Bình thường với gói miễn phí. Tiến độ đã lưu, chạy lại sau khi quota reset, hoặc thêm model dự phòng ở `[8]`. |
| Lặp lại "giới hạn theo phút (429)" | Tăng khoảng nghỉ: `REQUEST_DELAY=10` trong `.env` hoặc `--delay 10`. |
| Trang trả về rỗng nhiều lần | Có thể bị chặn nội dung. Thử `--no-autocontrast` hoặc giảm `--dpi`, và nhìn dòng lý do in ra bên cạnh. |
| Cảnh báo "PDF này khác với lần chạy trước" | File PDF đã bị thay đổi so với lần trước. Dùng `[4]` (`--force`) để làm lại từ đầu. |
| Chữ sai dấu hoặc số liệu nghi ngờ | Đối chiếu các trang liệt kê trong "nên soát" với sách giấy. Gemini **có thể chép sai hoặc tự sửa nhầm**, nhất là bảng và số liệu; đừng dùng kết quả cho nội dung y khoa mà không soát. |
| Đường dẫn Windows `C:\...` không nhận | Cần bản `process_book.py` đã vá hàm đổi đường dẫn (trên Windows giữ nguyên đường dẫn, trên WSL mới đổi sang `/mnt/c/...`). |

### Cần biết thêm

- Ảnh các trang sách được gửi tới dịch vụ của Google. Hãy tự đọc điều khoản của gói API bạn dùng (gói miễn phí và gói trả phí có thể khác nhau về việc dữ liệu có được dùng để cải thiện sản phẩm hay không); tôi chưa kiểm chứng điều khoản hiện hành.
- Thời gian: mặc định nghỉ 6 giây giữa hai trang, nên sách 700 trang mất khoảng 70 phút trở lên. Quota ngày của gói miễn phí có thể không đủ cho cả cuốn trong một ngày; tiến độ được lưu nên làm tiếp ngày hôm sau.


### Model, Flash-Lite, key trả phí và trang tối (cập nhật)

- **Model mặc định:** `gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3-flash-preview` (báo 404 thì tự thử `gemini-3-flash`), `gemma-4-31b-it` (nếu API không nhận system prompt thì script gộp vào lời nhắn). Đã bỏ `gemini-2.5-*` vì không còn cho tài khoản mới. Kết nối dùng API `v1` cho model ổn định; `v1beta` chỉ cho model preview, Gemma, `gemini-3-flash` và `gemini-2.5-flash-lite`. Thời gian chờ mỗi lần gọi mặc định 180 giây. Đổi bằng `GEMINI_MODEL` hoặc `--model`; xem tên model hiện có bằng `--list-models`.
- **Chọn model theo độ sáng trang:** trang sáng (đa số) chỉ dùng Flash-Lite: lỗi quá tải thì xoay giữa các model và key Flash-Lite (hoặc chờ), chỉ đổi sang model mạnh khi mọi Flash-Lite của mọi key đã khóa cứng; trang chụp tối (độ sáng trung bình dưới `--dark-threshold`, mặc định 150) ưu tiên `gemini-3.8-flash`, `gemini-3.6-flash`, rồi mới tới model khác. Hai nhóm dùng chung trạng thái quota của từng cặp (key, model).
- **Flash-Lite** chạy mỗi request 1 trang (`--lite-pages`), các model Flash lớn gộp `--pages-per-req` trang. Script giữ đúng giới hạn request/phút của từng model (Flash 5, Flash-Lite 15).
- **Key trả phí (chốt chặn cuối):** đặt `GEMINI_PAID_API_KEY` trong `.env` rồi chạy với `--allow-paid` (hoặc bật mục `[13]` trong menu `[15]`). Chỉ dùng khi mọi cặp key miễn phí đã khóa cứng vì hết quota ngày; mỗi lần chạy tối đa `--paid-max-pages` trang (mặc định 300, có thể vượt vài trang vì gộp batch); model mặc định `gemini-3.1-flash-lite`, đổi bằng `--paid-model`. Cuối phiên script in số trang, số request và số token đã dùng trên key trả phí. Mặc định TẮT.
- **Ghi nguồn từng trang:** file `output_md/.pages/<sách>/sources.json` ghi model đã chép từng trang; cuối mỗi sách log in tổng hợp theo model. Khi quota model tốt hơn hồi lại, `--redo-models gemini-3.1-flash-lite` làm lại riêng các trang do model đó chép.
- **Trang chụp thiếu sáng:** tự đo độ sáng từng trang; trang tối được tăng tương phản mạnh hơn (`--dark-threshold`, đặt 0 để tắt). Ảnh gửi đi dùng `media_resolution` cao; model nào từ chối tham số này thì tự bỏ.
- **RECITATION (Gemini từ chối chép):** một luồng chung cho mọi model và key. (1) Nhóm nhiều trang dính thì tách thành 1 trang/request. (2) Chạy **một lần** nhánh fallback trên Gemini: ảnh biến đổi nhẹ (xoay -0,4 độ, crop 2px, xoay 0,8 độ) và prompt yêu cầu chèn `[§]` sau mỗi 4 đến 5 từ để phá chuỗi trùng khớp; sau khi nhận, script xóa `[§]` và chuẩn hóa khoảng trắng. (3) Vẫn bị từ chối và có `GROQ_API_KEYS`: gửi ảnh gốc sang Groq Vision (`llama-4-maverick`, rồi `llama-4-scout`) với prompt chép nguyên văn. Nguồn trang ghi là `groq/...`, các trang đó nằm trong `_recitation_groq_fallback` của `sources.json` và được liệt kê cuối mỗi sách và cuối phiên chạy để bạn lướt kiểm tra lại dấu tiếng Việt. (4) Không có Groq hoặc Groq cũng không chép được: trang được báo "chưa chép được" và để lại cho lần chạy sau. Đặt key Groq bằng mục `[15]` trong menu `[15]` hoặc dòng `GROQ_API_KEYS=` trong `.env`; `--no-groq` để tắt, `GROQ_MODELS` để đổi model.
- **Thử lại nhiều vòng:** trang chưa xong vì lỗi tạm thời, quá tải hoặc phản hồi rỗng được làm lại nhiều vòng (`--retry-wait`, mặc định chờ 120 giây nhân số vòng, tối đa 600) cho tới khi xong, hết quota ngày, hoặc chạm `--max-runtime`. Không có `--max-runtime` thì tối đa 5 vòng (`--retry-rounds`). Trang bị RECITATION không thử lại trong vòng này.
- **Kiểm tra chất lượng offline (không dùng AI):** sau khi gộp file, và khi script nghỉ chờ quota từ 2 phút trở lên (chỉ khi có trang mới), script quét các trang đã xong và in cảnh báo ra log, đồng thời lưu vào mục `_warnings` của `sources.json`. Không tự sửa file, không gọi API. Gồm: trang ngắn bất thường, lặp dòng liên tiếp từ 3 lần, trang có từ 3 thẻ `[không rõ]` (`--max-unclear`), và chính tả: tiếng Việt kiểm tra từng âm tiết theo quy tắc ngữ âm (bắt lỗi mất dấu như `hoc` thay `học`, `tiêt` thay `tiết`, dấu sai, ký tự dính), tiếng Anh dùng từ điển `pyspellchecker`, thuật ngữ y khoa lấy từ `medical_terms.txt` (thêm từ bạn thấy bị báo nhầm). Tên riêng viết hoa giữa câu, từ viết tắt in hoa và từ có đuôi y khoa phổ biến (`-itis`, `-osis`...) được bỏ qua. Tắt bằng `--no-quality` hoặc `--no-spell`; `--merge-only` chạy lại riêng bước này mà không gọi API. Chưa tích hợp LanguageTool và Harper.
- **Prompt:** thêm quy tắc nối chữ cái phóng to đầu đoạn (drop cap), đọc xuyên vệt dạ quang, bỏ chữ ngược hằn từ mặt sau, bỏ watermark scan, số trang đứng riêng và nét bút ở lề.

---

## 13. Nguồn giáo viên (menu mục [16])

Gói này thêm transcript bài giảng (video), slide, tải nguồn lên notebook theo quy ước tên `[SGK]` / `[GV]` / `[SLIDE]`, rồi giảng bài / kiểm tra note **chỉ dựa trên nguồn đã chọn**. Hướng dẫn đầy đủ, thứ tự chạy thử và bảng debug nằm trong **`README_nguon_gv.md`**.

Mở bằng menu chính `[16]`, hoặc chạy riêng `uv run menu_nguon_gv.py`. Các script chạy **từ thư mục gốc toolkit**, ví dụ `uv run output/ask_notebook.py ca_hai "Sinh lý gan"`.

Luồng gợi ý cho mỗi môn (mỗi môn một notebook, đổi ID ở `[12]`):

0. Transcript video: `uv run input/transcripts/get_medical_transcript.py --url ...` dùng Groq Whisper rồi Gemini làm sạch (cần `GROQ_API_KEYS`, ffmpeg; chi tiết ở `README_nguon_gv.md`).
1. `[15]` chuyển sách sang Markdown → `[16]` tải lên với tiền tố `[SGK]` (`upload_sources.py --prefix SGK output_md/`).
2. Transcript video giáo viên → tải lên với tiền tố `[GV]`.
3. Slide → Markdown chỉ chữ (`*.notebooklm.md`) → tải lên với tiền tố `[SLIDE]`.
4. Giảng bài ba chế độ: `sach`, `giaovien`, `ca_hai`; thêm `kiemtra_note` để soát note của bạn.

> **Chưa kiểm chứng:** gói này chưa được chạy thật (cần key Gemini, tài khoản NotebookLM, GitHub Actions). Chạy thử từng bước, rồi báo lỗi kèm nguyên văn thông báo.


---

## 14. Giảng bài / câu hỏi tự động trên GitHub Actions

Workflow `.github/workflows/notebooklm_batch.yml` làm giống menu `[6]` đến `[10]`: đọc danh sách bài, nhờ NotebookLM làm từng bài, lưu thành file. **Mọi chức năng đều đọc `giang_bai.txt`**, mỗi lần chạy chỉ làm một chức năng. **Không commit gì vào repo**, nên thư mục của bạn không bị đụng tới.

| Thứ | Nằm ở đâu |
|---|---|
| **Kết quả mới** (file `.md`, log, tóm tắt) | **Một Release mới mỗi lần chạy**, tag `giang-YYYYMMDD-HHMM`, `hoi-...`, `mindmap-...` |
| Tiến độ (bài đã làm, để lần sau bỏ qua) | Release `giang-progress`, mỗi chức năng và notebook một file `progress-...tar.gz` bị ghi đè mỗi lần |

Phần mô tả của mỗi release liệt kê giống phần "TỔNG KẾT" khi chạy trên máy: danh sách đang dùng, số bài xong / bỏ qua / không tìm thấy / lỗi, các file mới và dung lượng, bài NotebookLM báo không tìm thấy trong nguồn. File đính kèm: `nlm_output.zip` (chỉ các file mới của lần chạy đó) và `run_log.txt` (log đầy đủ).

**Đối chiếu với menu** (Actions → *NotebookLM hàng loạt* → *Run workflow*):

| Menu | Ô trong workflow |
|---|---|
| `[6]` Giảng bài / `[7]` Câu hỏi / `[8]` Mindmap / `[9]` Infographic / `[10]` Video | `feature` = `giang` / `hoi` / `mindmap` / `infographic` / `video` |
| 1. Chạy thử bài đầu tiên | `mode` = `test` (kết quả hiện ở trang tóm tắt, không lưu, không tạo release) |
| 2. Chạy toàn bộ danh sách | `mode` = `run` |
| Nhập danh sách bài | `lessons` (xem bên dưới) |
| 3. Chạy một số bài | `only` (số thứ tự trong danh sách, ví dụ `1,3-5`) |
| 4. Làm lại toàn bộ | `mode` = `force` |
| 7. Xóa số trích dẫn `[1]` | `strip_cite` |
| 8. Thêm frontmatter | `frontmatter` |
| Câu hỏi: chế độ, định dạng Quiz | `quiz_mode`, `quiz_format` |
| Mindmap: loại | `mm_kind` |

Ngoài ra có `notebook_id` (ghi đè notebook mặc định) và `resume` (bỏ chọn thì làm lại từ đầu thay vì bỏ qua bài đã xong). Chế độ Obsidian không có trên CI vì không có vault. Mindmap, infographic, video không lưu tiến độ; muốn chạy lại thì dùng `only`.

Giảng một bài lẻ từ điện thoại theo nguồn `[SGK]`/`[GV]`/`[SLIDE]` vẫn dùng workflow `giang_bai.yml` có sẵn (mục 13).

**Nhập danh sách bài ở ô `lessons`:** các bài cách nhau bằng dấu `;` (ô nhập của GitHub chỉ có một dòng). Mỗi bài viết như trong `giang_bai.txt`, có thể kèm lưu ý riêng hoặc cờ sau dấu `|`, và dòng `## Tên chương` để nhóm bài. Ví dụ:

`## Gan; Sinh lý gan; Bệnh gan | nhấn mạnh cơ chế | khongcauhoi`

Workflow **ghi đè `giang_bai.txt`** trên máy chạy bằng danh sách này (không commit, file trong repo của bạn không đổi) và in danh sách đã đánh số ở đầu log. Ô `only` dùng số thứ tự này. Để trống ô `lessons` thì dùng `giang_bai.txt` trong repo. Chưa có bài nào thì workflow dừng ngay với thông báo rõ ràng.

**Thiết lập (một lần)**
1. **Repo public hoặc private**, đẩy toàn bộ toolkit lên.
2. **Secret `NOTEBOOKLM_AUTH_JSON`:** nội dung file `storage_state.json` của NotebookLM sau khi đăng nhập (thường nằm trong `~/.notebooklm/`). Ví dụ trên WSL: `gh secret set NOTEBOOKLM_AUTH_JSON < ~/.notebooklm/storage_state.json`. Cookie hết hạn khoảng 1 đến 2 tuần một lần, lúc đó đăng nhập lại trên máy và cập nhật secret. Nên dùng tài khoản Google riêng cho việc này.
3. **ID notebook:** điền vào ô `notebook_id` mỗi lần chạy, hoặc đặt một lần: *Settings* → *Secrets and variables* → *Actions* → *Variables* → `NOTEBOOKLM_NOTEBOOK` (hoặc secret cùng tên).
4. **Quyền ghi:** *Settings* → *Actions* → *General* → *Workflow permissions* → **Read and write permissions** (để tạo được Release).
5. *Actions* → *NotebookLM hàng loạt* → *Run workflow*. Lần đầu nên chọn `mode` = `test`.

**Lấy kết quả:** tab *Releases*, mở release mới nhất (ví dụ `giang-20261117-1530`), tải `nlm_output.zip`.

**Lưu ý**
- Secret `NOTEBOOKLM_AUTH_JSON` cho phép truy cập tài khoản NotebookLM đó. Chỉ cho người bạn tin quyền ghi vào repo.
- Release của repo public ai cũng tải được, nên nếu bài giảng sinh từ sách có bản quyền thì dùng repo private.
- Release `giang-...`, `hoi-...` tích dần theo từng lần chạy, bạn xoá bớt tay khi muốn. Đừng xoá `giang-progress`.
- OCR và PDF → Markdown vẫn chạy trên máy bạn (menu `[3]`, `[4]`, `[15]`), không còn workflow OCR trên GitHub.
