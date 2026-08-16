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
                     .select("name", "close", "change", "current_session")
                     .get_scanner_data())
            for _, r in df.iterrows():
                out[str(r["name"]).upper()] = (float(r["close"]), float(r["change"]))
                globals()["_SESSION"] = str(r.get("current_session", ""))
        except Exception as e:
            print(f"  (fiyat alınamadı: {e})")
    return out


def hesapla(kayit=None):
    """Döner: (bilgi, satirlar, karne)"""
    kayit = kayit or gecmis.son_kayit(bugun_haric=True) or gecmis.son_kayit(bugun_haric=False)
    if not kayit:
        return None, [], [], []

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

    # Strateji bazlı bölümler (ızgara düzeni için) — sıralı: en çok yükselen üstte
    bolumler = []
    for strateji, liste in stratejiler.items():
        blok = []
        for h in liste:
            kod = (h.get("hisse") or "").upper()
            eski = float(h.get("fiyat") or 0)
            yeni = fiyatlar.get(kod, (None, None))[0]
            deg = ((yeni - eski) / eski * 100) if (yeni and eski) else None
            blok.append({"hisse": kod, "eski": eski or None, "yeni": yeni, "degisim": deg})
        blok.sort(key=lambda s: (s["degisim"] is None, -(s["degisim"] or 0)))
        bolumler.append({"ad": strateji, "satirlar": blok})

    acik = globals().get("_SESSION") == "market"
    ayni_seans = all((s["degisim"] or 0) == 0 for s in satirlar) and satirlar
    uyari = ""
    if not acik and ayni_seans:
        uyari = ("⚠️ Borsa kapalı ve fiyatlar tarama anıyla aynı — gerçek fark "
                 "bir sonraki işlem gününün kapanışında görünecek.")
    elif not acik:
        uyari = "ℹ️ Borsa kapalı — son kapanış fiyatlarına göre hesaplandı."

    bilgi = {
        "tarama_zamani": kayit.get("zaman", "?"),
        "simdi": datetime.now(IST).strftime("%d.%m.%Y %H:%M"),
        "uyari": uyari,
        "bas_etiket": "Tarama fiyatı",
        "bit_etiket": "Güncel fiyat",
    }
    return bilgi, satirlar, karne, bolumler


def calistir():
    bilgi, satirlar, karne, bolumler = hesapla()
    if not bilgi:
        print("Karşılaştırılacak önceki tarama kaydı yok.")
        print("Önce bir tarama çalıştır (toplu_tara.py), ertesi gün bunu çalıştır.")
        return None

    print(f"📊 {bilgi['tarama_zamani']} taramasındaki kağıtların "
          f"{bilgi['simdi']} itibarıyla durumu:")
    if bilgi.get("uyari"):
        print(bilgi["uyari"])
    print()
    for s in satirlar[:10]:
        d = f"{s['degisim']:+.2f}%" if s["degisim"] is not None else "—"
        print(f"  {s['hisse']:8s} {d:>9s}   {s['strateji'][:40]}")
    if len(satirlar) > 10:
        print(f"  … ve {len(satirlar) - 10} tane daha")

    data = rapor_performans.grid_performans_excel(bilgi, bolumler, karne)
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


# ==========================================================================
# TARİH ARALIĞI performansı: seçilen günün 18:20 taramasındaki kağıtların
# bitiş günündeki kapanışa göre getirisi.
# ==========================================================================
def kapanis_fiyatlari(kodlar, tarih):
    """Verilen gündeki (YYYY-MM-DD) kapanış fiyatları. {HISSE: fiyat}"""
    import warnings
    warnings.filterwarnings("ignore")
    import yfinance as yf
    from datetime import datetime as _dt, timedelta as _td

    kodlar = sorted({(k or "").upper() for k in kodlar if k})
    if not kodlar:
        return {}
    bas = _dt.strptime(tarih, "%Y-%m-%d") - _td(days=6)
    bit = _dt.strptime(tarih, "%Y-%m-%d") + _td(days=1)
    try:
        df = yf.download([f"{k}.IS" for k in kodlar], start=bas.strftime("%Y-%m-%d"),
                         end=bit.strftime("%Y-%m-%d"), interval="1d",
                         progress=False, auto_adjust=False, group_by="column")
        kapanis = df["Close"]
    except Exception as e:
        print(f"  (geçmiş fiyat alınamadı: {e})")
        return {}

    out = {}
    for k in kodlar:
        try:
            seri = kapanis[f"{k}.IS"].dropna() if len(kodlar) > 1 else kapanis.dropna()
            if len(seri):
                out[k] = float(seri.iloc[-1])   # tarihe kadar olan son kapanış
        except Exception:
            continue
    return out


_EVREN = None


def hisse_evreni():
    """BIST'te işlem gören gerçek hisselerin kod listesi (fonlar hariç)."""
    global _EVREN
    if _EVREN is None:
        try:
            _, df = (Query().set_markets("turkey").select("name", "type")
                     .limit(1000).get_scanner_data())
            _EVREN = {str(x).upper() for x in df["name"]}
        except Exception:
            _EVREN = set()
    return _EVREN


def hesapla_aralik(bas_tarih, bit_tarih, secili=None):
    """bas_tarih/bit_tarih: 'YYYY-MM-DD'. secili: strateji adları listesi (None=hepsi).
    Döner: (bilgi, bolumler, karne)"""
    kayit = gecmis.gunun_kaydi(bas_tarih)
    if not kayit:
        return None, [], []

    stratejiler = kayit.get("stratejiler", {})
    if secili:
        stratejiler = {k: v for k, v in stratejiler.items() if k in secili}
    if not stratejiler:
        return None, [], []

    evren = hisse_evreni()
    if evren:  # eski kayıtlarda kalmış fonları (OPX30, ZGOLD…) ayıkla
        stratejiler = {k: [h for h in v if (h.get("hisse") or "").upper() in evren]
                       for k, v in stratejiler.items()}

    kodlar = [h.get("hisse") for lst in stratejiler.values() for h in lst]
    bitis = kapanis_fiyatlari(kodlar, bit_tarih)

    bolumler, karne = [], []
    for strateji, liste in stratejiler.items():
        blok, getiriler = [], []
        for h in liste:
            kod = (h.get("hisse") or "").upper()
            eski = float(h.get("fiyat") or 0)
            yeni = bitis.get(kod)
            deg = ((yeni - eski) / eski * 100) if (yeni and eski) else None
            if deg is not None:
                getiriler.append(deg)
            blok.append({"hisse": kod, "eski": eski or None, "yeni": yeni, "degisim": deg})
        blok.sort(key=lambda s: (s["degisim"] is None, -(s["degisim"] or 0)))
        bolumler.append({"ad": strateji, "satirlar": blok})
        karne.append({
            "strateji": strateji, "adet": len(liste),
            "ortalama": (sum(getiriler) / len(getiriler)) if getiriler else None,
            "kazanan": sum(1 for g in getiriler if g > 0),
            "kaybeden": sum(1 for g in getiriler if g < 0),
        })
    karne.sort(key=lambda k: (k["ortalama"] is None, -(k["ortalama"] or 0)))

    from datetime import datetime as _d
    _f = lambda t: _d.strptime(t, "%Y-%m-%d").strftime("%d.%m")
    bilgi = {
        "tarama_zamani": kayit.get("zaman", bas_tarih),
        "simdi": f"{bit_tarih} kapanışı",
        "uyari": "",
        "bas_etiket": f"{_f(bas_tarih)} fiyat",
        "bit_etiket": f"{_f(bit_tarih)} fiyat",
    }
    return bilgi, bolumler, karne
