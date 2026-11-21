Nhiệm vụ: Phân loại CHỈ các câu hỏi trắc nghiệm y học cơ sở (dạng ngắn) vào đúng một trong 6 nhóm phân môn dưới đây.

DANH SÁCH 6 PHÂN MÔN (`group_id`):
1 = Giải phẫu (cấu trúc đại thể, vị trí, liên quan, mạch máu, thần kinh chi phối)
2 = Giải phẫu bệnh (tổn thương đại thể/vi thể, mô bệnh học, biến đổi tế bào bệnh lý)
3 = Mô phôi (cấu tạo mô học bình thường, nguồn gốc phôi thai học, quá trình phát triển phôi)
4 = Sinh lý (chức năng bình thường của cơ quan/hệ cơ quan, cơ chế điều hòa hằng định nội môi)
5 = Sinh lý bệnh (cơ chế rối loạn chức năng, bệnh sinh, đáp ứng bù trừ khi mắc bệnh)
6 = Dược lý (dược động học, dược lực học, cơ chế tác dụng, chỉ định, chống chỉ định, tác dụng phụ của thuốc)

QUY TẮC LOẠI TRỪ (BỎ QUA, KHÔNG ĐƯA VÀO JSON):

- Bỏ qua các câu hỏi có đề cập đến hình ảnh, biểu đồ, tiêu bản, X-quang, CT, MRI, ECG (ví dụ chứa từ khóa: "hình bên", "mũi tên chỉ", "tiêu bản sau", "điện tâm đồ dưới đây").
- Bỏ qua các ca lâm sàng dài (bệnh án nhiều dữ kiện hỏi về chẩn đoán xác định, phác đồ điều trị lâm sàng hoặc xử trí cấp cứu).
- Lưu ý: Câu hỏi cơ sở có lồng 1–2 câu tình huống ngắn nhưng trọng tâm vẫn hỏi về cơ chế sinh lý/dược lý/giải phẫu thì VẪN phân loại vào nhóm 1–6 tương ứng.

ĐỊNH DẠNG ĐẦU RA:
Chỉ trả về một khối JSON hợp lệ duy nhất (không lời dẫn, không bọc ```):
{"groups":[{"id":"Q1","group_id":1}]}

Dữ liệu đầu vào:
$data
