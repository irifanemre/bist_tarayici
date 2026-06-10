# ☁️ Buluta Taşıma Rehberi

İki bağımsız kazanım:
- **A) Telefondan erişim** — uygulamayı Streamlit Cloud'da çalıştır, linkle gir.
- **B) 7/24 bildirim** — bilgisayar kapalıyken bile GitHub Actions Telegram'a yollar.

> Sırlar güvende: `telegram.json`, `bildirim.sh`, `kombinler.json` vb. `.gitignore`'da.
> Token'ı dosyaya değil, **GitHub/Streamlit "Secrets"** alanına gireceğiz.

---

## Ön hazırlık — kodu GitHub'a yükle
1. github.com'da ücretsiz hesap aç (yoksa).
2. Yeni bir depo oluştur: **New repository** → ad: `bist-tarayici` → **Private** seç → Create.
3. Bu klasörde (zaten `git init` yapıldı), GitHub'ın verdiği iki satırı çalıştır:
   ```bash
   cd ~/Desktop/bist_tarayici
   git remote add origin https://github.com/KULLANICI_ADIN/bist-tarayici.git
   git branch -M main
   git push -u origin main
   ```

---

## A) Telefondan erişim (Streamlit Community Cloud)
1. https://share.streamlit.io → GitHub ile giriş yap.
2. **New app** → depo: `bist-tarayici`, dosya: `app.py` → **Deploy**.
3. 1-2 dakikada bir `https://...streamlit.app` linki çıkar. Telefonda aç, ana ekrana ekle.

> Not: Streamlit Cloud'da kaydettiğin kombinler kalıcı değildir (her yeniden başlatmada
> sıfırlanır). Canlı **tarama** için sorun değil; kalıcı kombin/bildirim için (B)'yi kullan.

---

## B) 7/24 Telegram bildirimi (GitHub Actions)
İş akışı hazır: `.github/workflows/bildirim.yml` (hafta içi 09:45'te tüm kayıtlı kombinleri tarar).

1. **Kombinlerini repoya ekle** (gizli değiller):
   ```bash
   git add -f kombinler.json
   git commit -m "kombinler" && git push
   ```
2. **Secrets ekle:** GitHub'da depo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `TELEGRAM_BOT_TOKEN` → bot token'ın
   - `TELEGRAM_CHAT_ID` → kendi chat ID'in (Telegram'da @userinfobot verir)
3. **Actions** sekmesi → iş akışını **Enable** et. İstersen "Run workflow" ile hemen test et.
4. Saati değiştirmek için `bildirim.yml` içindeki `cron: '45 6 * * 1-5'` satırını düzenle
   (UTC; İstanbul = UTC+3, yani 09:45 → 06:45).

Artık bilgisayarın kapalı olsa da bildirimler gelir. ✅

---

## Yerelde ne değişir?
Hiçbir şey. Yerel `launchd` motoru ve `./baslat.sh` aynen çalışmaya devam eder.
Bulut, bunların **yedeği/uzantısıdır**.
