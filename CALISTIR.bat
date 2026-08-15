@echo off
cd /d "%~dp0"
set PY=py
py --version >nul 2>&1
if errorlevel 1 set PY=python
%PY% --version >nul 2>&1
if errorlevel 1 goto NOPY
echo ===========================================
echo    BIST TOPLU TARAMA
echo ===========================================
echo.
echo Guncellemeler kontrol ediliyor...
%PY% guncelle.py --sessiz
echo.
%PY% -m pip install --quiet -r requirements.txt
echo.
%PY% toplu_tara.py
echo.
echo Bitti. Bu pencereyi kapatabilirsin.
pause
exit /b 0

:NOPY
echo [HATA] Python bulunamadi!
echo.
echo  1) https://www.python.org/downloads/ adresine git
echo  2) Download Python butonuna bas
echo  3) KURARKEN alttaki 'Add python.exe to PATH' kutusunu ISARETLE
echo  4) Kurulum bitince bu dosyayi tekrar cift tikla
echo.
pause
