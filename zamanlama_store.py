"""
Otomatik bildirim zamanlamalarını zamanlamalar.json'da saklar.

Her kayıt:
  {
    "id": "ab12cd34",
    "kombin": "Momentum Test",
    "tip": "rutin" | "tek",
    "saat": "09:45",
    "gunler": "hergun" | "haftaici" | "haftalik",   # rutin için
    "hafta_gunu": 0,                                  # haftalık için (0=Pzt)
    "tarih": "2026-06-12",                            # tek seferlik için
    "chat_id": "123456789",
    "aktif": true,
    "son_calisma": "2026-06-10"
  }
"""

import os
import uuid

from depo_util import json_oku, json_yaz

DOSYA = os.path.join(os.path.dirname(__file__), "zamanlamalar.json")


def tum() -> list:
    return json_oku(DOSYA, [])


def _yaz(liste):
    json_yaz(DOSYA, liste)


def ekle(kayit: dict) -> str:
    liste = tum()
    kayit["id"] = uuid.uuid4().hex[:8]
    kayit.setdefault("aktif", True)
    liste.append(kayit)
    _yaz(liste)
    return kayit["id"]


def sil(_id: str):
    _yaz([z for z in tum() if z.get("id") != _id])


def guncelle(_id: str, **alanlar):
    liste = tum()
    for z in liste:
        if z.get("id") == _id:
            z.update(alanlar)
    _yaz(liste)
