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
        # GitHub arşivi kısa süre önbelleklenebiliyor; taze sürüm için
        # önbellek kırıcı parametre + no-cache başlığı gönderiyoruz.
        import time as _t
        istek = urllib.request.Request(
            f"{ZIP}?t={int(_t.time())}",
            headers={"Cache-Control": "no-cache", "Pragma": "no-cache",
                     "User-Agent": "bist-tarayici-guncelleyici"})
        with urllib.request.urlopen(istek, timeout=25) as r:
            veri = r.read()
        zf = zipfile.ZipFile(io.BytesIO(veri))

        degisen = 0
        yenilenenler = []
        for isim in zf.namelist():
            ad = os.path.basename(isim)
            if not ad or ad in KORUNAN:
                continue

            # ZIP içi yol: "bist_tarayici-main/<ic_yol>"
            ic_yol = isim.split("/", 1)[1] if "/" in isim else isim

            # Tarama geçmişi ve günlük kapanışlar — buluttaki günlük kayıtlar
            if ic_yol.startswith(("taramalar/", "fiyatlar/")) and ad.endswith(".json"):
                hedef = os.path.join(KONUM, ic_yol.split("/", 1)[0], ad)
                os.makedirs(os.path.dirname(hedef), exist_ok=True)
            else:
                if not (ad.endswith(UZANTILAR) or ad in EK_DOSYALAR):
                    continue
                if "/" in ic_yol:
                    continue  # diğer alt klasörleri atla (.github vb.)
                hedef = os.path.join(KONUM, ad)

            yeni = zf.read(isim)
            try:
                with open(hedef, "rb") as f:
                    if f.read() == yeni:
                        continue
            except FileNotFoundError:
                pass
            with open(hedef, "wb") as f:
                f.write(yeni)
            degisen += 1
            yenilenenler.append(ad)

        # requirements.txt değiştiyse eksik paketleri kur
        if "requirements.txt" in yenilenenler:
            print("[guncelleme] paket listesi degisti, eksikler kuruluyor...")
            try:
                import subprocess
                subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                                "-r", os.path.join(KONUM, "requirements.txt")],
                               timeout=600)
            except Exception as e:
                print(f"[guncelleme] paket kurulumu atlandi: {e}")

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
