@echo off
cd /d "%~dp0"

echo ===========================================
echo    BIST TARAYICI - KURULUM
echo ===========================================
echo.

set PY=
py --version >nul 2>&1
if not errorlevel 1 set PY=py
if "%PY%"=="" (
  python --version >nul 2>&1
  if not errorlevel 1 set PY=python
)

if "%PY%"=="" (
  echo [HATA] Python bulunamadi!
  echo.
  echo  1^) https://www.python.org/downloads/ adresine git
  echo  2^) Sari "Download Python" butonuna bas
  echo  3^) KURARKEN alttaki "Add python.exe to PATH" kutusunu ISARETLE
  echo  4^) Kurulum bitince bu dosyayi tekrar calistir
  echo.
  pause
  exit /b 1
)

echo [1/3] Python bulundu:
%PY% --version
echo.

echo [2/3] Paketler kuruluyor... Bu 2-3 dakika surebilir, bekle.
echo.
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo  Sabit surumler uymadi, esnek kurulum deneniyor...
  %PY% -m pip install -r requirements-esnek.txt
)
echo.

echo [3/3] Kontrol ediliyor...
%PY% -c "import pandas, streamlit, openpyxl, yfinance, tradingview_screener; print('   Tum paketler calisiyor.')"
if errorlevel 1 (
  echo.
  echo [HATA] Paketler kurulamadi. Yukaridaki kirmizi yaziyi paylas.
  echo.
  pause
  exit /b 1
)
echo.

set PROJ=%~dp0
if "%PROJ:~-1%"=="\" set PROJ=%PROJ:~0,-1%

set KISAYOL=%USERPROFILE%\Desktop\BIST Toplu Tarama.bat
echo @echo off> "%KISAYOL%"
echo cd /d "%PROJ%">> "%KISAYOL%"
echo echo BIST TOPLU TARAMA calisiyor, bekle...>> "%KISAYOL%"
echo %PY% toplu_tara.py>> "%KISAYOL%"
echo echo.>> "%KISAYOL%"
echo echo Bitti. Bu pencereyi kapatabilirsin.>> "%KISAYOL%"
echo pause>> "%KISAYOL%"

echo ===========================================
echo    KURULUM TAMAM!
echo ===========================================
echo.
echo  Masaustunde "BIST Toplu Tarama" dosyasi olustu.
echo  Ona cift tiklayarak taramayi baslatabilirsin.
echo.
pause
