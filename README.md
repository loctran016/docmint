# Bộ công cụ NotebookLM: OCR sách, giảng bài, tạo câu hỏi

Bộ script chạy trên **WSL Ubuntu** để: (1) OCR các PDF scan, (2) nhờ NotebookLM giảng từng bài thành file Markdown, (3) nhờ NotebookLM soạn câu hỏi ôn tập cho từng bài.

> Bộ này được kiểm tra bằng thư viện giả (không gọi NotebookLM thật), nên bước `--test` ở mục 5 và 6 luôn nên chạy trước.
> `notebooklm-py` là thư viện **không chính thức**, dùng API nội bộ của Google nên có thể hỏng khi Google thay đổi. Thông tin về thư viện trong tài liệu này lấy từ trang PyPI (bản 0.8.6, tháng 10/2026). Trang đó cũng ghi rằng NotebookLM đã được đổi tên thành **Gemini Notebook** (tháng 7/2026), vẫn là cùng một dịch vụ và thư viện chạy như cũ.

## Mục lục

0. [Cách nhanh nhất: dùng menu một file](#0-cách-nhanh-nhất-dùng-menu-một-file)
1. [Cấu trúc thư mục](#1-cấu-trúc-thư-mục)
2. [Cài đặt notebooklm-py](#2-cài-đặt-notebooklm-py)
3. [Cài đặt OCR](#3-cài-đặt-ocr)
4. [OCR cả thư mục PDF](#4-ocr-cả-thư-mục-pdf)
5. [Giảng bài (bai.txt)](#5-giảng-bài-baitxt)
6. [Tạo câu hỏi (cauhoi.txt)](#6-tạo-câu-hỏi-cauhoitxt)
7. [Debug: lỗi thường gặp](#7-debug-lỗi-thường-gặp)
8. [Đưa kết quả sang Obsidian](#8-đưa-kết-quả-sang-obsidian)

---

## 0. Cách nhanh nhất: dùng menu một file

Mọi bước bên dưới đều có thể chạy từ một menu đánh số duy nhất:

```bash
cd ~/notebooklm-toolkit
bash menu.sh
```

```
┌────────────────────────────────────────────────────────────────┐
│                 BỘ CÔNG CỤ NOTEBOOKLM CHO WSL                  │
│                       Ubuntu 24.04 LTS                         │
├────────────────────────────────────────────────────────────────┤
│  Notebook ID: 623ed002…                                        │
│  uv: có | OCR: có | đăng nhập: có                              │
├────────────────────────────────────────────────────────────────┤
│ [1] Hướng dẫn (README.md)                                      │
│ [2] Cài & set-up notebooklm-py                                 │
│ [3] Cài & set-up OCR                                           │
│ [4] OCR PDFs (cả thư mục)                                      │
│ [5] Giảng bài NotebookLM (bai.txt)                             │
│ [6] Tạo câu hỏi NotebookLM (cauhoi.txt)                        │
│                        ────────────────                        │
│ [7] Đặt ID notebook                                            │
│ [8] Kiểm tra trạng thái                                        │
│ [9] Mở thư mục trong Explorer                                  │
│                        ────────────────                        │
│ [0] Thoát                                                      │
└────────────────────────────────────────────────────────────────┘
```

Thứ tự dùng lần đầu: **[2] → [3] → [7] → [4]** (tải PDF đã OCR lên NotebookLM) **→ [5] → [6]**.

- **[7] Đặt ID notebook**: có thể liệt kê notebook của bạn để xem ID, rồi dán ID hoặc cả URL.
- **[4] OCR**: Enter để dùng `input_pdfs/` (menu tự mở thư mục này trong Explorer nếu đang trống để bạn chép PDF vào), hoặc dán/kéo thả đường dẫn thư mục khác.
- **[5] và [6]** mở menu con: chạy thử 1 bài, chạy toàn bộ, chạy một số bài (vd `1,3-5`), làm lại toàn bộ, sửa danh sách bằng `nano`, và các công tắc **Xóa số trích dẫn**, **Frontmatter Obsidian** (riêng [6] còn có **Chế độ** md/quiz/both và **Định dạng Quiz**). Các công tắc được nhớ lại cho lần sau (file ẩn `.menu_settings`).
- **[8] Kiểm tra trạng thái**: hiện uv, đăng nhập, OCR, ID notebook, số file đang có, và tùy chọn kiểm tra phiên đăng nhập trực tuyến.
- **[9]**: mở nhanh các thư mục input/output bằng Explorer.
- Menu chỉ gọi lại các script ở mục 2 đến 6, nên bạn vẫn có thể chạy từng script riêng như hướng dẫn bên dưới.
- Ctrl+C dừng tác vụ đang chạy nhưng không thoát menu. Chọn `0` để thoát.

Muốn gọi menu bằng một từ ngắn ở bất kỳ đâu (zsh):

```bash
echo "alias nlm='bash ~/notebooklm-toolkit/menu.sh'" >> ~/.zshrc
source ~/.zshrc
nlm
```

---

## 1. Cấu trúc thư mục

```
notebooklm-toolkit/
├── README.md                 file này
├── menu.sh                   menu tổng hợp (chạy: bash menu.sh)
├── 1_setup_notebooklm.sh     cài uv, trình duyệt, đăng nhập Google
├── 2_setup_ocr.sh            cài ocrmypdf + tesseract tiếng Việt
├── 3_ocr_pdfs.sh             OCR cả thư mục PDF
├── 4_giang_bai.py            giảng bài theo bai.txt
├── 5_tao_cau_hoi.py          tạo câu hỏi theo cauhoi.txt
├── common.py                 hàm dùng chung (đừng xóa)
├── bai.txt                   danh sách bài cần giảng
├── cauhoi.txt                danh sách bài cần tạo câu hỏi
├── notebook_id.txt           ID notebook
├── input_pdfs/               (tự tạo) chỗ để PDF gốc, nếu muốn
├── output_ocr/               (tự tạo) kết quả OCR
├── .menu_settings            (tự tạo, file ẩn) công tắc đã chọn trong menu
└── ket_qua/                  (tự tạo) kết quả giảng bài và câu hỏi
    ├── giang_bai/
    └── cau_hoi/
```

### Chép bộ công cụ vào WSL

Tải file `notebooklm-toolkit.zip` về Windows (thư mục Downloads), rồi trong terminal Ubuntu (đổi `TEN_WINDOWS`):

```bash
cp /mnt/c/Users/TEN_WINDOWS/Downloads/notebooklm-toolkit.zip ~/
python3 -m zipfile -e ~/notebooklm-toolkit.zip ~/
cd ~/notebooklm-toolkit
ls
```

Kiểm tra `ls` thấy đủ các file ở trên. Các script `.sh` luôn chạy bằng `bash tên_file.sh` nên không cần cấp quyền thực thi.

---

## 2. Cài đặt notebooklm-py

```bash
cd ~/notebooklm-toolkit
bash 1_setup_notebooklm.sh
```

Script làm lần lượt: cài `curl` và `libatomic1` → cài `uv` → cài Chromium cho Playwright → mở cửa sổ đăng nhập Google → kiểm tra phiên đăng nhập.

- Khi hỏi mật khẩu `sudo`, gõ mật khẩu Ubuntu (màn hình **không hiện gì khi gõ**, đó là bình thường).
- Cửa sổ Chromium hiện ra: đăng nhập Google, vào tới trang NotebookLM, rồi quay lại terminal làm theo hướng dẫn (thường là nhấn Enter).
- Bước cuối phải in ra `"status": "ok"`.

**Lấy ID notebook** (có hai cách):

```bash
uvx --from notebooklm-py notebooklm list      # liệt kê notebook kèm ID
```

hoặc mở notebook trên trình duyệt, ID là đoạn cuối URL: `https://notebooklm.google.com/notebook/<ID>`.

Sau đó mở `notebook_id.txt`, dán ID (hoặc cả URL) vào một dòng riêng:

```bash
echo "ID_NOTEBOOK_CUA_BAN" > notebook_id.txt
```

> Các script `.py` dùng `uv run` nên **không cần cài thư viện thủ công**: `uv` tự tạo môi trường và cài `notebooklm-py` ở lần chạy đầu.

---

## 3. Cài đặt OCR

```bash
bash 2_setup_ocr.sh
```

Cài `ocrmypdf`, `tesseract` kèm gói ngôn ngữ tiếng Việt và tiếng Anh, `ghostscript`. Cuối script có bước kiểm tra, phải thấy `vie` và `eng` trong danh sách ngôn ngữ.

---

## 4. OCR cả thư mục PDF

Bạn có thể đặt PDF vào thư mục tùy ý. Ví dụ thư mục `Sach` trong Downloads của Windows có nhiều file PDF:

```bash
bash 3_ocr_pdfs.sh /mnt/c/Users/TEN_WINDOWS/Downloads/Sach
```

Cách khác: tạo `input_pdfs/` ngay trong thư mục toolkit, chép PDF vào, rồi chạy không tham số:

```bash
bash 3_ocr_pdfs.sh
```

Có thể **kéo thả thư mục từ Windows vào cửa sổ terminal** để dán đường dẫn dạng `C:\Users\...`. Script tự đổi sang đường dẫn WSL, nên dán thẳng sau chữ `bash 3_ocr_pdfs.sh ` là được. Nếu đường dẫn có dấu cách, bọc trong dấu nháy kép.

| Tình huống | Lệnh |
|---|---|
| Thư mục bất kỳ | `bash 3_ocr_pdfs.sh /đường/dẫn/thư_mục` |
| Chọn thư mục kết quả | `bash 3_ocr_pdfs.sh thư_mục_vào thư_mục_ra` |
| Chỉ OCR tiếng Việt | `OCR_LANGS=vie bash 3_ocr_pdfs.sh ...` |
| Giảm tải RAM/CPU | `OCR_JOBS=1 bash 3_ocr_pdfs.sh ...` |

**Kết quả**: `output_ocr/<tên file sách> - OCR.pdf`. Vài điều cần biết:

- Chỉ quét các file `.pdf` nằm trực tiếp trong thư mục (không quét thư mục con).
- File nào đã có kết quả sẽ được bỏ qua, nên có thể chạy lại thoải mái sau khi bị ngắt. File lỗi được liệt kê cuối buổi.
- Trang nào đã có chữ sẽ được giữ nguyên (`--skip-text`), chỉ OCR trang ảnh.
- Sách dày có thể mất nhiều phút đến vài chục phút. Bạn có thể để máy chạy và quay lại sau.

**Sau khi OCR xong**: xóa source cũ trên NotebookLM, tải các file `- OCR.pdf` lên, chờ xử lý xong. Rồi tự hỏi thử một câu về nội dung trang đầu sách để chắc chắn NotebookLM đã đọc được. Tôi chưa kiểm chứng giới hạn dung lượng/số từ của mỗi source hiện nay, nếu NotebookLM từ chối file quá lớn thì tách sách theo chương rồi tải từng phần.

---

## 5. Giảng bài (bai.txt)

### 5.1. Viết danh sách bài

Mỗi dòng một bài, các phần cách nhau bằng dấu `|`:

```
Tên bài | lưu ý riêng (tùy chọn) | cờ (tùy chọn)
```

Ví dụ:

```
Bài 1. Dinh dưỡng và sức khỏe
Bài 2. Carbohydrate, lipid, protid | giảng kỹ phần chuyển hóa và so sánh các nhóm chất
Liên hệ thực tế 1: Dinh dưỡng lâm sàng, định nghĩa, đào tạo, lịch sử | tóm gọn, không cần giảng sâu | khongcauhoi
```

- **Tên bài** nên chép đúng như mục lục sách, vì NotebookLM tìm bài theo tên này.
- **Lưu ý riêng** là yêu cầu thêm cho đúng bài đó, được đưa vào prompt.
- **Cờ** (đặt ở phần thứ 2 trở đi, thứ tự nào cũng được): `tomtat` / `khongtomtat` bật hoặc tắt phần "Tóm tắt nhanh", `cauhoi` / `khongcauhoi` bật hoặc tắt phần "Câu hỏi tự kiểm tra" cho riêng bài đó.
- Dòng bắt đầu bằng `#` là chú thích, dòng trống bị bỏ qua.
- Mặc định mọi bài đều có tóm tắt và câu hỏi tự kiểm tra. Đổi mặc định ở đầu file `4_giang_bai.py` (`TOM_TAT_MAC_DINH`, `CAU_HOI_MAC_DINH`) hoặc chạy với `--no-tomtat`, `--no-cauhoi`.

### 5.2. Chạy

```bash
cd ~/notebooklm-toolkit
uv run 4_giang_bai.py --test       # thử bài đầu tiên, in ra màn hình, không lưu file
uv run 4_giang_bai.py              # chạy toàn bộ bai.txt
```

Lần chạy đầu `uv` cần tải thư viện nên hơi lâu. Kết quả: `ket_qua/giang_bai/01 - <tiêu đề H1 của bài>.md`. Nếu AI không viết H1 thì tên file lấy từ `bai.txt`.

Các tùy chọn hay dùng:

| Tùy chọn | Tác dụng |
|---|---|
| `--only 2,5-7` | chỉ chạy bài thứ 2 và 5 đến 7 trong `bai.txt` |
| `--force` | làm lại cả bài đã có file |
| `--strip-cite` | xóa số trích dẫn kiểu `[1]`, `[2, 3]` khỏi file |
| `--frontmatter` | thêm khối YAML (title, tags, created) đầu file cho Obsidian |
| `--no-tomtat`, `--no-cauhoi` | tắt phần tóm tắt, câu hỏi cuối bài cho tất cả bài |
| `--file ten_file.txt` | dùng danh sách khác thay `bai.txt` |
| `--delay 3,6` | khoảng nghỉ ngẫu nhiên giữa các bài (giây) |
| `ID_NOTEBOOK` | truyền ID ngay trên dòng lệnh thay vì đọc `notebook_id.txt` |

Chạy lại sau khi bị ngắt: script nhớ bài nào xong (trong `ket_qua/giang_bai/.state.json`, file ẩn) nên chỉ làm tiếp các bài còn lại.

Nếu NotebookLM trả lời **"Không tìm thấy bài này trong nguồn"**, script không lưu file và liệt kê bài đó ở phần tổng kết. Xem mục 7.

---

## 6. Tạo câu hỏi (cauhoi.txt)

### 6.1. Viết danh sách

```
Tên bài | lưu ý riêng | tn=số câu trắc nghiệm | tl=số câu tự luận | kho=de/vua/kho
```

Mọi phần sau tên bài đều tùy chọn:

```
Bài 1. Dinh dưỡng và sức khỏe
Bài 2. Carbohydrate, lipid, protid | tập trung vào so sánh và số liệu | tn=15 | tl=3 | kho=kho
Liên hệ thực tế 1: Dinh dưỡng lâm sàng, định nghĩa, đào tạo, lịch sử | tn=5 | tl=0 | kho=de
```

Mặc định (đổi ở đầu `5_tao_cau_hoi.py`): 10 câu trắc nghiệm, 2 câu tự luận, độ khó vừa. `tl=0` nghĩa là không có tự luận.

### 6.2. Ba chế độ

```bash
uv run 5_tao_cau_hoi.py --test            # thử bài đầu tiên, in ra màn hình
uv run 5_tao_cau_hoi.py                   # chế độ md (mặc định)
uv run 5_tao_cau_hoi.py --mode quiz       # dùng tính năng Quiz của NotebookLM
uv run 5_tao_cau_hoi.py --mode both       # cả hai
```

- **`md`**: NotebookLM viết đề bằng Markdown: H1 tiêu đề, H2 "Phần I. Trắc nghiệm", H2 "Phần II. Tự luận", H2 "Đáp án và giải thích" ở cuối. Trong Obsidian bạn có thể gập mục "Đáp án" lại để tự làm bài. Đây là chế độ ổn định nhất vì dùng cùng cơ chế hỏi đáp với giảng bài.
- **`quiz`**: tạo Quiz bằng tính năng riêng của NotebookLM, rồi tải về dạng `markdown` (mặc định), `json` hoặc `html` bằng `--quiz-format`. File có đuôi `(Quiz)`. Quiz tạo ra sẽ cũng xuất hiện trong mục Studio của notebook trên web.

### 6.3. Những điều chưa kiểm chứng ở chế độ quiz

Trang PyPI xác nhận thư viện có `generate_quiz`, `wait_for_completion` và `download_quiz` (xuất JSON, Markdown, HTML), nhưng tôi chưa xác nhận được:

- Hàm tạo Quiz có nhận hướng dẫn riêng để chỉ hỏi về một bài hay không. Script tự kiểm tra: nếu thư viện không nhận hướng dẫn, nó in cảnh báo rằng Quiz sẽ lấy từ toàn bộ nguồn.
- Khi một notebook có nhiều Quiz, `download_quiz` có tải đúng quiz vừa tạo hay không. Script tải ngay sau khi tạo để giảm rủi ro, nhưng bạn nên mở thử vài file xem có đúng bài không.
- Số câu và độ khó của Quiz (`tn`, `kho`) **không áp dụng cho chế độ quiz**, chỉ áp dụng cho chế độ `md`.

Để xem tham số thật của hàm trong phiên bản bạn đang dùng:

```bash
uv run 5_tao_cau_hoi.py --quiz-info
```

Nếu cần chỉnh số câu, độ khó cho Quiz, dán kết quả lệnh này cho tôi hoặc xem `notebooklm generate quiz --help`.

Các tùy chọn khác (`--only`, `--force`, `--strip-cite`, `--frontmatter`, `--delay`, `ID_NOTEBOOK`) giống mục 5. Kết quả nằm trong `ket_qua/cau_hoi/`.

---

## 7. Debug: lỗi thường gặp

Các lỗi dưới đây đều đã xảy ra trong quá trình thiết lập.

### Cài đặt

| Triệu chứng | Nguyên nhân và cách xử lý |
|---|---|
| `sudo: 3 incorrect password attempts`, sau đó `apt` không chạy | Mật khẩu `sudo` là mật khẩu **Ubuntu** bạn đặt lúc cài WSL, không nhất thiết trùng mật khẩu Windows. Khi gõ không hiện ký tự. Quên mật khẩu: mở PowerShell, chạy `wsl -u root`, rồi `passwd TEN_USER_UBUNTU`, đặt mật khẩu mới, `exit`. |
| `error while loading shared libraries: libatomic.so.1` | Thiếu thư viện hệ thống (thường do lệnh `apt install` ở bước trước bị lỗi). Chạy `sudo apt-get install -y libatomic1`, rồi chạy lại `bash 1_setup_notebooklm.sh`. |
| `uv: command not found` ngay sau khi cài | Chạy `source $HOME/.local/bin/env` hoặc mở lại terminal. |
| Cảnh báo `An executable named playwright is not provided by package notebooklm-py` | Chỉ là cảnh báo khi dùng sai cách gọi `uvx`. `1_setup_notebooklm.sh` đã dùng cách đúng. |
| `TypeError: onExit is not a function` khi cài Chromium trên Linux | Trang PyPI của thư viện có hướng dẫn riêng cho lỗi này ở mục "Linux" trong `docs/troubleshooting.md` của repo `teng-lin/notebooklm-py`. |
| Không mở được cửa sổ trình duyệt khi `login` | Cần WSLg (Windows 11) và `echo $DISPLAY` phải in giá trị như `:0`. Nếu không có, xem mục "Không mở được trình duyệt" bên dưới. |

#### Không mở được trình duyệt trong WSL

Cách này dựa trên việc thư viện lưu phiên đăng nhập trong thư mục `.notebooklm` ở thư mục home của bạn. Tôi chưa kiểm chứng điều này trên Windows.

1. Trong PowerShell (Windows): `winget install astral-sh.uv`, mở lại PowerShell, rồi chạy `uvx --from "notebooklm-py[browser]" playwright install chromium` và `uvx --from "notebooklm-py[browser]" notebooklm login`.
2. Quay lại Ubuntu, chép phiên đăng nhập: `cp -r /mnt/c/Users/TEN_WINDOWS/.notebooklm ~/`
3. Kiểm tra: `uvx --from "notebooklm-py[browser]" notebooklm auth check --test --json`.

Thư viện còn có cách đăng nhập khác (nhập cookie từ trình duyệt đã đăng nhập, hoặc master token), xem phần Authentication trong tài liệu của nó.

### Menu

| Triệu chứng | Cách xử lý |
|---|---|
| Khung menu bị lệch hoặc ký tự `┌ ─ │` hiện lạ | Terminal đang dùng font không có ký tự vẽ khung. Dùng Windows Terminal với font như Cascadia Mono, Consolas hoặc font Nerd Font. |
| Chọn "Sửa danh sách" báo `nano: command not found` | `sudo apt-get install -y nano`, hoặc chạy menu với editor khác: `EDITOR=vim bash menu.sh`. |
| Chọn mở thư mục mà Explorer không hiện | Kiểm tra `explorer.exe .` chạy được từ terminal Ubuntu. Explorer thường trả mã lỗi 1 dù đã mở được, đó là bình thường. |
| Báo "Chưa cài uv" / "Chưa có ID notebook" khi chạy [5] hoặc [6] | Chọn [2] để cài (hoặc `source $HOME/.local/bin/env`), chọn [7] để đặt ID. |
| Muốn xóa các công tắc đã nhớ | Xóa file ẩn `.menu_settings`. |

### Chạy script

| Triệu chứng | Nguyên nhân và cách xử lý |
|---|---|
| Script chạy mà **không in gì**, hoặc `SyntaxError ... cd ~/notebooklm` | File `.py` bị rỗng hoặc bị dán lẫn lệnh terminal khi tạo file bằng `cat > ... << EOF`. Dùng đúng file trong zip, kiểm tra bằng `wc -l 4_giang_bai.py` (phải vài trăm dòng, không phải 0). |
| `Chưa có ID notebook` | Ghi ID vào `notebook_id.txt` (không để dấu `#` ở đầu dòng ID) hoặc truyền ID trên dòng lệnh. |
| NotebookLM trả lời **"Không tìm thấy bài này trong nguồn"**, hoặc bảo nguồn chỉ có một số trang (ví dụ chỉ trang 154 đến 202) | PDF là bản scan chưa có lớp chữ, hoặc tên bài trong `bai.txt` không khớp sách. Xem bên dưới. |
| Nội dung bài giảng "trông hợp lý" nhưng không đúng sườn sách | NotebookLM không thấy bài đó nên ghép từ các bài khác. Prompt của bộ này đã yêu cầu nó từ chối thay vì ghép, nên bài sai sẽ báo "không tìm thấy" thay vì cho ra nội dung giả. Nếu vẫn gặp, đọc mục tiêu đề so với mục lục sách. |
| `Lỗi (lần 1/3): ...` rồi tự thử lại | Có thể do mạng, phiên đăng nhập hết hạn hoặc bị giới hạn tốc độ. Đợi và chạy lại; bài lỗi sẽ được thử lại. Nếu lỗi mang tính xác thực, đăng nhập lại: `uvx --from "notebooklm-py[browser]" notebooklm login`. |
| Hết thời gian chờ (timeout) | Câu trả lời dài. Tăng `TIMEOUT` ở đầu file `.py`. |
| Dòng "bạn đã quên cung cấp đoạn văn bản nguồn trong cặp ngoặc nhọn" | Là câu trả lời cho một prompt cũ còn chứa `{...}` chưa được thay. Bộ script này luôn thay đủ, nên chỉ cần bỏ qua câu trả lời cũ trong lịch sử chat. |
| `DeprecationWarning: Awaiting NotebookLMClient.from_storage(...)` | Bản script cũ. Bản trong bộ này đã dùng cú pháp mới. |
| Số trích dẫn `[1]`, `[2, 3]` dính trong file | Thêm `--strip-cite`. |
| Bài sau bị lẫn nội dung bài trước | Mỗi prompt đã có câu "bỏ qua các câu hỏi trước". Nếu vẫn lẫn, xóa lịch sử chat của notebook trên web rồi chạy lại với `--force`. |

#### Khi NotebookLM không thấy các trang đầu sách

Xem trước (preview) của nguồn hiển thị **hình ảnh** trang, nên bạn thấy chữ rõ ràng không có nghĩa NotebookLM đã trích được chữ. Cách kiểm tra:

1. Hỏi tay trong NotebookLM một câu về nội dung có thật ở trang đầu (ví dụ một mục cụ thể bạn đọc được trong ảnh xem trước). Nếu nó bảo không thấy, trang đó chưa có lớp chữ.
2. Kiểm tra PDF trong WSL, xem bao nhiêu trang không có chữ:

```bash
cd ~/notebooklm-toolkit
cp "/mnt/c/Users/TEN_WINDOWS/Downloads/TEN_FILE.pdf" sach.pdf
uv run --with pypdf python - << 'EOF'
from pypdf import PdfReader
r = PdfReader("sach.pdf")
trong = [i + 1 for i, p in enumerate(r.pages) if len((p.extract_text() or "").strip()) < 50]
print("Tổng số trang:", len(r.pages), "| Trang không có chữ:", len(trong))
print("Các trang đầu không có chữ:", trong[:30])
EOF
```

3. Nếu nhiều trang không có chữ: làm mục 4 (OCR), rồi **xóa source cũ và tải bản OCR lên**.
4. Nếu bản OCR có đủ chữ mà NotebookLM vẫn thiếu trang: file có thể quá lớn. Tách sách theo chương rồi tải từng phần lên, vẫn dùng chung một notebook.

### OCR

| Triệu chứng | Cách xử lý |
|---|---|
| `Chưa cài ocrmypdf` | Chạy `bash 2_setup_ocr.sh`. |
| `Không thấy thư mục` | Kiểm tra đường dẫn. Đường dẫn Windows chứa dấu cách cần bọc dấu nháy kép. |
| Thiếu gói ngôn ngữ | `sudo apt-get install -y tesseract-ocr-vie tesseract-ocr-eng` |
| Máy treo hoặc hết RAM khi OCR sách dày | Chạy `OCR_JOBS=1 bash 3_ocr_pdfs.sh ...`. |
| Một file bị `[lỗi] không OCR được` | File hỏng, bị mã hóa hoặc có mật khẩu. Thử mở bằng trình đọc PDF, lưu lại thành bản mới rồi OCR lại. |
| Chữ sau OCR sai dấu | Chất lượng ảnh scan kém. Kiểm tra vài trang bằng cách mở PDF OCR và bôi đen chữ. |

---

## 8. Đưa kết quả sang Obsidian

Mở thư mục kết quả bằng Explorer:

```bash
cd ~/notebooklm-toolkit/ket_qua && explorer.exe .
```

Hoặc chép thẳng vào vault (thay đường dẫn cho đúng):

```bash
cp ~/notebooklm-toolkit/ket_qua/giang_bai/*.md "/mnt/c/Users/TEN_WINDOWS/Documents/ObsidianVault/Dinh duong/"
cp ~/notebooklm-toolkit/ket_qua/cau_hoi/*.md   "/mnt/c/Users/TEN_WINDOWS/Documents/ObsidianVault/Dinh duong/"
```

Gợi ý:

- Chạy với `--frontmatter` để mỗi file có sẵn `title`, `tags`, `created` cho Obsidian.
- Tên file đã bỏ các ký tự Obsidian không cho dùng trong tên (`# ^ [ ] | : / \ ? * " < >`).
- File `.state.json` trong `ket_qua/*/` là file ẩn dùng để nhớ tiến độ. Đừng chép nó vào vault. Xóa nó (hoặc dùng `--force`) nếu muốn làm lại tất cả từ đầu.
- Số trích dẫn từ NotebookLM giữ lại dạng `[1]`, `[2, 3]` trừ khi bạn dùng `--strip-cite`. Nếu muốn xóa sau khi đã có file, dùng tìm/thay thế regex trong Obsidian: `\s?\[\d+(?:\s*[,\-–]\s*\d+)*\]`.

---

## Phụ lục: chạy nhanh toàn bộ quy trình (không dùng menu)

```bash
cd ~/notebooklm-toolkit
bash 1_setup_notebooklm.sh                      # một lần
bash 2_setup_ocr.sh                             # một lần
bash 3_ocr_pdfs.sh /mnt/c/Users/TEN/Downloads/Sach
# -> tải các file output_ocr/*- OCR.pdf lên NotebookLM, xóa source cũ
echo "ID_NOTEBOOK" > notebook_id.txt
nano bai.txt                                    # sửa danh sách bài
uv run 4_giang_bai.py --test
uv run 4_giang_bai.py --frontmatter
nano cauhoi.txt                                 # sửa danh sách bài cần ra đề
uv run 5_tao_cau_hoi.py --test
uv run 5_tao_cau_hoi.py --frontmatter
```
