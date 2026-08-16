"""
Tarama geçmişi — her taramanın "fotoğrafını" saklar.

Her kayıt: taramalar/YYYY-MM-DD_HHMM.json
  {"zaman": "13.08.2026 18:20",
   "veri_saati": "13.08 18:09",
   "stratejiler": {"MARGASİ orj": [{"hisse": "CUSAN", "fiyat": 30.46}, ...]}}

Ertesi gün performans karşılaştırması bu kayıtlardan yapılır.
"""

import os
import glob
from datetime import datetime, timezone, timedelta

from depo_util import json_oku, json_yaz

KONUM = os.path.dirname(os.path.abspath(__file__))
KLASOR = os.path.join(KONUM, "taramalar")
IST = timezone(timedelta(hours=3))


def kaydet(stratejiler: dict, veri_saati=None) -> str:
    """stratejiler: {strateji_adi: [{hisse, fiyat}]}"""
    os.makedirs(KLASOR, exist_ok=True)
    simdi = datetime.now(IST)
    dosya = os.path.join(KLASOR, simdi.strftime("%Y-%m-%d_%H%M") + ".json")
    json_yaz(dosya, {
        "zaman": simdi.strftime("%d.%m.%Y %H:%M"),
        "tarih": simdi.strftime("%Y-%m-%d"),
        "veri_saati": veri_saati,
        "stratejiler": stratejiler,
    })
    return dosya


def tum_kayitlar() -> list:
    """Eskiden yeniye sıralı dosya yolları."""
    return sorted(glob.glob(os.path.join(KLASOR, "*.json")))


def kayitli_gunler() -> list:
    """Kayıt bulunan günler (YYYY-MM-DD), yeniden eskiye."""
    gunler = []
    for yol in tum_kayitlar():
        v = json_oku(yol, None)
        if v and v.get("tarih") and v["tarih"] not in gunler:
            gunler.append(v["tarih"])
    return sorted(set(gunler), reverse=True)


def gunun_kaydi(tarih: str):
    """Verilen günün (YYYY-MM-DD) taraması. Aynı günde birden çok kayıt varsa
    18:20'ye en yakın olanı seçer (asıl günlük tarama odur)."""
    adaylar = []
    for yol in tum_kayitlar():
        v = json_oku(yol, None)
        if v and v.get("tarih") == tarih:
            try:
                ss, dd = v["zaman"].split()[1].split(":")
                fark = abs(int(ss) * 60 + int(dd) - (18 * 60 + 20))
            except Exception:
                fark = 9999
            adaylar.append((fark, v))
    if not adaylar:
        return None
    return min(adaylar, key=lambda x: x[0])[1]


def son_kayit(bugun_haric=True):
    """En son taramayı döndürür. bugun_haric=True ise bugünkü kayıtları atlar
    (ertesi gün karşılaştırması için 'dünkü' kaydı bulur)."""
    bugun = datetime.now(IST).strftime("%Y-%m-%d")
    for yol in reversed(tum_kayitlar()):
        veri = json_oku(yol, None)
        if not veri:
            continue
        if bugun_haric and veri.get("tarih") == bugun:
            continue
        return veri
    return None
