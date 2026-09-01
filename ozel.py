"""
ÖZEL TARAMALAR — TradingView screener'ında bulunmayan indikatörler.

Şu an: SuperTrend (Pine "SuperTrend Scanner" mantığının birebir kopyası).

Fiyat TradingView'den gelir. Bar geçmişi (OHLC) yfinance'ten gelmek zorunda —
TradingView screener'ı geçmiş bar veremiyor. İki kaynak tutmayan hisseler
elenir; ayrıntı için supertrend_tara() açıklamasına bak.

Kullanım (kombinler.json içinde):
    {"ozel": "supertrend", "ayarlar": {"periyot": 10, "carpan": 3.0, "yon": "AL"}}
"""

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def _atr_rma(yuksek, dusuk, kapanis, periyot):
    """Pine'daki ta.atr ile aynı: True Range'in RMA'sı (Wilder)."""
    onceki_kapanis = kapanis.shift(1)
    tr = pd.concat([
        yuksek - dusuk,
        (yuksek - onceki_kapanis).abs(),
        (dusuk - onceki_kapanis).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / periyot, adjust=False).mean()


def supertrend_trend(yuksek, dusuk, kapanis, periyot=10, carpan=3.0):
    """Pine kodundaki trend dizisini (+1 / -1) döndürür."""
    hl2 = (yuksek + dusuk) / 2
    atr = _atr_rma(yuksek, dusuk, kapanis, periyot)

    up_ham = (hl2 - carpan * atr).to_numpy(dtype=float)
    dn_ham = (hl2 + carpan * atr).to_numpy(dtype=float)
    c = kapanis.to_numpy(dtype=float)
    n = len(c)

    up = np.full(n, np.nan)
    dn = np.full(n, np.nan)
    trend = np.ones(n)

    for i in range(n):
        if i == 0 or np.isnan(up_ham[i]):
            up[i], dn[i] = up_ham[i], dn_ham[i]
            continue
        # up := close[1] > up1 ? max(up, up1) : up
        up[i] = max(up_ham[i], up[i - 1]) if c[i - 1] > up[i - 1] else up_ham[i]
        # dn := close[1] < dn1 ? min(dn, dn1) : dn
        dn[i] = min(dn_ham[i], dn[i - 1]) if c[i - 1] < dn[i - 1] else dn_ham[i]
        # trend geçişleri
        onceki = trend[i - 1]
        if onceki == -1 and c[i] > dn[i - 1]:
            trend[i] = 1
        elif onceki == 1 and c[i] < up[i - 1]:
            trend[i] = -1
        else:
            trend[i] = onceki
    return pd.Series(trend, index=kapanis.index)


TUTARSIZLIK_SINIRI = 3.0   # yfinance ile TradingView kapanışı arasında izin verilen % fark


def supertrend_tara(periyot=10, carpan=3.0, yon="AL", kodlar=None, gun=120):
    """Bugün SuperTrend sinyali veren BIST hisseleri.
    yon: 'AL' (trend -1→+1) veya 'SAT' (+1→-1)
    Döner: DataFrame(name, close, change, Recommend.All)

    Fiyat TradingView'den alınır (diğer 18 strateji ile aynı kaynak olsun diye).
    Bar geçmişi yfinance'ten gelmek zorunda — TradingView screener'ı 120 günlük
    OHLC veremiyor. Bu yüzden yfinance serisi TradingView kapanışıyla
    tutmayan hisseler ELENİR: orada seri farklı düzeltilmiş (bedelsiz/split)
    ya da donmuş demektir, o seriden çıkan sinyal de anlamsız olur."""
    import yfinance as yf

    if kodlar is None:
        from performans import hisse_evreni
        kodlar = sorted(hisse_evreni())
    if not kodlar:
        return pd.DataFrame(columns=["name", "close", "change", "Recommend.All"])

    veri = yf.download([f"{k}.IS" for k in kodlar], period=f"{gun}d", interval="1d",
                       progress=False, auto_adjust=False, group_by="ticker", threads=True)

    from performans import guncel_fiyatlar
    tv = guncel_fiyatlar(kodlar)

    satirlar, elenen = [], []
    for k in kodlar:
        try:
            df = veri[f"{k}.IS"].dropna()
            if len(df) < periyot + 5:
                continue
            trend = supertrend_trend(df["High"], df["Low"], df["Close"], periyot, carpan)
            if len(trend) < 2:
                continue
            son, onceki = trend.iloc[-1], trend.iloc[-2]
            sinyal = (son == 1 and onceki == -1) if yon == "AL" else (son == -1 and onceki == 1)
            if not sinyal:
                continue

            tv_fiyat, tv_degisim = tv.get(k, (None, None))
            if not tv_fiyat:
                elenen.append(f"{k} (TradingView fiyatı yok)")
                continue

            yf_kapanis = float(df["Close"].iloc[-1])
            sapma = abs(yf_kapanis - tv_fiyat) / tv_fiyat * 100
            if sapma > TUTARSIZLIK_SINIRI:
                elenen.append(f"{k} (yfinance {yf_kapanis:.2f} ≠ TradingView {tv_fiyat:.2f})")
                continue

            satirlar.append({
                "name": k,
                "close": tv_fiyat,
                "change": tv_degisim if tv_degisim is not None else 0.0,
                "Recommend.All": None,
            })
        except Exception:
            continue

    if elenen:
        print(f"  (SuperTrend — veri tutarsız, {len(elenen)} hisse elendi: "
              f"{', '.join(elenen[:5])}{'…' if len(elenen) > 5 else ''})")

    return pd.DataFrame(satirlar, columns=["name", "close", "change", "Recommend.All"])


# Kayıtlı özel taramalar
OZEL_TARAMALAR = {"supertrend": supertrend_tara}


def ozel_calistir(paket, limit=100):
    """kombinler.json'daki özel strateji paketini çalıştırır → (toplam, df)"""
    ad = paket.get("ozel")
    fn = OZEL_TARAMALAR.get(ad)
    if not fn:
        return 0, pd.DataFrame(columns=["name", "close", "change", "Recommend.All"])
    df = fn(**(paket.get("ayarlar") or {}))
    if len(df) > limit:
        df = df.head(limit)
    return len(df), df
