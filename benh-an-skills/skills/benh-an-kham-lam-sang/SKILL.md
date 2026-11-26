---
name: benh-an-kham-lam-sang
description: Đề nghị khám lâm sàng và nghiệm pháp cần làm (phần VI bệnh án sinh viên) bằng cách lấy các dấu hiệu khám thuộc loại chẩn đoán và loại trừ trong file kiến thức của các nguyên nhân còn nghi, kèm khám toàn diện theo thường quy; nếu bệnh án đã có kết quả khám thì đối chiếu và cập nhật giả thuyết. Dùng khi người dùng hỏi cần khám gì, tìm dấu hiệu gì, "khám lâm sàng", "nghiệm pháp", hoặc muốn xem kết quả khám làm nguyên nhân nào tăng hay giảm.
---

# Khám lâm sàng theo nguyên nhân còn nghi

Ngôn ngữ: tiếng Việt. Đầu vào: kết quả skill biện luận (nguyên nhân nghĩ nhiều/ít nghĩ), file kiến thức theo nguyên nhân, kết quả khám trong bệnh án nếu có.

## Nguyên tắc chống bịa
1. Không bao giờ tự đặt kết quả khám. Dấu hiệu bệnh án không ghi thì **CHƯA GHI NHẬN** (không phải "bình thường", không phải "âm tính").
2. Dấu hiệu và nghiệm pháp nhấn mạnh chỉ lấy từ các dòng Nguồn dữ kiện K của file kiến thức. Thêm ngoài file thì gắn nhãn **[NGOÀI KIẾN THỨC]** và để riêng.
3. Mỗi dòng nêu mã nguyên nhân và Loại (C/L/G/IN/LY) của dấu hiệu.

## Quy trình
1. **Khám thường quy theo cơ quan:** toàn thân và sinh hiệu, đầu mặt cổ, tim mạch, hô hấp, bụng, thần kinh, cơ xương khớp, da. Mỗi cơ quan liệt kê ngắn các bước chuẩn (nhìn, sờ, gõ, nghe nếu phù hợp). Khám toàn diện nhằm đánh giá ảnh hưởng của triệu chứng lên cơ quan khác và bệnh nền.
2. **Khám có trọng điểm (đề nghị):** với các nguyên nhân nghĩ nhiều và ít nghĩ, lấy dòng K có Loại **C và L trước**, rồi G và IN, mà bệnh án CHƯA GHI NHẬN. Gộp dấu hiệu trùng giữa các nguyên nhân: một dấu hiệu phân biệt được nhiều nguyên nhân thì xếp lên đầu. Mỗi dòng: dấu hiệu/nghiệm pháp | các nguyên nhân liên quan và Loại | nếu (+) thì ủng hộ nguyên nhân nào | nếu (−) thì ít nghĩ hoặc loại trừ nguyên nhân nào (chỉ ghi điều file kiến thức nói).
3. **Nếu bệnh án đã có kết quả khám:** mỗi dấu hiệu ghi (+)/(−)/CHƯA GHI NHẬN kèm trích nguyên văn bệnh án. Sau đó cập nhật: nguyên nhân nào được ủng hộ thêm, nguyên nhân nào giảm, và so sánh chẩn đoán thống nhất với chẩn đoán gồm hai bệnh. Nếu dữ kiện chưa đủ thì giữ nguyên và nói rõ lý do.
4. **Dấu hiệu quan trọng chưa ghi nhận:** liệt kê để bổ sung khi đi lâm sàng.

## Định dạng đầu ra
Phần VI: (a) khám thường quy, (b) bảng khám có trọng điểm, (c) bảng đối chiếu kết quả (nếu có), (d) giả thuyết sau khám, (e) việc còn thiếu. Không đưa chẩn đoán xác định ở bước này.
