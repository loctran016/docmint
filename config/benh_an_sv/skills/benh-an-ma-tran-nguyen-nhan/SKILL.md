---
name: benh-an-ma-tran-nguyen-nhan
description: Biện luận lâm sàng theo bảng của bộ môn (hỏi bệnh, khám lâm sàng, tiền căn × các chẩn đoán ứng viên, kèm hàng "lựa chọn chẩn đoán"). Đối chiếu dữ kiện bệnh án với file kiến thức theo nguyên nhân (dấu hiệu gợi ý/chẩn đoán/loại trừ của bệnh sử và tiền căn), đếm theo nguồn, đề xuất ký hiệu +++ đến --, và nêu chẩn đoán sơ bộ (bệnh chính + bệnh nền) cùng chẩn đoán phân biệt. Dùng sau khi đã trích xuất bệnh sử/tiền căn, khi người dùng hỏi biện luận, chẩn đoán sơ bộ, chẩn đoán phân biệt, "nghĩ nhiều/ít nghĩ/không nghĩ".
---

# Biện luận theo bảng bộ môn

Ngôn ngữ: tiếng Việt. Đầu vào: kết quả skill `benh-an-trich-xuat` (dữ kiện CÓ/KHÔNG/CHƯA KHAI THÁC, kèm ID và trích dẫn), file kiến thức theo nguyên nhân (`knowledge/<trieu-chung>.md`), `checklists/CAUSES.md`. Đầu ra là giả thuyết trước khi khám đầy đủ, không phải chẩn đoán xác định.

## Nguyên tắc chống bịa
1. Chỉ dùng dòng có trong file kiến thức và dữ kiện có trong kết quả trích xuất. Không thêm dấu hiệu, nguyên nhân hay tiêu chuẩn từ trí nhớ.
2. Một dòng kiến thức chỉ được tính là "khớp" khi dữ kiện bệnh án tương ứng thật sự có (trạng thái CÓ), ghi kèm ID dữ kiện và trích dẫn. Dữ kiện CHƯA KHAI THÁC không tính ủng hộ cũng không tính chống.
3. Ký hiệu +++ đến -- chỉ là ĐỀ XUẤT theo quy tắc đếm bên dưới; ghi rõ "cần bạn/giảng viên duyệt". Không viết như kết luận.
4. Nếu file kiến thức có trạng thái NHAP, nhắc ở đầu kết quả: "kiến thức chưa được người dùng duyệt".

## Quy trình
1. **Nguyên nhân ứng viên:** các khối nguyên nhân trong file kiến thức có ít nhất một dòng khớp (Loại G, C, L, IN, LY). Nguyên nhân không có dòng nào khớp thì không đưa vào bảng.
2. **Ghép dữ kiện với từng khối:** với mỗi nguyên nhân, duyệt các dòng theo Nguồn dữ kiện BS, TC (và K nếu bệnh án đã có kết quả khám) rồi ghi: dòng nào khớp (ID kiến thức, ID dữ kiện, trích dẫn) và dòng nào chưa khai thác.
3. **Đếm theo nguồn** cho mỗi nguyên nhân: số dòng C khớp, G khớp, IN khớp, L khớp, LY khớp, ở BS, TC, K.
4. **Đề xuất ký hiệu** từng ô (nguyên nhân × hàng Hỏi bệnh / Khám lâm sàng / Tiền căn):
   - `+++`: có dòng C khớp và không có IN hoặc L khớp.
   - `++`: chỉ có G khớp, hoặc có C khớp nhưng đồng thời có IN khớp.
   - `+`: chỉ có LY khớp.
   - `-`: chỉ có IN khớp.
   - `--`: có L khớp.
   - ô để trống ("chưa có dữ kiện") nếu không khớp dòng nào hoặc nguồn đó chưa khai thác/chưa khám. Đừng điền "-" cho ô chưa có dữ kiện.
5. **Hàng "Lựa chọn chẩn đoán":** nguyên nhân có ký hiệu mạnh nhất và không có `--` → "nghĩ nhiều (chẩn đoán sơ bộ)"; còn khớp một phần → "ít nghĩ, cần CLS để phân biệt"; có `--` hoặc không khớp dòng nào → "không nghĩ".
6. **Bệnh chính + bệnh nền:** chẩn đoán sơ bộ phải bao hàm mọi vấn đề (bệnh chính do nguyên nhân nghĩ nhiều + bệnh nền đã chẩn đoán trong tiền căn của bệnh án). Chẩn đoán phân biệt giải thích được một phần vấn đề và cần CLS để phân biệt về mức độ, nguyên nhân hoặc biến chứng.
7. **Gộp hay tách:** nếu một nguyên nhân giải thích hết các triệu chứng chính thì ưu tiên chẩn đoán thống nhất. Nếu có triệu chứng chính mà nguyên nhân đó không giải thích, đề xuất thêm nguyên nhân thứ hai (chẩn đoán gồm hai bệnh) và nói rõ triệu chứng nào còn lại.
8. **Bước kế tiếp:** liệt kê dòng C và L chưa khai thác (BS, TC) nên hỏi lại, và chuyển danh sách nguyên nhân còn nghi sang skill `benh-an-kham-lam-sang`.

## Định dạng đầu ra
1) Bảng biện luận (cột = nguyên nhân ứng viên, hàng = Hỏi bệnh [triệu chứng riêng rẻ; hội chứng lâm sàng], Khám lâm sàng, Tiền căn [triệu chứng gợi ý bệnh mạn chưa chẩn đoán; bệnh mạn đã chẩn đoán], Lựa chọn chẩn đoán). 2) Bảng chi tiết dòng khớp (ID kiến thức | ID dữ kiện | trích dẫn). 3) Chẩn đoán sơ bộ và phân biệt. 4) Dữ kiện chưa khai thác cần hỏi lại.
