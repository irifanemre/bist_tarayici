"""
Tarama sonucunu Excel (.xlsx) kaydı olarak üretir.

Babanın iş akışı: gün sonunda tarar → ertesi gün açılışında takip eder.
Bu yüzden kayıtta net olarak: TARAMA TARİHİ+SAATİ ve her hissenin O ANKİ FİYATI.
Değişim yüzdesi yeşil (+) / kırmızı (−) renklenir.
"""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

_KOYU = "FF1F2328"
_GRI = "FF6E7681"
_YESIL = "FF1A7F37"
_KIRMIZI = "FFB42318"
_BASLIK_BG = "FF2F81F7"
_BEYAZ = "FFFFFFFF"
_ince = Side(style="thin", color="FFD0D7DE")


def tarama_excel(satirlar, tarama_zamani, veri_saati=None) -> bytes:
    """
    satirlar: [{hisse, fiyat(float|None), degisim(float|None), rating, sektor}]
    tarama_zamani: "11.06.2026 18:45" (taramanın yapıldığı tam an)
    veri_saati: opsiyonel "11.06 18:09" (TradingView veri saati)
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Tarama"

    ws["A1"] = "BIST Tarama Kaydı"
    ws["A1"].font = Font(bold=True, size=14, color=_KOYU)
    ws["A2"] = f"Tarama zamanı: {tarama_zamani}"
    ws["A2"].font = Font(bold=True, size=11, color=_KOYU)
    if veri_saati:
        ws["A3"] = f"Veri saati: {veri_saati}  (15 dk gecikmeli)"
        ws["A3"].font = Font(size=10, color=_GRI)

    bas = 5
    basliklar = ["Hisse", "Fiyat (₺)", "Değişim %", "Rating", "Sektör"]
    for j, b in enumerate(basliklar, start=1):
        c = ws.cell(row=bas, column=j, value=b)
        c.font = Font(bold=True, color=_BEYAZ)
        c.fill = PatternFill("solid", fgColor=_BASLIK_BG)
        c.alignment = Alignment(horizontal="center")
        c.border = Border(bottom=_ince)

    for i, s in enumerate(satirlar, start=bas + 1):
        ws.cell(row=i, column=1, value=s.get("hisse", "")).font = Font(bold=True, color=_KOYU)

        fc = ws.cell(row=i, column=2)
        fiyat = s.get("fiyat")
        if fiyat is not None and fiyat == fiyat:  # NaN değil
            fc.value = round(float(fiyat), 2)
            fc.number_format = "#,##0.00"

        dc = ws.cell(row=i, column=3)
        deg = s.get("degisim")
        if deg is not None and deg == deg:
            deg = float(deg)
            dc.value = deg
            dc.number_format = '+0.00"%";-0.00"%";0.00"%"'
            renk = _YESIL if deg > 0 else (_KIRMIZI if deg < 0 else _KOYU)
            dc.font = Font(color=renk, bold=True)

        ws.cell(row=i, column=4, value=s.get("rating", "")).font = Font(color=_KOYU)
        ws.cell(row=i, column=5, value=s.get("sektor", "")).font = Font(color=_KOYU)

    for kol, gen in zip("ABCDE", (10, 12, 12, 16, 26)):
        ws.column_dimensions[kol].width = gen
    ws.freeze_panes = "A6"  # başlık sabit kalsın

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


if __name__ == "__main__":
    ornek = [
        {"hisse": "ASELS", "fiyat": 357.25, "degisim": 1.8, "rating": "🟢 Güçlü Al", "sektor": "Elektronik"},
        {"hisse": "GARAN", "fiyat": 130.40, "degisim": -0.85, "rating": "⚪ Nötr", "sektor": "Finans"},
    ]
    data = tarama_excel(ornek, "11.06.2026 18:45", "11.06 18:09")
    with open("/tmp/ornek_tarama.xlsx", "wb") as f:
        f.write(data)
    print("ornek_tarama.xlsx yazildi:", len(data), "bayt")
