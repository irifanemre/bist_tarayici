"""
FİYAT DEPOSU — günlük kapanışlar, TAMAMI TradingView'den.

Neden var: performans hesapları eskiden bitiş fiyatını yfinance'ten alıyordu,
tarama fiyatı ise TradingView'den geliyordu. İki kaynak BIST'te tutmuyor:
  • 18 hisse yfinance'te hiç yok (POLHO, KONYA, NETAS, PRKME, GRTHO, TSGYO…)
  • bedelsiz/split düzeltmesi farklı: SDTTR 265.25 ↔ 23.64 (-%91), ORGE -%80
  • bazı hisselerde veri donuyor: DUNYH tüm tarihlerde 109.10
Bu yüzden karnede günlük tavanı (±%10) aşan imkânsız değişimler çıkıyordu.

Her gün: fiyatlar/YYYY-MM-DD.json
  {"tarih": "2026-08-31", "zaman": "31.08.2026 18:21", "seans": "post_market",
   "fiyatlar": {"TURGG": 28.16, ...}}

Kural: BİR GÜNÜN FİYATI YOKSA UYDURULMAZ. Eski bir günün fiyatına kaymak
(yfinance yolunda 6 güne kadar oluyordu) sahte çok-günlük getiri üretir.
"""

import os
import glob
from datetime import datetime, timezone, timedelta

from depo_util import json_oku, json_yaz

KONUM = os.path.dirname(os.path.abspath(__file__))
KLASOR = os.path.join(KONUM, "fiyatlar")
IST = timezone(timedelta(hours=3))


def _yol(tarih: str) -> str:
    return os.path.join(KLASOR, f"{tarih}.json")


def tum_fiyatlar():
    """Tüm günlerin kapanışları: {tarih: {HISSE: fiyat}}"""
    out = {}
    for yol in sorted(glob.glob(os.path.join(KLASOR, "*.json"))):
        v = json_oku(yol, None)
        if v and v.get("tarih"):
            out[v["tarih"]] = {k.upper(): float(f) for k, f in (v.get("fiyatlar") or {}).items()}
    return out


def gunler() -> list:
    """Kapanış kaydı bulunan günler (YYYY-MM-DD), eskiden yeniye."""
    return sorted(tum_fiyatlar())


def gunun_fiyatlari(tarih: str) -> dict:
    """Sadece o güne ait kapanışlar. Kayıt yoksa boş sözlük."""
    v = json_oku(_yol(tarih), None)
    if not v:
        return {}
    return {k.upper(): float(f) for k, f in (v.get("fiyatlar") or {}).items()}


def kapanis(kodlar, tarih: str) -> dict:
    """Verilen GÜNÜN kapanışları. {HISSE: fiyat}

    Sadece o güne ait kayıt kullanılır — veri yoksa hisse sonuçta yer almaz.
    Böylece rapor uydurma yüzde yerine '—' gösterir."""
    m = gunun_fiyatlari(tarih)
    if not m:
        return {}
    istenen = {(k or "").upper() for k in kodlar if k}
    return {k: f for k, f in m.items() if k in istenen}


def sonraki_gun(tarih: str):
    """Depoda kayıtlı BİR SONRAKİ işlem günü (yoksa None)."""
    for g in gunler():
        if g > tarih:
            return g
    return None


# --------------------------------------------------------------- KAYIT
def _evren_fiyatlari():
    """Tüm BIST hisselerinin anlık fiyatı TradingView'den.
    Döner: (fiyatlar, seans)"""
    from tradingview_screener import Query, col, And

    # where2 çıplak koşul kabul etmiyor, And(...) ile sarmalanmalı (bkz. tarayici.py)
    _, df = (Query()
             .set_markets("turkey")
             .select("name", "close", "current_session")
             .where2(And(col("type") == "stock"))   # fonlar (OPX30, ZGOLD…) girmesin
             .limit(2000)
             .get_scanner_data())

    fiyatlar, seans = {}, ""
    for _, r in df.iterrows():
        try:
            fiyatlar[str(r["name"]).upper()] = float(r["close"])
        except (TypeError, ValueError):
            continue
        seans = str(r.get("current_session", "") or seans)
    return fiyatlar, seans


def gunluk_kaydet(veri_saati=None, zorla=False):
    """Bugünün kapanışlarını TradingView'den çekip kaydeder. Dosya yolunu döner.

    Günlük tarama 18:20'de (BIST 18:00'de kapanır) çalıştığı için değerler
    kapanıştır. Ama piyasa AÇILMADAN önce çalıştırılırsa TradingView hâlâ
    DÜNKÜ kapanışı verir; bunu bugünün kapanışı diye yazmak sahte bir
    '%0 değişim' günü uydurur. O yüzden seans başlamadıysa yazmayız."""
    os.makedirs(KLASOR, exist_ok=True)
    simdi = datetime.now(IST)
    fiyatlar, seans = _evren_fiyatlari()
    if not fiyatlar:
        raise RuntimeError("TradingView'den fiyat alınamadı")

    tarih = simdi.strftime("%Y-%m-%d")
    if seans == "out_of_session" and not zorla:
        print(f"  (kapanış yazılmadı: {tarih} seansı henüz başlamamış — "
              f"TradingView dünkü kapanışı veriyor)")
        return None
    dosya = _yol(tarih)
    json_yaz(dosya, {
        "tarih": tarih,
        "zaman": simdi.strftime("%d.%m.%Y %H:%M"),
        "veri_saati": veri_saati,
        "seans": seans,
        "kaynak": "tradingview",
        "fiyatlar": fiyatlar,
    })
    return dosya


def tohumla() -> dict:
    """Eski günleri taramalar/*.json içinden doldurur.

    Oradaki fiyatlar da TradingView'den geldiği için geçerli kapanışlardır;
    ancak kapsam sınırlıdır: sadece o gün BİR STRATEJİDE ÇIKAN hisseler vardır.
    Zaten kaydı olan günlere dokunmaz. Döner: {tarih: eklenen_hisse_sayisi}"""
    import gecmis

    os.makedirs(KLASOR, exist_ok=True)
    eklendi = {}
    gunluk = {}
    for yol in gecmis.tum_kayitlar():
        v = json_oku(yol, None)
        if not v or not v.get("tarih"):
            continue
        hedef = gunluk.setdefault(v["tarih"], {})
        for liste in (v.get("stratejiler") or {}).values():
            for h in liste:
                kod = (h.get("hisse") or "").upper()
                fiyat = h.get("fiyat")
                if kod and fiyat:
                    hedef[kod] = float(fiyat)

    for tarih, fiyatlar in sorted(gunluk.items()):
        if os.path.exists(_yol(tarih)) or not fiyatlar:
            continue
        json_yaz(_yol(tarih), {
            "tarih": tarih,
            "zaman": f"{tarih} (tarama kaydından)",
            "veri_saati": None,
            "seans": "",
            "kaynak": "tradingview (tarama kaydı — sadece o gün çıkan hisseler)",
            "fiyatlar": fiyatlar,
        })
        eklendi[tarih] = len(fiyatlar)
    return eklendi


if __name__ == "__main__":
    print("Eski günler tarama kayıtlarından dolduruluyor…")
    for t, n in sorted(tohumla().items()):
        print(f"  {t}: {n} hisse")
    print("\nBugünün kapanışları TradingView'den çekiliyor…")
    print("  →", gunluk_kaydet())
