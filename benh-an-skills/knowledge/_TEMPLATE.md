---
trieu_chung: <tên triệu chứng>
tien_to_id: <trùng tiền tố checklist, vd DN>
nguon: <Tên bài, tác giả, sách/năm>
cau_truc: theo-nguyen-nhan
trang_thai: NHAP   # chỉ người dùng được đổi thành DA_RA_SOAT sau khi đối chiếu sách/giảng viên
nguoi_tao: <AI hoặc người>
---

# Kiến thức <triệu chứng> (từ sách), xếp theo từng nguyên nhân

## Quy ước
- Mỗi nguyên nhân có một khối "## MÃ — tên" (MÃ nằm trong checklists/CAUSES.md). Trong khối, mỗi dòng là một dấu hiệu.
- Nguồn dữ kiện: BS bệnh sử, TC tiền căn, K khám/nghiệm pháp, CLS cận lâm sàng.
- Loại (xác định theo CÂU CHỮ của sách, không theo kiến thức của người soạn):
  - G gợi ý: sách dùng "gợi ý", "nghĩ đến", "thường gặp", yếu tố nguy cơ.
  - C chẩn đoán: sách nêu là tiêu chuẩn, biểu hiện điển hình/đặc trưng, hoặc "chẩn đoán khi...".
  - L loại trừ: sách dùng chữ "loại trừ" hoặc nói có dấu hiệu này/không có dấu hiệu này thì không phải bệnh đó.
  - IN ít nghĩ: sách nói "hiếm", "ít khi", "ít gặp".
  - LY lưu ý: "có thể gặp", không đặc hiệu, "không loại trừ hoàn toàn".
  - CPL chưa phân loại: câu chữ không rõ, để người dùng quyết định.
- ID dòng: KN-<tiền tố>-<B/K/C/P><số>@<MÃ>. Một câu sách ủng hộ nhiều nguyên nhân thì lặp ở mỗi khối với cùng trích dẫn.
- "Trích nguyên văn": chép Y NGUYÊN từ sách, đặt trong “ ”. Nhiều trích dẫn thì đặt liền nhau, mỗi cái trong “ ”.
- Chỉ ghi điều sách nói. Sách không nói thì KHÔNG điền. Mã suy ra (sách nói chung chung) phải ghi "[mã suy ra]" ở cột Nội dung.

## Danh sách nguyên nhân
| ID | Nguyên nhân (theo sách) | Mã nguyên nhân | Nguồn | Trích nguyên văn |
|---|---|---|---|---|
| KN-XX-N01 | ... | MÃ | mục ... | “...” |

## MÃ — tên nguyên nhân
| ID | Nguồn dữ kiện | Loại | Nội dung | Mục checklist | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|
| KN-XX-B01@MÃ | BS | G | ... | XX-01 | mục ... | “...” |
| KN-XX-B02@MÃ | TC | G | ... | XX-20 | mục ... | “...” |
| KN-XX-K01@MÃ | K | C | ... | — | mục ... | “...” |

## Bộ tiêu chuẩn / thang điểm
Chỉ điền khi nguồn có bộ tiêu chuẩn kèm quy tắc (ví dụ Wells, Framingham). Mỗi tiêu chí là một dòng gắn Nguồn dữ kiện và điểm.

| ID | Bộ tiêu chuẩn | Tiêu chí | Nguồn dữ kiện | Điểm | Quy tắc kết luận | Nguồn sách | Trích nguyên văn |
|---|---|---|---|---|---|---|---|
