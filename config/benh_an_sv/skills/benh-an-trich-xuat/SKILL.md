---
name: benh-an-trich-xuat
description: Trích xuất và kiểm tra độ đầy đủ cho phần I–V của bệnh án sinh viên (hành chính, lý do nhập viện, bệnh sử, tiền căn bản thân và gia đình, lược qua các cơ quan) bằng cách đối chiếu từng mục với checklist triệu chứng có sẵn trong thư mục checklists/. Dùng bất cứ khi nào người dùng đưa bệnh án/ghi chép hỏi bệnh và muốn lập timeline bệnh sử, kiểm tra còn thiếu gì, chọn checklist, hoặc nhắc tới "bệnh sử", "tiền căn", "lược qua các cơ quan", "lý do nhập viện", "checklist".
---

# Trích xuất & kiểm tra bệnh án (phần I–V)

Ngôn ngữ trả lời: tiếng Việt. Ở bước này CHƯA chẩn đoán, CHƯA phân tích yếu tố nguy cơ.

## Nguyên tắc chống bịa (bắt buộc)
1. Chỉ dùng dữ kiện có trong văn bản bệnh án. Mọi trạng thái CÓ/KHÔNG phải kèm **trích nguyên văn** (tối đa 1 câu) từ bệnh án.
2. Bệnh án im lặng về một mục → **CHƯA KHAI THÁC**. Chỉ ghi KHÔNG khi bệnh án nêu rõ phủ định (vd "không sốt").
3. Chỉ hỏi/kiểm tra các mục có trong checklist. Mục cần thêm ngoài checklist ghi riêng, gắn nhãn **[NGOÀI CHECKLIST]**.
4. Triệu chứng không có checklist trong INDEX → nói rõ "chưa có checklist cho <triệu chứng>", không tự bịa checklist.
5. Không suy luận chẩn đoán. Không sửa hay làm đẹp lời bệnh nhân.

## Quy trình
**Bước 0 — Chọn checklist.** Đọc `checklists/INDEX.md`. Từ lý do nhập viện và bệnh sử, chọn checklist theo từng triệu chứng chính, rồi đọc các file đó. Khi chọn nhiều checklist, gộp theo cột "Gộp với": mục trùng chỉ ghi một lần (ví dụ DN-11 và KT-01..06 cùng là khó thở).

**Bước 1 — Hành chính.** Ghi tuổi, giới, nghề nghiệp, nơi ở. Thiếu mục nào → CHƯA KHAI THÁC. Chưa phân tích.

**Bước 2 — Lý do nhập viện (kiểm tra hai chiều).**
- Trích nguyên văn than phiền chính của bệnh nhân.
- Chiều 1: lý do này gợi ý dùng checklist nào.
- Chiều 2: đối chiếu bệnh sử, triệu chứng nào thật sự xuất hiện sớm/nổi bật nhất. Nếu không khớp với lý do nhập viện → gắn nhãn **LỆCH** và nêu cả hai.

**Bước 3 — Bệnh sử.**
- Bảng timeline: mốc thời gian | triệu chứng cơ năng | hoàn cảnh khởi phát | diễn tiến | trích dẫn.
- Xác nhận hoàn cảnh khởi phát của từng triệu chứng chính (mục "hoàn cảnh khởi phát" trong checklist).
- Bảng đối chiếu: ID | nội dung | CÓ/KHÔNG/CHƯA KHAI THÁC | trích dẫn.

**Bước 4 — Tiền căn bản thân và gia đình.** Cùng định dạng bảng với bước 3, dùng các mục tiền căn (nội khoa, ngoại khoa, thói quen, dị ứng, gia đình) của checklist đã chọn.

**Bước 5 — Lược qua các cơ quan.** Với mỗi triệu chứng cơ năng ở bước 3: còn / hết / CHƯA KHAI THÁC. Sau đó liệt kê các cơ quan còn lại theo bệnh án. Chỉ ghi nhận, không suy diễn.

**Bước 6 — Tổng kết.**
- Đếm số mục CÓ / KHÔNG / CHƯA KHAI THÁC.
- Danh sách **Cần hỏi lại bệnh nhân**, ưu tiên mục CHƯA KHAI THÁC có nhiều mã trong cột thẻ nhất (mục phân biệt được nhiều nguyên nhân).
- Danh sách mâu thuẫn (nhãn LỆCH, thời gian không khớp).

## Định dạng đầu ra
Đánh số theo La Mã I–V như bệnh án. Cuối cùng có mục "Dữ liệu cho bước sau": danh sách ID đã CÓ và ID đã KHÔNG (để skill `benh-an-ma-tran-nguyen-nhan` dùng).
