"""
Analiz yardımcıları:
  1) guclu_sinyaller() — aynı gün birden çok stratejide çıkan hisseler (altın sinyal)
  2) endeks_getiri()   — BIST 100'ün iki tarih arasındaki getirisi (karşılaştırma için)
"""

import warnings
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

ENDEKS_SEMBOL = "XU100.IS"


def guclu_sinyaller(bolumler, en_az=2):
    """bolumler: [{'ad': strateji, 'satirlar': [{'hisse':..}]}]
    Döner: [{hisse, sayi, stratejiler}] — çok görünenden aza sıralı."""
    sayac = {}
    for b in bolumler:
        ad = b.get("ad", "")
        for h in b.get("satirlar", []):
            kod = (h.get("hisse") or "").upper()
            if not kod:
                continue
            k = sayac.setdefault(kod, {"hisse": kod, "sayi": 0, "stratejiler": []})
            if ad not in k["stratejiler"]:
                k["stratejiler"].append(ad)
                k["sayi"] += 1
    return sorted([v for v in sayac.values() if v["sayi"] >= en_az],
                  key=lambda x: (-x["sayi"], x["hisse"]))


def guclu_sinyal_metni(bolumler, en_az=2, en_fazla=None) -> str:
    """Telegram için kısa özet."""
    liste = guclu_sinyaller(bolumler, en_az)
    if not liste:
        return ""
    satir = [f"🔥 *GÜÇLÜ SİNYALLER* — {len(liste)} hisse (birden çok stratejide)"]
    gosterilecek = liste if en_fazla is None else liste[:en_fazla]
    for s in gosterilecek:
        satir.append(f"• *{s['hisse']}* — {s['sayi']} stratejide")
    return "\n".join(satir)


# --------------------------------------------------------------- ENDEKS
_ENDEKS_ONBELLEK = {}


def _endeks_serisi(bas, bit):
    """XU100 kapanış serisi (pandas Series, index=tarih)."""
    anahtar = (bas, bit)
    if anahtar in _ENDEKS_ONBELLEK:
        return _ENDEKS_ONBELLEK[anahtar]
    import yfinance as yf
    try:
        b = (datetime.strptime(bas, "%Y-%m-%d") - timedelta(days=8)).strftime("%Y-%m-%d")
        s = (datetime.strptime(bit, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")
        bugun = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        s = min(s, bugun)
        df = yf.download(ENDEKS_SEMBOL, start=b, end=s, interval="1d",
                         progress=False, auto_adjust=False)
        seri = df["Close"].dropna()
        if hasattr(seri, "columns"):          # tek sembolde bile MultiIndex gelebilir
            seri = seri.iloc[:, 0]
        _ENDEKS_ONBELLEK[anahtar] = seri
        return seri
    except Exception:
        return None


def endeks_getiri(bas_tarih, bit_tarih, ertesi_gun=False):
    """BIST 100'ün getirisi (%).
    ertesi_gun=True → bas_tarih kapanışı ile BİR SONRAKİ işlem günü kapanışı arası.
    ertesi_gun=False → bas_tarih ile bit_tarih kapanışları arası."""
    seri = _endeks_serisi(bas_tarih, bit_tarih)
    if seri is None or not len(seri):
        return None
    try:
        bas_ser = seri[seri.index <= bas_tarih]
        if not len(bas_ser):
            return None
        p0 = float(bas_ser.iloc[-1])

        if ertesi_gun:
            sonra = seri[seri.index > bas_tarih]
            if not len(sonra):
                return None
            p1 = float(sonra.iloc[0])
        else:
            bit_ser = seri[seri.index <= bit_tarih]
            if not len(bit_ser):
                return None
            p1 = float(bit_ser.iloc[-1])
        return (p1 - p0) / p0 * 100 if p0 else None
    except Exception:
        return None
