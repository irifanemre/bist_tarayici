"""
Kullanıcının kurduğu indikatör kombinlerini diske kaydeder/okur.
Atomik yazım için depo_util kullanılır (eşzamanlı erişimde bozulmaz).
"""

import os

from depo_util import json_oku, json_yaz

DOSYA = os.path.join(os.path.dirname(__file__), "kombinler.json")


def tum_kombinler() -> dict:
    """{kombin_adı: paket} döner."""
    return json_oku(DOSYA, {})


def kaydet(ad: str, paket) -> None:
    d = tum_kombinler()
    d[ad] = paket
    json_yaz(DOSYA, d)


def sil(ad: str) -> None:
    d = tum_kombinler()
    d.pop(ad, None)
    json_yaz(DOSYA, d)
