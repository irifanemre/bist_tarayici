"""
Canlı piyasa verileri.

  - piyasa_verileri(): BIST100, Altın, Dolar, Euro, Dow Jones anlık kurları (yfinance)
  - hisse_verileri():  takip listesindeki BIST hisseleri (tradingview-screener)
  - takip_oku/takip_yaz: takip listesini diske kaydeder
"""

import os
import warnings

import yfinance as yf
from tradingview_screener import Query

from depo_util import json_oku, json_yaz

warnings.filterwarnings("ignore")

# Görünen ad -> yfinance sembolü
PIYASA_SEMBOLLERI = {
    "BIST 100":     "XU100.IS",
    "Altın (ons $)": "GC=F",
    "Dolar / TL":   "USDTRY=X",
    "Euro / TL":    "EURTRY=X",
    "Dow Jones":    "^DJI",
}

_TAKIP_DOSYA = os.path.join(os.path.dirname(__file__), "takip.json")


def piyasa_verileri() -> list:
    """[{ad, fiyat, degisim(%)}] döner. Hata olursa fiyat=None."""
    sonuc = []
    try:
        data = yf.download(
            list(PIYASA_SEMBOLLERI.values()),
            period="5d", interval="1d",
            progress=False, auto_adjust=False,
        )
        close = data["Close"]
        for ad, sembol in PIYASA_SEMBOLLERI.items():
            try:
                seri = close[sembol].dropna()
                son = float(seri.iloc[-1])
                onceki = float(seri.iloc[-2]) if len(seri) > 1 else son
                degisim = (son - onceki) / onceki * 100 if onceki else 0.0
                sonuc.append({"ad": ad, "fiyat": son, "degisim": degisim})
            except Exception:
                sonuc.append({"ad": ad, "fiyat": None, "degisim": None})
    except Exception:
        for ad in PIYASA_SEMBOLLERI:
            sonuc.append({"ad": ad, "fiyat": None, "degisim": None})
    return sonuc


def hisse_verileri(kodlar) -> list:
    """BIST hisse kodları (örn. ['ASELS','THYAO']) için anlık fiyat + değişim.
    [{ad, fiyat, degisim, bulundu}] döner."""
    kodlar = [k.strip().upper() for k in kodlar if k.strip()]
    if not kodlar:
        return []

    bulunan = {}
    try:
        tickers = [f"BIST:{k}" for k in kodlar]
        _, df = (Query()
                 .set_markets("turkey")
                 .set_tickers(*tickers)
                 .select("name", "close", "change")
                 .get_scanner_data())
        for _, row in df.iterrows():
            bulunan[str(row["name"]).upper()] = row
    except Exception:
        bulunan = {}

    sonuc = []
    for k in kodlar:
        if k in bulunan:
            r = bulunan[k]
            sonuc.append({"ad": k, "fiyat": float(r["close"]),
                          "degisim": float(r["change"]), "bulundu": True})
        else:
            sonuc.append({"ad": k, "fiyat": None, "degisim": None, "bulundu": False})
    return sonuc


def takip_oku() -> str:
    return json_oku(_TAKIP_DOSYA, {}).get("kodlar", "")


def takip_yaz(kodlar_str: str) -> None:
    try:
        json_yaz(_TAKIP_DOSYA, {"kodlar": kodlar_str})
    except OSError:
        pass


def tl_format(x) -> str:
    """13741.89 -> '13.741,89' (Türkçe binlik/ondalık)."""
    if x is None:
        return "—"
    s = f"{x:,.2f}"  # 13,741.89
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def borsa_durumu():
    """Taramanın yapıldığı andaki genel piyasa tablosu.
    {endeks, endeks_degisim, yukselen, dusen, yatay, oran, dolar, acik}"""
    d = {"endeks": None, "endeks_degisim": None, "yukselen": None,
         "dusen": None, "yatay": None, "oran": None, "dolar": None, "acik": None}

    # BIST 100 ve dolar (yfinance)
    try:
        for v in piyasa_verileri():
            if v["ad"] == "BIST 100":
                d["endeks"], d["endeks_degisim"] = v["fiyat"], v["degisim"]
            elif v["ad"] == "Dolar / TL":
                d["dolar"] = v["fiyat"]
    except Exception:
        pass

    # Piyasa genişliği: kaç hisse yükseldi / düştü (TradingView)
    try:
        from tradingview_screener import Query, col, And
        _, df = (Query().set_markets("turkey")
                 .select("name", "change", "current_session")
                 .where2(And(col("type") == "stock"))
                 .limit(1000).get_scanner_data())
        deg = df["change"].astype(float)
        d["yukselen"] = int((deg > 0).sum())
        d["dusen"] = int((deg < 0).sum())
        d["yatay"] = int((deg == 0).sum())
        toplam = d["yukselen"] + d["dusen"]
        d["oran"] = round(d["yukselen"] / toplam * 100, 1) if toplam else None
        d["acik"] = str(df["current_session"].iloc[0]) == "market"
    except Exception:
        pass
    return d


def borsa_ozet_metni(d=None) -> str:
    """Tek satırlık okunur özet."""
    d = d or borsa_durumu()
    p = []
    if d.get("endeks") is not None:
        ok = "🟢" if (d.get("endeks_degisim") or 0) >= 0 else "🔴"
        p.append(f"{ok} BIST 100: {tl_format(d['endeks'])} ({d['endeks_degisim']:+.2f}%)")
    if d.get("yukselen") is not None:
        p.append(f"📊 {d['yukselen']} yükselen / {d['dusen']} düşen"
                 + (f" (%{d['oran']} yükselişte)" if d.get("oran") is not None else ""))
    if d.get("dolar"):
        p.append(f"💵 Dolar: {tl_format(d['dolar'])}")
    if d.get("acik") is False:
        p.append("🔴 Piyasa kapalı")
    return "  ·  ".join(p) if p else ""
