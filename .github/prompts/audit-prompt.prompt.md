---
mode: "agent"
description: "Đánh giá và nâng cấp các file prompt y khoa của docmint theo chuẩn Prompt Engineering mà không làm hỏng code Python."
---

@workspace Hãy đóng vai Kỹ sư Prompt (Prompt Engineer) chuyên về hệ thống xử lý tài liệu y khoa và chấm/giải đề chuẩn hóa cho dự án `docmint`.

Nhiệm vụ của bạn là **nhận xét và nâng cấp (nếu thực sự cần thiết)** file prompt mà tôi đang mở hoặc chỉ định (ví dụ: `#file:config/prompts/notebook_note_check.md`).

### BƯỚC 1: KIỂM TRA RÀNG BUỘC KỸ THUẬT (BẮT BUỘC)

Trước khi sửa nội dung prompt, hãy đối chiếu file prompt này với các file Python đang gọi nó trong `src/` để đảm bảo:

1. **Bảo toàn 100% biến `string.Template`:** Giữ nguyên chính xác tên và số lượng các biến dạng `$ten_bien` (không tự ý đổi tên, thêm hoặc xóa biến).
2. **Bảo toàn Schema JSON:** Nếu prompt yêu cầu trả về JSON, giữ nguyên toàn bộ tên trường (keys) và kiểu dữ liệu mà code Python đang parse.
3. **Đồng bộ Parser:** Nếu bạn đề xuất thêm thẻ nháp mới (ví dụ `<kiem_tra>...</kiem_tra>`, `<ban_chinh_thuc>...</ban_chinh_thuc>`), bạn BẮT BUỘC phải chỉ ra đúng dòng code Python trong `src/` cần cập nhật regex để trích xuất dữ liệu sạch.

### BƯỚC 2: ĐÁNH GIÁ THEO 4 TIÊU CHÍ PROMPT ENGINEERING

Hãy chấm điểm file prompt hiện tại theo 4 kỹ thuật sau:

1. **Structured Chain-of-Thought (Suy luận có cấu trúc):** Prompt giải đề/phân tích phức tạp có đang ép mô hình đi qua các bước lập luận y khoa cố định trước khi chốt đáp án hay không? (Mẹo: với JSON, đặt trường `explanation` TRƯỚC trường `answer` để mô hình suy luận xong mới chốt chữ cái đáp án).
2. **Self-Critique (Tự kiểm định chống sót dữ liệu):** Prompt biên tập/tổng hợp có cơ chế tự rà soát bản nháp với nguồn gốc để chống rơi con số, tỷ lệ %, liều thuốc, mốc giải phẫu hoặc bịa kiến thức ngoài nguồn không?
3. **Boundary Rules & Anti-Hallucination (Khóa ranh giới):** Có phân định rõ trường hợp biên (edge cases), tiêu chí loại trừ và câu trả lời chuẩn khi nguồn không đề cập (ví dụ: `"Không tìm thấy trong nguồn"`) chưa?
4. **Tính tinh gọn & Vệ sinh văn bản:** Có bị lặp dòng thừa, mâu thuẫn chỉ thị, hay bị "over-engineer" (nhồi nhét suy luận vào các file cấu hình đơn giản như initial prompt của Whisper hoặc mảnh ghép nối chuỗi) không?

### BƯỚC 3: ĐỊNH DẠNG PHẢN HỒI

Trả lời ngắn gọn theo đúng 3 phần sau:

1. **Kết luận phân loại:** Ghi rõ **`[NÊN NÂNG CẤP]`** hoặc **`[GIỮ NGUYÊN - KHÔNG CẦN SỬA]`** kèm 2–3 gạch đầu dòng giải thích lý do kỹ thuật.
2. **Bản nâng cấp đề xuất (nếu chọn NÊN NÂNG CẤP):** Xuất nguyên văn nội dung file `.md` mới sẵn sàng để ghi đè (giữ nguyên toàn bộ `$variable`).
3. **Tác động lên code Python (nếu có):** Liệt kê file và dòng code trong `src/` cần chỉnh sửa tương ứng (nếu không đụng vào code Python thì ghi `"Không cần sửa code Python"`).
