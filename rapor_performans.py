"""
Performans Excel'i: dün çıkan kağıtlar + bugünkü durumları, en iyiden kötüye.
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
_gri = Side(style="thin", color="FF808080")
_kenar = Border(left=_gri, right=_gri, top=_gri, bottom=_gri)


def _basliklar(ws, satir, adlar, genislikler=None):
    from openpyxl.utils import get_column_letter
    for j, ad in enumerate(adlar, start=1):
        c = ws.cell(row=satir, column=j, value=ad)
        c.font = Font(bold=True, color=_BEYAZ, size=10)
        c.fill = PatternFill("solid", fgColor=_BASLIK_BG)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = _kenar
        if genislikler:
            ws.column_dimensions[get_column_letter(j)].width = genislikler[j - 1]


def _yuzde(ws, satir, sutun, deger):
    c = ws.cell(row=satir, column=sutun)
    c.border = _kenar
    c.alignment = Alignment(horizontal="center")
    if deger is None:
        c.value = "—"
        c.font = Font(color=_GRI)
        return
    c.value = float(deger)
    c.number_format = '+0.00"%";-0.00"%";0.00"%"'
    c.font = Font(bold=True, color=(_YESIL if deger > 0 else (_KIRMIZI if deger < 0 else _KOYU)))


def performans_excel(bilgi, satirlar, karne) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Performans"

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)
    ws.cell(row=1, column=1,
            value=f"DÜN ÇIKAN KAĞITLAR — ERTESİ GÜN PERFORMANSI").font = Font(bold=True, size=13, color=_KOYU)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=6)
    ws.cell(row=2, column=1,
            value=f"Tarama: {bilgi['tarama_zamani']}   →   Şimdi: {bilgi['simdi']}"
            ).font = Font(size=10, color=_GRI)

    # --- sıralı liste ---
    bas = 4
    _basliklar(ws, bas, ["Sıra", "Hisse", "Tarama fiyatı", "Güncel fiyat",
                         "Değişim", "Çıktığı strateji(ler)"],
               [7, 11, 14, 14, 12, 46])

    r = bas + 1
    for i, s in enumerate(satirlar, start=1):
        ws.cell(row=r, column=1, value=i).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=1).border = _kenar
        h = ws.cell(row=r, column=2, value=s["hisse"])
        h.font = Font(bold=True, color=_KOYU)
        h.alignment = Alignment(horizontal="center")
        h.border = _kenar
        for kol, deg in ((3, s.get("eski")), (4, s.get("yeni"))):
            c = ws.cell(row=r, column=kol)
            c.border = _kenar
            c.alignment = Alignment(horizontal="center")
            if deg is not None:
                c.value = round(float(deg), 2)
                c.number_format = "#,##0.00"
            else:
                c.value = "—"
        _yuzde(ws, r, 5, s.get("degisim"))
        st = ws.cell(row=r, column=6, value=s.get("strateji", ""))
        st.font = Font(size=9, color=_GRI)
        st.border = _kenar
        r += 1

    # --- strateji karnesi ---
    r += 2
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.cell(row=r, column=1, value="STRATEJİ KARNESİ (ortalama getiriye göre)"
            ).font = Font(bold=True, size=12, color=_KOYU)
    r += 1
    _basliklar(ws, r, ["Sıra", "Strateji", "Kağıt", "Kazanan", "Kaybeden", "Ortalama"])
    r += 1
    for i, k in enumerate(karne, start=1):
        ws.cell(row=r, column=1, value=i).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=1).border = _kenar
        a = ws.cell(row=r, column=2, value=k["strateji"])
        a.font = Font(bold=True, color=_KOYU)
        a.border = _kenar
        for kol, val in ((3, k["adet"]), (4, k["kazanan"]), (5, k["kaybeden"])):
            c = ws.cell(row=r, column=kol, value=val)
            c.alignment = Alignment(horizontal="center")
            c.border = _kenar
        _yuzde(ws, r, 6, k.get("ortalama"))
        r += 1

    ws.freeze_panes = "A5"
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
