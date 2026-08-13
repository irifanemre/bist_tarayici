@echo off
cd /d "%~dp0"
set PY=py
py --version >nul 2>&1
if errorlevel 1 set PY=python
echo ===========================================
echo    DUNKU KAGITLARIN PERFORMANSI
echo ===========================================
%PY% performans.py
echo.
echo Bitti. Bu pencereyi kapatabilirsin.
pause
