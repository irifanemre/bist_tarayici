@echo off
cd /d "%~dp0"
set PY=py
py --version >nul 2>&1
if errorlevel 1 set PY=python
%PY% --version >nul 2>&1
if errorlevel 1 goto NOPY
echo ===========================================
echo    BIST TARAYICI UYGULAMASI
echo ===========================================
echo.
echo Guncellemeler kontrol ediliyor...
%PY% guncelle.py --sessiz
%PY% -m pip install --quiet -r requirements.txt
echo.
echo Uygulama aciliyor... Tarayicida acilacak.
echo Kapatmak icin bu pencereyi kapat.
echo.
%PY% -m streamlit run uygulama.py
goto :eof

:NOPY
echo [HATA] Python bulunamadi!
echo.
echo  https://www.python.org/downloads/ adresinden Python kur
echo  KURARKEN 'Add python.exe to PATH' kutusunu ISARETLE
echo.
pause
