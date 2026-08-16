"""
Kendini günceller: GitHub'daki en son sürümü indirip .py dosyalarını tazeler.

CALISTIR.bat / PERFORMANS.bat her çalıştığında sessizce çağırır.
İnternet yoksa veya bir sorun olursa hiçbir şey bozmaz, mevcut sürümle devam eder.
"""

import io
import os
import sys
import zipfile
import urllib.request

ZIP = "https://github.com/irifanemre/bist_tarayici/archive/refs/heads/main.zip"
KONUM = os.path.dirname(os.path.abspath(__file__))

# Buluttan güncellenecekler: kod + strateji listesi
# (stratejiler merkezi yönetiliyor, yeni indikatör eklenince herkese gitsin)
UZANTILAR = (".py", ".txt")
EK_DOSYALAR = {"kombinler.json"}

# Yerelde kalması gerekenler — ASLA üzerine yazılmaz
KORUNAN = {"telegram.json", "takip.json", "zamanlamalar.json", "gonderim.json"}


def guncelle(sessiz=True):
    try:
        with urllib.request.urlopen(ZIP, timeout=25) as r:
            veri = r.read()
        zf = zipfile.ZipFile(io.BytesIO(veri))

        degisen = 0
        for isim in zf.namelist():
            ad = os.path.basename(isim)
            if not ad or ad in KORUNAN:
                continue
            if not (ad.endswith(UZANTILAR) or ad in EK_DOSYALAR):
                continue
            if "/" in isim.split("/", 1)[1] and not isim.split("/", 1)[1].startswith(ad):
                continue  # alt klasörleri atla (.github vb.)
            yeni = zf.read(isim)
            hedef = os.path.join(KONUM, ad)
            try:
                with open(hedef, "rb") as f:
                    if f.read() == yeni:
                        continue
            except FileNotFoundError:
                pass
            with open(hedef, "wb") as f:
                f.write(yeni)
            degisen += 1

        if not sessiz or degisen:
            print(f"[guncelleme] {degisen} dosya yenilendi." if degisen
                  else "[guncelleme] zaten guncel.")
        return degisen
    except Exception as e:
        if not sessiz:
            print(f"[guncelleme] atlandi: {e}")
        return 0


if __name__ == "__main__":
    guncelle(sessiz="--sessiz" in sys.argv)
