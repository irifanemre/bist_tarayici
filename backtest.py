"""
Basit geçmiş testi (backtest).

Bir kombin için, seçili evrendeki (örn. BIST 30) hisselerin geçmiş verisinde
sinyalin oluştuğu günleri bulur ve sinyalden N gün sonraki getiriyi ölçer.

Dürüstlük notu:
  - Geçmiş veri yfinance'ten (kapanış, bölünme/temettü düzeltmeli).
  - İndikatörler burada elle hesaplanır; bu yüzden YALNIZCA desteklenen
    indikatörler işlenir (RSI, MACD, EMA/SMA, fiyat-ortalama, golden/death cross,
    günlük değişim, hacim). Desteklenmeyenler atlanır ve kullanıcıya bildirilir.
  - Gerçek alım-satım maliyeti, kayma, likidite dahil DEĞİLDİR. Kaba bir fikir verir.
"""

import warnings
from functools import reduce

import numpy as np
import pandas as pd
import yfinance as yf
from tradingview_screener import Query

warnings.filterwarnings("ignore")

# app'teki endeks etiketleri -> set_index sembolü
EVRENLER = {
    "BIST 30": "SYML:BIST;XU030",
    "BIST 50": "SYML:BIST;XU050",
    "BIST 100": "SYML:BIST;XU100",
}


class Desteklenmiyor(Exception):
    pass


# ----------------------------- indikatörler -------------------------------
def _ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def _sma(s, n):
    return s.rolling(n).mean()


def _rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _macd(s):
    macd = _ema(s, 12) - _ema(s, 26)
    return macd, _ema(macd, 9)


def _indikatorler(df):
    c = df["Close"].astype(float)
    ind = pd.DataFrame(index=df.index)
    ind["close"] = c
    ind["change"] = c.pct_change() * 100
    ind["volume"] = df["Volume"].astype(float)
    ind["RSI"] = _rsi(c)
    macd, sig = _macd(c)
    ind["MACD.macd"], ind["MACD.signal"] = macd, sig
    for n in (5, 10, 20, 50, 100, 200):
        ind[f"EMA{n}"] = _ema(c, n)
    for n in (20, 50, 200):
        ind[f"SMA{n}"] = _sma(c, n)
    return ind


def _cross_up(a, b):
    return (a > b) & (a.shift(1) <= b.shift(1))


def _cross_dn(a, b):
    return (a < b) & (a.shift(1) >= b.shift(1))


# desteklenen alanlar -> ind kolon adı (None = desteklenmiyor)
_DESTEK = {"RSI", "MACD.macd", "MACD.signal", "close", "change", "volume",
           "EMA5", "EMA10", "EMA20", "EMA50", "EMA100", "EMA200",
           "SMA20", "SMA50", "SMA200"}


def _seri(ind, secim):
    """Bir seçimi geçmiş veri üzerinde boolean (sinyal) serisine çevirir."""
    if secim["tip"] == "hazir":
        a = secim["anahtar"]
        if a == "macd_al":
            return ind["MACD.macd"] > ind["MACD.signal"]
        if a == "macd_yukari_keser":
            return _cross_up(ind["MACD.macd"], ind["MACD.signal"])
        if a == "golden_cross":
            return _cross_up(ind["EMA50"], ind["EMA200"])
        if a == "death_cross":
            return _cross_dn(ind["EMA50"], ind["EMA200"])
        if a == "fiyat_ema200_ustu":
            return ind["close"] > ind["EMA200"]
        raise Desteklenmiyor

    anahtar, op = secim["anahtar"], secim["op"]
    if anahtar not in _DESTEK:
        raise Desteklenmiyor
    kol = ind[anahtar]

    if op in ("arada", "arada değil"):
        s = (kol >= secim["deger"]) & (kol <= secim["deger2"])
        return s if op == "arada" else ~s

    if secim.get("hedef_turu") == "alan":
        if secim["hedef_alan"] not in _DESTEK and secim["hedef_alan"] != "close":
            raise Desteklenmiyor
        hedef = ind[secim["hedef_alan"]]
    else:
        hedef = secim["deger"]

    if op == "<":   return kol < hedef
    if op == "<=":  return kol <= hedef
    if op == ">":   return kol > hedef
    if op == ">=":  return kol >= hedef
    if op == "yukarı keser":
        return _cross_up(kol, hedef if not np.isscalar(hedef) else pd.Series(hedef, index=kol.index))
    if op == "aşağı keser":
        return _cross_dn(kol, hedef if not np.isscalar(hedef) else pd.Series(hedef, index=kol.index))
    raise Desteklenmiyor


def evren_kodlari(evren="BIST 30"):
    sembol = EVRENLER.get(evren, EVRENLER["BIST 30"])
    _, df = Query().set_index(sembol).select("name").get_scanner_data()
    return df["name"].tolist()


def backtest(secimler, mantik="VE", horizon=5, period="2y", evren="BIST 30"):
    """
    Döner: (ozet: dict, detay: list[dict])
      ozet: sinyal, isabet(%), ort_getiri(%), medyan(%), en_iyi/en_kotu(%),
            horizon, hisse_sayisi, desteklenmeyen[list]
    """
    kodlar = evren_kodlari(evren)
    tickers = [f"{k}.IS" for k in kodlar]
    veri = yf.download(tickers, period=period, interval="1d",
                       progress=False, auto_adjust=True, group_by="ticker")

    desteklenmeyen, getiriler, detay = set(), [], []

    for kod, tk in zip(kodlar, tickers):
        try:
            df = veri[tk].dropna()
        except Exception:
            continue
        if len(df) < 60:
            continue
        ind = _indikatorler(df)

        seriler = []
        for s in secimler:
            try:
                seriler.append(_seri(ind, s).fillna(False))
            except Desteklenmiyor:
                desteklenmeyen.add(_ad(s))
        if not seriler:
            continue

        birlesik = reduce(lambda a, b: a | b, seriler) if mantik == "VEYA" \
            else reduce(lambda a, b: a & b, seriler)
        giris = birlesik & (~birlesik.shift(1, fill_value=False))

        closes = ind["close"].values
        idx = np.where(giris.values)[0]
        for i in idx:
            if i + horizon < len(closes):
                g = closes[i + horizon] / closes[i] - 1
                if np.isfinite(g):
                    getiriler.append(g)
                    detay.append({"kod": kod, "tarih": ind.index[i].strftime("%Y-%m-%d"),
                                  "getiri": float(round(g * 100, 2))})

    g = np.array(getiriler) if getiriler else np.array([])
    ozet = {
        "sinyal": int(len(g)),
        "isabet": round(float((g > 0).mean() * 100), 1) if len(g) else 0.0,
        "ort_getiri": round(float(g.mean() * 100), 2) if len(g) else 0.0,
        "medyan": round(float(np.median(g) * 100), 2) if len(g) else 0.0,
        "en_iyi": round(float(g.max() * 100), 2) if len(g) else 0.0,
        "en_kotu": round(float(g.min() * 100), 2) if len(g) else 0.0,
        "horizon": horizon,
        "hisse_sayisi": len(kodlar),
        "desteklenmeyen": sorted(desteklenmeyen),
    }
    detay.sort(key=lambda d: d["getiri"], reverse=True)
    return ozet, detay


def _ad(secim):
    from indikatorler import KATALOG, HAZIR_SINYALLER
    if secim["tip"] == "hazir":
        return HAZIR_SINYALLER.get(secim["anahtar"], {}).get("ad", secim["anahtar"])
    return KATALOG.get(secim["anahtar"], {}).get("ad", secim["anahtar"])


if __name__ == "__main__":
    secim = [
        {"tip": "hazir", "anahtar": "golden_cross"},
        {"tip": "metrik", "anahtar": "EMA200", "op": "<", "hedef_turu": "alan", "hedef_alan": "close"},
    ]
    ozet, detay = backtest(secim, horizon=5)
    print("ÖZET:", ozet)
    print("İlk 5 işlem:", detay[:5])
