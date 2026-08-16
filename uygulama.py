"""
BIST Tarayıcı — basit uygulama arayüzü (baban için).

Akış:
  1) Ne yapmak istiyorsun?  [Tarama Yap] / [Performans Ölç]
  2) Tarama  → strateji seç → tara → Excel
  3) Performans → strateji seç + iki gün seç → Excel

Çalıştır:
    streamlit run uygulama.py
"""

from datetime import datetime, timezone, timedelta

import streamlit as st

import kombin_store as ks
import gecmis
import performans
import rapor
import rapor_performans
from otomasyon import _meta
from tarayici import tara, veri_bilgisi

IST = timezone(timedelta(hours=3))

st.set_page_config(page_title="BIST Tarayıcı", page_icon="📊", layout="centered")

st.markdown("""
<style>
  #MainMenu, footer, header [data-testid="stToolbar"] {visibility:hidden;}
  .block-container {padding-top:2.5rem; max-width:900px;}
  .baslik {font-size:2rem; font-weight:700; text-align:center; margin-bottom:.2rem;}
  .alt {text-align:center; color:#8b949e; margin-bottom:2rem;}
  .stButton button {height:5rem; font-size:1.15rem; font-weight:600; border-radius:12px;}
</style>
""", unsafe_allow_html=True)


def _basa_don():
    st.session_state.pop("mod", None)
    st.session_state.pop("sonuc", None)


# ---------------------------------------------------------------- ANA EKRAN
if "mod" not in st.session_state:
    st.markdown('<div class="baslik">📊 BIST Tarayıcı</div>', unsafe_allow_html=True)
    st.markdown('<div class="alt">Ne yapmak istiyorsun?</div>', unsafe_allow_html=True)

    s1, s2 = st.columns(2)
    if s1.button("🔍\n\nTARAMA YAP", use_container_width=True):
        st.session_state["mod"] = "tarama"
        st.rerun()
    if s2.button("📊\n\nPERFORMANS ÖLÇ", use_container_width=True):
        st.session_state["mod"] = "performans"
        st.rerun()

    st.markdown("")
    st.caption("**Tarama yap:** Seçtiğin stratejilerde şu an hangi hisseler çıkıyor → Excel")
    st.caption("**Performans ölç:** Geçmiş bir günün taramasındaki hisseler, "
               "seçtiğin güne kadar ne kazandırdı → Excel")
    st.stop()


kayitlar = ks.tum_kombinler()
if not kayitlar:
    st.error("Kayıtlı strateji yok.")
    st.button("← Geri", on_click=_basa_don)
    st.stop()

st.button("← Ana ekrana dön", on_click=_basa_don)

# ------------------------------------------------------------------ TARAMA
if st.session_state["mod"] == "tarama":
    st.markdown('<div class="baslik">🔍 Tarama Yap</div>', unsafe_allow_html=True)
    st.caption("Taramak istediğin stratejileri seç.")

    hepsi = list(kayitlar.keys())
    k1, k2 = st.columns(2)
    if k1.button("✅ Hepsini seç", use_container_width=True):
        st.session_state["sec_tara"] = hepsi
        st.rerun()
    if k2.button("✖️ Seçimi temizle", use_container_width=True):
        st.session_state["sec_tara"] = []
        st.rerun()

    secili = st.multiselect("Stratejiler", hepsi,
                            default=st.session_state.get("sec_tara", hepsi),
                            key="sec_tara", label_visibility="collapsed")

    if st.button("🔍  TARA", type="primary", use_container_width=True, disabled=not secili):
        bolumler, veri_saati, foto = [], None, {}
        ilerleme = st.progress(0.0, text="Taranıyor…")
        for i, ad in enumerate(secili, 1):
            ilerleme.progress(i / len(secili), text=f"Taranıyor: {ad}")
            try:
                sec, zaman, endeks, sektorler, mantik = _meta(kayitlar[ad])
                _, df = tara(sec, limit=100, zaman=zaman, endeks=endeks,
                             sektorler=sektorler, mantik=mantik)
                if veri_saati is None and df is not None and len(df):
                    veri_saati = veri_bilgisi(df).get("saat")
                satirlar = ([{"hisse": r.get("name", ""), "fiyat": float(r.get("close") or 0)}
                             for _, r in df.iterrows()] if df is not None else [])
            except Exception as e:
                st.warning(f"{ad}: {e}")
                satirlar = []
            bolumler.append({"ad": ad, "satirlar": satirlar})
            foto[ad] = satirlar
        ilerleme.empty()

        try:
            gecmis.kaydet(foto, veri_saati)
        except Exception:
            pass

        zaman_str = datetime.now(IST).strftime("%d.%m.%Y %H:%M")
        st.session_state["sonuc"] = {
            "excel": rapor.toplu_rapor_excel(bolumler, zaman_str, veri_saati),
            "ad": "tarama_" + datetime.now(IST).strftime("%d-%m-%Y_%H%M") + ".xlsx",
            "bolumler": bolumler,
        }

    sonuc = st.session_state.get("sonuc")
    if sonuc:
        st.success("Tarama tamam!")
        st.download_button("⬇️  EXCEL'İ İNDİR", sonuc["excel"], sonuc["ad"],
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           type="primary", use_container_width=True)
        for b in sonuc["bolumler"]:
            with st.expander(f"{b['ad']} — {len(b['satirlar'])} hisse"):
                st.write(", ".join(h["hisse"] for h in b["satirlar"]) or "—")

# -------------------------------------------------------------- PERFORMANS
else:
    st.markdown('<div class="baslik">📊 Performans Ölç</div>', unsafe_allow_html=True)

    gunler = gecmis.kayitli_gunler()
    if not gunler:
        st.warning("Henüz kayıtlı tarama yok. Önce birkaç gün tarama yapılmalı.")
        st.stop()

    st.caption("Hangi günün taraması ölçülsün? (o günün 18:20 taraması kullanılır)")
    bas = st.selectbox("Başlangıç günü (tarama günü)", gunler,
                       format_func=lambda t: datetime.strptime(t, "%Y-%m-%d").strftime("%d.%m.%Y"))
    bit = st.date_input("Bitiş günü (bu günün kapanışına göre ölçülür)",
                        value=datetime.now(IST).date(), format="DD.MM.YYYY")

    kayit = gecmis.gunun_kaydi(bas)
    mevcut = list((kayit or {}).get("stratejiler", {}).keys())
    secili = st.multiselect("Stratejiler", mevcut, default=mevcut)

    if st.button("📊  PERFORMANSI HESAPLA", type="primary",
                 use_container_width=True, disabled=not secili):
        with st.spinner("Geçmiş fiyatlar alınıyor…"):
            bilgi, bolumler, karne = performans.hesapla_aralik(
                bas, bit.strftime("%Y-%m-%d"), secili)
            gunler, matris = performans.gunluk_karne(
                bas, bit.strftime("%Y-%m-%d"), secili)
        if not bilgi:
            st.error("O güne ait tarama kaydı bulunamadı.")
        else:
            st.session_state["sonuc"] = {
                "excel": rapor_performans.grid_performans_excel(
                    bilgi, bolumler, karne, gunler, matris),
                "ad": f"performans_{bas}_{bit}.xlsx",
                "karne": karne, "bolumler": bolumler, "bilgi": bilgi,
                "gunler": gunler, "matris": matris,
            }

    sonuc = st.session_state.get("sonuc")
    if sonuc and "karne" in sonuc:
        b = sonuc["bilgi"]
        st.success(f"{b['tarama_zamani']} → {b['simdi']}")
        st.download_button("⬇️  EXCEL'İ İNDİR", sonuc["excel"], sonuc["ad"],
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           type="primary", use_container_width=True)
        if sonuc.get("matris"):
            import pandas as _pd
            from datetime import datetime as _dt
            g = sonuc["gunler"]
            tablo = {}
            for strateji, gunluk in sonuc["matris"].items():
                tablo[strateji] = {
                    _dt.strptime(x, "%Y-%m-%d").strftime("%d.%m"):
                        (round(gunluk.get(x), 2) if gunluk.get(x) is not None else None)
                    for x in g}
            df = _pd.DataFrame(tablo).T
            st.markdown("#### 📅 Gün gün karne (%)")
            st.dataframe(df.style.map(
                lambda v: "color:#1a7f37;font-weight:600" if isinstance(v, (int, float)) and v > 0
                else ("color:#b42318;font-weight:600" if isinstance(v, (int, float)) and v < 0 else "")),
                use_container_width=True)

        st.markdown("#### 🏆 Strateji karnesi")
        for k in sonuc["karne"]:
            o = k["ortalama"]
            st.write(f"**{k['strateji']}** — "
                     + (f"{o:+.2f}%" if o is not None else "—")
                     + f"  ({k['kazanan']}↑ / {k['kaybeden']}↓, {k['adet']} hisse)")
