"""
Çekirdek mantık testleri (ağ gerektirmez).
Çalıştır:  cd ~/Desktop/bist_tarayici && python3 -m pytest -q
"""

from datetime import datetime, timedelta

import depo_util as du
import kombin_store as ks
import zamanlama_store as zs
import zamanlayici as zl
import otomasyon
from indikatorler import (
    KATALOG, HAZIR_SINYALLER, STRATEJILER, ACIKLAMALAR,
    ZAMAN_DILIMLERI, ENDEKSLER, kosul_uret,
)
from tarayici import rating_etiket, rating_rozet


# ----------------------------- depo_util ----------------------------------
def test_depo_util_roundtrip(tmp_path):
    p = str(tmp_path / "d.json")
    du.json_yaz(p, {"a": 1, "ç": "ş"})
    assert du.json_oku(p, None) == {"a": 1, "ç": "ş"}


def test_depo_util_bozuk_dosya(tmp_path):
    p = tmp_path / "bozuk.json"
    p.write_text("{ bu gecersiz json", encoding="utf-8")
    assert du.json_oku(str(p), []) == []  # varsayılana düşer, patlamaz


def test_depo_util_tmp_birakmaz(tmp_path):
    p = str(tmp_path / "x.json")
    du.json_yaz(p, [1, 2, 3])
    kalan = [f for f in tmp_path.iterdir() if f.suffix == ".tmp"]
    assert kalan == []  # atomik yazımdan geçici dosya kalmamalı


# ----------------------------- depolar ------------------------------------
def test_kombin_store(tmp_path, monkeypatch):
    monkeypatch.setattr(ks, "DOSYA", str(tmp_path / "k.json"))
    ks.kaydet("A", {"secimler": [], "zaman": "Günlük"})
    assert "A" in ks.tum_kombinler()
    ks.sil("A")
    assert "A" not in ks.tum_kombinler()


def test_zamanlama_store(tmp_path, monkeypatch):
    monkeypatch.setattr(zs, "DOSYA", str(tmp_path / "z.json"))
    zid = zs.ekle({"kombin": "A", "tip": "rutin", "gunler": "hergun", "saat": "09:00"})
    assert any(z["id"] == zid for z in zs.tum())
    zs.guncelle(zid, son_calisma="2026-01-01")
    assert [z for z in zs.tum() if z["id"] == zid][0]["son_calisma"] == "2026-01-01"
    zs.sil(zid)
    assert not zs.tum()


# --------------------------- _fire_mi mantığı -----------------------------
def _gun(hedef_wd, saat="09:00"):
    d = datetime(2026, 6, 1, int(saat[:2]), int(saat[3:]))
    while d.weekday() != hedef_wd:
        d += timedelta(days=1)
    return d


def test_fire_saat_uyusmazligi():
    z = {"saat": "09:00", "tip": "rutin", "gunler": "hergun"}
    assert zl._fire_mi(z, _gun(0, "10:00")) is False


def test_fire_son_calisma_guard():
    pzt = _gun(0)
    z = {"saat": "09:00", "tip": "rutin", "gunler": "hergun",
         "son_calisma": pzt.strftime("%Y-%m-%d")}
    assert zl._fire_mi(z, pzt) is False  # bugün zaten gönderilmiş


def test_fire_hergun():
    z = {"saat": "09:00", "tip": "rutin", "gunler": "hergun"}
    assert zl._fire_mi(z, _gun(5)) is True  # cumartesi bile


def test_fire_haftaici():
    z = {"saat": "09:00", "tip": "rutin", "gunler": "haftaici"}
    assert zl._fire_mi(z, _gun(4)) is True   # cuma
    assert zl._fire_mi(z, _gun(5)) is False  # cumartesi


def test_fire_haftalik():
    z = {"saat": "09:00", "tip": "rutin", "gunler": "haftalik", "hafta_gunu": 2}
    assert zl._fire_mi(z, _gun(2)) is True   # çarşamba
    assert zl._fire_mi(z, _gun(3)) is False  # perşembe


def test_fire_tek_seferlik():
    gun = _gun(0)
    z = {"saat": "09:00", "tip": "tek", "tarih": gun.strftime("%Y-%m-%d")}
    assert zl._fire_mi(z, gun) is True
    assert zl._fire_mi(z, gun + timedelta(days=1)) is False


# --------------------------- otomasyon._meta ------------------------------
def test_meta_paket():
    paket = {"secimler": [{"tip": "hazir", "anahtar": "macd_al"}],
             "zaman": "4 Saatlik", "endeks": "BIST 100", "mantik": "VEYA",
             "sektorler": ["Finans"]}
    sec, zaman, endeks, sektorler, mantik = otomasyon._meta(paket)
    assert zaman == "|240"
    assert endeks == "SYML:BIST;XU100"
    assert sektorler == ["Finance"]   # TR -> EN çevrildi
    assert mantik == "VEYA"


def test_meta_eski_liste_formati():
    sec, zaman, endeks, sektorler, mantik = otomasyon._meta([{"tip": "hazir", "anahtar": "macd_al"}])
    assert zaman == "" and endeks is None and mantik == "VE"


# --------------------------- katalog bütünlüğü ----------------------------
def test_katalog_kosul_kurulur():
    """Her KATALOG girdisi hatasız koşula çevrilebilmeli (günlük + 4 saatlik)."""
    for anahtar, t in KATALOG.items():
        op = t["op"]
        secim = {"tip": "metrik", "anahtar": anahtar, "op": op}
        if op in ("arada", "arada değil"):
            secim["deger"] = t.get("deger", 0)
            secim["deger2"] = secim["deger"] + 1
        elif t["tur"] == "seviye":
            secim["hedef_turu"] = "alan"
            secim["hedef_alan"] = t.get("hedef_alan", "close")
        else:
            secim["hedef_turu"] = "deger"
            secim["deger"] = t.get("deger", 0)
        kosul_uret(secim)
        kosul_uret(secim, "|240")


def test_hazir_sinyaller_kurulur():
    for anahtar in HAZIR_SINYALLER:
        kosul_uret({"tip": "hazir", "anahtar": anahtar})
        kosul_uret({"tip": "hazir", "anahtar": anahtar}, "|1W")


def test_stratejiler_gecerli():
    for ad, s in STRATEJILER.items():
        assert s["zaman"] in ZAMAN_DILIMLERI
        assert s["endeks"] in ENDEKSLER
        assert s["mantik"] in ("VE", "VEYA")
        for secim in s["secimler"]:
            if secim["tip"] == "metrik":
                assert secim["anahtar"] in KATALOG, f"{ad}: {secim['anahtar']}"
            else:
                assert secim["anahtar"] in HAZIR_SINYALLER
            kosul_uret(secim)


def test_aciklama_kapsami():
    """Her metrik için bir Türkçe açıklama olmalı."""
    for anahtar in KATALOG:
        assert anahtar in ACIKLAMALAR, f"açıklama eksik: {anahtar}"


# ----------------------------- rating -------------------------------------
def test_rating_etiket():
    assert rating_etiket(0.7) == "Güçlü Al"
    assert rating_etiket(0.2) == "Al"
    assert rating_etiket(0.0) == "Nötr"
    assert rating_etiket(-0.3) == "Sat"
    assert rating_etiket(-0.8) == "Güçlü Sat"
    assert rating_etiket(None) == "—"


def test_rating_rozet_ikon():
    assert "🟢" in rating_rozet(0.7)
    assert "🔴" in rating_rozet(-0.8)
