"""
Güvenli JSON okuma/yazma.

json_yaz(): geçici dosyaya yazıp os.replace ile değiştirir (atomik).
Böylece uygulama ve zamanlayıcı aynı anda yazsa ya da yazarken çökse bile
dosya bozulmaz — ya eski ya yeni hâli kalır, asla yarım.
"""

import os
import json
import tempfile


def json_oku(path: str, varsayilan):
    if not os.path.exists(path):
        return varsayilan
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return varsayilan


def json_yaz(path: str, data) -> None:
    klasor = os.path.dirname(path) or "."
    fd, gecici = tempfile.mkstemp(dir=klasor, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(gecici, path)  # atomik
    except Exception:
        try:
            os.remove(gecici)
        except OSError:
            pass
        raise
