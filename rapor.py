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


def _deg_hucre(ws, satir, sutun, deger):
    c = ws.cell(row=satir, column=sutun)
    if deger is not None and deger == deger:
        deger = float(deger)
        c.value = deger
        c.number_format = '+0.00"%";-0.00"%";0.00"%"'
        c.font = Font(color=(_YESIL if deger > 0 else (_KIRMIZI if deger < 0 else _KOYU)), bold=True)
    return c


def toplu_rapor_excel(bolumler, tarama_zamani, veri_saati=None) -> bytes:
    """
    Çok kombinli (bölüm bölüm) rapor.
    bolumler: [{"ad": "Kombin adı", "satirlar": [{hisse, fiyat, degisim, rating, sektor}]}]
    Her kombinasyon ayrı bir bölüm olarak yazılır.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Toplu Tarama"

    ws["A1"] = "BIST Toplu Tarama Raporu"
    ws["A1"].font = Font(bold=True, size=14, color=_KOYU)
    ws["A2"] = f"Tarama zamanı: {tarama_zamani}"
    ws["A2"].font = Font(bold=True, size=11, color=_KOYU)
    if veri_saati:
        ws["A3"] = f"Veri saati: {veri_saati}  (15 dk gecikmeli)"
        ws["A3"].font = Font(size=10, color=_GRI)

    r = 5
    for bolum in bolumler:
        satirlar = bolum.get("satirlar", [])
        # bölüm başlığı (mavi şerit, birleştirilmiş)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
        bh = ws.cell(row=r, column=1, value=f"▸ {bolum.get('ad', '')}   ·   {len(satirlar)} firma")
        bh.font = Font(bold=True, size=12, color=_BEYAZ)
        bh.fill = PatternFill("solid", fgColor=_BASLIK_BG)
        bh.alignment = Alignment(horizontal="left", vertical="center")
        r += 1

        if not satirlar:
            ws.cell(row=r, column=1, value="— eşleşme yok —").font = Font(italic=True, color=_GRI)
            r += 2
            continue

        # sütun başlıkları
        for j, b in enumerate(["Hisse", "Fiyat (₺)", "Değişim %", "Rating", "Sektör"], start=1):
            c = ws.cell(row=r, column=j, value=b)
            c.font = Font(bold=True, color=_KOYU)
            c.border = Border(bottom=_ince)
        r += 1

        for s in satirlar:
            ws.cell(row=r, column=1, value=s.get("hisse", "")).font = Font(bold=True, color=_KOYU)
            f = s.get("fiyat")
            fc = ws.cell(row=r, column=2)
            if f is not None and f == f:
                fc.value = round(float(f), 2)
                fc.number_format = "#,##0.00"
            _deg_hucre(ws, r, 3, s.get("degisim"))
            ws.cell(row=r, column=4, value=s.get("rating", "")).font = Font(color=_KOYU)
            ws.cell(row=r, column=5, value=s.get("sektor", "")).font = Font(color=_KOYU)
            r += 1
        r += 1  # bölümler arası boşluk

    for kol, gen in zip("ABCDE", (12, 12, 12, 16, 26)):
        ws.column_dimensions[kol].width = gen
    ws.freeze_panes = "A5"

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


if __name__ == "__main__":
    bolumler = [
        {"ad": "Momentum Kırılımı", "satirlar": [
            {"hisse": "ASELS", "fiyat": 357.25, "degisim": 1.8, "rating": "🟢 Güçlü Al", "sektor": "Elektronik"},
            {"hisse": "THYAO", "fiyat": 296.75, "degisim": 3.2, "rating": "🟢 Al", "sektor": "Ulaştırma"},
        ]},
        {"ad": "Dip Avı", "satirlar": [
            {"hisse": "GARAN", "fiyat": 130.40, "degisim": -0.85, "rating": "⚪ Nötr", "sektor": "Finans"},
        ]},
        {"ad": "Golden Cross", "satirlar": []},
    ]
    data = toplu_rapor_excel(bolumler, "11.06.2026 18:45", "11.06 18:09")
    with open("/tmp/ornek_toplu.xlsx", "wb") as f:
        f.write(data)
    print("ornek_toplu.xlsx yazildi:", len(data), "bayt |", len(bolumler), "bölüm")
