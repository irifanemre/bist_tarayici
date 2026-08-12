#!/bin/bash
# BIST Tarayıcı kurulumu (macOS). Çalıştır:  bash kurulum.sh
set -e
KLASOR="$(cd "$(dirname "$0")" && pwd)"
cd "$KLASOR"

echo "═══════════════════════════════════════"
echo "   BIST TARAYICI — KURULUM"
echo "═══════════════════════════════════════"

PY=$(command -v python3 || true)
if [ -z "$PY" ]; then
  echo "❌ python3 bulunamadı."
  echo "   Terminal'e şunu yaz, Xcode araçlarını kur, sonra tekrar dene:"
  echo "   xcode-select --install"
  exit 1
fi
SURUM=$("$PY" -c 'import sys; print("%d.%d"%sys.version_info[:2])')
echo "✅ Python bulundu: $PY (sürüm $SURUM)"

UYGUN=$("$PY" -c 'import sys; print(1 if sys.version_info[:2] >= (3,9) else 0)')
if [ "$UYGUN" != "1" ]; then
  echo ""
  echo "⚠️  Python sürümün eski ($SURUM). En az 3.9 gerekiyor."
  echo "   Çözüm: https://www.python.org/downloads/ adresinden güncel Python'u"
  echo "   indirip kur, sonra bu kurulumu tekrar çalıştır."
  exit 1
fi

echo ""
echo "📦 Gerekli paketler kuruluyor (birkaç dakika sürebilir)…"
"$PY" -m pip install --user --quiet --upgrade pip 2>/dev/null || true
if ! "$PY" -m pip install --user --quiet -r requirements.txt 2>/dev/null; then
  echo "   (sabit sürümler uymadı, esnek kuruluma geçiliyor…)"
  "$PY" -m pip install --user --quiet -r requirements-esnek.txt
fi
echo "✅ Paketler kuruldu."

echo ""
echo "🔎 Kontrol ediliyor…"
if "$PY" -c "import pandas, streamlit, openpyxl, yfinance, tradingview_screener" 2>/dev/null; then
  echo "✅ Tüm paketler çalışıyor."
else
  echo "❌ Paketlerden biri yüklenemedi. Yukarıdaki hatayı paylaş."
  exit 1
fi

# Masaüstüne çift tıklanabilir kısayol
KISAYOL="$HOME/Desktop/BIST Toplu Tarama.command"
cat > "$KISAYOL" <<KOMUT
#!/bin/bash
cd "$KLASOR" || exit 1
echo "═══════════════════════════════════════"
echo "   BIST TOPLU TARAMA"
echo "═══════════════════════════════════════"
"$PY" toplu_tara.py
son=\$(ls -t toplu_tarama_*.xlsx 2>/dev/null | head -1)
if [ -n "\$son" ]; then
  echo ""
  echo "Excel açılıyor: \$son"
  open "\$son"
fi
echo ""
echo "Bitti. Bu pencereyi kapatabilirsin."
KOMUT
chmod +x "$KISAYOL"
echo "✅ Masaüstüne kısayol eklendi: BIST Toplu Tarama"

echo ""
echo "🎉 KURULUM TAMAM!"
echo "   Masaüstündeki 'BIST Toplu Tarama' dosyasına ÇİFT TIKLA."
echo "   (İlk açılışta uyarı çıkarsa: sağ tık → Aç → Aç)"
