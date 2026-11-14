#!/usr/bin/env bash
# Menu tổng hợp cho bộ công cụ NotebookLM trên WSL Ubuntu.
# Chạy:  bash menu.sh
# Mọi input/output nằm trong thư mục toolkit (input_pdfs, output_ocr, ket_qua, bai.txt, cauhoi.txt...).

export LC_ALL=C.UTF-8
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" || exit 1
trap ':' INT   # Ctrl+C dừng tác vụ đang chạy nhưng không thoát menu

# ------------------------------------------------------------------ cài đặt nhớ lại
SETTINGS=".menu_settings"
OPT_STRIP=0; OPT_FM=0; QUIZ_MODE="md"; QUIZ_FMT="markdown"
[[ -f "$SETTINGS" ]] && source "$SETTINGS" 2>/dev/null
[[ "$OPT_STRIP" =~ ^[01]$ ]] || OPT_STRIP=0
[[ "$OPT_FM" =~ ^[01]$ ]] || OPT_FM=0
[[ "$QUIZ_MODE" =~ ^(md|quiz|both)$ ]] || QUIZ_MODE="md"
[[ "$QUIZ_FMT" =~ ^(markdown|json|html)$ ]] || QUIZ_FMT="markdown"

save_settings() {
  printf 'OPT_STRIP=%s\nOPT_FM=%s\nQUIZ_MODE=%s\nQUIZ_FMT=%s\n' \
    "$OPT_STRIP" "$OPT_FM" "$QUIZ_MODE" "$QUIZ_FMT" > "$SETTINGS"
}

# ------------------------------------------------------------------ màu và khung
if [[ -t 1 ]]; then
  R=$'\e[0m'; B=$'\e[1m'; ORG=$'\e[38;5;208m'; CY=$'\e[36m'
  GR=$'\e[32m'; RD=$'\e[31m'; YL=$'\e[33m'; DM=$'\e[2m'
else
  R=""; B=""; ORG=""; CY=""; GR=""; RD=""; YL=""; DM=""
fi

W=62   # độ rộng phần chữ bên trong khung

rep() { local s="" i; for ((i = 0; i < $2; i++)); do s+="$1"; done; printf '%s' "$s"; }
top() { printf '%s┌%s┐%s\n' "$ORG" "$(rep ─ $((W + 2)))" "$R"; }
mid() { printf '%s├%s┤%s\n' "$ORG" "$(rep ─ $((W + 2)))" "$R"; }
bot() { printf '%s└%s┘%s\n' "$ORG" "$(rep ─ $((W + 2)))" "$R"; }

# row "chữ thường (để tính độ rộng)" ["chữ có màu để hiển thị"]
row() {
  local plain="$1" shown="${2:-$1}"
  local pad=$(( W - ${#plain} )); (( pad < 0 )) && pad=0
  printf '%s│%s %s%*s %s│%s\n' "$ORG" "$R" "$shown" "$pad" "" "$ORG" "$R"
}
center() {
  local s="$1" l=$(( (W - ${#1}) / 2 ))
  (( l < 0 )) && l=0
  row "$(printf '%*s%s' "$l" '' "$s")" "$(printf '%*s%s%s%s' "$l" '' "$B" "$s" "$R")"
}
item() { row "[$1] $2" "${CY}[$1]${R} $2"; }
sep() { row "$(printf '%*s' 23 '')$(rep ─ 16)"; }

# draw_menu "Tiêu đề" các_mục...   (mục: "phím|nhãn", SEP, MID, INFO:chữ, CTR:chữ)
draw_menu() {
  local title="$1"; shift
  top; center "$title"
  local it
  for it in "$@"; do
    case "$it" in
      SEP)    sep ;;
      MID)    mid ;;
      INFO:*) row " ${it#INFO:}" ;;
      CTR:*)  center "${it#CTR:}" ;;
      *)      item "${it%%|*}" "${it#*|}" ;;
    esac
  done
  bot
}

onoff() { [[ "$1" == "1" ]] && echo "BẬT" || echo "TẮT"; }
pause() { echo; read -rp "  Nhấn Enter để quay lại menu... " _ || exit 0; }
yn() { if "$@" >/dev/null 2>&1; then echo "có"; else echo "chưa"; fi; }

# ------------------------------------------------------------------ tiện ích
get_id() {
  [[ -f notebook_id.txt ]] || return 1
  grep -vE '^[[:space:]]*(#|$)' notebook_id.txt | head -n1 \
    | sed 's/[[:space:]]//g; s/[?#].*//; s#/*$##; s#.*/##'
}
id_short() {
  local id; id="$(get_id)"
  if [[ -z "$id" ]]; then echo "(chưa đặt)"; else echo "${id:0:8}…"; fi
}
count_items() {
  [[ -f "$1" ]] || { echo 0; return; }
  grep -cvE '^[[:space:]]*(#|$)' "$1"
}
need_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "  ${RD}Chưa cài uv.${R} Hãy chọn [2] ở menu chính để cài đặt trước."
    return 1
  fi
}
need_id() {
  if [[ -z "$(get_id)" ]]; then
    echo "  ${RD}Chưa có ID notebook.${R} Hãy chọn [7] ở menu chính để đặt ID trước."
    return 1
  fi
}
open_dir() {   # mở thư mục trong Windows Explorer
  mkdir -p "$1"
  ( cd "$1" && explorer.exe . ) >/dev/null 2>&1
  return 0
}

# ------------------------------------------------------------------ 1. hướng dẫn
show_guide() {
  if [[ ! -f README.md ]]; then echo "  Không thấy README.md"; pause; return; fi
  if command -v less >/dev/null 2>&1; then
    less -R README.md
  else
    cat README.md; pause
  fi
}

# ------------------------------------------------------------------ 2, 3. cài đặt
setup_nlm() {
  clear; echo "${B}== Cài & set-up notebooklm-py ==${R}"; echo
  bash 1_setup_notebooklm.sh
  if [[ -z "$(get_id)" ]]; then
    echo; echo "  Bước tiếp theo: chọn [7] ở menu chính để đặt ID notebook."
  fi
  pause
}
setup_ocr() {
  clear; echo "${B}== Cài & set-up OCR ==${R}"; echo
  bash 2_setup_ocr.sh
  pause
}

# ------------------------------------------------------------------ 4. OCR
do_ocr() {
  clear; echo "${B}== OCR PDF ==${R}"; echo
  if ! command -v ocrmypdf >/dev/null 2>&1; then
    echo "  ${RD}Chưa cài OCR.${R} Hãy chọn [3] ở menu chính trước."; pause; return
  fi
  echo "  Nhập thư mục chứa các file PDF:"
  echo "   - Enter để dùng thư mục input_pdfs/ trong toolkit"
  echo "   - hoặc dán/kéo thả đường dẫn thư mục (cả dạng C:\\... của Windows)"
  echo
  local dir
  read -rp "  Thư mục: " dir || exit 0
  dir="${dir:-input_pdfs}"

  if [[ "$dir" == "input_pdfs" ]]; then
    mkdir -p input_pdfs
    if [[ -z "$(find input_pdfs -maxdepth 1 -iname '*.pdf' 2>/dev/null | head -n1)" ]]; then
      echo
      echo "  input_pdfs/ đang trống. Mình mở thư mục này trong Explorer,"
      echo "  hãy chép các file PDF vào đó rồi quay lại đây."
      open_dir input_pdfs
      read -rp "  Nhấn Enter khi đã chép xong... " _ || exit 0
    fi
  fi

  echo
  bash 3_ocr_pdfs.sh "$dir"
  echo
  local a
  read -rp "  Mở thư mục output_ocr trong Explorer? [y/N] " a || exit 0
  [[ "$a" =~ ^[yY] ]] && open_dir output_ocr
  pause
}

# ------------------------------------------------------------------ 5, 6. giảng bài / câu hỏi
run_py() {   # run_py script cờ...
  local script="$1"; shift
  need_uv || return 1
  need_id || return 1
  local flags=()
  (( OPT_STRIP == 1 )) && flags+=(--strip-cite)
  (( OPT_FM == 1 )) && flags+=(--frontmatter)
  if [[ "$script" == 5_tao_cau_hoi.py ]]; then
    flags+=(--mode "$QUIZ_MODE" --quiz-format "$QUIZ_FMT")
  fi
  echo; echo "${DM}Lệnh: uv run $script ${flags[*]} $*${R}"; echo
  uv run "$script" "${flags[@]}" "$@"
}

lesson_menu() {   # $1 = giang | hoi
  local kind="$1" script list title
  if [[ "$kind" == giang ]]; then
    script=4_giang_bai.py; list=bai.txt; title="GIẢNG BÀI"
  else
    script=5_tao_cau_hoi.py; list=cauhoi.txt; title="TẠO CÂU HỎI"
  fi

  while true; do
    clear
    local items=(
      "INFO:Danh sách: $list ($(count_items "$list") mục) | Notebook: $(id_short)"
      MID
      "1|Chạy thử 1 bài đầu tiên (--test)"
      "2|Chạy toàn bộ danh sách"
      "3|Chạy một số bài (ví dụ 1,3-5)"
      "4|Làm lại toàn bộ, kể cả bài đã xong (--force)"
      "5|Sửa danh sách ($list)"
      SEP
      "6|Xóa số trích dẫn [1]: $(onoff "$OPT_STRIP")"
      "7|Thêm frontmatter Obsidian: $(onoff "$OPT_FM")"
    )
    if [[ "$kind" == hoi ]]; then
      items+=("8|Chế độ: $QUIZ_MODE  (md / quiz / both)" "9|Định dạng Quiz: $QUIZ_FMT")
    fi
    items+=(SEP "0|Quay lại menu chính")
    draw_menu "$title" "${items[@]}"

    local ch
    read -rp "  Nhập lựa chọn của bạn : " ch || exit 0
    case "$ch" in
      1) run_py "$script" --test; pause ;;
      2) run_py "$script"; pause ;;
      3) local only
         read -rp "  Nhập số thứ tự bài (ví dụ 1,3-5): " only || exit 0
         if [[ -n "$only" ]]; then run_py "$script" --only "$only"; pause; fi ;;
      4) local sure
         read -rp "  Làm lại TẤT CẢ và ghi đè file cũ? [y/N] " sure || exit 0
         if [[ "$sure" =~ ^[yY] ]]; then run_py "$script" --force; pause; fi ;;
      5) "${EDITOR:-nano}" "$list" ;;
      6) OPT_STRIP=$(( 1 - OPT_STRIP )); save_settings ;;
      7) OPT_FM=$(( 1 - OPT_FM )); save_settings ;;
      8) if [[ "$kind" == hoi ]]; then
           case "$QUIZ_MODE" in md) QUIZ_MODE=quiz ;; quiz) QUIZ_MODE=both ;; *) QUIZ_MODE=md ;; esac
           save_settings
         fi ;;
      9) if [[ "$kind" == hoi ]]; then
           case "$QUIZ_FMT" in markdown) QUIZ_FMT=json ;; json) QUIZ_FMT=html ;; *) QUIZ_FMT=markdown ;; esac
           save_settings
         fi ;;
      0|q|Q) return ;;
    esac
  done
}

# ------------------------------------------------------------------ 7. ID notebook
set_id() {
  while true; do
    clear
    draw_menu "ĐẶT ID NOTEBOOK" \
      "INFO:ID hiện tại: $(id_short)" \
      MID \
      "1|Liệt kê notebook của tôi (để xem ID)" \
      "2|Nhập ID hoặc URL notebook" \
      SEP \
      "0|Quay lại menu chính"
    local ch
    read -rp "  Nhập lựa chọn của bạn : " ch || exit 0
    case "$ch" in
      1) if need_uv; then
           echo; uvx --from notebooklm-py notebooklm list
         fi
         pause ;;
      2) local raw
         read -rp "  Dán ID hoặc URL notebook: " raw || exit 0
         if [[ -n "$raw" ]]; then
           printf '%s\n' "$raw" > notebook_id.txt
           echo "  Đã lưu. ID hiện tại: $(id_short)"
           sleep 1
         fi ;;
      0|q|Q) return ;;
    esac
  done
}

# ------------------------------------------------------------------ 8. trạng thái
status() {
  clear; echo "${B}== Kiểm tra trạng thái ==${R}"; echo
  local ok="${GR}✔${R}" bad="${RD}✘${R}"

  if command -v uv >/dev/null 2>&1; then echo " $ok uv $(uv --version | cut -d' ' -f2)"
  else echo " $bad chưa cài uv  → chọn [2]"; fi

  if [[ -d "$HOME/.notebooklm" ]]; then echo " $ok có dữ liệu đăng nhập NotebookLM (~/.notebooklm)"
  else echo " $bad chưa đăng nhập NotebookLM  → chọn [2]"; fi

  if command -v ocrmypdf >/dev/null 2>&1 && tesseract --list-langs 2>/dev/null | grep -qx vie; then
    echo " $ok ocrmypdf + tesseract tiếng Việt"
  else
    echo " $bad chưa cài OCR (hoặc thiếu tiếng Việt)  → chọn [3]"
  fi

  if [[ -n "$(get_id)" ]]; then echo " $ok ID notebook: $(get_id)"
  else echo " $bad chưa có ID notebook  → chọn [7]"; fi

  echo
  echo " PDF trong input_pdfs/        : $(find input_pdfs -maxdepth 1 -iname '*.pdf' 2>/dev/null | wc -l)"
  echo " PDF đã OCR trong output_ocr/ : $(find output_ocr -maxdepth 1 -iname '*.pdf' 2>/dev/null | wc -l)"
  echo " Số bài trong bai.txt         : $(count_items bai.txt)"
  echo " Số mục trong cauhoi.txt      : $(count_items cauhoi.txt)"
  echo " File bài giảng đã tạo        : $(find ket_qua/giang_bai -name '*.md' 2>/dev/null | wc -l)"
  echo " File câu hỏi đã tạo          : $(find ket_qua/cau_hoi -type f ! -name '.state.json' 2>/dev/null | wc -l)"

  echo
  local a
  read -rp "  Kiểm tra phiên đăng nhập trực tuyến (cần mạng, mất vài giây)? [y/N] " a || exit 0
  if [[ "$a" =~ ^[yY] ]]; then
    if need_uv; then
      echo
      uvx --from "notebooklm-py[browser]" notebooklm auth check --test --json
    fi
  fi
  pause
}

# ------------------------------------------------------------------ 9. mở thư mục
open_menu() {
  while true; do
    clear
    draw_menu "MỞ THƯ MỤC TRONG EXPLORER" \
      "1|Thư mục toolkit" \
      "2|input_pdfs  (PDF gốc)" \
      "3|output_ocr  (PDF đã OCR)" \
      "4|ket_qua/giang_bai  (bài giảng)" \
      "5|ket_qua/cau_hoi  (câu hỏi)" \
      SEP \
      "0|Quay lại menu chính"
    local ch
    read -rp "  Nhập lựa chọn của bạn : " ch || exit 0
    case "$ch" in
      1) open_dir . ;;
      2) open_dir input_pdfs ;;
      3) open_dir output_ocr ;;
      4) open_dir ket_qua/giang_bai ;;
      5) open_dir ket_qua/cau_hoi ;;
      0|q|Q) return ;;
    esac
  done
}

# ------------------------------------------------------------------ menu chính
OSNAME="$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME")"

main_menu() {
  while true; do
    clear
    draw_menu "BỘ CÔNG CỤ NOTEBOOKLM CHO WSL" \
      "CTR:${OSNAME:-Linux}" \
      MID \
      "INFO:Notebook ID: $(id_short)" \
      "INFO:uv: $(yn command -v uv) | OCR: $(yn command -v ocrmypdf) | đăng nhập: $(yn test -d "$HOME/.notebooklm")" \
      MID \
      "1|Hướng dẫn (README.md)" \
      "2|Cài & set-up notebooklm-py" \
      "3|Cài & set-up OCR" \
      "4|OCR PDFs (cả thư mục)" \
      "5|Giảng bài NotebookLM (bai.txt)" \
      "6|Tạo câu hỏi NotebookLM (cauhoi.txt)" \
      SEP \
      "7|Đặt ID notebook" \
      "8|Kiểm tra trạng thái" \
      "9|Mở thư mục trong Explorer" \
      SEP \
      "0|Thoát"
    local ch
    read -rp "  Nhập lựa chọn của bạn [1,2,3,4,5,6,7,8,9,0] : " ch || { echo; exit 0; }
    case "$ch" in
      1) show_guide ;;
      2) setup_nlm ;;
      3) setup_ocr ;;
      4) do_ocr ;;
      5) lesson_menu giang ;;
      6) lesson_menu hoi ;;
      7) set_id ;;
      8) status ;;
      9) open_menu ;;
      0|q|Q) echo; exit 0 ;;
    esac
  done
}

main_menu
