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
echo [1/3] Guncellemeler kontrol ediliyor...
if exist guncelle.py %PY% guncelle.py --sessiz
echo.
echo [2/3] Gerekli paketler kontrol ediliyor...
%PY% -c "import streamlit, pandas, openpyxl, yfinance, tradingview_screener" 2>nul
if errorlevel 1 (
  echo     Eksik paket var, kuruluyor... Bu birkac dakika surebilir.
  %PY% -m pip install -r requirements.txt
)
%PY% -c "import streamlit, pandas, openpyxl, yfinance, tradingview_screener" 2>nul
if errorlevel 1 goto PAKETHATA
echo     Paketler tamam.
echo.
echo [3/3] Basliyor...
echo.
%PY% toplu_tara.py
echo.
echo Bitti. Bu pencereyi kapatabilirsin.
pause
exit /b 0

:PAKETHATA
echo.
echo [HATA] Paketler kurulamadi.
echo  Internet baglantisini kontrol et ve tekrar dene.
echo  Sorun surerse yukaridaki kirmizi yaziyi paylas.
echo.
pause
exit /b 1

:NOPY
echo [HATA] Python bulunamadi!
echo.
echo  1) https://www.python.org/downloads/ adresine git
echo  2) Download Python butonuna bas
echo  3) KURARKEN alttaki 'Add python.exe to PATH' kutusunu ISARETLE
echo  4) Kurulum bitince bu dosyayi tekrar cift tikla
echo.
pause
