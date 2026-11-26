# Hướng dẫn tiếp theo: từ lúc sửa xong benh_an_sv.py đến giờ

## 1. Tóm tắt những gì đã làm kể từ đó
1. **Chọn checklist theo lý do nhập viện** (đã xong, trong `benh_an_sv.py`): tách mục "Lý do nhập viện", DS chọn một hay nhiều checklist; triệu chứng chưa có checklist được ghi riêng.
2. **Đánh giá hai phân tích của Gemini:** giữ kiến trúc docmint hiện tại. Ý lấy sau: lớp hậu kiểm (code kiểm tra trích dẫn/ID), skill `case-reviewer` cho bước Claude, cách chia nhóm cận lâm sàng cho mục XI (nếu khớp mẫu giảng viên).
3. **Tách "hỏi cho đủ" và "định hướng chẩn đoán":** checklist chỉ để không bỏ sót. Định hướng chẩn đoán phải lấy từ sách của bạn, mỗi dòng có trích nguyên văn. Bài 1 Tiếp cận đau ngực đã được đưa vào, có tool kiểm tra trích dẫn.
4. **Slide thầy Huỳnh Mạnh Tiến (slide 1–14 là phần chung):** có bảng biện luận (hỏi bệnh/khám/tiền căn × chẩn đoán ứng viên, +++ đến --, hàng lựa chọn chẩn đoán), cách viết one-liner, mốc thời gian, tiền căn, đặt vấn đề, chẩn đoán = bệnh chính + bệnh nền.
5. **Nguyên tắc bạn chốt:** kiến thức xếp theo từng nguyên nhân; bệnh sử và tiền căn đều có ba loại dấu hiệu (gợi ý, chẩn đoán, loại trừ); sau đó mới đề nghị khám và nghiệm pháp từ mục chẩn đoán và loại trừ.
6. **Hôm nay (bản v2 trong gói):** file kiến thức đau ngực xếp lại theo nguyên nhân, mẫu kiến thức mới, tool kiểm tra mới, skill trích kiến thức mới, skill biện luận theo bảng của thầy, skill khám theo nguyên nhân còn nghi, skill trích xuất thêm one-liner và mốc thời gian.

## 2. Hiện trạng
| Phần | Trạng thái |
|---|---|
| `benh_an_sv.py` | Có sẵn. Copilot chạy thấy chưa ổn, đang chờ log của bạn. **Mình không sửa file này** vì bạn có thể đã chỉnh cục bộ. |
| Checklist đau ngực, khó thở | Có. Thẻ trong checklist là NHÁP (mình gắn), không dùng để biện luận nữa. |
| Kiến thức đau ngực (từ sách) | Có, xếp theo nguyên nhân. Trích dẫn đã kiểm tra tự động. **Cột Loại do quy tắc tự động xếp, bạn cần duyệt.** Chưa có dòng L (loại trừ) vì Bài 1 không dùng chữ "loại trừ" cho một nguyên nhân cụ thể. |
| Wells, Framingham | Chưa có. Khối tiêu chuẩn để trống chờ nguồn của bạn. |
| Code nạp `knowledge/` | **Chưa có.** Làm bằng Prompt B bên dưới. |
| Kiến thức/checklist tiêu hóa (XHTH, vàng da, bụng to, tiêu chảy–táo bón, sụt cân) | Chưa làm. Nội dung có trong slide thầy từ slide 15 trở đi. |
| Hậu kiểm đầu ra trong code, `case-reviewer` | Chưa làm, để sau. |

## 3. Bạn cần làm, theo thứ tự
**Bước 1. Đưa gói v2 vào repo.** Tải `benh-an-skills.zip`, giải nén. Chép `skills/`, `checklists/`, `knowledge/`, `tools/` vào `config/benh_an_sv/` (ghi đè bản cũ). Không chép dữ liệu bệnh nhân vào thư mục này. `HUONG_DAN_TIEP_THEO.md` và `README.md` để ngoài cũng được.

**Bước 2. Làm cho pipeline để lại log.** Dán Prompt A cho Copilot. Mục đích: lần chạy sau tự ghi file log, bạn không phải chép terminal.

**Bước 3. Chạy thử một bệnh án đã ẩn danh** (PDF từ Word). Lỗi thì lấy: `benh_an_sv.log` và `meta.json` trong thư mục kết quả. Chạy được thì xem `01_trich_xuat.md`, `02_ma_tran.md`, `03_kham.md`.

**Bước 4. Nối kiến thức vào code.** Khi bước 3 chạy được, dán Prompt B cho Copilot.

**Bước 5. Duyệt file kiến thức đau ngực** (`knowledge/dau-nguc.md`):
- Cột Loại: C đang nhiều (105 dòng) vì mọi dòng từ mục 6.x, từ Bảng 2–3 và cận lâm sàng đều bị xếp C. Bạn xem dòng nào nên là G.
- Các dòng ghi "[mã suy ra]".
- Xong thì đổi `trang_thai` thành DA_RA_SOAT.

**Bước 6. Đưa nguồn để mình trích tiếp** (nhắn "hãy tạo" kèm file hoặc ảnh chụp):
- Bài về suy tim (có Framingham) và thuyên tắc phổi (có Wells): để có khối tiêu chuẩn có quy tắc và dấu hiệu loại trừ thật.
- Bài khó thở, để khớp với checklist khó thở.
- Phần tiêu hóa của slide thầy: cần thêm mục "các bước tiếp cận" và "phân độ" vào mẫu kiến thức.

**Bước 7. Test đầu-cuối:** chạy một bệnh án có đáp án, gửi `04_gui_claude.md` sang Claude để kiểm tra chéo.

## 4. Prompt A (dán cho Copilot): log và chẩn đoán lỗi
```
Mục tiêu: khi chạy mục menu "Phân tích bệnh án sinh viên" (src/llm/benh_an_sv.py), mọi lỗi phải để lại log đầy đủ để người dùng gửi lại mà không cần chép terminal.
Tuân theo Copilot instructions hiện có của repo. Không thêm mục menu. Không đọc hay sửa dữ liệu trong workspace/. Không đổi logic xử lý trong benh_an_sv.py (file có thể đã sửa cục bộ): chỉ thêm tối thiểu ở lớp menu gọi run_pipeline().
1. Trước khi gọi run_pipeline(), cấu hình logging ghi vào file <thư mục kết quả của bệnh án>/benh_an_sv.log ở mức DEBUG (console mức INFO). Tạo thư mục nếu chưa có.
2. Bọc lời gọi run_pipeline() bằng try/except Exception: ghi traceback đầy đủ vào log; in ra console một dòng tóm tắt (loại lỗi + thông báo) kèm đường dẫn file log. Vẫn in thông báo tiếng Việt cho BenhAnError và ScannedPdfError như cũ.
3. Ghi vào đầu log phần "môi trường": phiên bản Python; đường dẫn tuyệt đối của file benh_an_sv.py đang được import; giá trị Config (skills_dir tuyệt đối và có tồn tại hay không, model, effort); biến DEEPSEEK_API_KEY có hay không (chỉ ghi có/không, KHÔNG ghi giá trị); phiên bản thư viện openai và pymupdf (hoặc "chưa cài"); danh sách file trong skills_dir/skills và skills_dir/checklists.
4. Báo cáo lại các file đã sửa kèm diff ngắn.
```

## 5. Prompt B (dán cho Copilot): nối thư mục kiến thức
Chỉ dán khi Bước 3 đã chạy được.
```
Nối thư mục kiến thức vào src/llm/benh_an_sv.py. Đây là thay đổi nhỏ; file có thể có sửa đổi cục bộ nên chỉ thêm, không viết lại cả file. Tuân theo Copilot instructions hiện có của repo, không thêm mục menu.
Bối cảnh: skills_dir (config/benh_an_sv) nay có thêm thư mục knowledge/ cùng cấp với skills/ và checklists/. File kiến thức của một triệu chứng có cùng tên file với checklist (vd checklists/dau-nguc.md tương ứng knowledge/dau-nguc.md). Đầu file kiến thức có frontmatter với trường trang_thai (NHAP hoặc DA_RA_SOAT).
1. Trong run_pipeline(), sau khi có danh sách checklist đã chọn, đọc knowledge/<tên file> cho từng checklist. Thiếu file kiến thức thì bỏ qua và ghi cảnh báo "chưa có kiến thức cho <triệu chứng>" (không báo lỗi).
2. Trong _stage_user(): ở bước 02_ma_tran và 03_kham thêm các thẻ <KIEN_THUC file="..."> chứa nội dung file kiến thức, đặt sau các thẻ <CHECKLIST>. Bước 01_trich_xuat không cần kiến thức.
3. GLOBAL_RULES: thêm một dòng: "Kiến thức theo nguyên nhân nằm trong <KIEN_THUC>; chỉ dùng các dòng có trong đó; trạng thái NHAP nghĩa là kiến thức chưa được người dùng duyệt."
4. Đọc trang_thai từ frontmatter, ghi vào meta.json (khoá knowledge_status: {tên file: trạng thái}).
5. build_claude_bundle() / 04_gui_claude.md: thêm các thẻ <KIEN_THUC> để Claude kiểm tra chéo.
6. Báo cáo lại các file đã sửa kèm diff ngắn.
```

## 6. Khi quay lại, gửi mình
- Nội dung `benh_an_sv.log` (hoặc ảnh chụp đoạn lỗi) và `meta.json`.
- Ba file kết quả `01`, `02`, `03` nếu chạy được.
- Nhận xét của bạn về cột Loại trong `knowledge/dau-nguc.md` (dòng nào sai).
- Nguồn cho Bước 6.

## 7. Chạy tay trên điện thoại (khi code chưa chạy)
Xem mục "Chạy tay" trong `README.md`. Cách này không cần code: dán SKILL.md, checklist, file kiến thức và bệnh án ẩn danh vào DeepSeek hoặc Claude theo 3 lượt.
