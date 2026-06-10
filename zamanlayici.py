"""
Zamanlama motoru — launchd her 60 sn bunu çalıştırır.
Vakti gelen bildirimleri tarar ve Telegram'a gönderir.

Sağlamlık:
  - Her bildirim ayrı try/except içinde; biri patlarsa diğerleri etkilenmez.
  - Telegram gönderimi 3 kez denenir (geçici ağ hatalarına dayanıklı).
  - Olaylar motor.log'a yazılır (1 MB'ı geçince eski yarısı atılır).
  - Her çalışma durum.json'a "son_tik" yazar (uygulama bunu gösterir).

Token/chat: önce ortam değişkeni, yoksa telegram.json'dan okunur.
"""

import os
import json
import time
from datetime import datetime

import requests

import zamanlama_store as zs
from depo_util import json_yaz

KONUM = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(KONUM, "motor.log")
DURUM = os.path.join(KONUM, "durum.json")


def _log(mesaj: str):
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > 1_000_000:
            with open(LOG, encoding="utf-8", errors="ignore") as f:
                satirlar = f.readlines()[-500:]
            with open(LOG, "w", encoding="utf-8") as f:
                f.writelines(satirlar)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {mesaj}\n")
    except OSError:
        pass


def _durum_yaz(olay: str = ""):
    try:
        json_yaz(DURUM, {"son_tik": datetime.now().isoformat(timespec="seconds"),
                         "son_olay": olay})
    except OSError:
        pass


def _telegram_cfg():
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


def _gonder(chat_id, metin, deneme=3) -> bool:
    """Telegram'a gönderir; geçici hatalarda yeniden dener. Başarı=True."""
    token, _ = _telegram_cfg()
    if not token or not chat_id:
        _log("UYARI: token/chat tanımsız, gönderilemedi")
        return False
    for i in range(deneme):
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": metin, "parse_mode": "Markdown"},
                timeout=20,
            )
            if r.ok:
                return True
            _log(f"Telegram yanıt {r.status_code}: {r.text[:120]}")
        except requests.RequestException as e:
            _log(f"Gönderim denemesi {i+1}/{deneme} hata: {e}")
        time.sleep(2 * (i + 1))
    return False


def _fire_mi(z, now) -> bool:
    if z.get("saat") != now.strftime("%H:%M"):
        return False
    if z.get("son_calisma") == now.strftime("%Y-%m-%d"):
        return False
    if z.get("tip") == "tek":
        return z.get("tarih") == now.strftime("%Y-%m-%d")
    g = z.get("gunler", "hergun")
    wd = now.weekday()
    if g == "hergun":
        return True
    if g == "haftaici":
        return wd < 5
    if g == "haftalik":
        return int(z.get("hafta_gunu", 0)) == wd
    return False


def tick():
    now = datetime.now()
    bugun = now.strftime("%Y-%m-%d")
    _, varsayilan_chat = _telegram_cfg()
    gonderilen = 0

    for z in zs.tum():
        try:
            if not z.get("aktif", True):
                continue
            if not _fire_mi(z, now):
                continue

            # Ağır modüller yalnızca gerçekten tetiklenince yüklenir
            from otomasyon import tarama_metni
            import kombin_store as ks

            paket = ks.tum_kombinler().get(z["kombin"])
            if paket is None:
                _log(f"UYARI: '{z.get('kombin')}' kombini yok, atlandı")
                continue

            metin = tarama_metni(z["kombin"], paket) or f"📊 *{z['kombin']}* — eşleşme yok."
            hedef = z.get("chat_id") or varsayilan_chat

            if _gonder(hedef, "⏰ Otomatik tarama\n\n" + metin):
                if z.get("tip") == "tek":
                    zs.guncelle(z["id"], aktif=False, son_calisma=bugun)
                else:
                    zs.guncelle(z["id"], son_calisma=bugun)
                gonderilen += 1
                _log(f"GÖNDERİLDİ: '{z['kombin']}' -> {hedef}")
            else:
                _log(f"GÖNDERİLEMEDİ: '{z['kombin']}' (ağ/Telegram hatası)")
        except Exception as e:  # bir bildirim diğerlerini düşürmesin
            _log(f"HATA ({z.get('kombin', '?')}): {e}")

    _durum_yaz(f"{gonderilen} gönderildi" if gonderilen else "tetiklenen yok")


if __name__ == "__main__":
    tick()
