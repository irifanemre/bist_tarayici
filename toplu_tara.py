"""
Tüm kayıtlı kombinleri tek seferde tarar, çıkan firmaları sütunlu Excel'e döker.
Her strateji = bir sütun, altında o taramada çıkan firmalar (tek sayfada).

Çalıştır:
    cd ~/Desktop/bist_tarayici
    python3 toplu_tara.py
"""

import os
from datetime import datetime

import kombin_store as ks
from tarayici import tara, veri_bilgisi
from otomasyon import _meta
import rapor


def calistir(limit=100):
    kayitlar = ks.tum_kombinler()
    if not kayitlar:
        print("Kayıtlı kombin yok — önce uygulamada kombin kaydet.")
        return None

    print(f"{len(kayitlar)} strateji taranıyor…\n")
    bolumler = []
    veri_saati = None

    for ad, paket in kayitlar.items():
        secimler, zaman, endeks, sektorler, mantik = _meta(paket)
        try:
            toplam, df = tara(secimler, limit=limit, zaman=zaman,
                              endeks=endeks, sektorler=sektorler, mantik=mantik)
            if veri_saati is None and df is not None and len(df):
                veri_saati = veri_bilgisi(df).get("saat")
            firmalar = [{"hisse": r.get("name", "")} for _, r in df.iterrows()] if df is not None else []
            print(f"  {ad}: {len(firmalar)} firma")
        except Exception as e:
            print(f"  {ad}: HATA ({e})")
            firmalar = []
        bolumler.append({"ad": ad, "satirlar": firmalar})

    zaman_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    data = rapor.toplu_rapor_excel(bolumler, zaman_str, veri_saati)

    dosya = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "toplu_tarama_" + datetime.now().strftime("%d-%m-%Y_%H%M") + ".xlsx",
    )
    with open(dosya, "wb") as f:
        f.write(data)
    print(f"\n✅ Excel yazıldı: {dosya}")

    # Dosyayı otomatik aç (Windows / macOS / Linux)
    try:
        import sys, subprocess
        if sys.platform.startswith("win"):
            os.startfile(dosya)           # noqa: S606 (Windows)
        elif sys.platform == "darwin":
            subprocess.run(["open", dosya], check=False)
        else:
            subprocess.run(["xdg-open", dosya], check=False)
    except Exception:
        pass
    return dosya


if __name__ == "__main__":
    calistir()
