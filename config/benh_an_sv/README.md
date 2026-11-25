# Bộ skill bệnh án sinh viên (phần I–VI)

## Gồm những gì
- `skills/benh-an-trich-xuat` — phần I–V: trích xuất, đối chiếu checklist, phát hiện thiếu sót.
- `skills/benh-an-ma-tran-nguyen-nhan` — ma trận nguyên nhân × triệu chứng, giả thuyết thống nhất (H-U) vs hai bệnh chồng (H-D).
- `skills/benh-an-kham-lam-sang` — phần VI: khám thường quy + dấu hiệu nhấn mạnh theo giả thuyết.
- `checklists/` — dữ liệu đầu vào AI phải chọn từ đó (đây là phần chống bịa chính): `INDEX.md`, `CAUSES.md`, `_TEMPLATE.md`, `dau-nguc.md`, `kho-tho.md`.

## Cách dùng với DeepSeek (thinking mode cao nhất)
Chạy 3 lượt, mỗi lượt một skill. Với mỗi lượt, dán: nội dung SKILL.md + `INDEX.md` + `CAUSES.md` + các file checklist liên quan + (lượt 1) bệnh án đã ẩn danh / (lượt 2–3) kết quả lượt trước.

Prompt mẫu lượt 1:
```
Làm theo skill dưới đây. Chỉ dùng dữ kiện có trong bệnh án; thiếu thì ghi CHƯA KHAI THÁC.
[dán SKILL.md benh-an-trich-xuat]
[dán INDEX.md, CAUSES.md, checklist liên quan]
BỆNH ÁN:
[dán bệnh án]
```
Nếu bạn chạy DS trong một agent có đọc thư mục skills thì chỉ cần để nguyên cấu trúc thư mục, không cần dán.

## Cách thêm checklist mới
1. Lấy checklist gốc của bạn (từ giáo trình/giảng viên) cho triệu chứng mới, vd "Sốt", "Đau bụng".
2. Sao chép `checklists/_TEMPLATE.md` thành `<ten-trieu-chung>.md`; đặt tiền tố ID 2 chữ cái chưa dùng (DN, KT đã dùng).
3. Chuyển từng câu hỏi thành một dòng có ID cố định (XX-01, XX-02...). Mỗi dòng một ý có thể trả lời CÓ/KHÔNG.
4. Cột "Gộp với": ghi ID của mục trùng ở checklist khác (vd Ho = KT-10). Đây là cách xử lý triệu chứng chồng lấp.
5. Cột thẻ: ghi mã từ `CAUSES.md`. Nguyên nhân mới → thêm vào `CAUSES.md` trước (không đổi tên mã cũ). Chỉ gắn thẻ khi giáo trình ghi rõ; chưa chắc thì để "—".
6. Điền mục D (nguyên nhân gây triệu chứng) và mục E (khám lâm sàng nên tìm). Giữ `trang_thai_the: NHAP` tới khi bạn đối chiếu xong, rồi đổi thành `DA_RA_SOAT`.
7. Thêm một dòng vào `INDEX.md`.

Prompt nhờ AI chuyển checklist thô sang mẫu (AI chỉ chuyển dạng, không thêm nội dung):
```
Chuyển checklist thô dưới đây sang định dạng _TEMPLATE.md. Quy tắc: không thêm câu hỏi, không thêm nguyên nhân hay dấu hiệu nào không có trong văn bản gốc; mục không rõ thẻ thì để "—"; mã nguyên nhân chỉ lấy từ CAUSES.md, nếu cần mã mới thì liệt kê riêng ở cuối để tôi duyệt.
[dán _TEMPLATE.md, CAUSES.md, INDEX.md]
CHECKLIST THÔ:
[dán checklist]
```

## Gửi sang Claude kiểm tra chéo
```
Đây là bệnh án ẩn danh, checklist, và kết quả DS đã làm. Hãy kiểm tra: (1) có dữ kiện nào DS nêu mà bệnh án không có; (2) mục nào ghi KHÔNG trong khi bệnh án chỉ im lặng; (3) giả thuyết H-U/H-D có bỏ sót hay ép gộp; (4) thẻ/dấu hiệu khám nào sai so với kiến thức chuẩn. Chỉ ra từng lỗi kèm trích dẫn.
```

## Lưu ý
- Thẻ "ủng hộ/ít nghĩ" và mục E khám lâm sàng do Claude gắn dựa trên ghi chú trong checklist gốc của bạn: đang NHÁP, cần đối chiếu giáo trình/giảng viên.
- Chưa chạy thử với DS. Nên thử một bệnh án đã biết đáp án rồi chỉnh.
- Về sau tham khảo thêm: github.com/JuneYaooo/awesome-medical-ai-skills và github.com/FreedomIntelligence/OpenClaw-Medical-Skills.
