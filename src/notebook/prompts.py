import sys
from pathlib import Path as _Path
_DOCMINT_REPO_BOOTSTRAP = True
_DOCMINT_ROOT = next((d for d in (_Path(__file__).resolve(), *_Path(__file__).resolve().parents)
                      if (d / ".git").exists()), _Path.cwd())
if str(_DOCMINT_ROOT) not in sys.path:
    sys.path.insert(0, str(_DOCMINT_ROOT))
"""Prompt tách riêng để chỉnh lời lẽ mà không đụng logic.

Quy ước tiền tố nguồn: [SGK] sách, [GV] transcript giáo viên, [SLIDE] slide.
"""

COMMON = """Bạn là gia sư y khoa. Chỉ dùng thông tin có trong các nguồn đã chọn, \
TUYỆT ĐỐI không thêm kiến thức ngoài nguồn. Nếu nguồn không đề cập thì nói rõ \
"nguồn không đề cập", không tự bổ sung. Giữ nguyên thuật ngữ và số liệu như trong nguồn. \
Giảng theo thứ tự logic của bài, giải thích dễ hiểu, giữ độ chính xác. Không cần trích số trang."""

MODES = {
    "sach": """Hãy giảng bài "{lesson}" chỉ dựa trên sách giáo khoa [SGK]. \
Đi theo cấu trúc của sách, giải thích từng mục, nhấn mạnh các ý then chốt, \
số liệu, phân loại, cơ chế.""",

    "giaovien": """Hãy giảng lại bài "{lesson}" đúng theo cách thầy/cô giảng trong bản ghi [GV] \
và slide [SLIDE]. Giữ trọng tâm, thứ tự và các ví dụ/lưu ý mà giáo viên nhấn mạnh \
(kể cả những chỗ giáo viên dặn "cái này hay thi"). Dùng slide để bổ sung phần sơ đồ.""",

    "ca_hai": """Hãy giảng bài "{lesson}" kết hợp sách [SGK] và giáo viên [GV]/[SLIDE]. \
Lấy khung theo sách, chèn phần giáo viên nhấn mạnh. Cuối cùng thêm mục \
"Khác biệt giữa sách và giáo viên": liệt kê chỗ nào hai nguồn nói khác nhau hoặc \
chỉ một nguồn có, ghi rõ nguồn nào nói gì.""",
}

# Thêm vào các chế độ giảng bài để kết quả có cấu trúc, tiện đưa vào Obsidian
FORMAT_MD = """Trình bày bằng Markdown: tiêu đề bài là H1 (#), mỗi mục lớn là H2 (##), \
mục con là H3 (###), giữ đúng thứ tự và tên mục của nguồn chính (sách nếu có). \
Dùng gạch đầu dòng và bảng khi nguồn có. Kết bài bằng phần "Tóm tắt nhanh" (3-5 gạch đầu dòng)."""

NOTE_CHECK = """Dưới đây là note của tôi về bài "{lesson}". Với TỪNG ý trong note, \
hãy đối chiếu với các nguồn đã chọn và xếp vào một trong 3 loại:
1. KHỚP: nguồn xác nhận.
2. MÂU THUẪN: nguồn nói khác. Nêu ý của tôi, ý của nguồn, và trích đoạn nguồn tương ứng.
3. KHÔNG CÓ TRONG NGUỒN: không kết luận đúng hay sai.
Đừng sửa lại cách viết của tôi, chỉ đối chiếu. Kết thúc bằng danh sách các ý loại 2 \
để tôi kiểm tra lại với sách giấy.

[NOTE]
{note}"""


def build_prompt(mode, lesson, note_text=None, structured=True):
    """mode: sach | giaovien | ca_hai | kiemtra_note.
    structured: thêm yêu cầu định dạng H1/H2/H3 (không áp dụng cho kiemtra_note)."""
    if mode == "kiemtra_note":
        if not note_text:
            raise ValueError("Chế độ kiểm tra note cần nội dung note.")
        body = NOTE_CHECK.format(lesson=lesson, note=note_text)
        return COMMON + "\n\n" + body
    body = MODES[mode].format(lesson=lesson)
    parts = [COMMON, body]
    if structured:
        parts.append(FORMAT_MD)
    return "\n\n".join(parts)
