"""
BIST İndikatör Kombin Tarayıcı — Streamlit arayüzü (koyu tema).

Çalıştırmak için:
    cd ~/Desktop/bist_tarayici
    streamlit run app.py
"""

import os
import json
from datetime import datetime, time

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from indikatorler import (
    KATALOG, HAZIR_SINYALLER, KARSILASTIRMA_ALANLARI, OPERATORLER,
    ZAMAN_DILIMLERI, ENDEKSLER, SEKTORLER, STRATEJILER, aciklama_al,
)
from tarayici import tara, rating_rozet, veri_bilgisi
import kombin_store as ks
import zamanlama_store as zs
import piyasa
import haberler
import backtest


def _varsayilan_chat():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telegram.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("chat_id", "")
    except Exception:
        return ""


def _motor_durum():
    """Zamanlayıcı motorunun son çalışma zamanını döndürür (yoksa None)."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "durum.json")
    try:
        with open(p, encoding="utf-8") as f:
            t = json.load(f).get("son_tik", "")
        return datetime.fromisoformat(t).strftime("%d.%m %H:%M:%S")
    except Exception:
        return None

MAKS = 30        # en fazla kaç indikatör kombinlenebilir
TAKIP_MAKS = 3   # takip listesine en fazla kaç hisse

st.set_page_config(
    page_title="BIST Tarayıcı", page_icon="📊",
    layout="wide", initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------
# Önbellekli veri çekiciler
# --------------------------------------------------------------------------
@st.cache_data(ttl=120, show_spinner=False)
def _piyasa_cached():
    return piyasa.piyasa_verileri()


@st.cache_data(ttl=60, show_spinner=False)
def _hisse_cached(kodlar: tuple):
    return piyasa.hisse_verileri(list(kodlar))


@st.cache_data(ttl=1800, show_spinner=False)
def _haberler_cached():
    return haberler.haberler(10)


def _buyuk_tl(x):
    """Piyasa değerini okunur biçime çevirir: 1,7 Tn / 12 Mr / 340 Mn."""
    if x is None or pd.isna(x):
        return "—"
    x = float(x)
    if x >= 1e12: return f"{x/1e12:.1f} Tn".replace(".", ",")
    if x >= 1e9:  return f"{x/1e9:.1f} Mr".replace(".", ",")
    if x >= 1e6:  return f"{x/1e6:.0f} Mn"
    return f"{x:,.0f}"


# --- TradingView grafik gömme (kombin indikatörleriyle) ---
TV_STUDY = {
    "RSI": "RSI@tv-basicstudies", "RSI7": "RSI@tv-basicstudies",
    "Stoch.K": "Stochastic@tv-basicstudies", "Stoch.D": "Stochastic@tv-basicstudies",
    "Stoch.RSI.K": "StochasticRSI@tv-basicstudies",
    "CCI20": "CCI@tv-basicstudies", "W.R": "WilliamR@tv-basicstudies",
    "Mom": "Momentum@tv-basicstudies", "AO": "AwesomeOscillator@tv-basicstudies",
    "UO": "UltimateOscillator@tv-basicstudies", "BBPower": "BullBearPower@tv-basicstudies",
    "ADX": "averagedirectionalindex@tv-basicstudies", "ADX+DI": "averagedirectionalindex@tv-basicstudies",
    "ADX-DI": "averagedirectionalindex@tv-basicstudies",
    "Aroon.Up": "Aroon@tv-basicstudies", "Aroon.Down": "Aroon@tv-basicstudies",
    "MACD.macd": "MACD@tv-basicstudies", "MACD.signal": "MACD@tv-basicstudies",
    "VWAP": "VWAP@tv-basicstudies", "VWMA": "MAVolumeWeighted@tv-basicstudies",
    "HullMA9": "hullMA@tv-basicstudies",
    "BB.upper": "BB@tv-basicstudies", "BB.lower": "BB@tv-basicstudies",
    "P.SAR": "PSAR@tv-basicstudies", "ATR": "ATR@tv-basicstudies",
    "ROC": "ROC@tv-basicstudies", "MoneyFlow": "MF@tv-basicstudies",
    "ChaikinMoneyFlow": "ChaikinMoneyFlow@tv-basicstudies",
    "change": None, "close": None, "volume": None, "relative_volume_10d_calc": None,
    # hazır sinyaller
    "macd_al": "MACD@tv-basicstudies", "macd_yukari_keser": "MACD@tv-basicstudies",
    "golden_cross": "MAExp@tv-basicstudies", "death_cross": "MAExp@tv-basicstudies",
    "fiyat_ema200_ustu": "MAExp@tv-basicstudies",
    "ichimoku_bulut_ustu": "IchimokuCloud@tv-basicstudies",
    "ichimoku_tk_kesisim": "IchimokuCloud@tv-basicstudies",
}


def _study_for(anahtar):
    if anahtar.startswith("EMA"): return "MAExp@tv-basicstudies"
    if anahtar.startswith("SMA"): return "MASimple@tv-basicstudies"
    if anahtar.startswith("Pivot"): return "PivotPointsStandard@tv-basicstudies"
    if anahtar.startswith("Ichimoku"): return "IchimokuCloud@tv-basicstudies"
    return TV_STUDY.get(anahtar)


def _tv_studies(secimler):
    out = []
    for s in secimler:
        sid = _study_for(s["anahtar"])
        if sid and sid not in out:
            out.append(sid)
    return out


def _study_adlari(secimler):
    adlar = []
    for s in secimler:
        if not _study_for(s["anahtar"]):
            continue
        adlar.append(HAZIR_SINYALLER[s["anahtar"]]["ad"] if s["tip"] == "hazir"
                     else KATALOG[s["anahtar"]]["ad"])
    return adlar


def _tv_interval(zaman_label):
    return {"Günlük": "D", "1 Saatlik": "60", "4 Saatlik": "240", "Haftalık": "W"}.get(zaman_label, "D")


def _grafik_html(symbol, studies, interval):
    cfg = {
        "autosize": True, "symbol": symbol, "interval": interval,
        "timezone": "Europe/Istanbul", "theme": "dark", "style": "1", "locale": "tr",
        "toolbar_bg": "#161b22", "hide_side_toolbar": False, "allow_symbol_change": True,
        "studies": studies, "container_id": "tvchart",
    }
    return f"""
    <div class="tradingview-widget-container" style="height:540px;width:100%;">
      <div id="tvchart" style="height:540px;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">new TradingView.widget({json.dumps(cfg)});</script>
    </div>"""


def _strateji_yukle(strat_ad):
    s = STRATEJILER[strat_ad]
    st.session_state["_yukle"] = {
        "secimler": s["secimler"], "zaman": s["zaman"],
        "endeks": s["endeks"], "mantik": s["mantik"], "sektorler": [],
    }
    st.rerun()


# --------------------------------------------------------------------------
# Stil — koyu, sade, profesyonel
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
      #MainMenu, footer, header [data-testid="stToolbar"] {visibility: hidden;}
      .block-container {padding-top: 2.2rem; max-width: 1180px;}
      .app-title {font-size: 1.9rem; font-weight: 700; letter-spacing:-.02em; margin-bottom:.1rem; color:#e6edf3;}
      .app-sub   {color:#8b949e; font-size:.95rem; margin-bottom:1.2rem;}
      .step {font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em;
             color:#58a6ff; margin:.6rem 0 .5rem;}
      div[data-testid="stVerticalBlockBorderWrapper"] {
          border-radius:12px; border:1px solid #30363d; background:#161b22;
          box-shadow:0 1px 2px rgba(0,0,0,.25);}
      .card-name {font-weight:650; font-size:.95rem; margin-bottom:.2rem; color:#e6edf3;}
      .card-grp  {font-size:.72rem; color:#8b949e; text-transform:uppercase; letter-spacing:.05em;}
      .chip {display:inline-block; background:rgba(47,129,247,.14); color:#79c0ff;
             border:1px solid rgba(47,129,247,.4); border-radius:20px;
             padding:3px 12px; margin:3px 4px 3px 0; font-size:.82rem; font-weight:550;}
      .chip-and {color:#6e7681; font-weight:600; margin:0 2px; font-size:.8rem;}
      .stButton button {border-radius:10px; font-weight:600;}
      div[data-testid="stMetricValue"] {font-size:1.6rem;}
      .disclaimer {color:#6e7681; font-size:.78rem; margin-top:1rem; border-top:1px solid #21262d; padding-top:.6rem;}
      .haber {margin:.3rem 0; font-size:.9rem; line-height:1.35;}
      .haber a {color:#79c0ff; text-decoration:none;}
      .haber a:hover {text-decoration:underline;}
      .haber-meta {color:#6e7681; font-size:.78rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Seçim havuzu:  görünen ad <-> (tip, anahtar)
# --------------------------------------------------------------------------
secenekler = {}
for anahtar, t in HAZIR_SINYALLER.items():
    secenekler[f"⚡ {t['ad']}"] = ("hazir", anahtar)
for anahtar, t in KATALOG.items():
    secenekler[f"{t['ad']}  ·  {t['grup']}"] = ("metrik", anahtar)
ters_secenek = {v: k for k, v in secenekler.items()}

# --------------------------------------------------------------------------
# Kayıtlı kombin / strateji yükleme — widget'lar OLUŞMADAN ÖNCE durumu yükle
# --------------------------------------------------------------------------
if "_yukle" in st.session_state:
    paket = st.session_state.pop("_yukle")
    if isinstance(paket, list):
        yuklenecek, meta = paket, {}
    else:
        yuklenecek, meta = paket.get("secimler", []), paket

    gorunenler = []
    for s in yuklenecek:
        kimlik = (s.get("tip"), s.get("anahtar"))
        if kimlik not in ters_secenek:
            continue
        gorunenler.append(ters_secenek[kimlik])
        if s["tip"] != "metrik":
            continue
        a = s["anahtar"]
        st.session_state[f"op_{a}"] = s["op"]
        if s["op"] in ("arada", "arada değil"):
            st.session_state[f"d1_{a}"] = float(s["deger"])
            st.session_state[f"d2_{a}"] = float(s["deger2"])
        elif s.get("hedef_turu") == "alan":
            st.session_state[f"ht_{a}"] = "Başka indikatör"
            st.session_state[f"ha_{a}"] = s["hedef_alan"]
        else:
            st.session_state[f"ht_{a}"] = "Sabit değer"
            st.session_state[f"d_{a}"] = float(s["deger"])
    st.session_state["indik_secim"] = gorunenler

    if meta.get("zaman") in ZAMAN_DILIMLERI:
        st.session_state["zaman_dilimi"] = meta["zaman"]
    if meta.get("endeks") in ENDEKSLER:
        st.session_state["endeks_sec"] = meta["endeks"]
    if meta.get("mantik") in ("VE", "VEYA"):
        st.session_state["mantik_sec"] = meta["mantik"]
    if isinstance(meta.get("sektorler"), list):
        st.session_state["sektor_sec"] = meta["sektorler"]

# --------------------------------------------------------------------------
# Başlık
# --------------------------------------------------------------------------
st.markdown('<div class="app-title">📊 BIST İndikatör Tarayıcı</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-sub">Hazır bir strateji seç ya da kendi indikatör kombinini kur — '
    'koşulları sağlayan BIST hisseleri anında listelensin.</div>',
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Adım 0 — Hazır strateji
# --------------------------------------------------------------------------
st.markdown('<div class="step">Hazır strateji (en kolay başlangıç)</div>', unsafe_allow_html=True)
sc1, sc2 = st.columns([3, 1])
strat_ad = sc1.selectbox("Strateji", ["— Kendim kuracağım —"] + list(STRATEJILER.keys()),
                         key="strateji_sec", label_visibility="collapsed")
if strat_ad != "— Kendim kuracağım —":
    sc1.caption("ℹ️ " + STRATEJILER[strat_ad]["aciklama"])
if sc2.button("⚙️ Uygula", use_container_width=True, disabled=(strat_ad == "— Kendim kuracağım —")):
    _strateji_yukle(strat_ad)

# --------------------------------------------------------------------------
# Adım 1 — indikatör seçimi
# --------------------------------------------------------------------------
st.markdown('<div class="step">İndikatörleri seç</div>', unsafe_allow_html=True)
secili_adlar = st.multiselect(
    "İndikatör seç", options=list(secenekler.keys()), max_selections=MAKS,
    placeholder=f"İndikatör ara veya seç (en fazla {MAKS})…",
    label_visibility="collapsed", key="indik_secim",
)

# --------------------------------------------------------------------------
# Adım 2 — koşul kartları (3'lü ızgara, her birinde Türkçe ipucu)
# --------------------------------------------------------------------------
secimler = []
if secili_adlar:
    st.markdown('<div class="step">Koşulları ayarla</div>', unsafe_allow_html=True)
    sutunlar = st.columns(3)
    for i, gorunen in enumerate(secili_adlar):
        tip, anahtar = secenekler[gorunen]
        kart = sutunlar[i % 3].container(border=True)

        if tip == "hazir":
            t = HAZIR_SINYALLER[anahtar]
            kart.markdown(f'<div class="card-grp">Hazır Sinyal</div>'
                          f'<div class="card-name">{t["ad"]}</div>', unsafe_allow_html=True)
            kart.caption("Ayar gerektirmez.")
            secimler.append({"tip": "hazir", "anahtar": anahtar})
            continue

        tanim = KATALOG[anahtar]
        kart.markdown(f'<div class="card-grp">{tanim["grup"]}</div>'
                      f'<div class="card-name">{tanim["ad"]}</div>', unsafe_allow_html=True)
        ipucu = aciklama_al(anahtar)
        if ipucu:
            kart.caption("💡 " + ipucu)
        op = kart.selectbox("Operatör", OPERATORLER,
                            index=OPERATORLER.index(tanim["op"]), key=f"op_{anahtar}")
        secim = {"tip": "metrik", "anahtar": anahtar, "op": op}

        if op in ("arada", "arada değil"):
            amin, amax = tanim.get("aralik", (-1000, 1000))
            c1, c2 = kart.columns(2)
            secim["deger"] = c1.number_input("Alt", value=float(tanim.get("deger", amin)), key=f"d1_{anahtar}")
            secim["deger2"] = c2.number_input("Üst", value=float(tanim.get("deger", amax)), key=f"d2_{anahtar}")
        else:
            varsayilan_alan = tanim["tur"] == "seviye"
            hedef_turu = kart.radio("Karşılaştır", ["Sabit değer", "Başka indikatör"],
                                    index=1 if varsayilan_alan else 0, horizontal=True, key=f"ht_{anahtar}")
            if hedef_turu == "Sabit değer":
                secim["hedef_turu"] = "deger"
                secim["deger"] = kart.number_input("Değer", value=float(tanim.get("deger", 0)), key=f"d_{anahtar}")
            else:
                secim["hedef_turu"] = "alan"
                vars_alan = tanim.get("hedef_alan", "close")
                secim["hedef_alan"] = kart.selectbox(
                    "Karşılaştırılan alan", KARSILASTIRMA_ALANLARI,
                    index=KARSILASTIRMA_ALANLARI.index(vars_alan) if vars_alan in KARSILASTIRMA_ALANLARI else 0,
                    key=f"ha_{anahtar}")
        secimler.append(secim)


# --------------------------------------------------------------------------
# Kombin özeti yardımcısı
# --------------------------------------------------------------------------
def _ozet(s):
    if s["tip"] == "hazir":
        return HAZIR_SINYALLER[s["anahtar"]]["ad"]
    t = KATALOG[s["anahtar"]]
    if s["op"] in ("arada", "arada değil"):
        return f"{t['ad']} {s['op']} {s['deger']:g}–{s['deger2']:g}"
    if s.get("hedef_turu") == "alan":
        return f"{t['ad']} {s['op']} {s['hedef_alan']}"
    return f"{t['ad']} {s['op']} {s['deger']:g}"


# --------------------------------------------------------------------------
# Gelişmiş ayarlar (varsayılanlar; açılır panelin içinde — ana ekran sade kalsın)
# --------------------------------------------------------------------------
zaman_label, endeks_label, mantik, sektor_tr = "Günlük", "Tüm BIST", "VE", []

if secili_adlar:
    with st.expander("⚙️ Gelişmiş ayarlar  ·  zaman dilimi · endeks · sektör · mantık"):
        ay1, ay2, ay3 = st.columns(3)
        zaman_label = ay1.selectbox("Zaman dilimi", list(ZAMAN_DILIMLERI.keys()), key="zaman_dilimi",
                                    help="Koşulların hesaplandığı periyot.")
        endeks_label = ay2.selectbox("Evren", list(ENDEKSLER.keys()), key="endeks_sec",
                                     help="Hangi hisse grubunda aransın.")
        mantik = ay3.radio("Koşul mantığı", ["VE", "VEYA"], horizontal=True, key="mantik_sec",
                           help="VE: tüm koşullar sağlanmalı. VEYA: herhangi biri yeterli.")
        sektor_tr = st.multiselect("Sektör (opsiyonel — boş = tümü)",
                                   list(SEKTORLER.values()), key="sektor_sec")

    # Kombin özeti (chips) + ayar rozeti
    baglac = "VEYA" if mantik == "VEYA" else "VE"
    chips = f'<span class="chip-and">{baglac}</span>'.join(
        f'<span class="chip">{_ozet(s)}</span>' for s in secimler)
    st.markdown('<div class="step">Kombin özeti</div>', unsafe_allow_html=True)
    st.markdown(chips, unsafe_allow_html=True)
    st.caption(f"⏱ {zaman_label}  ·  🏛 {endeks_label}  ·  🔗 {mantik}"
               + (f"  ·  🏷 {', '.join(sektor_tr)}" if sektor_tr else ""))
    st.markdown("")

    c1, c2, _ = st.columns([1.4, 1, 3])
    limit = c1.slider("Maks. sonuç", 10, 500, 100, step=10, label_visibility="collapsed")
    tara_butonu = c2.button("🔍  Tara", type="primary", use_container_width=True)
    c1.caption(f"En fazla {limit} sonuç")

    # ---- Geçmiş testi (backtest) ----
    with st.expander("🧪 Geçmiş testi — bu kombin geçmişte ne kadar isabetliydi?"):
        st.caption("Kombinin sinyallerini geçmiş veride bulup, sinyalden N gün sonraki "
                   "ortalama getiriyi ölçer. Yalnızca RSI, MACD, EMA/SMA, fiyat-ortalama, "
                   "golden/death cross, değişim ve hacim desteklenir.")
        bc1, bc2, bc3 = st.columns(3)
        bt_horizon = bc1.selectbox("Kaç gün sonrası?", [3, 5, 10, 20], index=1, key="bt_h")
        bt_period = bc2.selectbox("Geçmiş dönem", ["1y", "2y", "5y"], index=1, key="bt_p")
        bt_evren = bc3.selectbox("Evren", list(backtest.EVRENLER.keys()), index=0, key="bt_e")

        if st.button("🧪  Backtest'i çalıştır", use_container_width=True):
            with st.spinner("Geçmiş taranıyor (biraz sürebilir)…"):
                try:
                    bt_ozet, bt_detay = backtest.backtest(
                        secimler, mantik=mantik, horizon=bt_horizon,
                        period=bt_period, evren=bt_evren)
                except Exception:
                    st.error("Backtest şu an çalıştırılamadı, tekrar dene.")
                    bt_ozet = None
            if bt_ozet:
                if bt_ozet["sinyal"] == 0:
                    st.warning("Bu kombin için geçmişte (desteklenen indikatörlerle) sinyal bulunamadı.")
                else:
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Sinyal sayısı", bt_ozet["sinyal"])
                    k2.metric("İsabet (kâr oranı)", f"%{bt_ozet['isabet']}")
                    k3.metric(f"Ort. {bt_ozet['horizon']}g getiri", f"%{bt_ozet['ort_getiri']}")
                    k4.metric("Medyan getiri", f"%{bt_ozet['medyan']}")
                    st.caption(f"En iyi %{bt_ozet['en_iyi']} · En kötü %{bt_ozet['en_kotu']} · "
                               f"{bt_ozet['hisse_sayisi']} hisse · {bt_period} dönem")
                if bt_ozet["desteklenmeyen"]:
                    st.info("⚠️ Backtest'te atlanan indikatörler: "
                            + ", ".join(bt_ozet["desteklenmeyen"]))
                if bt_detay:
                    dfd = pd.DataFrame(bt_detay).rename(columns={
                        "kod": "Hisse", "tarih": "Sinyal tarihi",
                        "getiri": f"{bt_ozet['horizon']}g getiri %"})
                    st.dataframe(dfd, hide_index=True, use_container_width=True)
        st.caption("⚠️ Geçmiş performans gelecek için garanti değildir; maliyet/kayma dahil edilmemiştir.")

    if tara_butonu:
        tr2en = {v: k for k, v in SEKTORLER.items()}
        with st.spinner("TradingView taranıyor…"):
            try:
                toplam, df = tara(
                    secimler, limit=limit,
                    zaman=ZAMAN_DILIMLERI[zaman_label],
                    endeks=ENDEKSLER[endeks_label],
                    sektorler=[tr2en[s] for s in sektor_tr] if sektor_tr else None,
                    mantik=mantik,
                )
                st.session_state["sonuc"] = {
                    "df": df, "toplam": toplam, "secimler": list(secimler),
                    "zaman_label": zaman_label, "veri": veri_bilgisi(df),
                }
            except Exception:
                st.error("Şu an veriye ulaşılamadı. Birazdan tekrar dene.")
                st.session_state.pop("sonuc", None)

    # ---- Sonuçlar (session_state'ten — satır tıklayınca kaybolmaz) ----
    sonuc = st.session_state.get("sonuc")
    if sonuc is not None and sonuc.get("df") is not None:
        df, toplam = sonuc["df"], sonuc["toplam"]
        vb = sonuc.get("veri") or {}
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Eşleşen kağıt", toplam)
        m2.metric("Gösterilen", len(df))
        m3.metric("📅 Veri saati", vb.get("saat") or "—",
                  help="Verinin TradingView'deki gerçek saati (İstanbul).")

        ipuc = []
        if vb.get("gecikme_dk"):
            ipuc.append(f"⏱ {vb['gecikme_dk']} dk gecikmeli")
        elif vb.get("gecikme_dk") == 0:
            ipuc.append("⚡ canlı")
        if vb.get("acik") is True:
            ipuc.append("🟢 Piyasa açık")
        elif vb.get("acik") is False:
            ipuc.append("🔴 Piyasa kapalı — son kapanış verisi")
        ipuc.append(f"⏱ {sonuc['zaman_label']} mum")
        st.caption("Bu tarama, **" + (vb.get("saat") or "?") + "** itibarıyla "
                   + " · ".join(ipuc) + " veriye göre yapıldı.")

        if len(df) == 0:
            st.warning("Bu kombini sağlayan kağıt yok. Koşulları gevşet ya da mantığı VEYA yap.")
        else:
            st.caption("👆 Bir hisseye **tıkla** — kombindeki indikatörlerle grafiği en altta açılır.")
            g = df.copy()
            g["Rating"] = g["Recommend.All"].apply(rating_rozet)
            g["Sektör"] = g["sector"].map(SEKTORLER).fillna(g["sector"])
            g["Piyasa Değeri"] = g["market_cap_basic"].apply(_buyuk_tl)
            if "ticker" in g.columns:
                g["Grafik"] = g["ticker"].apply(
                    lambda x: f"https://tradingview.com/symbols/{x.replace(':', '-')}/")

            goster = g[["name", "close", "change", "Rating", "RSI", "ADX",
                        "price_earnings_ttm", "Piyasa Değeri", "Sektör", "Grafik"]].copy()
            for kol in ["close", "change", "RSI", "ADX", "price_earnings_ttm"]:
                goster[kol] = pd.to_numeric(goster[kol], errors="coerce").round(2)

            secim_event = st.dataframe(
                goster, use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row", key="sonuc_tablo",
                column_config={
                    "name": "Hisse",
                    "close": "Fiyat",
                    "change": st.column_config.NumberColumn("Değ %", format="%.2f"),
                    "price_earnings_ttm": st.column_config.NumberColumn("F/K", format="%.1f"),
                    "Grafik": st.column_config.LinkColumn("Grafik", display_text="Aç ↗"),
                },
            )
            _gizli = ["ticker", "update_mode", "current_session", "last-price-update-time"]
            st.download_button("⬇️  CSV indir",
                               g.drop(columns=_gizli, errors="ignore").to_csv(index=False).encode("utf-8"),
                               "bist_tarama.csv", "text/csv")

            # ---- Tıklanan hissenin grafiği (CSV'nin ALTINDA) ----
            try:
                secili_rows = list(secim_event.selection.rows)
            except Exception:
                secili_rows = []

            st.markdown("")
            if secili_rows:
                trow = g.iloc[secili_rows[0]]
                symbol = str(trow.get("ticker") or f"BIST:{trow['name']}")
                studies = _tv_studies(sonuc["secimler"])
                st.markdown(f'<div class="step">📈 {trow["name"]} grafiği · {sonuc["zaman_label"]}</div>',
                            unsafe_allow_html=True)
                adlar = _study_adlari(sonuc["secimler"])
                if adlar:
                    st.caption("Yüklü indikatörler: " + ", ".join(adlar))
                components.html(_grafik_html(symbol, studies, _tv_interval(sonuc["zaman_label"])), height=560)
            else:
                st.info("👆 Tablodan bir hisseye tıkla — indikatörlü TradingView grafiği burada açılır.")
else:
    st.session_state.pop("sonuc", None)  # indikatör kalmadıysa eski sonucu temizle
    # ---- Boş ekran: tıkla-uygula örnek kartları ----
    st.markdown('<div class="step">Hızlı başla — bir örneğe tıkla</div>', unsafe_allow_html=True)
    ornekler = list(STRATEJILER.items())
    kolonlar = st.columns(len(ornekler))
    for kol, (sad, sbilgi) in zip(kolonlar, ornekler):
        with kol.container(border=True):
            st.markdown(f'<div class="card-name">{sad}</div>', unsafe_allow_html=True)
            st.caption(sbilgi["aciklama"])
            if st.button("Uygula", key=f"ornek_{sad}", use_container_width=True):
                _strateji_yukle(sad)

    # ---- Günlük finans haberleri ----
    st.markdown("")
    bh1, bh2 = st.columns([4, 1])
    bh1.markdown('<div class="step">📰 Günlük Finans Haberleri</div>', unsafe_allow_html=True)
    if bh2.button("🔄", key="haber_yenile", help="Haberleri yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    _hbr = _haberler_cached()
    if not _hbr:
        st.caption("Haberler şu an alınamadı, birazdan tekrar dene.")
    else:
        for h in _hbr:
            saat = h["tarih"].strftime("%H:%M") if h["tarih"] else ""
            meta = h["kaynak"] + (f" · {saat}" if saat else "")
            link = h["link"] or "#"
            st.markdown(
                f'<div class="haber">📄 <a href="{link}" target="_blank">{h["baslik"]}</a>'
                f'<span class="haber-meta"> — {meta}</span></div>',
                unsafe_allow_html=True)

st.markdown(
    '<div class="disclaimer">⚠️ Bu araç yalnızca teknik tarama yapar; '
    '<b>yatırım tavsiyesi değildir</b>. Veriler TradingView ve Yahoo Finance kaynaklıdır, '
    'gecikmeli olabilir.</div>',
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Kenar çubuğu — Kombinlerim · Piyasa · Takip Listesi
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💾 Kombinlerim")
    st.caption("Kurduğun kombini (ayarlarıyla) kaydet, tek tıkla geri yükle.")

    ad = st.text_input("Kombin adı", placeholder="örn. RSI dip avı", key="kaydet_ad")
    if st.button("💾  Kaydet", use_container_width=True, disabled=not secimler):
        if not ad.strip():
            st.warning("Önce bir ad gir.")
        else:
            ks.kaydet(ad.strip(), {
                "secimler": secimler, "zaman": zaman_label,
                "endeks": endeks_label, "mantik": mantik, "sektorler": sektor_tr,
            })
            st.toast(f"“{ad.strip()}” kaydedildi ✓", icon="💾")

    st.divider()
    kayitlar = ks.tum_kombinler()
    if not kayitlar:
        st.caption("Henüz kayıtlı kombin yok.")
    else:
        sec_ad = st.selectbox("Kayıtlı kombinler", list(kayitlar.keys()), key="yukle_sec")
        paket = kayitlar[sec_ad]
        sec_list = paket["secimler"] if isinstance(paket, dict) else paket
        st.caption(f"{len(sec_list)} koşul içeriyor.")
        b1, b2 = st.columns(2)
        if b1.button("📂  Yükle", use_container_width=True):
            st.session_state["_yukle"] = paket
            st.rerun()
        if b2.button("🗑️  Sil", use_container_width=True):
            ks.sil(sec_ad)
            st.toast(f"“{sec_ad}” silindi", icon="🗑️")
            st.rerun()

    # ----- Otomatik bildirim -----
    st.divider()
    with st.expander("⏰ Otomatik Bildirim"):
        st.caption("Kayıtlı bir kombini, istediğin saatte otomatik tarayıp Telegram'a yollar.")
        GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        z_kayitlar = ks.tum_kombinler()

        if not z_kayitlar:
            st.info("Önce yukarıdan bir kombin kaydet, sonra ona bildirim kurabilirsin.")
        else:
            z_kombin = st.selectbox("Hangi kombin?", list(z_kayitlar.keys()), key="z_kombin")
            z_tip = st.radio("Sıklık", ["Rutin", "Tek seferlik"], horizontal=True, key="z_tip")

            z_siklik = z_haftagunu = z_tarih = None
            if z_tip == "Rutin":
                z_siklik = st.selectbox("Ne sıklıkla?", ["Her gün", "Hafta içi", "Haftalık"], key="z_siklik")
                if z_siklik == "Haftalık":
                    z_haftagunu = st.selectbox("Hangi gün?", GUNLER, key="z_gun")
            else:
                z_tarih = st.date_input("Tarih", key="z_tarih")

            z_saat = st.time_input("Saat", value=time(9, 45), key="z_saat")
            z_alici = st.text_input(
                "Alıcı (Telegram chat ID)", value=_varsayilan_chat(), key="z_alici",
                help="Kendine göndermek için olduğu gibi bırak. Başkasına için: o kişi "
                     "@iri_bist_bot'a /start demeli, sonra chat ID'sini buraya yaz.")
            st.caption("📱 Mesaj, bota /start demiş Telegram hesabına (telefonuna) gider.")

            if st.button("➕  Bildirimi kur", use_container_width=True, type="primary"):
                kayit = {
                    "kombin": z_kombin,
                    "tip": "rutin" if z_tip == "Rutin" else "tek",
                    "saat": z_saat.strftime("%H:%M"),
                    "chat_id": z_alici.strip(), "aktif": True,
                }
                if z_tip == "Rutin":
                    kayit["gunler"] = {"Her gün": "hergun", "Hafta içi": "haftaici",
                                       "Haftalık": "haftalik"}[z_siklik]
                    if z_siklik == "Haftalık":
                        kayit["hafta_gunu"] = GUNLER.index(z_haftagunu)
                else:
                    kayit["tarih"] = str(z_tarih)
                zs.ekle(kayit)
                st.toast("Bildirim kuruldu ⏰")
                st.rerun()

        # Kurulu bildirimler listesi
        mevcut = zs.tum()
        if mevcut:
            st.divider()
            st.caption("Kurulu bildirimler")
            ad_gun = {"hergun": "Her gün", "haftaici": "Hafta içi", "haftalik": "Haftalık"}
            for z in mevcut:
                if z.get("tip") == "tek":
                    ozet = f"📅 {z.get('tarih','')} · {z.get('saat','')}"
                else:
                    ozet = f"🔁 {ad_gun.get(z.get('gunler'), '')} · {z.get('saat','')}"
                durum = "" if z.get("aktif", True) else "  (bitti)"
                c1, c2 = st.columns([5, 1])
                c1.write(f"**{z.get('kombin')}**  \n{ozet}{durum}")
                if c2.button("🗑", key=f"zsil_{z['id']}"):
                    zs.sil(z["id"])
                    st.rerun()
        _md = _motor_durum()
        if _md:
            st.caption(f"⚙️ Motor son kontrol: {_md} · her 60 sn'de bir çalışır "
                       "(bilgisayar açıkken).")
        else:
            st.caption("⚙️ Motor her 60 sn'de bir kontrol eder; bilgisayarın o saatte açık olmalı.")

    # ----- Canlı piyasa -----
    st.divider()
    bsl1, bsl2 = st.columns([3, 1])
    bsl1.markdown("### 📈 Piyasa")
    if bsl2.button("🔄", help="Verileri yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    for v in _piyasa_cached():
        if v["fiyat"] is None:
            st.metric(v["ad"], "—")
        else:
            st.metric(v["ad"], piyasa.tl_format(v["fiyat"]), f"{v['degisim']:+.2f}%")

    # ----- Takip listesi -----
    st.divider()
    st.markdown("### ⭐ Takip Listesi")
    st.caption(f"En fazla {TAKIP_MAKS} BIST kodu — virgülle ayır (örn. ASELS, THYAO).")
    kodlar_str = st.text_input("Hisse kodları", value=piyasa.takip_oku(),
                               placeholder="ASELS, THYAO, GARAN",
                               key="takip_kodlari", label_visibility="collapsed")
    girilenler = [k.strip().upper() for k in kodlar_str.split(",") if k.strip()]
    kodlar = girilenler[:TAKIP_MAKS]
    piyasa.takip_yaz(", ".join(kodlar))
    if len(girilenler) > TAKIP_MAKS:
        st.caption(f"⚠️ Yalnızca ilk {TAKIP_MAKS} kod gösteriliyor.")
    if kodlar:
        for h in _hisse_cached(tuple(kodlar)):
            if h["bulundu"]:
                st.metric(h["ad"], piyasa.tl_format(h["fiyat"]), f"{h['degisim']:+.2f}%")
            else:
                st.metric(h["ad"], "bulunamadı")
    else:
        st.caption("Henüz hisse eklenmedi.")
