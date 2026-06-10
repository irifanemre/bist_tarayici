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
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat, "text": metin, "parse_mode": "Markdown"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


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

    tam = "\n\n".join(parcalar) if parcalar else "Taranacak kombin yok."
    print(tam)

    if gonder:
        telegram_gonder(tam)
        print("\n✅ Telegram'a gönderildi.")
    else:
        print("\n(dry-run: gönderilmedi)")


if __name__ == "__main__":
    gonder = "--dry-run" not in sys.argv
    calistir(gonder=gonder)
