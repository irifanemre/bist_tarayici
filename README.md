# 📊 BIST İndikatör Tarayıcı

TradingView verisiyle Borsa İstanbul hisselerini, seçtiğin indikatör kombinine göre tarayan Streamlit uygulaması.

## Özellikler
- **58 indikatör + 20 hazır sinyal** (mum formasyonları, Ichimoku dahil), en fazla 30'unu kombinleme (VE / VEYA)
- Zaman dilimi (günlük / 1s / 4s / haftalık), endeks (BIST 30/50/100), sektör filtresi
- Teknik Rating + temel analiz (F/K, PD/DD, ROE, ciro büyümesi, piyasa değeri…)
- Hazır strateji şablonları, kombin kaydet/yükle
- Sonuçta hisseye tıkla → indikatörlü TradingView grafiği gömülü açılır
- Canlı piyasa paneli (BIST100, altın, dolar, euro, Dow) + 3 hisselik takip listesi
- **Otomatik bildirim**: kombini istediğin saatte tarayıp Telegram'a yollar (launchd motoru)

## Kurulum
```bash
pip install -r requirements.txt     # sürümler kararlılık için sabit
```

## Çalıştırma
```bash
./baslat.sh
# veya:  python3 -m streamlit run app.py
```

## Testler
```bash
python3 -m pytest -q                 # çekirdek mantık testleri (ağ gerektirmez)
```

## Otomatik bildirim (Telegram)
1. `telegram.json` içine bot token + chat id yaz (@BotFather'dan).
2. Uygulamada sol panel **⏰ Otomatik Bildirim** → kombin/saat/sıklık/alıcı seç → kur.
3. Motor (`zamanlayici.py`) `~/Library/LaunchAgents/com.iri.bisttarayici.zamanlayici.plist`
   ile her 60 sn çalışır; vakti gelince Telegram'a yollar.
   - ⚠️ Bilgisayar o saatte **açık** olmalı.
   - Manuel tek seferlik gönderim: `./bildirim.sh`

## Kararlılık notları
- Tüm JSON dosyaları **atomik** yazılır (eşzamanlı erişimde bozulmaz).
- Motorda her bildirim ayrı `try/except`; biri patlarsa diğerleri sürer.
- Telegram gönderimi ve tarama **3 kez** denenir (geçici ağ hatalarına dayanıklı).
- Motor durumu `durum.json` + olay günlüğü `motor.log` (otomatik döndürülür).

## Buluta yükleme (telefondan erişim — opsiyonel)
1. Klasörü GitHub deposuna yükle (`telegram.json`, `bildirim.sh`, `kombinler.json` `.gitignore`'da — sırlar sızmaz).
2. https://share.streamlit.io → New app → depo + `app.py` → Deploy.

## Dosyalar
| Dosya | Görev |
|-------|-------|
| `app.py` | Streamlit arayüzü |
| `indikatorler.py` | İndikatör kataloğu, koşul kurucu, strateji şablonları |
| `tarayici.py` | Tarama motoru (zaman/endeks/sektör/VE-VEYA + retry) |
| `piyasa.py` | Canlı kurlar + takip listesi |
| `kombin_store.py` / `zamanlama_store.py` / `depo_util.py` | Atomik JSON depolama |
| `zamanlayici.py` / `otomasyon.py` / `bildirim.sh` | Otomatik bildirim |
| `test_temel.py` | pytest testleri |

> ⚠️ Yatırım tavsiyesi değildir. Veriler TradingView / Yahoo Finance kaynaklı, gecikmeli olabilir.
