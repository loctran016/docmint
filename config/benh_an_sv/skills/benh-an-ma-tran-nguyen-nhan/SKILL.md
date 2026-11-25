---
name: benh-an-ma-tran-nguyen-nhan
description: Lập ma trận nguyên nhân × triệu chứng và sinh giả thuyết (một bệnh giải thích tất cả hay hai bệnh chồng nhau) cho bệnh nhân có nhiều triệu chứng chồng lấp như đau ngực + khó thở. Dùng sau khi đã trích xuất bệnh sử/tiền căn, hoặc khi người dùng hỏi "gộp hay tách chẩn đoán", "nguyên nhân nào giải thích được triệu chứng nào", "nghĩ nhiều/ít nghĩ/loại trừ", "chẩn đoán phân biệt" ở giai đoạn trước khi khám.
---

# Ma trận nguyên nhân × triệu chứng

Ngôn ngữ: tiếng Việt. Đầu vào: kết quả của skill `benh-an-trich-xuat` (danh sách ID CÓ/KHÔNG) và các file checklist đã chọn. Đầu ra là **giả thuyết trước khám**, không phải chẩn đoán.

## Nguyên tắc chống bịa
1. Chỉ dùng mã nguyên nhân trong `checklists/CAUSES.md`. Nguyên nhân khác → ghi riêng **[NGOÀI DANH SÁCH — cần giảng viên/giáo trình xác nhận]**.
2. Quan hệ "nguyên nhân gây triệu chứng" lấy từ mục D của từng checklist; quan hệ "dữ kiện ủng hộ/ít nghĩ" lấy từ cột thẻ. Không tự thêm quan hệ. Nếu thẻ ghi NHÁP, nhắc người dùng đối chiếu giáo trình.
3. Mọi nhận định phải dẫn ID dữ kiện (vd DN-03, KT-05). Dữ kiện CHƯA KHAI THÁC không được dùng làm bằng chứng cho hay chống.

## Quy trình
1. **Danh sách triệu chứng chính** (có ID, từ bước trích xuất).
2. **Ma trận:** hàng = nguyên nhân (hợp của mục D các checklist liên quan), cột = triệu chứng chính; ô ✔ nếu mã nằm trong mục D của checklist triệu chứng đó. Cột cuối = số triệu chứng được giải thích.
3. **Mức hỗ trợ từng nguyên nhân:** dữ kiện ủng hộ (ID, từ cột "Nếu CÓ"), dữ kiện ít nghĩ (ID, từ cột "Nếu KHÔNG" khi bệnh án ghi rõ KHÔNG), yếu tố nguy cơ (tuổi, giới, nghề, nơi ở, tiền căn, thói quen).
4. **Sinh giả thuyết song song:**
   - **H-U (thống nhất):** một bệnh giải thích mọi triệu chứng chính. Liệt kê các ứng viên.
   - **H-D (hai bệnh chồng):** cặp bệnh mà mỗi bệnh giải thích phần còn lại và hợp lại giải thích hết. Luôn nêu ít nhất một H-D để so sánh.
5. **Quy tắc chọn:** ưu tiên H-U nếu giải thích hết và không có dữ kiện mâu thuẫn. Chuyển sang H-D khi: (a) có triệu chứng mà H-U không giải thích, (b) có tiền căn/yếu tố nguy cơ mạnh cho bệnh thứ hai, (c) có dữ kiện đặc trưng không khớp H-U. Nếu chưa đủ dữ kiện → nói thẳng "chưa đủ để chọn", không ép chọn.
6. **Cần tìm khi khám:** với mỗi cặp giả thuyết cạnh tranh, lấy từ mục E của checklist các dấu hiệu phân biệt (ghi mã nguyên nhân nó ủng hộ/ít nghĩ).

## Định dạng đầu ra
Ma trận → bảng nguyên nhân (ủng hộ/ít nghĩ/yếu tố nguy cơ, kèm ID) → danh sách H-U và H-D → bảng "Dấu hiệu cần tìm khi khám để phân biệt" → mục "Chưa khai thác nhưng quan trọng".
