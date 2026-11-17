# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Cài công cụ OCR cho PDF scan (OCRmyPDF + Tesseract tiếng Việt/Anh + Ghostscript).

    uv run 2_setup_ocr.py
    uv run 2_setup_ocr.py --dry-run     # chỉ in các lệnh sẽ chạy, không chạy thật

- WSL/Linux (Debian/Ubuntu): cài bằng apt (hỏi mật khẩu sudo).
- Windows: cài Tesseract (bản UB Mannheim) và Ghostscript bằng winget, tải gói ngôn ngữ vie/eng về
  thư mục tessdata/ trong toolkit. OCRmyPDF được uv tải khi cần (không phải cài Python riêng).
- macOS: chỉ in lệnh brew cần chạy.
"""
import argparse
import os
import shutil
import subprocess
import sys
import urllib.request

import common

LANGS = ("vie", "eng")
TESSDATA_URLS = [
    "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/HEAD/{lang}.traineddata",
    "https://github.com/tesseract-ocr/tessdata_fast/raw/main/{lang}.traineddata",
    "https://github.com/tesseract-ocr/tessdata_fast/raw/master/{lang}.traineddata",
]
MIN_BYTES = 200_000   # file traineddata hợp lệ lớn hơn mức này


def run(cmd, dry, check=False):
    print("\n$ " + " ".join(cmd))
    if dry:
        return 0
    try:
        code = subprocess.run(cmd).returncode
    except FileNotFoundError:
        print(f"  Không tìm thấy lệnh: {cmd[0]}")
        code = 127
    if check and code != 0:
        raise SystemExit(f"Lệnh trên bị lỗi (mã {code}).")
    return code


def download_lang(lang, dry):
    dest = common.LOCAL_TESSDATA / f"{lang}.traineddata"
    if dest.exists() and dest.stat().st_size > MIN_BYTES:
        print(f"  Đã có {dest}")
        return True
    for template in TESSDATA_URLS:
        url = template.format(lang=lang)
        print(f"  Tải {url}")
        if dry:
            return True
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                data = resp.read()
        except Exception as e:  # noqa: BLE001
            print(f"    Không tải được: {type(e).__name__}: {e}")
            continue
        if len(data) < MIN_BYTES:
            print("    File tải về quá nhỏ, bỏ qua.")
            continue
        common.LOCAL_TESSDATA.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        print(f"    Đã lưu {dest} ({len(data) // 1024} KB)")
        return True
    return False


def setup_linux(dry):
    print("== Cài ocrmypdf, tesseract (vie + eng), ghostscript bằng apt (hỏi mật khẩu sudo) ==")
    sudo = [] if (hasattr(os, "geteuid") and os.geteuid() == 0) else ["sudo"]
    run(sudo + ["apt-get", "update"], dry, check=True)
    run(sudo + ["apt-get", "install", "-y", "ocrmypdf", "tesseract-ocr", "tesseract-ocr-vie",
                "tesseract-ocr-eng", "ghostscript"], dry, check=True)


def setup_windows(dry):
    winget = shutil.which("winget")
    choco = shutil.which("choco")
    flags = ["--accept-package-agreements", "--accept-source-agreements"]

    print("== 1/3  Tesseract OCR ==")
    if common.find_tesseract():
        print(f"  Đã có: {common.find_tesseract()}")
    elif winget:
        print("  (Windows có thể hiện hộp thoại xin quyền quản trị, hãy chọn Yes)")
        run([winget, "install", "-e", "--id", "UB-Mannheim.TesseractOCR"] + flags, dry)
    elif choco:
        run([choco, "install", "-y", "tesseract"], dry)
    else:
        print("  Không có winget hay Chocolatey. Hãy cài Tesseract bản 64-bit (UB Mannheim) thủ công,")
        print("  rồi chạy lại bước này.")

    print("\n== 2/3  Ghostscript ==")
    if common.find_ghostscript():
        print(f"  Đã có: {common.find_ghostscript()}")
    else:
        code = 1
        if winget:
            code = run([winget, "install", "-e", "--id", "ArtifexSoftware.GhostScript"] + flags, dry)
        if code != 0 and choco:
            code = run([choco, "install", "-y", "ghostscript"], dry)
        if code != 0:
            print("  Không cài tự động được Ghostscript (bản mới của nó không còn hỗ trợ cài tự động).")
            print("  Hãy tải bản 64-bit từ trang chính thức ghostscript.com, cài xong chạy lại bước này.")

    print("\n== 3/3  Gói ngôn ngữ Tesseract (tiếng Việt + tiếng Anh) ==")
    have = common.tesseract_langs() if common.find_tesseract() else []
    missing = [lang for lang in LANGS if lang not in have]
    if not missing and not dry:
        print("  Tesseract đã có đủ vie + eng.")
    else:
        print(f"  Cần tải: {', '.join(LANGS)} -> {common.LOCAL_TESSDATA}")
        for lang in LANGS:
            if not download_lang(lang, dry):
                print(f"  KHÔNG tải được {lang}.traineddata. Hãy tải thủ công file này từ kho "
                      f"tesseract-ocr/tessdata_fast trên GitHub rồi chép vào {common.LOCAL_TESSDATA}")


def verify(dry):
    print("\n== Kiểm tra ==")
    if dry:
        print("  (bỏ qua vì --dry-run)")
        return
    tess = common.find_tesseract()
    gs = common.find_ghostscript()
    langs = common.tesseract_langs(tess) if tess else []
    print(f"  Tesseract  : {tess or 'CHƯA CÓ'}")
    print(f"  Ghostscript: {gs or 'CHƯA CÓ'}")
    print(f"  Ngôn ngữ   : {', '.join(langs) if langs else '(không đọc được)'}")
    ok = bool(tess and gs and all(lang in langs for lang in LANGS))
    uv = shutil.which("uv")
    if shutil.which("ocrmypdf"):
        print(f"  ocrmypdf   : {shutil.which('ocrmypdf')}")
    elif uv:
        print("  ocrmypdf   : sẽ được uv tải khi chạy OCR (lần đầu hơi lâu)")
    if ok:
        print("\nOCR đã sẵn sàng. Bước tiếp theo: chạy OCR cho thư mục PDF.")
    else:
        print("\nCòn thiếu thành phần ở trên. Xem README mục Debug > OCR, sửa xong chạy lại bước này.")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="chỉ in lệnh, không chạy")
    dry = ap.parse_args().dry_run

    if common.IS_WIN:
        setup_windows(dry)
    elif common.IS_MAC:
        print("macOS: chạy lệnh sau rồi chạy OCR:\n   brew install ocrmypdf tesseract-lang")
        return
    else:
        setup_linux(dry)
    verify(dry)


if __name__ == "__main__":
    main()
