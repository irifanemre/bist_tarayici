@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ═══════════════════════════════════════
echo    BIST TARAYICI - KURULUM (Windows)
echo ═══════════════════════════════════════
echo.

REM --- Python bul ---
set PY=
where py >nul 2>&1 && set PY=py
if "%PY%"=="" (
  where python >nul 2>&1 && set PY=python
)
if "%PY%"=="" (
  echo [HATA] Python bulunamadi.
  echo.
  echo    Cozum: https://www.python.org/downloads/ adresinden Python indir.
  echo    KURARKEN "Add Python to PATH" kutusunu MUTLAKA isaretle!
  echo    Kurduktan sonra bu dosyayi tekrar calistir.
  echo.
  pause
  exit /b 1
)

for /f "tokens=*" %%v in ('%PY% -c "import sys;print('%%d.%%d'%%sys.version_info[:2])"') do set SURUM=%%v
echo [OK] Python bulundu (surum !SURUM!)

REM --- Surum kontrolu ---
for /f "tokens=*" %%u in ('%PY% -c "import sys;print(1 if sys.version_info[:2]>=(3,9) else 0)"') do set UYGUN=%%u
if not "!UYGUN!"=="1" (
  echo.
  echo [UYARI] Python surumun eski. En az 3.9 gerekiyor.
  echo    https://www.python.org/downloads/ adresinden guncelle.
  pause
  exit /b 1
)

echo.
echo [*] Gerekli paketler kuruluyor (birkac dakika surebilir)...
%PY% -m pip install --quiet --upgrade pip >nul 2>&1
%PY% -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo     ^(sabit surumler uymadi, esnek kuruluma geciliyor...^)
  %PY% -m pip install --quiet -r requirements-esnek.txt
)

echo.
echo [*] Kontrol ediliyor...
%PY% -c "import pandas, streamlit, openpyxl, yfinance, tradingview_screener" 2>nul
if errorlevel 1 (
  echo [HATA] Paketlerden biri yuklenemedi. Yukaridaki hatayi paylas.
  pause
  exit /b 1
)
echo [OK] Tum paketler calisiyor.

REM --- Masaustune kisayol olustur (proje yolu icine gomulur) ---
set PROJ=%~dp0
set KISAYOL=%USERPROFILE%\Desktop\BIST Toplu Tarama.bat
(
  echo @echo off
  echo chcp 65001 ^>nul
  echo cd /d "!PROJ!"
  echo echo ═══════════════════════════════════════
  echo echo    BIST TOPLU TARAMA
  echo echo ═══════════════════════════════════════
  echo !PY! toplu_tara.py
  echo echo.
  echo echo Bitti. Bu pencereyi kapatabilirsin.
  echo pause
) > "%KISAYOL%"

echo [OK] Masaustune kisayol eklendi: BIST Toplu Tarama.bat
echo.
echo ═══════════════════════════════════════
echo    KURULUM TAMAM!
echo ═══════════════════════════════════════
echo   Masaustundeki "BIST Toplu Tarama" dosyasina CIFT TIKLA.
echo.
pause
