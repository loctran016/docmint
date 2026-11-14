#!/usr/bin/env bash
# OCR hàng loạt: PDF scan (chỉ là ảnh) -> PDF có lớp chữ để NotebookLM đọc được.
#
# Cách dùng:
#   bash 3_ocr_pdfs.sh                         # đọc thư mục input_pdfs/, ghi ra output_ocr/
#   bash 3_ocr_pdfs.sh /đường/dẫn/thư_mục      # thư mục bất kỳ chứa các file PDF
#   bash 3_ocr_pdfs.sh "C:\Users\ten\Sach"     # đường dẫn Windows (kéo thả thư mục vào terminal) cũng được
#   bash 3_ocr_pdfs.sh thư_mục_vào thư_mục_ra
#
# Kết quả: output_ocr/<tên file sách> - OCR.pdf
# Biến môi trường tuỳ chọn:  OCR_LANGS=vie+eng   OCR_JOBS=2

IN_DIR="${1:-input_pdfs}"
OUT_DIR="${2:-output_ocr}"
LANGS="${OCR_LANGS:-vie+eng}"
CPU="$(nproc 2>/dev/null || echo 2)"
JOBS="${OCR_JOBS:-$(( CPU > 4 ? 4 : CPU ))}"

# Đổi đường dẫn Windows (C:\... hoặc C:/...) sang đường dẫn WSL, bỏ dấu nháy thừa
to_wsl() {
  local p="$1"
  p="${p%\"}"; p="${p#\"}"; p="${p%\'}"; p="${p#\'}"
  if [[ "$p" =~ ^[A-Za-z]:[\\/] ]]; then
    wslpath -u "$p"
  else
    printf '%s' "$p"
  fi
}
IN_DIR="$(to_wsl "$IN_DIR")"
OUT_DIR="$(to_wsl "$OUT_DIR")"

if ! command -v ocrmypdf >/dev/null 2>&1; then
  echo "Chưa cài ocrmypdf. Chạy trước:  bash 2_setup_ocr.sh"
  exit 1
fi
if [ ! -d "$IN_DIR" ]; then
  echo "Không thấy thư mục: $IN_DIR"
  echo "Hãy tạo thư mục input_pdfs rồi chép PDF vào, hoặc truyền đường dẫn thư mục khác."
  exit 1
fi

mkdir -p "$OUT_DIR"
echo "Thư mục vào : $IN_DIR"
echo "Thư mục ra  : $OUT_DIR"
echo "Ngôn ngữ OCR: $LANGS | Số luồng: $JOBS"
echo

ok=0; skip=0; fail=0; total=0
failed_list=()

while IFS= read -r -d '' f; do
  total=$((total + 1))
  name="$(basename "$f")"
  base="${name%.*}"
  # bỏ qua file đã là kết quả OCR
  if [[ "$base" == *" - OCR" ]]; then
    continue
  fi
  out="$OUT_DIR/$base - OCR.pdf"
  if [ -s "$out" ]; then
    echo "[bỏ qua] đã có: $out"
    skip=$((skip + 1))
    continue
  fi
  echo "[OCR] $name  (sách dày có thể mất nhiều phút)"
  # --skip-text: trang nào đã có chữ thì giữ nguyên, chỉ OCR các trang ảnh
  if ocrmypdf -l "$LANGS" --skip-text --output-type pdf --optimize 1 --jobs "$JOBS" "$f" "$out"; then
    ok=$((ok + 1))
    echo "[xong] $out"
  else
    echo "[lỗi] không OCR được: $name"
    rm -f "$out"
    fail=$((fail + 1))
    failed_list+=("$name")
  fi
  echo
done < <(find "$IN_DIR" -maxdepth 1 -type f -iname '*.pdf' -print0 | sort -z)

if [ "$total" -eq 0 ]; then
  echo "Không thấy file PDF nào trong: $IN_DIR"
  exit 1
fi

echo "==== TỔNG KẾT ===="
echo "OCR xong: $ok | Bỏ qua (đã có): $skip | Lỗi: $fail"
if [ "$fail" -gt 0 ]; then
  echo "Các file lỗi:"
  for n in "${failed_list[@]}"; do echo "  - $n"; done
fi
echo
echo "Kết quả:"
ls -lh "$OUT_DIR" 2>/dev/null
echo
echo "Bước tiếp theo: xóa source cũ trên NotebookLM, tải các file '- OCR.pdf' lên,"
echo "chờ xử lý xong rồi hỏi thử một câu về trang đầu sách để chắc chắn nó đọc được."
