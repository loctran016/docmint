Nhiệm vụ: Truy xuất và trích xuất các sự thật, định nghĩa, cơ chế và số liệu nguyên gốc từ tài liệu NotebookLM tương ứng với từng câu hỏi trong danh sách.

QUY TẮC NGHIÊM NGẶT:

1. CHỈ sử dụng thông tin có trong các nguồn NotebookLM đang được chọn. Tuyệt đối không dùng kiến thức bên ngoài.
2. Bảo toàn nguyên văn thuật ngữ y khoa, con số, ngưỡng chỉ số, tên thuốc và mối quan hệ nhân - quả đúng như textbook trình bày.
3. KHÔNG giải đề, KHÔNG chọn đáp án A/B/C/D và KHÔNG tự suy đoán nếu nguồn không viết rõ.
4. Nếu tài liệu NotebookLM không có thông tin liên quan đến câu hỏi nào, ghi chính xác `"Không tìm thấy trong nguồn"` vào trường `facts` của câu đó.

ĐỊNH DẠNG ĐẦU RA:
Chỉ trả về duy nhất một khối JSON hợp lệ (không lời dẫn, không bọc ```):
{"rag":[{"id":"Q1","facts":"Trích dẫn các ý và số liệu liên quan từ nguồn..."}]}

Dữ liệu câu hỏi:
$data
