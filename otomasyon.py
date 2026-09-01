"""
Otomatik tarama + Telegram bildirimi.

Kayıtlı kombinleri (kombinler.json) tarar, sonucu Telegram'a gönderir.
Zamanlanmış çalıştırmak için (örn. her sabah 09:45) cron / Görev Zamanlayıcı kullan:

    45 9 * * 1-5  cd ~/Desktop/bist_tarayici && /usr/bin/python3 otomasyon.py

Gerekli ortam değişkenleri (Telegram için):
    TELEGRAM_BOT_TOKEN  — @BotFather'dan alınan bot token'ı
    TELEGRAM_CHAT_ID    — mesajın gideceği sohbet/kullanıcı id'si

Test (göndermeden, ekrana bas):
    python3 otomasyon.py --dry-run
"""

import os
import sys

import time as _time

import requests

import kombin_store as ks
from indikatorler import ZAMAN_DILIMLERI, ENDEKSLER, SEKTORLER
from tarayici import tara, rating_etiket

_TR2EN = {v: k for k, v in SEKTORLER.items()}


def _meta(paket):
    """Kayıtlı paketi tara() argümanlarına çevirir (eski liste formatını da destekler)."""
    if isinstance(paket, list):
        return paket, "", None, None, "VE"
    secimler = paket.get("secimler", [])
    zaman = ZAMAN_DILIMLERI.get(paket.get("zaman", "Günlük"), "")
    endeks = ENDEKSLER.get(paket.get("endeks", "Tüm BIST"))
    sektor_tr = paket.get("sektorler", []) or []
    sektorler = [_TR2EN[s] for s in sektor_tr if s in _TR2EN] or None
    mantik = paket.get("mantik", "VE")
    return secimler, zaman, endeks, sektorler, mantik


def strateji_df(paket, limit=100):
    """Strateji tipine göre çalıştırır → (toplam, df).
    Normal stratejiler TradingView'den, 'ozel' olanlar yerel hesaplanır."""
    if isinstance(paket, dict) and paket.get("ozel"):
        import ozel
        return ozel.ozel_calistir(paket, limit)
    secimler, zaman, endeks, sektorler, mantik = _meta(paket)
    if not secimler:
        return 0, None
    return tara(secimler, limit=limit, zaman=zaman,
                endeks=endeks, sektorler=sektorler, mantik=mantik)


def tarama_veri(ad: str, paket, limit: int = 12):
    """(metin, [{hisse, fiyat}]) döndürür."""
    toplam, df = strateji_df(paket, limit)
    if toplam == 0 and df is None:
        return None, []
    if not toplam or df is None or len(df) == 0:
        return f"📊 *{ad}* — eşleşme yok.", []

    satirlar, kayitlar = [], []
    for _, r in df.iterrows():
        satirlar.append(
            f"• {r['name']}  {float(r['close']):g}  "
            f"({float(r['change']):+.1f}%)  [{rating_etiket(r.get('Recommend.All'))}]"
        )
        kayitlar.append({"hisse": str(r["name"]), "fiyat": float(r["close"])})
    basi = f"📊 *{ad}* — {toplam} eşleşme"
    basi += f" (ilk {len(df)})" if toplam > len(df) else ""
    metin = basi + ":\n" + "\n".join(satirlar)
    if toplam > len(df):
        metin += f"\n…ve {toplam - len(df)} tane daha"
    return metin, kayitlar


def tarama_metni(ad: str, paket, limit: int = 15):
    """Bir kombin için Telegram'a uygun özet metni döndürür (None = boş kombin)."""
    return tarama_veri(ad, paket, limit)[0]


def _parcala(metin, limit=3600):
    """Mesajı MANTIKLI yerlerden böler (strateji blokları arası).
    Böylece *kalın* işaretleri yarıda kalmaz, Telegram mesajı reddetmez."""
    if len(metin) <= limit:
        return [metin]
    parcalar, tampon = [], ""
    for blok in metin.split("\n\n"):
        # tek başına çok uzun blok → satır satır böl
        if len(blok) > limit:
            if tampon:
                parcalar.append(tampon); tampon = ""
            satir_tamponu = ""
            for satir in blok.split("\n"):
                if len(satir_tamponu) + len(satir) + 1 > limit:
                    parcalar.append(satir_tamponu); satir_tamponu = satir
                else:
                    satir_tamponu += ("\n" if satir_tamponu else "") + satir
            if satir_tamponu:
                tampon = satir_tamponu
            continue
        if len(tampon) + len(blok) + 2 > limit:
            parcalar.append(tampon); tampon = blok
        else:
            tampon += ("\n\n" if tampon else "") + blok
    if tampon:
        parcalar.append(tampon)
    return parcalar


def telegram_gonder(metin: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID ortam değişkenleri tanımlı değil.")
    # Birden çok alıcı: TELEGRAM_CHAT_ID="123,456" şeklinde virgülle ayrılabilir
    sonuc = []
    for cid in str(chat).replace(" ", "").split(","):
        if not cid:
            continue
        for parca in _parcala(metin):
            ok = False
            for deneme in range(4):
                try:
                    r = requests.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": cid, "text": parca, "parse_mode": "Markdown"},
                        timeout=25)
                    if not r.ok:   # biçim bozulduysa düz metin dene
                        r = requests.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={"chat_id": cid, "text": parca}, timeout=25)
                    if r.ok:
                        ok = True
                        break
                    # 429 = hız sınırı → Telegram'ın istediği kadar bekle
                    bekle = 3
                    try:
                        bekle = int(r.json().get("parameters", {}).get("retry_after", 3))
                    except Exception:
                        pass
                    _time.sleep(bekle + 1)
                except requests.RequestException:
                    _time.sleep(2 * (deneme + 1))
            sonuc.append({cid: ok})
            _time.sleep(0.7)   # hız sınırına takılmamak için mesajlar arası bekleme
    return sonuc


def calistir(gonder: bool = True):
    kayitlar = ks.tum_kombinler()
    if not kayitlar:
        print("Kayıtlı kombin yok — önce uygulamadan bir kombin kaydet.")
        return

    parcalar, foto = [], {}
    for ad, paket in kayitlar.items():
        try:
            metin, kayit_satirlar = tarama_veri(ad, paket)
            if metin:
                parcalar.append(metin)
            foto[ad] = kayit_satirlar
        except Exception as e:
            parcalar.append(f"📊 *{ad}* — tarama hatası: {e}")

    # Taramanın fotoğrafını sakla (ertesi gün performans karşılaştırması için)
    try:
        import gecmis
        gecmis.kaydet(foto)
    except Exception as e:
        print("(geçmiş kaydedilemedi:", e, ")")

    # Tüm BIST'in bugünkü kapanışı — performans hesapları bunu kullanır.
    # Sadece taramada çıkanları değil HERKESİ kaydeder, çünkü ertesi gün
    # karşılaştırılacak hisse o gün hiçbir stratejide çıkmamış olabilir.
    try:
        import fiyat_deposu
        fiyat_deposu.gunluk_kaydet()
    except Exception as e:
        print("(günlük kapanışlar kaydedilemedi:", e, ")")

    from datetime import datetime, timezone, timedelta
    ist = datetime.now(timezone(timedelta(hours=3)))  # İstanbul saati
    try:
        import piyasa as _p
        _borsa = _p.borsa_ozet_metni()
    except Exception:
        _borsa = ""
    baslik = (f"🔮 *YARIN İÇİN ÖNERİLER*\n"
              f"📅 {ist:%d.%m.%Y %H:%M} · {len(kayitlar)} strateji\n"
              + (f"🏛 {_borsa}\n" if _borsa else "")
              + "─" * 22)
    try:
        import analiz
        _guclu = analiz.guclu_sinyal_metni([{"ad": a, "satirlar": v} for a, v in foto.items()])
    except Exception:
        _guclu = ""
    # Tüm stratejilerin özeti — mesaj bölünse bile hepsi ilk parçada görünür
    ozet = ["📋 *ÖZET* (tüm stratejiler)"]
    for ad, lst in foto.items():
        n = len(lst)
        ozet.append(f"{'✅' if n else '▫️'} {ad}: *{n}*")
    _ozet = "\n".join(ozet)

    tam = baslik + "\n\n" + _ozet + "\n\n" + ((_guclu + "\n\n") if _guclu else "") \
        + ("\n\n".join(parcalar) if parcalar else "Taranacak kombin yok.")
    print(tam)

    if gonder:
        telegram_gonder(tam)   # bölme işini telegram_gonder yapıyor
        print("\n✅ Telegram'a gönderildi.")
    else:
        print("\n(dry-run: gönderilmedi)")


import json  # noqa: E402  (günlük gönderim kaydı için)

KONUM = os.path.dirname(os.path.abspath(__file__))
DURUM_DOSYA = os.path.join(KONUM, "gonderim.json")


def gunluk_kontrol(hedef_saat="18:20"):
    """Günde bir kez, hedef saatten sonra gönderim yapılmasını sağlar.
    GitHub zamanlamayı geciktirse bile gün içindeki ilk uygun çalışmada gönderir.
    Döner: (gonderilsin_mi, aciklama)"""
    from datetime import datetime, timezone, timedelta
    ist = datetime.now(timezone(timedelta(hours=3)))
    bugun = ist.strftime("%Y-%m-%d")

    if ist.weekday() >= 5:
        return False, "hafta sonu"

    ss, dd = (int(x) for x in hedef_saat.split(":"))
    if (ist.hour, ist.minute) < (ss, dd):
        return False, f"vakit gelmedi ({ist:%H:%M} < {hedef_saat})"

    try:
        with open(DURUM_DOSYA, encoding="utf-8") as f:
            if json.load(f).get("son_gonderim") == bugun:
                return False, "bugün zaten gönderildi"
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    return True, f"gönderilecek ({ist:%H:%M})"


def gunluk_isaretle():
    from datetime import datetime, timezone, timedelta
    ist = datetime.now(timezone(timedelta(hours=3)))
    try:
        with open(DURUM_DOSYA, "w", encoding="utf-8") as f:
            json.dump({"son_gonderim": ist.strftime("%Y-%m-%d"),
                       "saat": ist.strftime("%H:%M")}, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def performans_metni(en_fazla=None):
    """Dünkü taramadaki kağıtların bugünkü durumu — strateji strateji, TAMAMI."""
    import performans
    bilgi, satirlar, karne, bolumler = performans.hesapla()
    if not bilgi:
        return "Karşılaştırılacak önceki tarama kaydı yok."

    parcalar = ["📊 *DÜNKÜ TARAMA KARNESİ*\n"
                f"🕐 Tarama: {bilgi['tarama_zamani']} → Şimdi: {bilgi['simdi']}\n"
                + "─" * 22 + (("\n" + bilgi["uyari"]) if bilgi.get("uyari") else "")]

    for b in bolumler:
        if not b["satirlar"]:
            parcalar.append(f"📈 *{b['ad']}* — kağıt yoktu")
            continue
        satir = [f"📈 *{b['ad']}*"]
        for s in b["satirlar"]:
            fiyat = f"{s['yeni']:g}" if s.get("yeni") else "—"
            if s.get("supheli"):
                # Tavanı aşan fark = bedelsiz/split düzeltmesi, getiri diye gösterme
                satir.append(f"⚠️ {s['hisse']}  {fiyat}  (veri şüpheli)")
                continue
            d = f"{s['degisim']:+.2f}%" if s["degisim"] is not None else "—"
            ok = "🟢" if (s["degisim"] or 0) > 0 else ("🔴" if (s["degisim"] or 0) < 0 else "⚪")
            satir.append(f"{ok} {s['hisse']}  {fiyat}  ({d})")
        parcalar.append("\n".join(satir))

    kn = ["🏆 *STRATEJİ KARNESİ*"]
    _e = next((k.get("endeks") for k in karne if k.get("endeks") is not None), None)
    if _e is not None:
        kn.append(f"_(BIST 100 aynı dönemde: {_e:+.2f}%)_")
    for k in karne:
        o = f"{k['ortalama']:+.2f}%" if k["ortalama"] is not None else "—"
        f = f"  → endekse göre *{k['fark']:+.2f}%*" if k.get("fark") is not None else ""
        kn.append(f"• {k['strateji']}: {o}  ({k['kazanan']}↑/{k['kaybeden']}↓){f}")
    parcalar.append("\n".join(kn))

    return "\n\n".join(parcalar)


if __name__ == "__main__":
    if "--gunluk" in sys.argv:
        tamam, neden = gunluk_kontrol()
        print(f"günlük kontrol: {neden}")
        if tamam:
            # ÖNCE dünkü taramanın karnesi, SONRA bugünün önerileri
            try:
                telegram_gonder(performans_metni())
                print("✅ dünkü karne gönderildi.")
            except Exception as e:
                print("(karne gönderilemedi:", e, ")")
            calistir(gonder=True)
            gunluk_isaretle()
    else:
        calistir(gonder="--dry-run" not in sys.argv)
