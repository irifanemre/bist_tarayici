"""
Telegram komut botu — sen mesaj at, o taramayı yapıp göndersin.

Komutlar:
    /tara            → 15 stratejinin hepsini tara, sonucu gönder
    /tara <isim>     → sadece o stratejiyi tara (örn: /tara MARGASİ orj)
    /liste           → kayıtlı stratejileri listele
    /yardim          → komutları göster

Çalıştır:
    python3 bot.py            (arka planda sürekli dinler)
"""

import os
import json
import time
from datetime import datetime, timezone, timedelta

import requests

import kombin_store as ks
from otomasyon import tarama_metni

KONUM = os.path.dirname(os.path.abspath(__file__))
IST = timezone(timedelta(hours=3))


def _cfg():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    p = os.path.join(KONUM, "telegram.json")
    if (not token or not chat) and os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            token = token or d.get("bot_token")
            chat = chat or d.get("chat_id")
        except (json.JSONDecodeError, OSError):
            pass
    return token, chat


TOKEN, VARSAYILAN_CHAT = _cfg()
API = f"https://api.telegram.org/bot{TOKEN}"


def gonder(chat_id, metin):
    """Uzun mesajları bölerek gönderir."""
    for i in range(0, len(metin), 3800):
        try:
            requests.post(f"{API}/sendMessage",
                          json={"chat_id": chat_id, "text": metin[i:i + 3800],
                                "parse_mode": "Markdown"}, timeout=20)
        except requests.RequestException as e:
            print("gönderim hatası:", e)


def tum_tarama():
    kayitlar = ks.tum_kombinler()
    if not kayitlar:
        return "Kayıtlı strateji yok."
    parcalar = []
    for ad, paket in kayitlar.items():
        try:
            parcalar.append(tarama_metni(ad, paket) or f"📊 *{ad}* — eşleşme yok.")
        except Exception as e:
            parcalar.append(f"📊 *{ad}* — hata: {e}")
    bas = (f"🔔 *BIST TARAMASI*\n📅 {datetime.now(IST):%d.%m.%Y %H:%M} · "
           f"{len(kayitlar)} strateji\n{'─' * 22}")
    return bas + "\n\n" + "\n\n".join(parcalar)


def tek_tarama(isim):
    kayitlar = ks.tum_kombinler()
    # büyük/küçük harf duyarsız eşleştirme
    eslesen = next((a for a in kayitlar if a.lower() == isim.lower()), None)
    if not eslesen:
        eslesen = next((a for a in kayitlar if isim.lower() in a.lower()), None)
    if not eslesen:
        return (f"'{isim}' bulunamadı.\n\nKayıtlılar:\n"
                + "\n".join("• " + a for a in kayitlar))
    govde = tarama_metni(eslesen, kayitlar[eslesen]) or f"📊 *{eslesen}* — eşleşme yok."
    return f"🕐 *{datetime.now(IST):%d.%m.%Y %H:%M}* itibarıyla tarandı\n{'─' * 22}\n" + govde


def komut_isle(metin, chat_id):
    m = (metin or "").strip()
    dusuk = m.lower()

    if dusuk.startswith("/tara"):
        arg = m[5:].strip()
        gonder(chat_id, "⏳ Taranıyor, birkaç saniye…")
        return tek_tarama(arg) if arg else tum_tarama()

    if dusuk.startswith("/liste"):
        k = ks.tum_kombinler()
        return (f"📋 *{len(k)} kayıtlı strateji:*\n"
                + "\n".join(f"{i}. {a}" for i, a in enumerate(k, 1)))

    if dusuk.startswith("/id"):
        return f"🆔 Senin chat ID'in: `{chat_id}`\n\nBu numarayı bildirim listesine eklemek için paylaş."

    if dusuk.startswith("/start") or dusuk.startswith("/yardim") or dusuk.startswith("/help"):
        return (f"🤖 *BIST Tarayıcı Bot*\n🆔 Chat ID'in: `{chat_id}`\n\n"
                "*/tara* — tüm stratejileri tara\n"
                "*/tara <isim>* — tek strateji (örn: `/tara HAFT`)\n"
                "*/liste* — stratejileri listele\n"
                "*/id* — chat ID'ini göster\n"
                "*/yardim* — bu mesaj\n\n"
                "_Ayrıca hafta içi 18:20'de otomatik tarama gelir._")

    return "Anlamadım. */yardim* yazarak komutları görebilirsin."


def calistir():
    if not TOKEN:
        print("TELEGRAM_BOT_TOKEN yok — telegram.json'u kontrol et.")
        return
    print("🤖 Bot dinlemede… (Telegram'dan /tara yaz)")
    # Bulutta (GitHub Actions) çalışırken belirli süre sonra temiz çık;
    # iş akışı saat başı yeniden başlatır. Yerelde sınırsız çalışır.
    sure = int(os.environ.get("BOT_SURE_SN", "0"))
    bitis = time.time() + sure if sure else None

    offset = None
    while True:
        if bitis and time.time() > bitis:
            print("süre doldu, temiz çıkış")
            return
        try:
            r = requests.get(f"{API}/getUpdates",
                             params={"timeout": 50, "offset": offset}, timeout=60)
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message")
                if not msg:
                    continue
                chat_id = msg["chat"]["id"]
                metin = msg.get("text", "")
                print(f"[{datetime.now(IST):%H:%M:%S}] {chat_id}: {metin}")
                try:
                    gonder(chat_id, komut_isle(metin, chat_id))
                except Exception as e:
                    gonder(chat_id, f"Hata: {e}")
        except requests.RequestException:
            time.sleep(5)
        except Exception as e:
            print("hata:", e)
            time.sleep(5)


if __name__ == "__main__":
    calistir()
