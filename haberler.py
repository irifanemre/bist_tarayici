"""
Günlük finans haberleri — Türk finans sitelerinin RSS akışlarından.
Ağ hatasında sessizce boş döner (uygulamayı düşürmez).
"""

import xml.etree.ElementTree as ET
from datetime import datetime

import requests

FEEDS = [
    ("BloombergHT", "https://www.bloomberght.com/rss"),
    ("Dünya", "https://www.dunya.com/rss?dunya"),
    ("AA Ekonomi", "https://www.aa.com.tr/tr/rss/default?cat=ekonomi"),
]
_HDR = {"User-Agent": "Mozilla/5.0"}


def _parse_tarih(s):
    s = (s or "").strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%a, %d %b %Y %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def haberler(limit=10):
    """[{baslik, link, kaynak, tarih}] döner (tarihe göre yeni->eski)."""
    out, gorulen = [], set()
    for kaynak, url in FEEDS:
        try:
            r = requests.get(url, headers=_HDR, timeout=8)
            root = ET.fromstring(r.content)
            for it in root.findall(".//item")[:6]:
                baslik = (it.findtext("title") or "").strip()
                if not baslik or baslik in gorulen:
                    continue
                gorulen.add(baslik)
                out.append({
                    "baslik": baslik,
                    "link": (it.findtext("link") or "").strip(),
                    "kaynak": kaynak,
                    "tarih": _parse_tarih(it.findtext("pubDate")),
                })
        except Exception:
            continue

    out.sort(key=lambda h: h["tarih"].timestamp() if h["tarih"] else 0, reverse=True)
    return out[:limit]


if __name__ == "__main__":
    for h in haberler(8):
        saat = h["tarih"].strftime("%d.%m %H:%M") if h["tarih"] else "-"
        print(f"[{h['kaynak']:11s} {saat}] {h['baslik'][:70]}")
