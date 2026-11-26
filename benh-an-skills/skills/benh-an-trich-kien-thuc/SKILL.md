---
name: benh-an-trich-kien-thuc
description: Trích kiến thức định hướng chẩn đoán cho MỘT triệu chứng từ chương sách/bài giảng do người dùng cung cấp, thành file knowledge/<trieu-chung>.md xếp theo từng nguyên nhân; mỗi nguyên nhân có dấu hiệu bệnh sử, tiền căn, khám, cận lâm sàng, mỗi dòng gắn loại gợi ý/chẩn đoán/loại trừ, kèm trích nguyên văn và nguồn. Dùng khi người dùng đưa một chương/bài giảng về một triệu chứng hoặc một bệnh (đau ngực, khó thở, suy tim, thuyên tắc phổi...) và muốn đưa vào kho kiến thức, hoặc muốn thêm/sửa file kiến thức.
---

# Trích kiến thức từ sách vào file kiến thức (theo nguyên nhân)

Ngôn ngữ: tiếng Việt. Đầu vào: (1) văn bản chương sách, (2) `knowledge/_TEMPLATE.md`, (3) `checklists/CAUSES.md`, (4) checklist của triệu chứng (để điền cột "Mục checklist"), (5) nếu đang bổ sung: file kiến thức hiện có. Đầu ra: nội dung file `knowledge/<trieu-chung>.md`.

## Nguyên tắc chống bịa (bắt buộc)
1. Chỉ ghi điều văn bản chương nói. Văn bản không nói thì KHÔNG điền, kể cả khi kiến thức nền của bạn biết. Không "hoàn thiện cho đủ ô".
2. Mỗi dòng có "Trích nguyên văn": chép Y NGUYÊN (từng chữ, dấu câu, dấu gạch) từ văn bản chương, trong “ ”. Không sửa, không rút gọn ở giữa câu, không ghép các câu cách xa nhau. Trích đoạn ngắn nhưng đủ nghĩa.
3. Cột "Nội dung" được diễn đạt lại ngắn gọn, nhưng không thêm ý mà trích dẫn không có.
4. **Loại xác định theo câu chữ của sách:**
   - G: "gợi ý", "nghĩ đến", "thường gặp", yếu tố nguy cơ.
   - C: sách nêu là tiêu chuẩn, "điển hình", "đặc trưng", "chẩn đoán khi", hoặc là thang điểm/tiêu chí.
   - L: sách dùng chữ "loại trừ", hoặc nói thiếu/có dấu hiệu đó thì không phải bệnh đó. Không dùng L cho câu "hiếm khi".
   - IN: "hiếm", "ít khi", "ít gặp".
   - LY: "có thể gặp", không đặc hiệu, "không loại trừ hoàn toàn".
   - CPL: không chắc, để người dùng quyết định. Không đoán.
5. Tiền căn (TC) cũng có đủ G/C/L như bệnh sử (ví dụ nằm lâu ngày trong một thang điểm là dấu hiệu chẩn đoán thuộc TC). Nguồn dữ kiện của mỗi dòng: BS, TC, K hoặc CLS, theo đúng nơi dấu hiệu đó được hỏi/khám/làm.
6. Chỉ dùng mã trong `checklists/CAUSES.md`. Nguyên nhân sách nhắc mà chưa có mã: KHÔNG tự dùng; liệt kê ở cuối câu trả lời dưới "Mã đề xuất thêm vào CAUSES.md" (mã, tên, nhóm). Khi sách nói chung chung ("bệnh lý tiêu hóa khác") mà bạn phải gán mã cụ thể, ghi "[mã suy ra]" ở cột Nội dung và liệt kê các dòng đó ở cuối.
7. Bộ tiêu chuẩn có quy tắc điểm (Wells, Framingham...): chỉ đưa vào khối "Bộ tiêu chuẩn / thang điểm" khi văn bản chương nêu đủ tiêu chí và quy tắc. Không điền từ trí nhớ.
8. Không đánh giá đúng/sai của sách. `trang_thai` luôn là NHAP; chỉ người dùng được đổi thành DA_RA_SOAT.

## Quy trình
1. Đọc cả chương: xác định danh sách nguyên nhân (bảng/mục liệt kê), phần mô tả từng bệnh, bảng so sánh, tiêu chuẩn, phần hỏi bệnh/tiền căn/khám/cận lâm sàng chung.
2. Lập "Danh sách nguyên nhân" rồi mỗi nguyên nhân một khối "## MÃ — tên".
3. Với mỗi dấu hiệu: xác định nguyên nhân nào nó thuộc về. Dấu hiệu ủng hộ nhiều nguyên nhân thì lặp ở mỗi khối (ID khác nhau theo @MÃ, cùng trích dẫn). Dấu hiệu sách không gắn nguyên nhân cụ thể thì đặt ở khối "(Chưa gắn nguyên nhân)".
4. Điền cột "Mục checklist" bằng ID mục trong checklist cùng triệu chứng mà dòng đó giúp trả lời; không khớp thì "—".
5. Bảng so sánh của sách (chẩn đoán phân biệt): mỗi ô của cột là một dấu hiệu riêng trong khối nguyên nhân của cột đó, Loại C; không trộn cột này sang cột khác. Nếu văn bản bảng mất cấu trúc nên không chắc cột nào, ghi "[cần xem lại bảng gốc]".
6. Tự kiểm tra: mỗi trích dẫn có thật trong văn bản; mỗi mã có trong CAUSES.md; mỗi ID có @MÃ đúng khối.
7. Cuối câu trả lời ghi: "Mã đề xuất thêm vào CAUSES.md", "Dòng có mã suy ra", "Dòng Loại CPL", "Nội dung sách mà mẫu không có chỗ chứa" (nếu có), và nhắc chạy `python tools/kiem_tra_kien_thuc.py <file> --nguon <file chương>`.
