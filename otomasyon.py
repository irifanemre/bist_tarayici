"""
Otomatik tarama + Telegram bildirimi.

Kayıtlı kombinleri (kombinler.json) tarar, sonucu Telegram'a gönderir.
Zamanlanmış çalıştırmak için (örn. her sabah 09:45) cron / Görev Zamanlayıcı kullan:

    45 9 * * 1-5  cd ~/Desktop/bist_tarayici && /usr/bin/python3 otomasyon.py

Gerekli ortam değişkenleri (Telegram için):
    TELEGRAM_BOT_TOKEN  — @BotFather'dan alınan bot token'ı
    TELEGRAM_CHAT_ID    — mesajın gideceği sohbet/kullanıcı id'si

Test (göndermeden, ekrana bas):
    python3 otomasyon.py --dry-run
"""

import os
import sys

import requests

import kombin_store as ks
from indikatorler import ZAMAN_DILIMLERI, ENDEKSLER, SEKTORLER
from tarayici import tara, rating_etiket

_TR2EN = {v: k for k, v in SEKTORLER.items()}


def _meta(paket):
    """Kayıtlı paketi tara() argümanlarına çevirir (eski liste formatını da destekler)."""
    if isinstance(paket, list):
        return paket, "", None, None, "VE"
    secimler = paket.get("secimler", [])
    zaman = ZAMAN_DILIMLERI.get(paket.get("zaman", "Günlük"), "")
    endeks = ENDEKSLER.get(paket.get("endeks", "Tüm BIST"))
    sektor_tr = paket.get("sektorler", []) or []
    sektorler = [_TR2EN[s] for s in sektor_tr if s in _TR2EN] or None
    mantik = paket.get("mantik", "VE")
    return secimler, zaman, endeks, sektorler, mantik


def tarama_metni(ad: str, paket, limit: int = 15):
    """Bir kombin için Telegram'a uygun özet metni döndürür (None = boş kombin)."""
    secimler, zaman, endeks, sektorler, mantik = _meta(paket)
    if not secimler:
        return None
    toplam, df = tara(secimler, limit=limit, zaman=zaman,
                      endeks=endeks, sektorler=sektorler, mantik=mantik)
    if not toplam or df is None or len(df) == 0:
        return f"📊 *{ad}* — eşleşme yok."

    satirlar = []
    for _, r in df.iterrows():
        satirlar.append(
            f"• {r['name']}  {float(r['close']):g}  "
            f"({float(r['change']):+.1f}%)  [{rating_etiket(r['Recommend.All'])}]"
        )
    return f"📊 *{ad}* — {toplam} eşleşme (ilk {len(df)}):\n" + "\n".join(satirlar)


def telegram_gonder(metin: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID ortam değişkenleri tanımlı değil.")
    # Birden çok alıcı: TELEGRAM_CHAT_ID="123,456" şeklinde virgülle ayrılabilir
    sonuc = []
    for cid in str(chat).replace(" ", "").split(","):
        if not cid:
            continue
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": cid, "text": metin, "parse_mode": "Markdown"},
            timeout=20,
        )
        sonuc.append({cid: r.ok})
    return sonuc


def calistir(gonder: bool = True):
    kayitlar = ks.tum_kombinler()
    if not kayitlar:
        print("Kayıtlı kombin yok — önce uygulamadan bir kombin kaydet.")
        return

    parcalar = []
    for ad, paket in kayitlar.items():
        try:
            metin = tarama_metni(ad, paket)
            if metin:
                parcalar.append(metin)
        except Exception as e:
            parcalar.append(f"📊 *{ad}* — tarama hatası: {e}")

    from datetime import datetime, timezone, timedelta
    ist = datetime.now(timezone(timedelta(hours=3)))  # İstanbul saati
    baslik = (f"🔔 *GÜNLÜK BIST TARAMASI*\n"
              f"📅 {ist:%d.%m.%Y %H:%M} · {len(kayitlar)} strateji\n"
              f"{'─' * 22}")
    tam = baslik + "\n\n" + ("\n\n".join(parcalar) if parcalar else "Taranacak kombin yok.")
    print(tam)

    if gonder:
        # Telegram mesaj sınırı 4096 karakter — uzunsa parçalara böl
        for i in range(0, len(tam), 3800):
            telegram_gonder(tam[i:i + 3800])
        print("\n✅ Telegram'a gönderildi.")
    else:
        print("\n(dry-run: gönderilmedi)")


import json  # noqa: E402  (günlük gönderim kaydı için)

KONUM = os.path.dirname(os.path.abspath(__file__))
DURUM_DOSYA = os.path.join(KONUM, "gonderim.json")


def gunluk_kontrol(hedef_saat="18:20"):
    """Günde bir kez, hedef saatten sonra gönderim yapılmasını sağlar.
    GitHub zamanlamayı geciktirse bile gün içindeki ilk uygun çalışmada gönderir.
    Döner: (gonderilsin_mi, aciklama)"""
    from datetime import datetime, timezone, timedelta
    ist = datetime.now(timezone(timedelta(hours=3)))
    bugun = ist.strftime("%Y-%m-%d")

    if ist.weekday() >= 5:
        return False, "hafta sonu"

    ss, dd = (int(x) for x in hedef_saat.split(":"))
    if (ist.hour, ist.minute) < (ss, dd):
        return False, f"vakit gelmedi ({ist:%H:%M} < {hedef_saat})"

    try:
        with open(DURUM_DOSYA, encoding="utf-8") as f:
            if json.load(f).get("son_gonderim") == bugun:
                return False, "bugün zaten gönderildi"
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    return True, f"gönderilecek ({ist:%H:%M})"


def gunluk_isaretle():
    from datetime import datetime, timezone, timedelta
    ist = datetime.now(timezone(timedelta(hours=3)))
    try:
        with open(DURUM_DOSYA, "w", encoding="utf-8") as f:
            json.dump({"son_gonderim": ist.strftime("%Y-%m-%d"),
                       "saat": ist.strftime("%H:%M")}, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


if __name__ == "__main__":
    if "--gunluk" in sys.argv:
        tamam, neden = gunluk_kontrol()
        print(f"günlük kontrol: {neden}")
        if tamam:
            calistir(gonder=True)
            gunluk_isaretle()
    else:
        calistir(gonder="--dry-run" not in sys.argv)
