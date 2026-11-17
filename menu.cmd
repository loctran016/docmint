@echo off
REM Mo menu tren Windows: nhap dup file nay. Can cai uv (tu tai Python khi can).
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  echo Chua cai uv. Dang cai bang winget...
  winget install --id astral-sh.uv -e --accept-package-agreements --accept-source-agreements
  echo.
  echo Da cai xong uv. Hay DONG cua so nay roi nhap dup lai menu.cmd.
  pause
  exit /b
)
uv run menu.py
if errorlevel 1 pause
