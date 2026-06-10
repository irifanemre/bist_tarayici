"""
Tarama motoru: seçilen koşulları BIST üzerinde çalıştırır.
Zaman dilimi, endeks evreni, sektör filtresi ve VE/VEYA mantığını destekler.
"""

import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from tradingview_screener import Query, col, And, Or
from indikatorler import kosul_uret

_IST = ZoneInfo("Europe/Istanbul")


def _getir(sorgu, deneme=3):
    """get_scanner_data'yı geçici ağ hatalarına karşı birkaç kez dener."""
    son_hata = None
    for i in range(deneme):
        try:
            return sorgu.get_scanner_data()
        except Exception as e:  # ağ/HTTP geçici hataları
            son_hata = e
            time.sleep(1.5 * (i + 1))
    raise son_hata


# Sonuç tablosunda her zaman göstereceğimiz alanlar
TEMEL_ALANLAR = [
    "name", "close", "change", "volume",
    "Recommend.All", "RSI", "MACD.macd", "MACD.signal",
    "EMA50", "EMA200", "ADX", "price_earnings_ttm", "market_cap_basic", "sector",
    # veri tazeliği (gösterilmez, bilgi amaçlı)
    "update_mode", "current_session", "last-price-update-time",
]


def veri_bilgisi(df) -> dict:
    """Sonuç verisinin gerçek saati, gecikmesi ve piyasa durumu.
    {saat: 'dd.mm HH:MM' | None, gecikme_dk: int | None, acik: bool | None}"""
    bilgi = {"saat": None, "gecikme_dk": None, "acik": None}
    if df is None or len(df) == 0:
        return bilgi
    try:
        ts = pd.to_numeric(df["last-price-update-time"], errors="coerce").max()
        if pd.notna(ts):
            bilgi["saat"] = datetime.fromtimestamp(float(ts), _IST).strftime("%d.%m %H:%M")
    except Exception:
        pass
    try:
        mode = str(df["update_mode"].iloc[0])
        m = re.search(r"(\d+)", mode)
        if "delayed" in mode and m:
            bilgi["gecikme_dk"] = int(m.group(1)) // 60
        elif "realtime" in mode or "streaming" in mode and not m:
            bilgi["gecikme_dk"] = 0
    except Exception:
        pass
    try:
        bilgi["acik"] = str(df["current_session"].iloc[0]) == "market"
    except Exception:
        pass
    return bilgi


def rating_etiket(x) -> str:
    """TradingView Recommend.All (-1…1) -> Türkçe etiket."""
    if x is None:
        return "—"
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    if x >= 0.5:   return "Güçlü Al"
    if x >= 0.1:   return "Al"
    if x > -0.1:   return "Nötr"
    if x > -0.5:   return "Sat"
    return "Güçlü Sat"


def rating_rozet(x) -> str:
    """Rating'i renkli ikonlu etikete çevirir (🟢 Güçlü Al gibi)."""
    et = rating_etiket(x)
    ikon = {"Güçlü Al": "🟢", "Al": "🟢", "Nötr": "⚪",
            "Sat": "🔴", "Güçlü Sat": "🔴"}.get(et, "")
    return f"{ikon} {et}".strip()


def tara(secimler, limit=100, *, zaman="", endeks=None, sektorler=None, mantik="VE"):
    """
    secimler : kosul_uret() ile uyumlu sözlük listesi
    zaman    : '' | '|60' | '|240' | '|1W'
    endeks   : None (tüm BIST) veya set_index sembolü (örn. 'SYML:BIST;XU030')
    sektorler: None veya TradingView sektör adları listesi (her zaman VE ile uygulanır)
    mantik   : 'VE' (tüm koşullar) | 'VEYA' (herhangi biri)

    Döner: (toplam_sayi, DataFrame)
    """
    sorgu = Query().select(*TEMEL_ALANLAR)

    # Evren: endeks mi, tüm BIST mi?
    if endeks:
        sorgu = sorgu.set_index(endeks)
    else:
        sorgu = sorgu.set_markets("turkey")

    sorgu = sorgu.order_by("volume", ascending=False).limit(limit)

    # İndikatör koşulları
    kosullar = [kosul_uret(s, zaman) for s in secimler]
    if mantik == "VEYA" and len(kosullar) > 1:
        indikator_ifade = Or(*kosullar)
    elif kosullar:
        indikator_ifade = And(*kosullar)
    else:
        indikator_ifade = None

    # Sektör filtresi her zaman VE ile uygulanır
    sektor_ifade = col("sector").isin(list(sektorler)) if sektorler else None

    parcalar = [x for x in (indikator_ifade, sektor_ifade) if x is not None]
    if parcalar:
        sorgu = sorgu.where2(And(*parcalar))

    return _getir(sorgu)


if __name__ == "__main__":
    secimler = [
        {"tip": "metrik", "anahtar": "RSI", "op": "<", "hedef_turu": "deger", "deger": 60},
        {"tip": "hazir", "anahtar": "macd_al"},
    ]
    toplam, df = tara(secimler, limit=8, zaman="|240",
                      endeks="SYML:BIST;XU100", sektorler=["Finance"], mantik="VE")
    print(f"Eşleşen: {toplam}")
    print(df[["name", "close", "Recommend.All", "RSI", "sector"]].to_string())
