"""
Ertesi gün performans raporu.

Önceki taramada çıkan kağıtların GÜNCEL fiyatını çeker, tarama anındaki
fiyatla karşılaştırır ve en çok yükselenden düşene sıralayarak Excel üretir.
Ayrıca strateji karnesi çıkarır (hangi strateji ortalama ne kazandırdı).

Çalıştır:
    python3 performans.py
"""

import os
from datetime import datetime, timezone, timedelta

from tradingview_screener import Query

import gecmis
import rapor_performans

IST = timezone(timedelta(hours=3))
KONUM = os.path.dirname(os.path.abspath(__file__))


def guncel_fiyatlar(kodlar):
    """{HISSE: (fiyat, gunluk_degisim)} döner."""
    kodlar = sorted({k for k in kodlar if k})
    if not kodlar:
        return {}
    out = {}
    # 40'lık gruplar halinde sor (uzun ticker listesi sorun çıkarmasın)
    for i in range(0, len(kodlar), 40):
        grup = kodlar[i:i + 40]
        try:
            _, df = (Query()
                     .set_markets("turkey")
                     .set_tickers(*[f"BIST:{k}" for k in grup])
                     .select("name", "close", "change")
                     .get_scanner_data())
            for _, r in df.iterrows():
                out[str(r["name"]).upper()] = (float(r["close"]), float(r["change"]))
        except Exception as e:
            print(f"  (fiyat alınamadı: {e})")
    return out


def hesapla(kayit=None):
    """Döner: (bilgi, satirlar, karne)"""
    kayit = kayit or gecmis.son_kayit(bugun_haric=True) or gecmis.son_kayit(bugun_haric=False)
    if not kayit:
        return None, [], []

    stratejiler = kayit.get("stratejiler", {})
    tum_kodlar = [h.get("hisse") for lst in stratejiler.values() for h in lst]
    fiyatlar = guncel_fiyatlar(tum_kodlar)

    # Aynı hisse birden çok stratejide çıkabilir → stratejileri birleştir
    birlesik = {}
    for strateji, liste in stratejiler.items():
        for h in liste:
            kod = (h.get("hisse") or "").upper()
            if not kod:
                continue
            eski = float(h.get("fiyat") or 0)
            kayit_ = birlesik.setdefault(kod, {"hisse": kod, "eski": eski, "stratejiler": []})
            kayit_["stratejiler"].append(strateji)
            if not kayit_["eski"]:
                kayit_["eski"] = eski

    satirlar = []
    for kod, v in birlesik.items():
        yeni, _ = fiyatlar.get(kod, (None, None))
        degisim = ((yeni - v["eski"]) / v["eski"] * 100) if (yeni and v["eski"]) else None
        satirlar.append({
            "hisse": kod,
            "strateji": ", ".join(dict.fromkeys(v["stratejiler"])),
            "eski": v["eski"] or None,
            "yeni": yeni,
            "degisim": degisim,
        })
    satirlar.sort(key=lambda s: (s["degisim"] is None, -(s["degisim"] or 0)))

    # Strateji karnesi
    karne = []
    for strateji, liste in stratejiler.items():
        getiriler = []
        for h in liste:
            kod = (h.get("hisse") or "").upper()
            eski = float(h.get("fiyat") or 0)
            yeni = fiyatlar.get(kod, (None, None))[0]
            if eski and yeni:
                getiriler.append((yeni - eski) / eski * 100)
        karne.append({
            "strateji": strateji,
            "adet": len(liste),
            "ortalama": (sum(getiriler) / len(getiriler)) if getiriler else None,
            "kazanan": sum(1 for g in getiriler if g > 0),
            "kaybeden": sum(1 for g in getiriler if g < 0),
        })
    karne.sort(key=lambda k: (k["ortalama"] is None, -(k["ortalama"] or 0)))

    bilgi = {
        "tarama_zamani": kayit.get("zaman", "?"),
        "simdi": datetime.now(IST).strftime("%d.%m.%Y %H:%M"),
    }
    return bilgi, satirlar, karne


def calistir():
    bilgi, satirlar, karne = hesapla()
    if not bilgi:
        print("Karşılaştırılacak önceki tarama kaydı yok.")
        print("Önce bir tarama çalıştır (toplu_tara.py), ertesi gün bunu çalıştır.")
        return None

    print(f"📊 {bilgi['tarama_zamani']} taramasındaki kağıtların "
          f"{bilgi['simdi']} itibarıyla durumu:\n")
    for s in satirlar[:10]:
        d = f"{s['degisim']:+.2f}%" if s["degisim"] is not None else "—"
        print(f"  {s['hisse']:8s} {d:>9s}   {s['strateji'][:40]}")
    if len(satirlar) > 10:
        print(f"  … ve {len(satirlar) - 10} tane daha")

    data = rapor_performans.performans_excel(bilgi, satirlar, karne)
    dosya = os.path.join(KONUM, "performans_" +
                         datetime.now(IST).strftime("%d-%m-%Y_%H%M") + ".xlsx")
    with open(dosya, "wb") as f:
        f.write(data)
    print(f"\n✅ Excel yazıldı: {dosya}")

    try:
        import sys, subprocess
        if sys.platform.startswith("win"):
            os.startfile(dosya)
        elif sys.platform == "darwin":
            subprocess.run(["open", dosya], check=False)
    except Exception:
        pass
    return dosya


if __name__ == "__main__":
    calistir()
