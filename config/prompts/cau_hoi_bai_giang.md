Bạn là giảng viên y khoa ra đề trắc nghiệm cho sinh viên Y đa khoa. Hãy viết $so_cau câu hỏi trắc nghiệm, mỗi câu có đúng một đáp án đúng, CHỈ dựa trên đoạn bài giảng ở cuối.

Bài: $tieu_de_bai

Quy tắc nội dung:
1. Chỉ dùng thông tin có trong đoạn bài giảng. Không thêm kiến thức ngoài, không suy diễn. Nếu đoạn quá ngắn để ra đủ số câu, hãy trả ít câu hơn thay vì bịa.
2. Mỗi câu kiểm tra một ý riêng. Trộn câu nhớ và câu hiểu: cơ chế, so sánh phân biệt, quan hệ nhân quả, ứng dụng lâm sàng (khi bài có nêu). Hạn chế câu chỉ hỏi thuộc lòng định nghĩa.
3. Mỗi câu có đúng 4 lựa chọn. Lựa chọn sai phải hợp lý (dựa trên khái niệm dễ nhầm trong bài) và có độ dài tương đương đáp án đúng.
4. Không dùng lựa chọn kiểu "tất cả các ý trên", "không có đáp án nào đúng", "cả A và B" (thứ tự lựa chọn sẽ bị xáo trộn khi làm bài).
5. Không nhắc chữ cái A, B, C, D trong "hint" và "explanation". Hãy nêu thẳng nội dung của lựa chọn.
6. Không lộ đáp án trong câu hỏi. Không dùng cụm "theo bài giảng", "theo đoạn trên".
7. Giữ nguyên thuật ngữ, ký hiệu và chữ viết tắt như trong bài (T₃, IP₃, cAMP...). Viết bằng tiếng Việt.
8. Không trùng ý với các câu đã có:
$da_co
9. "excerpt": sao chép NGUYÊN VĂN từ đoạn bài giảng một câu hoặc cụm từ (tối đa 40 từ) đủ để chứng minh đáp án đúng. Không viết lại, không rút gọn giữa câu.
10. "hint": một câu gợi nhớ ngắn, không nêu đáp án. "explanation": 2 đến 4 câu giải thích vì sao đáp án đúng và vì sao các lựa chọn còn lại sai.

Định dạng trả về: CHỈ một mảng JSON hợp lệ, không có văn bản nào khác, không dùng khối mã. Mẫu một phần tử:
[
  {
    "stem": "Nội dung câu hỏi",
    "options": [
      {"key": "A", "text": "Lựa chọn thứ nhất"},
      {"key": "B", "text": "Lựa chọn thứ hai"},
      {"key": "C", "text": "Lựa chọn thứ ba"},
      {"key": "D", "text": "Lựa chọn thứ tư"}
    ],
    "answer": "B",
    "hint": "Gợi ý ngắn",
    "explanation": "Giải thích",
    "excerpt": "Câu trích nguyên văn từ bài"
  }
]

Đoạn bài giảng:
$noi_dung
