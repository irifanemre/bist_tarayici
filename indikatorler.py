"""
BIST tarayıcı — indikatör kataloğu, esnek koşul kurucu, strateji şablonları.

Mantık:
  - KATALOG: seçilebilen tüm indikatörler (osilatör, ortalama, bant, hacim,
    trend, temel analiz) + birkaç hazır sinyal.
  - Kullanıcı bir indikatör seçer, ona OPERATÖR ve HEDEF verir.
      * Hedef = sabit sayı   (örn. RSI < 30)
      * Hedef = başka alan   (örn. close > EMA50)
  - Koşullar VE veya VEYA ile birleşir; istenen zaman diliminde çalışır.

Zaman dilimi: teknik alanlara son ek eklenir (RSI -> RSI|240 = 4 saatlik,
RSI|1W = haftalık). Temel analiz alanları zaman diliminden etkilenmez.
"""

from tradingview_screener import col, And


KATALOG = {
    # ===================== OSİLATÖRLER =====================
    "RSI":         {"ad": "RSI (14)",              "alan": "RSI",        "grup": "Osilatör", "tur": "osilator", "aralik": (0, 100),  "op": "<",  "deger": 30},
    "RSI7":        {"ad": "RSI (7)",               "alan": "RSI7",       "grup": "Osilatör", "tur": "osilator", "aralik": (0, 100),  "op": "<",  "deger": 30},
    "Stoch.K":     {"ad": "Stokastik %K",          "alan": "Stoch.K",    "grup": "Osilatör", "tur": "osilator", "aralik": (0, 100),  "op": "<",  "deger": 20},
    "Stoch.D":     {"ad": "Stokastik %D",          "alan": "Stoch.D",    "grup": "Osilatör", "tur": "osilator", "aralik": (0, 100),  "op": "<",  "deger": 20},
    "Stoch.RSI.K": {"ad": "Stokastik RSI",         "alan": "Stoch.RSI.K","grup": "Osilatör", "tur": "osilator", "aralik": (0, 100),  "op": "<",  "deger": 20},
    "CCI20":       {"ad": "CCI (20)",              "alan": "CCI20",      "grup": "Osilatör", "tur": "osilator", "aralik": (-300, 300),"op": "<", "deger": -100},
    "W.R":         {"ad": "Williams %R",           "alan": "W.R",        "grup": "Osilatör", "tur": "osilator", "aralik": (-100, 0), "op": "<",  "deger": -80},
    "Mom":         {"ad": "Momentum (10)",         "alan": "Mom",        "grup": "Osilatör", "tur": "osilator", "aralik": (-100, 100),"op": ">", "deger": 0},
    "AO":          {"ad": "Awesome Oscillator",    "alan": "AO",         "grup": "Osilatör", "tur": "osilator", "aralik": (-50, 50), "op": ">",  "deger": 0},
    "UO":          {"ad": "Ultimate Oscillator",   "alan": "UO",         "grup": "Osilatör", "tur": "osilator", "aralik": (0, 100),  "op": "<",  "deger": 30},
    "BBPower":     {"ad": "Bull/Bear Power",       "alan": "BBPower",    "grup": "Osilatör", "tur": "osilator", "aralik": (-50, 50), "op": ">",  "deger": 0},
    "ROC":         {"ad": "ROC (değişim hızı)",    "alan": "ROC",        "grup": "Osilatör", "tur": "osilator", "aralik": (-50, 50), "op": ">",  "deger": 0},
    "MoneyFlow":   {"ad": "Para Akışı (MFI)",      "alan": "MoneyFlow",  "grup": "Osilatör", "tur": "osilator", "aralik": (0, 100),  "op": "<",  "deger": 20},
    "ChaikinMoneyFlow": {"ad": "Chaikin Para Akışı", "alan": "ChaikinMoneyFlow", "grup": "Osilatör", "tur": "osilator", "aralik": (-1, 1), "op": ">", "deger": 0},

    # ===================== TREND / YÖN =====================
    "ADX":     {"ad": "ADX (14) — trend gücü",  "alan": "ADX",      "grup": "Trend", "tur": "osilator", "aralik": (0, 100), "op": ">", "deger": 25},
    "ADX+DI":  {"ad": "+DI",                     "alan": "ADX+DI",   "grup": "Trend", "tur": "osilator", "aralik": (0, 100), "op": ">", "deger": 20},
    "ADX-DI":  {"ad": "-DI",                     "alan": "ADX-DI",   "grup": "Trend", "tur": "osilator", "aralik": (0, 100), "op": "<", "deger": 20},
    "Aroon.Up":   {"ad": "Aroon Up",            "alan": "Aroon.Up",  "grup": "Trend", "tur": "osilator", "aralik": (0, 100), "op": ">", "deger": 70},
    "Aroon.Down": {"ad": "Aroon Down",          "alan": "Aroon.Down","grup": "Trend", "tur": "osilator", "aralik": (0, 100), "op": "<", "deger": 30},

    # ===================== MACD =====================
    "MACD.macd":   {"ad": "MACD çizgisi",  "alan": "MACD.macd",   "grup": "MACD", "tur": "osilator", "aralik": (-50, 50), "op": ">", "deger": 0},
    "MACD.signal": {"ad": "MACD sinyal",   "alan": "MACD.signal", "grup": "MACD", "tur": "osilator", "aralik": (-50, 50), "op": ">", "deger": 0},

    # ===================== HAREKETLİ ORTALAMALAR (varsayılan: fiyat ortalamanın ÜSTÜNDE) =====================
    "EMA5":   {"ad": "EMA 5",   "alan": "EMA5",   "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "EMA10":  {"ad": "EMA 10",  "alan": "EMA10",  "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "EMA20":  {"ad": "EMA 20",  "alan": "EMA20",  "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "EMA50":  {"ad": "EMA 50",  "alan": "EMA50",  "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "EMA100": {"ad": "EMA 100", "alan": "EMA100", "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "EMA200": {"ad": "EMA 200", "alan": "EMA200", "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "SMA10":  {"ad": "SMA 10",  "alan": "SMA10",  "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "SMA20":  {"ad": "SMA 20",  "alan": "SMA20",  "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "SMA50":  {"ad": "SMA 50",  "alan": "SMA50",  "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "SMA200": {"ad": "SMA 200", "alan": "SMA200", "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "VWAP":   {"ad": "VWAP",    "alan": "VWAP",   "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "VWMA":   {"ad": "VWMA",    "alan": "VWMA",   "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "HullMA9":{"ad": "Hull MA (9)", "alan": "HullMA9", "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},

    # ===================== BANTLAR / VOLATİLİTE =====================
    "BB.upper": {"ad": "Bollinger Üst Bant", "alan": "BB.upper", "grup": "Bantlar", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "BB.lower": {"ad": "Bollinger Alt Bant", "alan": "BB.lower", "grup": "Bantlar", "tur": "seviye", "op": ">", "hedef_alan": "close"},
    "P.SAR":    {"ad": "Parabolic SAR",      "alan": "P.SAR",    "grup": "Bantlar", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "Ichimoku.BLine": {"ad": "Ichimoku Taban", "alan": "Ichimoku.BLine", "grup": "Bantlar", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "ATR":      {"ad": "ATR (volatilite)",   "alan": "ATR",      "grup": "Bantlar", "tur": "osilator", "aralik": (0, 100), "op": ">", "deger": 0},

    # ===================== PİVOT / ICHIMOKU (fiyat seviyeleri) =====================
    "Pivot.M.Classic.Middle": {"ad": "Pivot (orta nokta)",   "alan": "Pivot.M.Classic.Middle", "grup": "Pivot/Ichimoku", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "Pivot.M.Classic.R1": {"ad": "Pivot Direnç R1",          "alan": "Pivot.M.Classic.R1", "grup": "Pivot/Ichimoku", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "Pivot.M.Classic.R2": {"ad": "Pivot Direnç R2",          "alan": "Pivot.M.Classic.R2", "grup": "Pivot/Ichimoku", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "Pivot.M.Classic.S1": {"ad": "Pivot Destek S1",          "alan": "Pivot.M.Classic.S1", "grup": "Pivot/Ichimoku", "tur": "seviye", "op": ">", "hedef_alan": "close"},
    "Pivot.M.Classic.S2": {"ad": "Pivot Destek S2",          "alan": "Pivot.M.Classic.S2", "grup": "Pivot/Ichimoku", "tur": "seviye", "op": ">", "hedef_alan": "close"},
    "Ichimoku.CLine": {"ad": "Ichimoku Çevirme (Tenkan)",    "alan": "Ichimoku.CLine", "grup": "Pivot/Ichimoku", "tur": "seviye", "op": "<", "hedef_alan": "close"},

    # ===================== FİYAT / HACİM =====================
    "close":  {"ad": "Fiyat (kapanış)",   "alan": "close",  "grup": "Fiyat/Hacim", "tur": "seviye", "op": ">", "deger": 10},
    "change": {"ad": "Günlük değişim %",  "alan": "change", "grup": "Fiyat/Hacim", "tur": "osilator", "aralik": (-20, 20), "op": ">", "deger": 0},
    "volume": {"ad": "Hacim (adet)",      "alan": "volume", "grup": "Fiyat/Hacim", "tur": "hacim", "op": ">", "deger": 1_000_000},
    "relative_volume": {"ad": "Bağıl hacim (1g/anlık)", "alan": "relative_volume", "grup": "Fiyat/Hacim", "tur": "osilator", "aralik": (0, 10), "op": ">", "deger": 1},
    "relative_volume_10d_calc": {"ad": "Bağıl hacim (10g)", "alan": "relative_volume_10d_calc", "grup": "Fiyat/Hacim", "tur": "osilator", "aralik": (0, 10), "op": ">", "deger": 1.5},
    "average_volume_10d_calc": {"ad": "Ort. hacim (10g)", "alan": "average_volume_10d_calc", "grup": "Fiyat/Hacim", "tur": "hacim", "op": ">", "deger": 1_000_000},
    "average_volume_30d_calc": {"ad": "Ort. hacim (30g)", "alan": "average_volume_30d_calc", "grup": "Fiyat/Hacim", "tur": "hacim", "op": ">", "deger": 1_000_000},
    "gap": {"ad": "Açılış boşluğu (gap %)", "alan": "gap", "grup": "Fiyat/Hacim", "tur": "osilator", "aralik": (-20, 20), "op": ">", "deger": 0},
    "Perf.W": {"ad": "Haftalık getiri %", "alan": "Perf.W", "grup": "Fiyat/Hacim", "tur": "osilator", "aralik": (-30, 30), "op": ">", "deger": 0},
    "Perf.1M": {"ad": "Aylık getiri %", "alan": "Perf.1M", "grup": "Fiyat/Hacim", "tur": "osilator", "aralik": (-50, 50), "op": ">", "deger": 0},
    "Perf.Y": {"ad": "Yıllık getiri %", "alan": "Perf.Y", "grup": "Fiyat/Hacim", "tur": "osilator", "aralik": (-100, 300), "op": ">", "deger": 0},
    "price_52_week_high": {"ad": "52 hafta zirve", "alan": "price_52_week_high", "grup": "Fiyat/Hacim", "tur": "seviye", "op": ">", "hedef_alan": "close"},
    "price_52_week_low": {"ad": "52 hafta dip", "alan": "price_52_week_low", "grup": "Fiyat/Hacim", "tur": "seviye", "op": "<", "hedef_alan": "close"},

    # ===================== EK İNDİKATÖRLER (geniş TradingView kapsamı) =====================
    "EMA30":  {"ad": "EMA 30",  "alan": "EMA30",  "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "SMA30":  {"ad": "SMA 30",  "alan": "SMA30",  "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "SMA100": {"ad": "SMA 100", "alan": "SMA100", "grup": "Hareketli Ort.", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "BB.basis":      {"ad": "Bollinger Orta", "alan": "BB.basis",      "grup": "Bantlar", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "KltChnl.upper": {"ad": "Keltner Üst",    "alan": "KltChnl.upper", "grup": "Bantlar", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "KltChnl.lower": {"ad": "Keltner Alt",    "alan": "KltChnl.lower", "grup": "Bantlar", "tur": "seviye", "op": ">", "hedef_alan": "close"},
    "KltChnl.basis": {"ad": "Keltner Orta",   "alan": "KltChnl.basis", "grup": "Bantlar", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "Ichimoku.Lead1": {"ad": "Ichimoku Öncü A", "alan": "Ichimoku.Lead1", "grup": "Pivot/Ichimoku", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "Ichimoku.Lead2": {"ad": "Ichimoku Öncü B", "alan": "Ichimoku.Lead2", "grup": "Pivot/Ichimoku", "tur": "seviye", "op": "<", "hedef_alan": "close"},
    "Stoch.RSI.D":   {"ad": "Stokastik RSI %D", "alan": "Stoch.RSI.D", "grup": "Osilatör", "tur": "osilator", "aralik": (0, 100), "op": "<", "deger": 20},

    # ===================== TEMEL ANALİZ / RATING (zaman diliminden bağımsız) =====================
    "Recommend.All":        {"ad": "Teknik Rating (-1…1)", "alan": "Recommend.All", "grup": "Temel/Rating", "tur": "osilator", "aralik": (-1, 1), "op": ">", "deger": 0.3, "zaman_yok": True},
    "price_earnings_ttm":   {"ad": "F/K oranı",            "alan": "price_earnings_ttm", "grup": "Temel/Rating", "tur": "osilator", "aralik": (0, 200), "op": "<", "deger": 15, "zaman_yok": True},
    "price_book_fq":        {"ad": "PD/DD oranı",          "alan": "price_book_fq", "grup": "Temel/Rating", "tur": "osilator", "aralik": (0, 30), "op": "<", "deger": 3, "zaman_yok": True},
    "dividends_yield":      {"ad": "Temettü verimi %",     "alan": "dividends_yield", "grup": "Temel/Rating", "tur": "osilator", "aralik": (0, 30), "op": ">", "deger": 3, "zaman_yok": True},
    "market_cap_basic":     {"ad": "Piyasa değeri (TL)",   "alan": "market_cap_basic", "grup": "Temel/Rating", "tur": "hacim", "op": ">", "deger": 1_000_000_000, "zaman_yok": True},
    "return_on_equity":     {"ad": "Özkaynak Karlılığı (ROE %)", "alan": "return_on_equity", "grup": "Temel/Rating", "tur": "osilator", "aralik": (-50, 100), "op": ">", "deger": 15, "zaman_yok": True},
    "net_margin":           {"ad": "Net Kar Marjı %",      "alan": "net_margin", "grup": "Temel/Rating", "tur": "osilator", "aralik": (-50, 100), "op": ">", "deger": 10, "zaman_yok": True},
    "debt_to_equity":       {"ad": "Borç / Özkaynak",      "alan": "debt_to_equity", "grup": "Temel/Rating", "tur": "osilator", "aralik": (0, 5), "op": "<", "deger": 1, "zaman_yok": True},
    "total_revenue_yoy_growth_ttm": {"ad": "Ciro Büyümesi (yıllık %)", "alan": "total_revenue_yoy_growth_ttm", "grup": "Temel/Rating", "tur": "osilator", "aralik": (-50, 300), "op": ">", "deger": 20, "zaman_yok": True},
    "current_ratio":        {"ad": "Cari Oran",            "alan": "current_ratio", "grup": "Temel/Rating", "tur": "osilator", "aralik": (0, 5), "op": ">", "deger": 1.5, "zaman_yok": True},
}


# Hazır sinyaller — seçenek sormaz; zaman dilimi son ekini (s) alır.
HAZIR_SINYALLER = {
    "golden_cross": {"ad": "🟢 Golden Cross (EMA50 ↑ keser EMA200)", "grup": "Hazır Sinyal",
                     "kosul": lambda s="": col(f"EMA50{s}").crosses_above(col(f"EMA200{s}"))},
    "death_cross":  {"ad": "🔴 Death Cross (EMA50 ↓ keser EMA200)",  "grup": "Hazır Sinyal",
                     "kosul": lambda s="": col(f"EMA50{s}").crosses_below(col(f"EMA200{s}"))},
    "macd_al":      {"ad": "🟢 MACD al (MACD > Signal)",             "grup": "Hazır Sinyal",
                     "kosul": lambda s="": col(f"MACD.macd{s}") > col(f"MACD.signal{s}")},
    "macd_yukari_keser": {"ad": "🟢 MACD ↑ keser Signal",            "grup": "Hazır Sinyal",
                     "kosul": lambda s="": col(f"MACD.macd{s}").crosses_above(col(f"MACD.signal{s}"))},
    "fiyat_ema200_ustu": {"ad": "🟢 Fiyat EMA200 üstünde (boğa)",    "grup": "Hazır Sinyal",
                     "kosul": lambda s="": col(f"close{s}") > col(f"EMA200{s}")},

    # --- Ichimoku ---
    "ichimoku_bulut_ustu": {"ad": "🟢 Fiyat Ichimoku bulutunun üstünde", "grup": "Ichimoku",
                     "kosul": lambda s="": And(col(f"close{s}") > col(f"Ichimoku.Lead1{s}"),
                                               col(f"close{s}") > col(f"Ichimoku.Lead2{s}"))},
    "ichimoku_tk_kesisim": {"ad": "🟢 Tenkan ↑ keser Kijun (TK al)", "grup": "Ichimoku",
                     "kosul": lambda s="": col(f"Ichimoku.CLine{s}").crosses_above(col(f"Ichimoku.BLine{s}"))},

    # --- Mum formasyonları (formasyon oluştuysa) ---
    "mum_yutan_boga": {"ad": "🟢 Yutan Boğa (Bullish Engulfing)", "grup": "Mum Formasyonu",
                       "kosul": lambda s="": col(f"Candle.Engulfing.Bullish{s}") != 0},
    "mum_cekic": {"ad": "🟢 Çekiç (Hammer)", "grup": "Mum Formasyonu",
                  "kosul": lambda s="": col(f"Candle.Hammer{s}") != 0},
    "mum_ters_cekic": {"ad": "🟢 Ters Çekiç (Inverted Hammer)", "grup": "Mum Formasyonu",
                       "kosul": lambda s="": col(f"Candle.InvertedHammer{s}") != 0},
    "mum_sabah_yildizi": {"ad": "🟢 Sabah Yıldızı (Morning Star)", "grup": "Mum Formasyonu",
                          "kosul": lambda s="": col(f"Candle.MorningStar{s}") != 0},
    "mum_3_asker": {"ad": "🟢 Üç Beyaz Asker", "grup": "Mum Formasyonu",
                    "kosul": lambda s="": col(f"Candle.3WhiteSoldiers{s}") != 0},
    "mum_boga_harami": {"ad": "🟢 Boğa Harami", "grup": "Mum Formasyonu",
                        "kosul": lambda s="": col(f"Candle.Harami.Bullish{s}") != 0},
    "mum_yutan_ayi": {"ad": "🔴 Yutan Ayı (Bearish Engulfing)", "grup": "Mum Formasyonu",
                      "kosul": lambda s="": col(f"Candle.Engulfing.Bearish{s}") != 0},
    "mum_asilan_adam": {"ad": "🔴 Asılan Adam (Hanging Man)", "grup": "Mum Formasyonu",
                        "kosul": lambda s="": col(f"Candle.HangingMan{s}") != 0},
    "mum_kayan_yildiz": {"ad": "🔴 Kayan Yıldız (Shooting Star)", "grup": "Mum Formasyonu",
                         "kosul": lambda s="": col(f"Candle.ShootingStar{s}") != 0},
    "mum_aksam_yildizi": {"ad": "🔴 Akşam Yıldızı (Evening Star)", "grup": "Mum Formasyonu",
                          "kosul": lambda s="": col(f"Candle.EveningStar{s}") != 0},
    "mum_3_karga": {"ad": "🔴 Üç Kara Karga", "grup": "Mum Formasyonu",
                    "kosul": lambda s="": col(f"Candle.3BlackCrows{s}") != 0},
    "mum_ayi_harami": {"ad": "🔴 Ayı Harami", "grup": "Mum Formasyonu",
                       "kosul": lambda s="": col(f"Candle.Harami.Bearish{s}") != 0},
    "mum_doji": {"ad": "⚪ Doji (kararsızlık)", "grup": "Mum Formasyonu",
                 "kosul": lambda s="": col(f"Candle.Doji{s}") != 0},
}


# Operatör hedefi olarak seçilebilecek "başka indikatör" alanları
# Karşılaştırma hedefleri OTOMATİK türetilir: ham fiyat alanları + katalogdaki
# tüm teknik indikatörler + sık kullanılan çapraz zaman dilimi varyantları.
# Böylece her yeni indikatör eklendiğinde "karşılaştırılabilir alan" da otomatik gelir.
_HAM_ALANLAR = ["close", "open", "high", "low"]
_CAPRAZ_ZAMAN = [
    "RSI|60", "RSI|240", "RSI|1W",
    "ChaikinMoneyFlow|60", "ChaikinMoneyFlow|240",
    "MoneyFlow|60", "Stoch.K|60", "MACD.macd|1W",
]


def _karsilastirma_alanlari():
    alanlar = list(_HAM_ALANLAR)
    for tanim in KATALOG.values():
        if tanim.get("grup") == "Temel/Rating":  # F/K, piyasa değeri vb. hedef olmaz
            continue
        if tanim["alan"] not in alanlar:
            alanlar.append(tanim["alan"])
    for a in _CAPRAZ_ZAMAN:
        if a not in alanlar:
            alanlar.append(a)
    return alanlar


KARSILASTIRMA_ALANLARI = _karsilastirma_alanlari()

OPERATORLER = ["<", "<=", ">", ">=", "yukarı keser", "aşağı keser", "arada", "arada değil"]

# Zaman dilimleri: görünen ad -> alan son eki
ZAMAN_DILIMLERI = {
    "Günlük":     "",
    "1 Saatlik":  "|60",
    "4 Saatlik":  "|240",
    "Haftalık":   "|1W",
}

# Endeks evreni: görünen ad -> set_index sembolü (None = tüm BIST)
ENDEKSLER = {
    "Tüm BIST":  None,
    "BIST 30":   "SYML:BIST;XU030",
    "BIST 50":   "SYML:BIST;XU050",
    "BIST 100":  "SYML:BIST;XU100",
}

# Sektör adları: TradingView (İngilizce) -> Türkçe görünen ad
SEKTORLER = {
    "Commercial Services": "Ticari Hizmetler",
    "Communications": "İletişim",
    "Consumer Durables": "Dayanıklı Tüketim",
    "Consumer Non-Durables": "Dayanıksız Tüketim",
    "Consumer Services": "Tüketici Hizmetleri",
    "Distribution Services": "Dağıtım Hizmetleri",
    "Electronic Technology": "Elektronik Teknoloji",
    "Energy Minerals": "Enerji Madenleri",
    "Finance": "Finans",
    "Health Services": "Sağlık Hizmetleri",
    "Health Technology": "Sağlık Teknolojisi",
    "Industrial Services": "Sanayi Hizmetleri",
    "Miscellaneous": "Diğer",
    "Non-Energy Minerals": "Enerji Dışı Madenler",
    "Process Industries": "İşleme Sanayi",
    "Producer Manufacturing": "Üretim/İmalat",
    "Retail Trade": "Perakende",
    "Technology Services": "Teknoloji Hizmetleri",
    "Transportation": "Ulaştırma",
    "Utilities": "Kamu Hizmetleri (Enerji/Su)",
}


# İndikatör başına kısa Türkçe açıklama (arayüzde ipucu olarak gösterilir)
ACIKLAMALAR = {
    "RSI": "Aşırı alım/satımı ölçer. 30 altı ucuz (tepki gelebilir), 70 üstü pahalı bölge.",
    "RSI7": "Daha hızlı RSI; kısa vadeli aşırılıkları erken yakalar.",
    "Stoch.K": "Stokastik. 20 altı aşırı satım, 80 üstü aşırı alım.",
    "Stoch.D": "Stokastik sinyal çizgisi (%K'nın ortalaması).",
    "Stoch.RSI.K": "RSI'ın stokastiği; çok hassas aşırılık göstergesi.",
    "CCI20": "Fiyatın ortalamadan sapması. -100 altı/+100 üstü uç bölgeler.",
    "W.R": "Williams %R. -80 altı aşırı satım, -20 üstü aşırı alım.",
    "Mom": "Momentum; fiyat ivmesi. 0 üstü yukarı ivme.",
    "AO": "Awesome Oscillator; momentum. 0 üstü boğa eğilimi.",
    "UO": "Ultimate Oscillator; üç periyotlu momentum dengesi.",
    "BBPower": "Alıcı/satıcı gücü. 0 üstü alıcılar baskın.",
    "ADX": "Trendin GÜCÜ (yön değil). 25 üstü = güçlü trend var.",
    "ADX+DI": "Yukarı yön gücü.",
    "ADX-DI": "Aşağı yön gücü.",
    "Aroon.Up": "Son zirvenin tazeliği. 70 üstü güçlü yükseliş.",
    "Aroon.Down": "Son dibin tazeliği. Düşük olması iyiye işaret.",
    "MACD.macd": "MACD çizgisi; momentum yönü. 0 üstü pozitif.",
    "MACD.signal": "MACD sinyal çizgisi; kesişimler al/sat üretir.",
    "EMA5": "5 günlük üssel ortalama; fiyat üstündeyse kısa vade yukarı.",
    "EMA10": "10 günlük üssel ortalama.",
    "EMA20": "20 günlük üssel ortalama; kısa-orta vade trend.",
    "EMA50": "50 günlük üssel ortalama; orta vade trend çizgisi.",
    "EMA100": "100 günlük üssel ortalama.",
    "EMA200": "200 günlük üssel ortalama; uzun vade boğa/ayı sınırı.",
    "SMA10": "10 günlük basit ortalama; kısa vade.",
    "SMA20": "20 günlük basit ortalama.",
    "SMA50": "50 günlük basit ortalama.",
    "SMA200": "200 günlük basit ortalama; uzun vade.",
    "VWAP": "Hacim ağırlıklı ortalama fiyat; gün içi 'adil değer'.",
    "VWMA": "Hacim ağırlıklı hareketli ortalama.",
    "HullMA9": "Hızlı ve pürüzsüz ortalama; trend dönüşünü erken verir.",
    "BB.upper": "Bollinger üst bandı; fiyatın üstü pahalı/aşırı.",
    "BB.lower": "Bollinger alt bandı; fiyatın altı ucuz/aşırı satım.",
    "P.SAR": "Trend takip noktası; fiyat üstündeyse yükseliş.",
    "Ichimoku.BLine": "Ichimoku taban çizgisi; destek/direnç seviyesi.",
    "ATR": "Ortalama gerçek aralık; volatiliteyi (oynaklık) ölçer.",
    "close": "Kapanış fiyatı.",
    "change": "Günlük yüzde değişim.",
    "volume": "İşlem gören pay adedi; likidite filtresi.",
    "relative_volume": "Anlık/günlük bağıl hacim (bugünkü hacim tipik hacme göre). 1+ = normalden hareketli.",
    "relative_volume_10d_calc": "Hacmin 10 günlük ortalamaya oranı. 1.5+ = hareketlilik.",
    "average_volume_10d_calc": "Son 10 günün ortalama işlem hacmi (likidite).",
    "average_volume_30d_calc": "Son 30 günün ortalama işlem hacmi.",
    "gap": "Açılış boşluğu: bugünkü açılışın önceki kapanışa göre farkı (%).",
    "Perf.W": "Son bir haftanın getirisi (%).",
    "Perf.1M": "Son bir ayın getirisi (%).",
    "Perf.Y": "Son bir yılın getirisi (%).",
    "price_52_week_high": "Son 52 haftanın en yüksek fiyatı (direnç/zirve).",
    "price_52_week_low": "Son 52 haftanın en düşük fiyatı (destek/dip).",
    "EMA30": "30 günlük üssel ortalama.",
    "SMA30": "30 günlük basit ortalama.",
    "SMA100": "100 günlük basit ortalama.",
    "BB.basis": "Bollinger orta bandı (20 günlük ortalama).",
    "KltChnl.upper": "Keltner kanalı üst sınırı.",
    "KltChnl.lower": "Keltner kanalı alt sınırı.",
    "KltChnl.basis": "Keltner kanalı orta çizgisi.",
    "Ichimoku.Lead1": "Ichimoku öncü çizgi A (bulut sınırı).",
    "Ichimoku.Lead2": "Ichimoku öncü çizgi B (bulut sınırı).",
    "Stoch.RSI.D": "Stokastik RSI %D (sinyal çizgisi).",
    "Recommend.All": "TradingView teknik özeti. +0.5 üstü Güçlü Al.",
    "price_earnings_ttm": "F/K oranı; düşük olması görece ucuz (sektöre göre yorumla).",
    "price_book_fq": "PD/DD; defter değerine göre fiyat. Düşük = ucuz.",
    "dividends_yield": "Temettü verimi (%).",
    "market_cap_basic": "Şirketin toplam piyasa değeri (TL).",
    "ROC": "Fiyat değişim hızı (%). 0 üstü yukarı ivme.",
    "MoneyFlow": "Para Akışı Endeksi (MFI). 20 altı aşırı satım, 80 üstü aşırı alım.",
    "ChaikinMoneyFlow": "Hacimle para giriş/çıkışı. 0 üstü alım baskısı.",
    "Pivot.M.Classic.Middle": "Günün denge noktası; fiyat üstündeyse boğa eğilimi.",
    "Pivot.M.Classic.R1": "1. direnç seviyesi; üstüne çıkış kırılım sayılır.",
    "Pivot.M.Classic.R2": "2. direnç seviyesi (daha güçlü).",
    "Pivot.M.Classic.S1": "1. destek seviyesi; üstünde kalması olumlu.",
    "Pivot.M.Classic.S2": "2. destek seviyesi (daha güçlü).",
    "Ichimoku.CLine": "Tenkan (çevirme) çizgisi; kısa vade denge.",
    "return_on_equity": "Özkaynak kârlılığı (ROE). Yüksek = verimli şirket.",
    "net_margin": "Net kâr marjı (%). Satışın ne kadarı kâra dönüyor.",
    "debt_to_equity": "Borç/özkaynak. Düşük = sağlam bilanço.",
    "total_revenue_yoy_growth_ttm": "Yıllık ciro büyümesi (%).",
    "current_ratio": "Cari oran; kısa vadeli borç ödeme gücü. 1.5+ rahat.",
}


def aciklama_al(anahtar: str) -> str:
    return ACIKLAMALAR.get(anahtar, "")


def _suffix(tanim, zaman):
    """Temel analiz alanları zaman diliminden etkilenmez."""
    return "" if tanim.get("zaman_yok") else zaman


def _uygula(alan, op, hedef):
    c = col(alan)
    if op == "<":   return c < hedef
    if op == "<=":  return c <= hedef
    if op == ">":   return c > hedef
    if op == ">=":  return c >= hedef
    if op == "yukarı keser": return c.crosses_above(hedef)
    if op == "aşağı keser":  return c.crosses_below(hedef)
    raise ValueError(f"Operatör için _uygula uygun değil: {op}")


def kosul_uret(secim: dict, zaman: str = ""):
    """Tek bir seçimi tradingview-screener koşuluna çevirir.
    zaman: '' (günlük) | '|60' | '|240' | '|1W'."""
    if secim["tip"] == "hazir":
        return HAZIR_SINYALLER[secim["anahtar"]]["kosul"](zaman)

    tanim = KATALOG[secim["anahtar"]]
    s = _suffix(tanim, zaman)
    alan = f"{tanim['alan']}{s}"
    op = secim["op"]

    if op in ("arada", "arada değil"):
        d1, d2 = secim["deger"], secim["deger2"]
        return col(alan).between(d1, d2) if op == "arada" else col(alan).not_between(d1, d2)

    if secim.get("hedef_turu") == "alan":
        hedef = col(f"{secim['hedef_alan']}{s}")
    else:
        hedef = secim["deger"]

    return _uygula(alan, op, hedef)


# ==========================================================================
# HAZIR STRATEJİ ŞABLONLARI — tek tıkla yüklenir (app.py kombin yükleme yolu)
# ==========================================================================
STRATEJILER = {
    "🎯 Dip Avı": {
        "aciklama": "Aşırı satım + likidite: tepki yükselişi adayları.",
        "zaman": "Günlük", "endeks": "BIST 100", "mantik": "VE",
        "secimler": [
            {"tip": "metrik", "anahtar": "RSI", "op": "<", "hedef_turu": "deger", "deger": 30},
            {"tip": "metrik", "anahtar": "Stoch.K", "op": "<", "hedef_turu": "deger", "deger": 20},
            {"tip": "metrik", "anahtar": "volume", "op": ">", "hedef_turu": "deger", "deger": 1_000_000},
        ],
    },
    "🚀 Momentum Kırılımı": {
        "aciklama": "Fiyat EMA20 üstünde, MACD pozitif, güçlü trend, RSI > 50.",
        "zaman": "Günlük", "endeks": "Tüm BIST", "mantik": "VE",
        "secimler": [
            {"tip": "metrik", "anahtar": "EMA20", "op": "<", "hedef_turu": "alan", "hedef_alan": "close"},
            {"tip": "hazir", "anahtar": "macd_al"},
            {"tip": "metrik", "anahtar": "ADX", "op": ">", "hedef_turu": "deger", "deger": 25},
            {"tip": "metrik", "anahtar": "RSI", "op": ">", "hedef_turu": "deger", "deger": 50},
        ],
    },
    "⭐ Golden Cross + Hacim": {
        "aciklama": "EMA50, EMA200'ü yukarı kesmiş ve hacim yüksek.",
        "zaman": "Günlük", "endeks": "Tüm BIST", "mantik": "VE",
        "secimler": [
            {"tip": "hazir", "anahtar": "golden_cross"},
            {"tip": "metrik", "anahtar": "volume", "op": ">", "hedef_turu": "deger", "deger": 2_000_000},
            {"tip": "metrik", "anahtar": "EMA200", "op": "<", "hedef_turu": "alan", "hedef_alan": "close"},
        ],
    },
    "📈 Trend Takibi": {
        "aciklama": "Sağlam yükseliş: fiyat > EMA50, EMA200 üstünde, ADX güçlü, RSI 50–70.",
        "zaman": "Günlük", "endeks": "BIST 100", "mantik": "VE",
        "secimler": [
            {"tip": "metrik", "anahtar": "EMA50", "op": "<", "hedef_turu": "alan", "hedef_alan": "close"},
            {"tip": "hazir", "anahtar": "fiyat_ema200_ustu"},
            {"tip": "metrik", "anahtar": "ADX", "op": ">", "hedef_turu": "deger", "deger": 25},
            {"tip": "metrik", "anahtar": "RSI", "op": "arada", "deger": 50, "deger2": 70},
        ],
    },
    "💎 Ucuz + Teknik Güçlü": {
        "aciklama": "Düşük F/K, pozitif teknik rating, likit.",
        "zaman": "Günlük", "endeks": "Tüm BIST", "mantik": "VE",
        "secimler": [
            {"tip": "metrik", "anahtar": "price_earnings_ttm", "op": "arada", "deger": 0, "deger2": 10},
            {"tip": "metrik", "anahtar": "Recommend.All", "op": ">", "hedef_turu": "deger", "deger": 0.3},
            {"tip": "metrik", "anahtar": "volume", "op": ">", "hedef_turu": "deger", "deger": 1_000_000},
        ],
    },
}
