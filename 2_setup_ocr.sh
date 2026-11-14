#!/usr/bin/env bash
# Cài công cụ OCR (ocrmypdf + tesseract tiếng Việt và tiếng Anh) trên WSL Ubuntu.
# Cách chạy:  bash 2_setup_ocr.sh
set -e

echo "== Cài ocrmypdf, tesseract (vie + eng), ghostscript (hỏi mật khẩu sudo) =="
sudo apt-get update
sudo apt-get install -y ocrmypdf tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng ghostscript

echo
echo "== Kiểm tra =="
ocrmypdf --version
echo "Ngôn ngữ tesseract đã cài:"
tesseract --list-langs | grep -E "^(vie|eng)$" || {
  echo "LỖI: chưa thấy gói ngôn ngữ vie/eng."
  exit 1
}

echo
echo "Xong. Bước tiếp theo:"
echo "   bash 3_ocr_pdfs.sh /đường/dẫn/thư_mục_chứa_pdf"
