# Bộ skill bệnh án sinh viên (phần I–VI), bản v2

## Gồm những gì
- `skills/benh-an-trich-xuat`: phần I–V (hành chính, lý do nhập viện, bệnh sử có one-liner và mốc thời gian, tiền căn, lược cơ quan), đối chiếu checklist.
- `skills/benh-an-ma-tran-nguyen-nhan`: **biện luận theo bảng của bộ môn** (hỏi bệnh/khám/tiền căn × chẩn đoán ứng viên, hàng "lựa chọn chẩn đoán"). Giữ tên thư mục cũ để code không phải đổi.
- `skills/benh-an-kham-lam-sang`: đề nghị khám và nghiệm pháp từ các dòng chẩn đoán và loại trừ của nguyên nhân còn nghi.
- `skills/benh-an-trich-kien-thuc`: trích kiến thức từ một chương sách vào file kiến thức.
- `checklists/`: câu hỏi để không bỏ sót triệu chứng (`dau-nguc.md`, `kho-tho.md`), `CAUSES.md` (mã nguyên nhân dùng chung), `INDEX.md`.
- `knowledge/`: kiến thức theo nguyên nhân từ sách của bạn. `dau-nguc.md` (từ Bài 1), `_TEMPLATE.md`, `INDEX.md`, `sources/` (văn bản chương), `_old/` (bản v1).
- `tools/kiem_tra_kien_thuc.py`: kiểm tra trích dẫn có thật trong chương, mã hợp lệ, giá trị Loại hợp lệ.

## Cấu trúc kiến thức (theo nguyên nhân)
Mỗi nguyên nhân có một khối. Mỗi dòng gắn Nguồn dữ kiện (BS bệnh sử, TC tiền căn, K khám, CLS) và Loại (G gợi ý, C chẩn đoán, L loại trừ, IN ít nghĩ, LY lưu ý, CPL chưa phân loại). Khám lâm sàng được đề nghị từ các dòng K loại C và L của nguyên nhân còn nghi.

## Chạy tay (khi code chưa chạy được)
Chạy 3 lượt với DeepSeek hoặc Claude. Mỗi lượt dán: SKILL.md của bước đó, `checklists/CAUSES.md`, checklist và file kiến thức của triệu chứng, rồi dữ liệu của bước:
1. `benh-an-trich-xuat` + bệnh án ẩn danh.
2. `benh-an-ma-tran-nguyen-nhan` + kết quả lượt 1.
3. `benh-an-kham-lam-sang` + kết quả lượt 2 + bệnh án (để lấy phần khám).
Sau đó dán cả bốn thứ (bệnh án, 3 kết quả) sang Claude để kiểm tra chéo và viết tiếp VII–XIII.

## Thêm kiến thức cho một triệu chứng
1. Lưu văn bản chương thành `knowledge/sources/<trieu-chung>_<bai>.txt` (nên dùng file gốc hoặc OCR của bạn).
2. Đưa AI: skill `benh-an-trich-kien-thuc` + `knowledge/_TEMPLATE.md` + `checklists/CAUSES.md` + checklist của triệu chứng + văn bản chương. Lưu kết quả thành `knowledge/<trieu-chung>.md`.
3. Duyệt "mã đề xuất" AI nêu, thêm vào `checklists/CAUSES.md`; thêm một dòng vào `knowledge/INDEX.md`.
4. Chạy: `python tools/kiem_tra_kien_thuc.py knowledge/<trieu-chung>.md --nguon knowledge/sources/<trieu-chung>_<bai>.txt --causes checklists/CAUSES.md`
5. Duyệt cột Loại, các dòng "[mã suy ra]" và CPL; xong thì đổi `trang_thai` thành DA_RA_SOAT.

## Lưu ý
- Kiểm tra tự động chỉ chứng minh trích dẫn có trong sách, không chứng minh sách đúng hay Loại được xếp hợp lý.
- Bản chép chương trong `knowledge/sources/dau-nguc_bai1.txt` do Claude chép lại từ đoạn bạn gửi; hãy thay bằng file gốc rồi chạy lại kiểm tra.
- `benh_an_sv.py` hiện chỉ nạp checklist và CAUSES, chưa nạp `knowledge/`. Xem HUONG_DAN_TIEP_THEO.md để nối.
