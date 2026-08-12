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
echo "✅ Python bulundu: $PY"

echo ""
echo "📦 Gerekli paketler kuruluyor (birkaç dakika sürebilir)…"
"$PY" -m pip install --user --quiet --upgrade pip 2>/dev/null || true
"$PY" -m pip install --user --quiet -r requirements.txt
echo "✅ Paketler kuruldu."

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
