import math
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle, Wedge
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, KeepTogether, Flowable, NextPageTemplate,
                                CondPageBreak, Preformatted)
from reportlab.platypus.tableofcontents import TableOfContents

OUT = "System_Design_Specification_Live_Updates_v2026_Editorial.pdf"

# ------------------------------------------------------------------ fonts
import os

FD_LINUX = "/usr/share/fonts/truetype/crosextra/"
DJ_LINUX = "/usr/share/fonts/truetype/dejavu/"
WIN_FONTS = "C:/Windows/Fonts/"

if os.path.exists(os.path.join(FD_LINUX, "Carlito-Regular.ttf")):
    pdfmetrics.registerFont(TTFont("Body", FD_LINUX + "Carlito-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Body-Bold", FD_LINUX + "Carlito-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Body-Italic", FD_LINUX + "Carlito-Italic.ttf"))
    pdfmetrics.registerFont(TTFont("Body-BoldItalic", FD_LINUX + "Carlito-BoldItalic.ttf"))
elif os.path.exists(os.path.join(WIN_FONTS, "calibri.ttf")):
    pdfmetrics.registerFont(TTFont("Body", WIN_FONTS + "calibri.ttf"))
    pdfmetrics.registerFont(TTFont("Body-Bold", WIN_FONTS + "calibrib.ttf"))
    pdfmetrics.registerFont(TTFont("Body-Italic", WIN_FONTS + "calibrii.ttf"))
    pdfmetrics.registerFont(TTFont("Body-BoldItalic", WIN_FONTS + "calibriz.ttf"))
elif os.path.exists(os.path.join(WIN_FONTS, "arial.ttf")):
    pdfmetrics.registerFont(TTFont("Body", WIN_FONTS + "arial.ttf"))
    pdfmetrics.registerFont(TTFont("Body-Bold", WIN_FONTS + "arialbd.ttf"))
    pdfmetrics.registerFont(TTFont("Body-Italic", WIN_FONTS + "ariali.ttf"))
    pdfmetrics.registerFont(TTFont("Body-BoldItalic", WIN_FONTS + "arialbi.ttf"))

pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-BoldItalic")

if os.path.exists(os.path.join(DJ_LINUX, "DejaVuSansMono.ttf")):
    pdfmetrics.registerFont(TTFont("Mono", DJ_LINUX + "DejaVuSansMono.ttf"))
    pdfmetrics.registerFont(TTFont("Mono-Bold", DJ_LINUX + "DejaVuSansMono-Bold.ttf"))
elif os.path.exists(os.path.join(WIN_FONTS, "consola.ttf")):
    pdfmetrics.registerFont(TTFont("Mono", WIN_FONTS + "consola.ttf"))
    pdfmetrics.registerFont(TTFont("Mono-Bold", WIN_FONTS + "consolab.ttf"))
elif os.path.exists(os.path.join(WIN_FONTS, "cour.ttf")):
    pdfmetrics.registerFont(TTFont("Mono", WIN_FONTS + "cour.ttf"))
    pdfmetrics.registerFont(TTFont("Mono-Bold", WIN_FONTS + "courbd.ttf"))

pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-Bold", italic="Mono", boldItalic="Mono-Bold")


# ------------------------------------------------------------------ palette (2026 Editorial Forecast)
NAVY = HexColor("#111111")     # Ultra-high contrast near-black
INK = HexColor("#1A1A1A")      
SLATE = HexColor("#404040")
MUTED = HexColor("#737373")
LINE = HexColor("#D4D4D4")
BG = HexColor("#F7F7F5")       # Gallery off-white matte background
TEAL = HexColor("#4F46E5")     # Electric Indigo gradient stop
BLUE = HexColor("#3B82F6")
GREEN = HexColor("#10B981")    # Cyber Emerald
AMBER = HexColor("#F59E0B")
MAGENTA = HexColor("#EC4899")  # Fuchsia / Rose
RED = HexColor("#F43F5E")
VIOLET = HexColor("#8B5CF6")

def tint(c, f=0.92):
    return Color(c.red + (1 - c.red) * f, c.green + (1 - c.green) * f, c.blue + (1 - c.blue) * f)

def hexs(c):
    return "#%02X%02X%02X" % (int(c.red * 255), int(c.green * 255), int(c.blue * 255))

W, H = A4
LM = RM = 50
TM, BM = 74, 60
CW = W - LM - RM  

# ------------------------------------------------------------------ styles
def S(name, **kw):
    base = dict(fontName="Body", fontSize=10, leading=14.8, textColor=SLATE)
    base.update(kw)
    return ParagraphStyle(name, **base)

st_body = S("Body2", spaceAfter=6)
st_lede = S("Lede", fontSize=12, leading=18, textColor=INK, spaceAfter=8)
st_h2 = S("H2", fontName="Body-Bold", fontSize=14, leading=18, textColor=NAVY, spaceBefore=14, spaceAfter=6, keepWithNext=1)
st_h1u = S("H1U", fontName="Body-Bold", fontSize=28, leading=32, textColor=NAVY, spaceAfter=4)
st_h3 = S("H3", fontName="Body-Bold", fontSize=10.5, leading=14, textColor=INK, spaceBefore=6, spaceAfter=3, keepWithNext=1)
st_label = S("Label", fontName="Body-Bold", fontSize=8, leading=11, textColor=TEAL, charSpace=1.1)
st_caption = S("Caption", fontName="Body-Italic", fontSize=8.5, leading=11.5, textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=10)
st_small = S("Small", fontSize=8.5, leading=11.5, textColor=MUTED)
st_cell = S("Cell", fontSize=8.8, leading=12, textColor=SLATE)
st_cellb = S("CellB", fontName="Body-Bold", fontSize=8.8, leading=12, textColor=INK)
st_cellc = S("CellC", fontSize=8.8, leading=12, alignment=TA_CENTER)
st_th = S("TH", fontName="Body-Bold", fontSize=8, leading=10.5, textColor=NAVY, charSpace=0.6)
st_thc = S("THC", fontName="Body-Bold", fontSize=8, leading=10.5, textColor=NAVY, charSpace=0.6, alignment=TA_CENTER)
st_bullet = S("Bullet", leftIndent=14, bulletIndent=2, bulletFontName="Body-Bold", bulletColor=TEAL, spaceAfter=3.5)
st_ct = S("CalloutT", fontName="Body-Bold", fontSize=9.5, leading=12.5, spaceAfter=2)
st_cb = S("CalloutB", fontSize=9.2, leading=13.2, textColor=SLATE)
st_cardT = S("CardT", fontName="Body-Bold", fontSize=11, leading=14, textColor=NAVY, spaceAfter=3)
st_cardB = S("CardB", fontSize=9, leading=12.8)
st_big = S("Big", fontName="Body-Bold", fontSize=26, leading=28, textColor=NAVY)
st_mono = S("MonoBlk", fontName="Mono", fontSize=7.6, leading=10.4, textColor=HexColor("#E5E7EB"))
st_toc0 = S("TOC0", fontName="Body-Bold", fontSize=11, leading=15, textColor=NAVY, spaceBefore=7, spaceAfter=1, rightIndent=26)
st_toc1 = S("TOC1", fontSize=9.5, leading=13, textColor=SLATE, leftIndent=16, rightIndent=26)

def P(t, st=st_body):
    return Paragraph(t, st)

def bullets(items, st=st_bullet):
    return [Paragraph(i, st, bulletText="•") for i in items]

def chip(text, color):
    return f'<font name="Body-Bold" size="7.5" color="#FFFFFF" backColor="{hexs(color)}">&nbsp;{text}&nbsp;</font>'

# ------------------------------------------------------------------ building blocks
def data_table(rows, widths, zebra=True, center_cols=(), first_col_bold=False, extra=None):
    out = []
    for ri, row in enumerate(rows):
        r = []
        for ci, cell in enumerate(row):
            if isinstance(cell, str):
                if ri == 0:
                    r.append(Paragraph(cell.upper(), st_thc if ci in center_cols else st_th))
                else:
                    st = st_cellc if ci in center_cols else (st_cellb if (first_col_bold and ci == 0) else st_cell)
                    r.append(Paragraph(cell, st))
            else:
                r.append(cell)
        out.append(r)
    t = Table(out, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), tint(LINE, 0.5)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
    ]
    if zebra:
        for i in range(2, len(out), 2):
            style.append(("BACKGROUND", (0, i), (-1, i), white))
        for i in range(1, len(out), 2):
            style.append(("BACKGROUND", (0, i), (-1, i), BG))
    if extra:
        style += extra
    t.setStyle(TableStyle(style))
    return t

def callout(title, body, kind="info"):
    col = {"info": TEAL, "warn": AMBER, "ok": GREEN, "bad": RED, "note": BLUE}[kind]
    inner = [Paragraph(f'<font color="{hexs(col)}">{title.upper()}</font>', st_ct), Paragraph(body, st_cb)]
    t = Table([[inner]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), white),
        ("LINEBEFORE", (0, 0), (0, -1), 3.2, col),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t

def cards(items, widths=None, gap=12):
    n = len(items)
    w = (CW - gap * (n - 1)) / n
    cells, colw, style = [], [], [("VALIGN", (0, 0), (-1, -1), "TOP")]
    for i, (col, title, body) in enumerate(items):
        ci = i * 2
        cells.append([Paragraph(title.upper(), st_cardT), Paragraph(body, st_cardB)])
        colw.append(w)
        style += [
            ("BACKGROUND", (ci, 0), (ci, 0), white),
            ("BOX", (ci, 0), (ci, 0), 0.5, LINE),
            ("LINEABOVE", (ci, 0), (ci, 0), 3, col),
            ("LEFTPADDING", (ci, 0), (ci, 0), 14), ("RIGHTPADDING", (ci, 0), (ci, 0), 14),
            ("TOPPADDING", (ci, 0), (ci, 0), 12), ("BOTTOMPADDING", (ci, 0), (ci, 0), 14),
        ]
        if i < n - 1:
            cells.append("")
            colw.append(gap)
    t = Table([cells], colWidths=colw)
    t.setStyle(TableStyle(style))
    return t

def kpi_strip(items):
    n = len(items)
    w = CW / n
    row_v = [Paragraph(f'<font color="{hexs(c)}">{v}</font>', ParagraphStyle("kv", parent=st_big, alignment=TA_CENTER)) for v, l, c in items]
    row_l = [Paragraph(l, ParagraphStyle("kl", parent=st_small, alignment=TA_CENTER, textColor=SLATE)) for v, l, c in items]
    t = Table([row_v, row_l], colWidths=[w] * n)
    style = [("BACKGROUND", (0, 0), (-1, -1), white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("BOX", (0, 0), (-1, -1), 0.5, LINE),
             ("TOPPADDING", (0, 0), (-1, 0), 16), ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
             ("TOPPADDING", (0, 1), (-1, 1), 4), ("BOTTOMPADDING", (0, 1), (-1, 1), 16)]
    for i in range(1, n):
        style.append(("LINEBEFORE", (i, 0), (i, -1), 0.5, LINE))
    t.setStyle(TableStyle(style))
    return t

def code_block(text):
    pre = Preformatted(text.strip("\n"), st_mono)
    t = Table([[pre]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LINEBEFORE", (0, 0), (0, -1), 3.2, TEAL),
    ]))
    return t

class SectionOpener(Flowable):
    def __init__(self, num, title):
        super().__init__()
        self.num, self.title = num, title
        self.key = f"sec{num}"
        self.lines = simpleSplit(title, "Body-Bold", 24, 370)
        self.height = 50 + 28 * len(self.lines)
        self.width = CW

    def wrap(self, aw, ah):
        return CW, self.height

    def draw(self):
        c = self.canv
        c.bookmarkPage(self.key)
        c.addOutlineEntry(f"{self.num}. {self.title}", self.key, 0, 0)
        c.saveState()
        
        # Big architectural number watermark
        c.setFillColor(LINE)
        c.setFont("Body-Bold", 100)
        c.drawRightString(CW + 2, 0, f"{self.num:02d}")
        
        top = self.height
        
        # Tech badge
        c.setStrokeColor(TEAL)
        c.setLineWidth(1)
        c.roundRect(0, top - 18, 90, 14, 7, fill=0, stroke=1)
        c.setFont("Body-Bold", 7.5)
        c.setFillColor(TEAL)
        c.drawString(10, top - 14.5, f"SECTION // {self.num:02d}")
        
        c.setFillColor(NAVY)
        c.setFont("Body-Bold", 24)
        y = top - 46
        for ln in self.lines:
            c.drawString(0, y, ln.upper())
            y -= 28
            
        c.setFillColor(TEAL)
        c.rect(0, 2, 48, 3, fill=1, stroke=0)
        c.setFillColor(LINE)
        c.rect(48, 3.2, CW - 48, 0.8, fill=1, stroke=0)
        c.restoreState()

# ------------------------------------------------------------------ drawing helpers
def dtext(d, x, y, s, size=8, color=SLATE, font="Body", anchor="start"):
    d.add(String(x, y, s, fontName=font, fontSize=size, fillColor=color, textAnchor=anchor))

def dbox(d, x, y, w, h, title, lines=(), color=BLUE, num=None, chip_text=None, tsize=8.5):
    # Cyber-UI wireframe style
    d.add(Rect(x+3, y-3, w, h, rx=4, ry=4, fillColor=None, strokeColor=LINE, strokeWidth=1)) 
    d.add(Rect(x, y, w, h, rx=4, ry=4, fillColor=white, strokeColor=color, strokeWidth=1.5))
    
    ty = y + h - 16
    dtext(d, x + w / 2, ty, title.upper(), tsize, NAVY, "Body-Bold", "middle")
    
    ly = ty - 13
    for ln in lines:
        dtext(d, x + w / 2, ly, ln, 7.8, SLATE, "Body", "middle")
        ly -= 10.5
        
    if chip_text:
        d.add(Rect(x + 12, y + 8, w - 24, 14, rx=3, ry=3, fillColor=tint(color, 0.88), strokeColor=color, strokeWidth=0.5))
        dtext(d, x + w / 2, y + 11.5, chip_text.upper(), 6.8, color, "Body-Bold", "middle")
        
    if num is not None:
        dtext(d, x + 6, y + h - 11, f"{num:02d}", 7.5, color, "Body-Bold", "start")

def darrow(d, x1, y1, x2, y2, color=MUTED, width=1.2, head=6, both=False, dashed=False):
    ang = math.atan2(y2 - y1, x2 - x1)
    sx, sy = x1, y1
    ex, ey = x2, y2
    ex2, ey2 = x2 - head * math.cos(ang) * 0.9, y2 - head * math.sin(ang) * 0.9
    if both:
        sx, sy = x1 + head * math.cos(ang) * 0.9, y1 + head * math.sin(ang) * 0.9
    ln = Line(sx, sy, ex2, ey2, strokeColor=color, strokeWidth=width)
    if dashed:
        ln.strokeDashArray = [3, 2.5]
    d.add(ln)

    def headpoly(px, py, a):
        pts = [px, py,
               px - head * math.cos(a - 0.45), py - head * math.sin(a - 0.45),
               px - head * math.cos(a + 0.45), py - head * math.sin(a + 0.45)]
        d.add(Polygon(pts, fillColor=color, strokeColor=color, strokeWidth=0.5))

    headpoly(ex, ey, ang)
    if both:
        headpoly(x1, y1, ang + math.pi)

def dpoly_line(d, pts, color=MUTED, width=1.2, dashed=False):
    for (a, b), (c, e) in zip(pts[:-1], pts[1:]):
        ln = Line(a, b, c, e, strokeColor=color, strokeWidth=width)
        if dashed:
            ln.strokeDashArray = [3, 2.5]
        d.add(ln)

# ------------------------------------------------------------------ figures
def fig_overview():
    d = Drawing(CW, 262)
    w, h = 119, 72
    xs = [0, 188, 376]
    ya, yb = 172, 40
    dbox(d, xs[0], ya, w, h, "01.A / CLIENT UI", ["React Dashboard", "WebSocket / SSE"], BLUE, 1)
    dbox(d, xs[1], ya, w, h, "01.B / GATEWAY", ["API & WebSocket"], TEAL, 2, chip_text="Outbox Publisher")
    dbox(d, xs[2], ya, w, h, "02.A / RELATIONAL", ["WAL & Outbox Engine", "System of record"], GREEN, 3)
    dbox(d, xs[0], yb, w, h, "02.D / EVENT BUS", ["Telemetry & change", "broadcast bus"], RED, 6)
    dbox(d, xs[1], yb, w, h, "04.B / CLASSIFIER", ["DeBERTa-v3 cross-encoder", "Claim splitter &", "abstention gate"], MAGENTA, 5)
    dbox(d, xs[2], yb, w, h, "02.C / VECTOR GRAPH", ["Dense chunks & hashes", "Collection: civic_records"], AMBER, 4)
    ymid = ya + h / 2
    darrow(d, w, ymid, xs[1], ymid, MUTED, both=True)
    dtext(d, (w + xs[1]) / 2, ymid + 6, "WebSocket / SSE", 7.2, MUTED, "Body-Italic", "middle")
    darrow(d, xs[1] + w, ymid, xs[2], ymid, GREEN)
    dtext(d, (xs[1] + w + xs[2]) / 2, ymid + 6, "write + outbox", 7.2, MUTED, "Body-Italic", "middle")
    darrow(d, xs[2] + w / 2, ya, xs[2] + w / 2, yb + h, AMBER)
    dtext(d, xs[2] + w / 2 + 6, (ya + yb + h) / 2 - 2, "CDC sync", 7.2, MUTED, "Body-Italic")
    ylow = yb + h / 2
    darrow(d, xs[2], ylow, xs[1] + w, ylow, AMBER)
    dtext(d, (xs[2] + xs[1] + w) / 2, ylow + 6, "evidence chunks", 7.2, MUTED, "Body-Italic", "middle")
    darrow(d, xs[1] + w / 2, yb + h, xs[1] + w / 2, ya, MAGENTA)
    dtext(d, xs[1] + w / 2 + 6, (ya + yb + h) / 2 - 2, "verified answer", 7.2, MUTED, "Body-Italic")
    darrow(d, xs[1], ylow, w, ylow, RED)
    dtext(d, (xs[1] + w) / 2, ylow + 6, "telemetry", 7.2, MUTED, "Body-Italic", "middle")
    darrow(d, w / 2, yb + h, w / 2, ya, RED)
    dtext(d, w / 2 + 6, (ya + yb + h) / 2 - 2, "live counters", 7.2, MUTED, "Body-Italic")
    darrow(d, xs[1] + w - 14, ya, xs[2] + 12, yb + h, TEAL, 1.2, dashed=True)
    dtext(d, 358, 150, "retrieval", 7.2, TEAL, "Body-Italic", "middle")
    return d

def fig_outbox():
    d = Drawing(CW, 205)
    w, h = 140, 66
    xs = [0, 177.5, 355]
    y1, y2 = 128, 16
    dbox(d, xs[0], y1, w, h, "01 / STAFF ACTION", ["Status & department triage"], BLUE, 1)
    dbox(d, xs[1], y1, w, h, "02 / TRANSACTION", ["1. UPDATE complaints", "2. INSERT outbox_events"], GREEN, 2)
    dbox(d, xs[2], y1, w, h, "03 / CDC WORKER", ["Polls WAL / outbox"], TEAL, 3)
    dbox(d, xs[0], y2, w, h, "04 / EMBEDDING", ["Dense vector for the", "new record state"], VIOLET, 4)
    dbox(d, xs[1], y2, w, h, "05 / VECTOR DB", ["Upsert point", "{id, vector, payload}"], AMBER, 5)
    dbox(d, xs[2], y2, w, h, "06 / TELEMETRY BUS", ["Broadcast to", "live dashboards"], RED, 6)
    ym1, ym2 = y1 + h / 2, y2 + h / 2
    darrow(d, w, ym1, xs[1], ym1, MUTED)
    darrow(d, xs[1] + w, ym1, xs[2], ym1, MUTED)
    darrow(d, w, ym2, xs[1], ym2, MUTED)
    darrow(d, xs[1] + w, ym2, xs[2], ym2, MUTED)
    midy = (y1 + y2 + h) / 2
    dpoly_line(d, [(xs[2] + w / 2, y1), (xs[2] + w / 2, midy), (xs[0] + w / 2, midy)], MUTED)
    darrow(d, xs[0] + w / 2, midy, xs[0] + w / 2, y2 + h, MUTED)
    dtext(d, xs[1] + w / 2, midy + 5, "event handed to embedding stage", 7.2, MUTED, "Body-Italic", "middle")
    return d

def fig_epoch():
    d = Drawing(CW, 150)
    dbox(d, 0, 55, 112, 44, "Citizen query", ["arrives at gateway"], BLUE)
    cx, cy = 218, 77
    d.add(Polygon([cx - 62, cy, cx, cy + 40, cx + 62, cy, cx, cy - 40], fillColor=tint(AMBER, 0.9), strokeColor=AMBER, strokeWidth=1.2))
    dtext(d, cx, cy + 4, "Pending outbox epoch", 7.6, NAVY, "Body-Bold", "middle")
    dtext(d, cx, cy - 6, "> index epoch?", 7.6, NAVY, "Body-Bold", "middle")
    darrow(d, 112, cy, cx - 62, cy, MUTED)
    dbox(d, 318, 100, 177, 44, "Serve from Qdrant", ["hybrid dense + keyword retrieval"], TEAL)
    dbox(d, 318, 6, 177, 44, "Read PostgreSQL primary", ["consistent read (row-level locks)"], GREEN)
    dpoly_line(d, [(cx, cy + 40), (cx, 122)], MUTED)
    darrow(d, cx, 122, 318, 122, MUTED)
    dtext(d, cx + 10, 128, "No - index is current", 7.4, GREEN, "Body-Bold")
    dpoly_line(d, [(cx, cy - 40), (cx, 28)], MUTED)
    darrow(d, cx, 28, 318, 28, MUTED)
    dtext(d, cx + 10, 33, "Yes - index is behind", 7.4, RED, "Body-Bold")
    return d

def fig_timeline():
    d = Drawing(CW, 132)
    xs = [40 + i * 83 for i in range(6)]
    d.add(Line(18, 64, CW - 18, 64, strokeColor=LINE, strokeWidth=3))
    phases = [("Citizen", "lodging", "T + 0.00 s", BLUE), ("Officer", "triage", "T + 12.4 m", GREEN),
              ("Vector", "sync", "\u0394t = 88 ms", AMBER), ("Citizen", "query", "T + 14.1 m", BLUE),
              ("Raw", "generation", "\u0394t = 780 ms", RED), ("NLI", "interception", "\u0394t = 240 ms", MAGENTA)]
    for i, (a, b, lat, col) in enumerate(phases):
        x = xs[i]
        d.add(Circle(x, 64, 14, fillColor=col, strokeColor=white, strokeWidth=2))
        dtext(d, x, 59.8, str(i + 1), 11, white, "Body-Bold", "middle")
        dtext(d, x, 100, a.upper(), 8.5, NAVY, "Body-Bold", "middle")
        dtext(d, x, 89, b, 8.5, NAVY, "Body-Bold", "middle")
        d.add(Rect(x - 36, 20, 72, 19, rx=4, ry=4, fillColor=white, strokeColor=col, strokeWidth=0.8))
        dtext(d, x, 26, lat, 8.2, INK, "Body-Bold", "middle")
    return d

def fig_pipeline():
    d = Drawing(CW, 205)
    dbox(d, 0, 70, 100, 62, "01 / RAW DRAFT", ["from generator LLM", "\u201craw candidate text\u201d"], BLUE, 1)
    dbox(d, 122, 70, 100, 62, "04.A / PARSER", ["atomic decomposition", "C1, C2, \u2026, Cn"], VIOLET, 2)
    dbox(d, 244, 70, 112, 62, "04.B / CROSS-ENCODER", ["pair [premise, claim]", "DeBERTa-v3-base-mnli"], MAGENTA, 3)
    dbox(d, 244, 150, 112, 46, "03.A / ORCHESTRATION", ["Qdrant chunks (premise)"], AMBER)
    darrow(d, 100, 101, 122, 101, MUTED)
    darrow(d, 222, 101, 244, 101, MUTED)
    darrow(d, 300, 150, 300, 132, AMBER)
    outs = [(145, GREEN, "Supported (faithful)", "\u2192 Send"), (74, RED, "Contradicted", "\u2192 Correct"), (3, AMBER, "Low evidence", "\u2192 Abstain")]
    for y, col, t1, t2 in outs:
        dbox(d, 385, y, 110, 46, t1, [t2], col)
        dpoly_line(d, [(356, 101), (370, 101), (370, y + 23)], MUTED)
        darrow(d, 370, y + 23, 385, y + 23, MUTED)
    return d

def fig_contra_axis():
    d = Drawing(CW, 74)
    x0, x1, y, hh = 10, CW - 10, 34, 24
    span = x1 - x0
    segs = [(0, 0.15, GREEN, "Supported zone*"), (0.15, 0.35, AMBER, "No decision"), (0.35, 1.0, RED, "Contradicted: correct claim")]
    for a, b, col, lab in segs:
        d.add(Rect(x0 + a * span, y, (b - a) * span, hh, fillColor=col, strokeColor=white, strokeWidth=1.5))
        dtext(d, x0 + (a + b) / 2 * span, y + 8, lab, 8, white, "Body-Bold", "middle")
    for v in (0, 0.15, 0.35, 1.0):
        dtext(d, x0 + v * span, y - 12, f"{v:.2f}", 8.5, INK, "Body-Bold", "middle")
    dtext(d, x0, y + hh + 10, "P(contradiction)", 8.5, INK, "Body-Bold")
    dtext(d, x1, y + hh + 10, "*also requires P(entailment) \u2265 0.75", 8, MUTED, "Body-Italic", "end")
    return d

def fig_latency_bar():
    d = Drawing(CW, 84)
    total = 1440.0
    segs = [("Generation", 780, RED), ("NLI verification", 240, MAGENTA), ("Retrieval & orchestration", 420, MUTED)]
    x, y, hh = 0, 38, 26
    for lab, v, col in segs:
        wseg = v / total * CW
        d.add(Rect(x, y, wseg, hh, fillColor=col, strokeColor=white, strokeWidth=1.5))
        dtext(d, x + wseg / 2, y + 9, f"{v} ms", 9.5, white, "Body-Bold", "middle")
        x += wseg
    x = 0
    for lab, v, col in segs:
        wseg = v / total * CW
        lines = simpleSplit(lab.upper(), "Body-Bold", 8, wseg - 8)
        for k, ln in enumerate(lines[:2]):
            dtext(d, x + wseg / 2, y - 12 - 10 * k, ln, 7.8, NAVY, "Body-Bold", "middle")
        x += wseg
    dtext(d, 0, y + hh + 12, "Indicative budget for one query path, total 1,440 ms (benchmark average)", 8.5, INK, "Body-Bold")
    return d

def fig_donut(counts, colors_, total):
    d = Drawing(170, 170)
    cx, cy, r, r1 = 85, 85, 74, 46
    start = 90.0
    for n, col in zip(counts, colors_):
        sweep = 360.0 * n / total
        d.add(Wedge(cx, cy, r, start - sweep, start, radius1=r1, fillColor=col, strokeColor=white, strokeWidth=2))
        start -= sweep
    dtext(d, cx, cy + 2, str(total), 26, NAVY, "Body-Bold", "middle")
    dtext(d, cx, cy - 12, "QUERIES", 8, MUTED, "Body-Bold", "middle")
    return d

def fig_benchmarks():
    d = Drawing(CW, 232)
    left, base, top = 38, 44, 196
    gw = 262
    ch = top - base
    dtext(d, 0, 218, "FACTUAL ACCURACY VS HALLUCINATION RATE (%)", 9, NAVY, "Body-Bold")
    for v in (0, 25, 50, 75, 100):
        yy = base + ch * v / 100
        d.add(Line(left, yy, left + gw, yy, strokeColor=LINE, strokeWidth=0.6))
        dtext(d, left - 5, yy - 3, str(v), 7.5, MUTED, "Body", "end")
    data = [("CONFIG A", "Standalone LLM", 58.4, 41.6), ("CONFIG B", "LLM + RAG", 84.2, 15.8), ("CONFIG C", "RAG + NLI", 98.1, 0.0)]
    gwid = gw / 3
    bw = 30
    for i, (nm, sub, acc, hal) in enumerate(data):
        cx = left + gwid * (i + 0.5)
        for j, (val, col) in enumerate(((acc, TEAL), (hal, RED))):
            bx = cx - bw - 2 + j * (bw + 4)
            hh = ch * val / 100
            if hh > 0:
                d.add(Rect(bx, base, bw, hh, fillColor=col, strokeColor=None))
            dtext(d, bx + bw / 2, base + hh + 4, f"{val:.1f}", 8.5, INK, "Body-Bold", "middle")
        dtext(d, cx, base - 13, nm, 8.8, NAVY, "Body-Bold", "middle")
        dtext(d, cx, base - 23, sub, 7.6, MUTED, "Body", "middle")
    d.add(Rect(left, 6, 8, 8, fillColor=TEAL, strokeColor=None))
    dtext(d, left + 12, 7, "Factual accuracy", 8, SLATE)
    d.add(Rect(left + 92, 6, 8, 8, fillColor=RED, strokeColor=None))
    dtext(d, left + 104, 7, "Hallucination rate", 8, SLATE)
    
    px = 340
    dtext(d, px, 218, "AVERAGE LATENCY (s)", 9, NAVY, "Body-Bold")
    lat = [("A", 0.82, MUTED), ("B", 1.18, BLUE), ("C", 1.44, MAGENTA)]
    scale = 118 / 1.44
    for k, (nm, v, col) in enumerate(lat):
        yy = 168 - k * 40
        dtext(d, px, yy + 8, f"Config {nm}", 8.5, NAVY, "Body-Bold")
        d.add(Rect(px, yy - 12, v * scale, 15, fillColor=col, strokeColor=None))
        dtext(d, px + v * scale + 5, yy - 8, f"{v:.2f} s", 9, INK, "Body-Bold")
    dtext(d, px, 36, "Verification adds 0.26 s over RAG alone", 8, MUTED, "Body-Italic")
    return d

def caption(text):
    return Paragraph(text, st_caption)

# ------------------------------------------------------------------ cover
def draw_cover(c, doc):
    c.saveState()
    # Gallery Off-White Background
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    
    # Immersive Holographic Glassmorphism Blobs
    c.setFillColor(TEAL)
    c.setFillAlpha(0.12)
    c.circle(W - 40, H - 60, 220, fill=1, stroke=0)
    c.circle(W - 40, H - 60, 140, fill=1, stroke=0)
    c.setFillColor(MAGENTA)
    c.setFillAlpha(0.08)
    c.circle(80, 180, 200, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFillAlpha(0.06)
    c.circle(W - 80, 280, 150, fill=1, stroke=0)
    c.setFillAlpha(1)
    
    # Cyber-UI Dot Grid
    c.setFillColor(NAVY)
    c.setFillAlpha(0.08)
    for gx in range(0, 9):
        for gy in range(0, 5):
            c.circle(W - 150 + gx * 12, 275 + gy * 12, 1.2, fill=1, stroke=0)
    c.setFillAlpha(1)
    
    # Modern Editorial Typography
    c.setFillColor(NAVY)
    c.setFont("Body-Bold", 46)
    y = 505
    for ln in ["Live Updates", "& Verification", "Telemetry"]:
        c.drawString(LM, y, ln)
        y -= 52
    
    c.setFillColor(TEAL)
    c.rect(LM, y + 24, 80, 4, fill=1, stroke=0)
    c.setFillColor(SLATE)
    c.setFont("Body", 14)
    y -= 10
    for ln in simpleSplit("System Design Specification for Event-Driven Civic Telemetry, CDC Vector Sync, and Hallucination Interception",
                          "Body", 14, 400):
        c.drawString(LM, y, ln)
        y -= 20
        
    # Technical Stamps & Edition Tags
    c.setFillColor(NAVY)
    c.setFont("Body-Bold", 10)
    c.drawString(LM, H - 50, "DESIGN FORECAST")
    c.drawRightString(W - RM, H - 50, "EDITION 01/2026")
    
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.5)
    c.circle(LM + 14, H - 100, 20, fill=0, stroke=1)
    c.setFont("Body-Bold", 10)
    c.drawCentredString(LM + 14, H - 103.5, "AI")
    c.setFont("Body-Bold", 9)
    c.drawString(LM + 44, H - 100, "THE FUTURE OF CREATIVITY")
    c.setFont("Body", 8)
    c.drawString(LM + 44, H - 110, "AI-Grounded Civic Infrastructure")
    
    # Cyber UI Stat Cards
    stats = [("98.1%", "FACTUAL ACCURACY", "RAG + NLI configuration"), ("0.0%", "UNGROUNDED CLAIMS", "none observed in 250 queries"),
             ("< 100 ms", "CDC SYNC CONVERGENCE", "event to vector index"), ("1.44 s", "AVG PIPELINE LATENCY", "incl. verification")]
    gap = 12
    cw_ = (CW - 3 * gap) / 4
    for i, (v, l, s) in enumerate(stats):
        x = LM + i * (cw_ + gap)
        c.setFillColor(white)
        c.roundRect(x, 150, cw_, 86, 6, fill=1, stroke=0)
        
        c.setStrokeColor(LINE)
        c.setLineWidth(1)
        c.roundRect(x, 150, cw_, 86, 6, fill=0, stroke=1)
        
        c.setFillColor(TEAL if i % 2 == 0 else MAGENTA)
        c.rect(x + 12, 218, 22, 2.5, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont("Body-Bold", 22)
        c.drawString(x + 12, 188, v)
        c.setFont("Body-Bold", 7.8)
        c.drawString(x + 12, 174, l)
        c.setFont("Body", 7.8)
        c.setFillColor(SLATE)
        c.drawString(x + 12, 162, s)
        
    c.setFont("Body-Italic", 8.2)
    c.setFillColor(MUTED)
    c.drawString(LM, 126, "Figures as reported in the v2.4 evaluation (250 standardised village grievance queries, Configuration C).")
    
    # Footer
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(LM, 78, W - RM, 78)
    c.setFont("Body-Bold", 8.5)
    c.setFillColor(NAVY)
    c.drawString(LM, 58, "FastAPI   \u00B7   PostgreSQL   \u00B7   Qdrant   \u00B7   Redis   \u00B7   Sentence-BERT   \u00B7   DeBERTa-v3")
    c.setFont("Body", 8.5)
    c.drawRightString(W - RM, 58, "Expanded & redesigned 2026 edition")
    c.restoreState()

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self.chrome(self._pageNumber, n)
            super().showPage()
        super().save()

    def chrome(self, pn, total):
        if pn == 1:
            return
        self.saveState()
        self.setFillColor(TEAL)
        self.roundRect(LM, H - 41, 7, 7, 1.5, fill=1, stroke=0)
        self.setFont("Body-Bold", 7.6)
        self.setFillColor(NAVY)
        self.drawString(LM + 13, H - 40, "SYSTEM DESIGN SPECIFICATION // VOL. 2026")
        self.setFont("Body-Bold", 8)
        self.setFillColor(TEAL)
        self.drawRightString(W - RM, H - 40, "V2.4")
        self.setStrokeColor(LINE)
        self.setLineWidth(0.7)
        self.line(LM, H - 49, W - RM, H - 49)
        self.line(LM, 46, W - RM, 46)
        self.setFont("Body", 8.2)
        self.setFillColor(SLATE)
        self.drawString(LM, 32, "AI-Grounded Civic Infrastructure \u2022 System Design Specification")
        self.setFont("Body-Bold", 8.2)
        self.setFillColor(NAVY)
        self.drawRightString(W - RM, 32, f"Page {pn} of {total}")
        self.restoreState()

class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, **kw)
        self.h_seq = 0

    def beforeDocument(self):
        self.h_seq = 0

    def afterFlowable(self, fl):
        if not hasattr(self, 'h_seq'):
            self.h_seq = 0
        if isinstance(fl, SectionOpener):
            self.notify("TOCEntry", (0, escape(f"{fl.num}.  {fl.title}"), self.page, fl.key))
        elif isinstance(fl, Paragraph) and fl.style.name in ("H2", "H1U"):
            text = fl.getPlainText()
            lvl = 1 if fl.style.name == "H2" else 0
            key = f"h{self.h_seq}"
            self.h_seq += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, lvl, 0)
            self.notify("TOCEntry", (lvl, escape(text), self.page, key))

# ------------------------------------------------------------------ content
story = []
story += [NextPageTemplate("Body"), Spacer(1, 1), PageBreak()]

# ---- Executive summary
story += [P("EXECUTIVE SUMMARY", st_label), Paragraph("The short version", st_h1u),
          P("Rural civic portals fail citizens quietly: the database is right, but the answer the AI gives is out of date or invented. "
            "This specification describes a reactive architecture that keeps relational records, vector memory and conversational answers "
            "synchronised in under 100 ms, and that verifies every generated claim against the source record before a citizen sees it.", st_lede),
          Spacer(1, 4)]
story.append(cards([
    (RED, "The problem", "When a Panchayat officer reassigns a pipeline repair, a typical portal updates one database row. Cached or "
                         "ungrounded AI answers keep citing the old assignment, and the language model fills gaps from its own parametric memory."),
    (TEAL, "The approach", "A transactional outbox streams every change into Qdrant and a Redis telemetry bus. Each candidate answer is split into "
                           "atomic claims; a DeBERTa-v3 cross-encoder checks each against retrieved evidence and routes it to send, correct or abstain."),
    (GREEN, "The result", "In the v2.4 evaluation of 250 queries, factual accuracy rose from 58.4% (standalone LLM) to 98.1%, with no ungrounded "
                          "claims observed, at an average of 1.44 s per answer."),
]))
story += [Spacer(1, 12), kpi_strip([("98.1%", "factual accuracy<br/>(Config C)", TEAL), ("0.0%", "ungrounded claims<br/>(none observed)", GREEN),
                                    ("&lt; 100 ms", "CDC sync<br/>convergence", BLUE), ("1.44 s", "average end-to-end<br/>latency", MAGENTA)])]
story += [Paragraph("Five design decisions that shape everything else", st_h2)]
decisions = [
    ("Events, not polling.", "Changes flow through a transactional outbox and are pushed to clients over WebSocket/SSE. Polling would leave citizens with 5\u201315 s of stale information."),
    ("Two stores, one truth.", "PostgreSQL stays the system of record (ACID, joins, audit); Qdrant holds the derived semantic view. Neither can do the other's job."),
    ("Verify claims, not paragraphs.", "Answers are decomposed into atomic propositions and each is tested for entailment against the evidence."),
    ("Abstain rather than guess.", "If retrieval similarity is below 0.65 or the NLI evidence is weak, the system says it does not know."),
    ("Leave an audit trail.", "Every verification decision is written, with prompt, context and scores, to an append-only ledger."),
]
dt = [[Paragraph(f'<font name="Body-Bold" color="{hexs(TEAL)}" size="15">{i + 1}</font>', st_cellc), Paragraph(f"<b>{a}</b> {b}", st_cell)]
      for i, (a, b) in enumerate(decisions)]
t = Table(dt, colWidths=[30, CW - 30])
t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 0), (-1, -2), 0.5, LINE),
                       ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
story += [t, Spacer(1, 10)]
story += [data_table([["If you are\u2026", "Start with", "Because"],
                      ["Building or operating the system", "Sections 1, 2, 4, 6", "Architecture, sync mechanics, verification gates, operations"],
                      ["Evaluating the research claims", "Sections 3, 5, 7", "Live trace, benchmarks, and the limits of the evidence"],
                      ["A Panchayat administrator", "Sections 3 and 6", "What a citizen sees, and who can see and change what"]],
                     [150, 120, CW - 270], first_col_bold=True)]
story.append(PageBreak())

# ---- Contents
story += [P("CONTENTS", st_label), Paragraph("What\u2019s inside", st_h1u), Spacer(1, 6)]
toc = TableOfContents()
toc.levelStyles = [st_toc0, st_toc1]
toc.dotsMinLevel = 0
story += [toc, Spacer(1, 16)]
story += [Paragraph("Document information", st_h3)]
story += [data_table([["Item", "Detail"],
                      ["Document", "System Design Specification \u2014 Real-Time Live Updates &amp; Verification Telemetry Architecture"],
                      ["Version", "2.4 (expanded 2026 edition)"],
                      ["Type", "Engineering design document"],
                      ["Subject system", "AI-Grounded Civic Infrastructure for village grievance redressal"],
                      ["Components covered", "FastAPI gateway, PostgreSQL, Qdrant, Redis, Sentence-BERT, DeBERTa-v3 cross-encoder, React dashboards"],
                      ["Evaluation basis", "250 standardised village grievance queries; a 26-query, 24-hour telemetry window"]],
                     [120, CW - 120], first_col_bold=True)]
story += [Spacer(1, 10), Paragraph("How to read the diagrams", st_h3)]
legend = [(BLUE, "Dashboard / citizen"), (TEAL, "Gateway / workers"), (GREEN, "PostgreSQL"), (AMBER, "Qdrant"),
          (VIOLET, "Embedding"), (MAGENTA, "NLI verification"), (RED, "Redis / unverified")]
lt = Table([[Paragraph(f'<font color="{hexs(c)}">\u25A0</font>&nbsp;{n}', st_cell) for c, n in legend[:4]],
            [Paragraph(f'<font color="{hexs(c)}">\u25A0</font>&nbsp;{n}', st_cell) for c, n in legend[4:]] + [""]],
           colWidths=[CW / 4] * 4)
lt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), white), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
story += [lt, P("Colours identify the same component in every figure. Items marked <b>recommended</b> or <b>illustrative</b> are design proposals or "
                "example values added to make the specification implementable; they are not measurements.", st_small)]
story.append(PageBreak())

# ---- Section 1
story += [SectionOpener(1, "Architecture Overview & Core Motivations"),
          P("In rural civic governance, digital portals often suffer from <b>information decoupling</b>: when a Panchayat officer reassigns a "
            "water-supply pipeline repair, standard web applications only update static database rows. Consequently, conversational AI systems "
            "continue to serve stale, ungrounded cached answers.", st_lede),
          P("The <b>Live Updates &amp; Telemetry Architecture</b> solves this by creating an event-driven loop that unifies administrative "
            "operations, vector search synchronisation, and real-time Natural Language Inference (NLI) telemetry.")]
story += [Paragraph("1.1  The information-decoupling problem", st_h2)]
story += [data_table([["Moment", "Conventional portal + chatbot", "Live Updates architecture"],
                      ["Staff updates a complaint", "One relational row changes", "Row change and an outbox event commit in the <b>same transaction</b>"],
                      ["Semantic index", "Rebuilt in batches, or never", "Updated per event (\u0394t = 88 ms in the traced case)"],
                      ["Citizen asks a question", "Answer from cache or model memory", "Answer generated from <b>retrieved evidence</b>, then verified"],
                      ["A claim is wrong", "It reaches the citizen", "Suppressed and corrected, or the system abstains"],
                      ["Dashboards", "Refresh or poll every few seconds", "Pushed over WebSocket / SSE"],
                      ["Accountability", "Application logs", "Append-only ledger of prompt, context and NLI scores"]],
                     [112, 170, CW - 282], first_col_bold=True)]
story += [Paragraph("1.2  System architecture", st_h2)]
story += [KeepTogether([fig_overview(), caption("Figure 1.1 \u2014 High-level pipeline of the reactive event bus, dual-store sync and NLI verification telemetry. "
                                                "Numbers match the component table in section 1.4.")])]
story += [Paragraph("1.3  Architectural justifications", st_h2)]
story += [callout("Why no client polling and no direct SQL from the LLM",
                  "We deliberately avoid client-side polling and direct relational queries from the LLM. Polling introduces <b>5\u201315 s delays</b>, "
                  "during which citizens receive outdated information, while unindexed relational queries fail to capture unstructured semantic nuance. "
                  "By decoupling ingestion via an event-driven outbox and streaming telemetry updates over persistent WebSockets, the system "
                  "targets <b>sub-second sync convergence</b> while intercepting ungrounded candidate claims before they reach citizens.", "info"),
          Spacer(1, 8)]
story += [Paragraph("Design principles", st_h3)]
story += bullets([
    "<b>One source of truth.</b> PostgreSQL commits first; every other view (vectors, dashboards, telemetry) is derived from it.",
    "<b>Derived views converge fast.</b> The vector index and live dashboards follow committed changes within a sub-second bound.",
    "<b>Ground, then verify.</b> The model only sees retrieved evidence, and its output is checked against that same evidence.",
    "<b>Fail safe.</b> When evidence is thin, abstain; when the verifier is slow, degrade to a simpler check rather than skip it.",
    "<b>Everything is explainable.</b> Each decision can be replayed from the audit ledger.",
])
story += [CondPageBreak(200), Paragraph("1.4  Component responsibilities", st_h2)]
story += [data_table([["#", "Component", "Responsibility", "Interface"],
                      ["1", "React dashboards", "Citizen and staff UI for complaints, answers and live telemetry", "WebSocket / SSE subscription"],
                      ["2", "FastAPI gateway", "REST and WebSocket endpoints; hosts the Outbox Publisher", "API &amp; WebSocket"],
                      ["3", "PostgreSQL", "System of record; transactions, WAL and the outbox table", "SQL, outbox_events"],
                      ["4", "Qdrant", "Vector store for dense chunks and payload hashes", "Upsert point {id, vector, payload}"],
                      ["5", "NLI verification", "Claim splitter, DeBERTa-v3 cross-encoder, abstention gate", "[P<sub>entail</sub>, P<sub>neutral</sub>, P<sub>contra</sub>]"],
                      ["6", "Redis Pub/Sub", "Carries change and telemetry events to live dashboards", "Topics, rolling 24 h aggregation"],
                      ["\u2022", "CDC worker", "Moves outbox events into vector space", "Polls WAL / outbox"],
                      ["\u2022", "Sentence-BERT", "Dense embeddings for new record states", "Called by the worker"]],
                     [26, 112, CW - 26 - 112 - 150, 150], center_cols=(0,), first_col_bold=False)]
story.append(PageBreak())

# ---- Section 2
story += [SectionOpener(2, "Reactive Ingestion & Dual-Store Synchronization"),
          P("A central challenge in real-time civic AI is maintaining <b>absolute cache coherence</b> between structured relational tables "
            "(PostgreSQL) and dense semantic embeddings (Qdrant).", st_lede),
          P("When Panchayat staff members reassign a complaint or update resolution milestones, the system executes an atomic transaction using the "
            "<b>Transactional Outbox Pattern</b>. This decouples the operational transaction from vector indexing without introducing "
            "distributed locking overhead.")]
story += [Paragraph("2.1  The transactional outbox flow", st_h2)]
story += [KeepTogether([fig_outbox(), caption("Figure 2.1 \u2014 The Transactional Outbox pattern ensures zero-loss CDC propagation to Qdrant vector memory.")])]
story += bullets([
    "<b>1 \u2192 2</b> A staff action updates the complaint row and inserts an <font name='Mono' size='8.4'>outbox_events</font> row in <b>one</b> transaction: both commit or neither does.",
    "<b>3</b> The CDC ingestion worker picks the event up from the WAL / outbox, so indexing never blocks the staff member\u2019s request.",
    "<b>4 \u2192 5</b> Sentence-BERT embeds the new record state and the worker upserts it into Qdrant as {id, vector, payload}.",
    "<b>6</b> A Redis Pub/Sub event is broadcast so open dashboards update without a refresh.",
])
story += [Paragraph("2.2  Outbox event contract", st_h2),
          P("The outbox row carries everything the worker needs, so it never has to re-query PostgreSQL to build an embedding. "
            "The field set below is <b>recommended</b>; values are illustrative.")]
story += [code_block('''{
  "event_id": 8841,
  "aggregate": "complaint",
  "aggregate_id": "GRV-2026-001024",
  "event_type": "complaint.status_changed",
  "version_epoch": 1042,
  "payload": {
    "category": "Water Supply",   "ward": 4,
    "status": "Under Review",
    "department": "Village Water Department",
    "updated_by": "Officer Vikram"
  },
  "payload_hash": "sha256:\u2026"
}'''), Spacer(1, 8)]
story += [data_table([["Field", "Purpose"],
                      ["<font name='Mono' size='8'>version_epoch</font>", "Monotonically increasing; compared with the epoch last applied to the vector index (section 2.3)"],
                      ["<font name='Mono' size='8'>aggregate_id</font>", "Complaint ID; becomes the Qdrant point id, which makes upserts idempotent"],
                      ["<font name='Mono' size='8'>payload</font>", "Snapshot of the record state used to build embedding text and the Qdrant payload"],
                      ["<font name='Mono' size='8'>payload_hash</font>", "Checked after upsert (\u201cpayload hash verified\u201d) to confirm the vector store matches PostgreSQL"]],
                     [120, CW - 120])]
story += [Paragraph("2.3  Race-condition mitigation &amp; snapshot isolation", st_h2),
          P("Under traditional asynchronous architectures, an immediate read-after-write query from an asking citizen could hit the vector database "
            "before embedding computation finishes, yielding stale responses. To prevent this, each outbox event contains a monotonically increasing "
            "<font name='Mono' size='8.6'>version_epoch</font>. If an incoming citizen query detects a pending outbox entry with a higher epoch than "
            "the vector index, the retrieval orchestrator performs a fast fallback to primary PostgreSQL row-level locks.")]
story += [KeepTogether([fig_epoch(), caption("Figure 2.2 \u2014 Epoch check on every query: the index is trusted only when it has caught up with committed changes.")])]
story += [callout("Outcome", "Deterministic consistency across all rural endpoints: a citizen can never be answered from an index older than the "
                             "record that staff just changed.", "ok"), Spacer(1, 4)]
story += [Paragraph("2.4  Why dual storage over pure vector search?", st_h2),
          P("While vector databases excel at semantic similarity, they lack ACID guarantees, efficient relational joins, and the cryptographic "
            "auditability required for government complaint logging. Conversely, PostgreSQL lacks dense semantic recall across vernacular descriptions. "
            "By combining both through real-time CDC, the design achieves sub-120 ms ingestion latency with strict transactional safety.")]
yes = chip("STRONG", GREEN)
no = chip("NOT A FIT", RED)
part = chip("LIMITED", AMBER)
story += [data_table([["Capability", "PostgreSQL", "Qdrant", "Combined"],
                      ["ACID transactions", yes, no, yes],
                      ["Relational joins", yes, part, yes],
                      ["Audit trail for complaint logging", yes, no, yes],
                      ["Semantic recall on vernacular text", no, yes, yes],
                      ["Latency from change to searchable", "n/a", "n/a", "&lt; 120 ms ceiling"]],
                     [190, 95, 95, CW - 380], center_cols=(1, 2, 3), first_col_bold=True)]
story += [CondPageBreak(190), Paragraph("2.5  Delivery guarantees &amp; failure handling", st_h2),
          P("The following mechanisms are <b>recommended</b> to make the outbox pipeline safe to operate unattended.")]
story += [data_table([["Concern", "Mechanism"],
                      ["Lost events", "The outbox row commits atomically with the change, so nothing is lost if the worker is down; it simply catches up."],
                      ["Duplicate delivery", "At-least-once delivery with idempotent upserts keyed on the complaint ID; unchanged payload hashes are no-ops."],
                      ["Ordering", "The worker applies events in <font name='Mono' size='8'>version_epoch</font> order and ignores any event older than what is already indexed."],
                      ["Poison events", "Retry with back-off, then park in a dead-letter table and alert staff; the PostgreSQL record is unaffected."],
                      ["Rebuild", "Because PostgreSQL is the source of truth, the entire vector collection can be regenerated from it at any time."]],
                     [110, CW - 110], first_col_bold=True)]
story.append(PageBreak())

# ---- Section 3
story += [SectionOpener(3, "Live Data Trace: Complaint Lifecycle"),
          P("To demonstrate the live updates engine under real-world conditions, we trace the full lifecycle of complaint "
            "<font name='Mono' size='9.6'>GRV-2026-001024</font>, originating from Chandanpur Ward 4 about contaminated water supply.", st_lede),
          P("The case shows how administrative updates immediately guard the conversational LLM against generating misleading information.")]
story += [Paragraph("3.1  Six phases, end to end", st_h2)]
story += [KeepTogether([fig_timeline(), caption("Figure 3.1 \u2014 Timeline of complaint GRV-2026-001024. Phases 1\u20132 are staff-side events; phases 4\u20136 happen "
                                                "within one citizen query.")])]
trace_rows = [
    ["Phase", "Payload / event data", "Latency / delta", "Verification &amp; system state"],
    [Paragraph(f'<font color="{hexs(BLUE)}"><b>1</b></font>&nbsp; <b>Citizen lodging</b>', st_cell),
     "ID: GRV-2026-001024<br/>Category: Water Supply \u2022 Ward 4<br/>Desc: \u201cBrownish tap water leaking\u201d", "T + 0.00 s<br/>(HTTP POST)",
     chip("REGISTERED", BLUE) + "<br/>Row committed to PostgreSQL"],
    [Paragraph(f'<font color="{hexs(GREEN)}"><b>2</b></font>&nbsp; <b>Officer triage</b>', st_cell),
     "Officer Vikram updates status to <b>Under Review</b> and assigns <b>Village Water Department</b>", "T + 12.4 m<br/>(admin action)",
     chip("UNDER REVIEW", GREEN) + "<br/>Outbox event emitted"],
    [Paragraph(f'<font color="{hexs(AMBER)}"><b>3</b></font>&nbsp; <b>Vector sync</b>', st_cell),
     "CDC worker embeds new metadata into Qdrant vector space (collection <font name='Mono' size='8'>civic_records</font>)", "\u0394t = 88 ms<br/>(async worker)",
     chip("SYNCED", AMBER) + "<br/>Payload hash verified"],
    [Paragraph(f'<font color="{hexs(BLUE)}"><b>4</b></font>&nbsp; <b>Citizen query</b>', st_cell),
     "Citizen asks: \u201cWho is handling my complaint GRV-1024?\u201d", "T + 14.1 m<br/>(chat interface)",
     chip("HYBRID RETRIEVAL", BLUE) + "<br/>Dense Qdrant similarity: 0.94"],
    [Paragraph(f'<font color="{hexs(RED)}"><b>5</b></font>&nbsp; <b>Raw generation</b>', st_cell),
     "Raw LLM drafts: \u201cYour complaint is being handled by Road Department\u2026\u201d", "\u0394t = 780 ms<br/>(LLM inference)",
     chip("UNVERIFIED CANDIDATE", RED) + "<br/>Contains severe factual drift"],
    [Paragraph(f'<font color="{hexs(MAGENTA)}"><b>6</b></font>&nbsp; <b>NLI interception</b>', st_cell),
     "Cross-encoder flags contradiction against the record; auto-corrects to Village Water Department", "\u0394t = 240 ms<br/>(verification)",
     chip("FAITHFUL DELIVERED", GREEN) + "<br/>100% grounded answer returned"],
]
story += [data_table(trace_rows, [92, 175, 88, CW - 355], extra=[("VALIGN", (0, 1), (-1, -1), "TOP")])]
story += [Spacer(1, 6), callout("Reading the trace",
                                "The citizen\u2019s short form \u201cGRV-1024\u201d is matched to the full record ID by hybrid retrieval (dense similarity 0.94). "
                                "Roughly 1.7 minutes passed between triage (12.4 m) and the query (14.1 m), far longer than the 88 ms sync, so the epoch "
                                "check in section 2.3 finds the index current and no PostgreSQL fallback is needed.", "note")]
story += [CondPageBreak(300), Paragraph("3.2  Failure-mode analysis: intercepting a hallucination in flight", st_h2),
          P("At phase 5, a standard ungrounded LLM defaults to parametric memory and asserts that the Road Department owns the issue, because the "
            "prompt mentioned \u201cleaking near Kali Mandir junction\u201d. The NLI claim verification engine extracts the triple "
            "<font name='Mono' size='8.6'>(GRV-2026-001024, handled_by, Road Department)</font> and tests it against the retrieved Qdrant chunk. "
            "The contradiction score clears the gate (P<sub>contra</sub> &gt; 0.35, section 4.3), so the output is suppressed and corrected to "
            "Village Water Department before transmission.")]
panel = Table([[
    [Paragraph(chip("EVIDENCE", AMBER), st_cell), Spacer(1, 4),
     Paragraph("<b>Retrieved record</b><br/>GRV-2026-001024<br/>Water Supply \u2022 Ward 4<br/>Status: <b>Under Review</b><br/>Department: <b>Village Water Department</b><br/>Updated by: Officer Vikram", st_cell)],
    [Paragraph(chip("RAW DRAFT \u2014 BLOCKED", RED), st_cell), Spacer(1, 4),
     Paragraph("<b>Unverified candidate</b><br/>\u201cYour complaint is being handled by <font color='#E24D4D'><b>Road Department</b></font>\u2026\u201d<br/><br/>"
               "<i>Contradicts the record: severe factual drift.</i>", st_cell)],
    [Paragraph(chip("DELIVERED \u2014 VERIFIED", GREEN), st_cell), Spacer(1, 4),
     Paragraph("<b>Citizen receives</b><br/>\u201cYour complaint GRV-2026-001024 is currently <b>Under Review</b> by the <font color='#1F9D6B'><b>Village Water Department</b></font>. "
               "It was assigned by Officer Vikram.\u201d", st_cell)],
]], colWidths=[CW / 3] * 3)
panel.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                           ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
                           ("BACKGROUND", (0, 0), (0, 0), white), ("BACKGROUND", (1, 0), (1, 0), white),
                           ("BACKGROUND", (2, 0), (2, 0), white),
                           ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                           ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 14)]))
story += [panel, caption("Figure 3.2 \u2014 One query, three artefacts: the evidence, the blocked draft, and the answer the citizen actually sees."),
          callout("End-to-end safety audit", "The citizen receives only the verified answer, and the telemetry counters increment in real time. The blocked draft "
                                             "is retained in the audit ledger for administrators.", "ok")]
story += [Paragraph("3.3  Latency budget for the traced query", st_h2),
          P("Generation (780 ms) and verification (240 ms) are the two measured stages in the trace. The remaining budget is an <b>implied</b> "
            "figure: the 1.44 s benchmark average minus those two stages, covering retrieval, orchestration and network time. It is indicative, "
            "not a measured breakdown.")]
story += [KeepTogether([fig_latency_bar(), caption("Figure 3.3 \u2014 Where the time goes: verification costs about a sixth of the budget.")])]
story.append(PageBreak())

# ---- Section 4
story += [SectionOpener(4, "Verification Telemetry Engine & Claim Decomposition"),
          P("The Live Monitoring dashboard reflects the output of the automated Natural Language Inference (NLI) verification layer. Rather than "
            "evaluating generated text as an opaque block, the engine executes <b>claim decomposition</b>, converting candidate responses into "
            "atomic propositional units.", st_lede),
          P("Each proposition is evaluated against retrieved evidence chunks using a cross-encoder model to determine <b>entailment, neutral, or "
            "contradiction</b> probabilities.")]
story += [Paragraph("4.1  The verification pipeline", st_h2)]
story += [KeepTogether([fig_pipeline(), caption("Figure 4.1 \u2014 Atomic claim decomposition, NLI verification routing, and real-time telemetry emission.")])]
story += [Paragraph("4.2  Worked example: decomposing the traced answer", st_h2),
          P("Each claim is a (subject, relation, object) triple tested against the retrieved record. Verdicts below follow the decision gate in section 4.3.")]
story += [data_table([["Answer", "Atomic claim", "Evidence says", "Verdict"],
                      ["Raw draft", "(GRV-2026-001024, handled_by, Road Department)", "Department: Village Water Department", chip("CONTRADICTED", RED)],
                      ["Corrected", "(GRV-2026-001024, status, Under Review)", "Status: Under Review", chip("SUPPORTED", GREEN)],
                      ["Corrected", "(GRV-2026-001024, handled_by, Village Water Department)", "Department: Village Water Department", chip("SUPPORTED", GREEN)],
                      ["Corrected", "(GRV-2026-001024, assigned_by, Officer Vikram)", "Updated by: Officer Vikram", chip("SUPPORTED", GREEN)]],
                     [62, 205, 148, CW - 415], first_col_bold=True)]
story += [Paragraph("4.3  Decision gate logic", st_h2),
          P("Let <i>E</i> represent the retrieved evidence text and <i>c</i> an extracted candidate claim. The NLI model outputs a normalised "
            "three-way probability vector <b>[P<sub>entail</sub>, P<sub>neutral</sub>, P<sub>contra</sub>]</b> that sums to 1.0. "
            "The pipeline enforces deterministic decision bounds:")]
story += [cards([
    (GREEN, "Supported", "<font name='Mono' size='8.4'>P<sub>entail</sub> \u2265 0.75</font><br/><font name='Mono' size='8.4'>and P<sub>contra</sub> \u2264 0.15</font><br/><br/>Faithful claim: safe to send."),
    (RED, "Contradicted", "<font name='Mono' size='8.4'>P<sub>contra</sub> &gt; 0.35</font><br/><br/><br/>Conflicts with the record: correct it."),
    (AMBER, "Abstain", "<font name='Mono' size='8.4'>max(P<sub>entail</sub>, P<sub>contra</sub>) &lt; 0.50</font><br/><br/>Insufficient context: do not guess."),
])]
story += [Spacer(1, 8), KeepTogether([fig_contra_axis(), caption("Figure 4.2 \u2014 The contradiction axis. The grey area between the gates is where no rule fires.")])]
story += [callout("Evaluation order and fail-safe default",
                  "The three rules as written leave gaps (for example P<sub>entail</sub> = 0.60 with P<sub>contra</sub> = 0.10 matches none). Evaluate "
                  "<b>Contradicted first, then Supported</b>, and treat anything that matches neither as <b>Abstain</b>. At answer level: deliver the original text only if "
                  "<i>every</i> claim is Supported; replace any Contradicted claim with text built from the record and re-verify it; drop or abstain on "
                  "any claim that remains undecided.", "warn"), Spacer(1, 4)]
story += [CondPageBreak(250), Paragraph("4.4  Telemetry metrics aggregation", st_h2),
          P("Each decision publishes an event over the Redis telemetry topic. The Live Monitoring dashboard aggregates these events into rolling "
            "24-hour windows. In the current telemetry window, 18 of 26 queries are classified as Supported, 3 are intercepted and auto-corrected, "
            "and 5 trigger safe abstention.")]
donut = fig_donut([18, 3, 5], [GREEN, MAGENTA, AMBER], 26)
mix = Table([[donut, [
    Paragraph(f'<font size="20" color="{hexs(GREEN)}"><b>18</b></font>&nbsp; <b>Supported</b> \u2014 69.2%', st_cell), Spacer(1, 3),
    Paragraph("Delivered as generated; every claim entailed.", st_small), Spacer(1, 9),
    Paragraph(f'<font size="20" color="{hexs(MAGENTA)}"><b>3</b></font>&nbsp; <b>Auto-corrected</b> \u2014 11.5%', st_cell), Spacer(1, 3),
    Paragraph("Contradiction intercepted; corrected from the record.", st_small), Spacer(1, 9),
    Paragraph(f'<font size="20" color="{hexs(AMBER)}"><b>5</b></font>&nbsp; <b>Safe abstention</b> \u2014 19.2%', st_cell), Spacer(1, 3),
    Paragraph("Evidence too thin; the system declined to answer.", st_small)]]],
    colWidths=[185, CW - 185])
mix.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOX", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (-1, -1), white),
                         ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
story += [mix, caption("Figure 4.3 \u2014 Decision mix over the 26-query, 24-hour window. Percentages are of 26 queries and sum to 100% (rounded)."),
          callout("What this window does and doesn\u2019t show",
                  "No ungrounded claim reached a citizen in this window. With only 26 queries that is encouraging, not conclusive; see the confidence "
                  "note in section 5.2.", "note")]
story += [CondPageBreak(230), Paragraph("4.5  Telemetry event schema", st_h2),
          P("Each verification decision emits one event. The field list is <b>recommended</b>.")]
story += [data_table([["Field", "Type", "Meaning"],
                      ["<font name='Mono' size='8'>query_id</font>", "uuid", "Links the event to the audit-ledger record"],
                      ["<font name='Mono' size='8'>decision</font>", "enum", "supported | corrected | abstained"],
                      ["<font name='Mono' size='8'>claims_total / claims_contradicted</font>", "int", "How many atomic claims were extracted and how many failed"],
                      ["<font name='Mono' size='8'>min_p_entail / max_p_contra</font>", "float", "Weakest and strongest NLI scores across the claims"],
                      ["<font name='Mono' size='8'>retrieval_score</font>", "float", "Top similarity; below 0.65 forces abstention"],
                      ["<font name='Mono' size='8'>latency_ms</font>", "int", "Total time from query to delivery"],
                      ["<font name='Mono' size='8'>mode</font>", "enum", "normal | degraded (BM25 fallback, section 5.5)"]],
                     [190, 50, CW - 240])]
story.append(PageBreak())

# ---- Section 5
story += [SectionOpener(5, "Experimental Benchmarks, SLAs & Resilience"),
          P("To satisfy the core research objectives, three system configurations were evaluated across <b>250 standardised village grievance "
            "queries</b>. The empirical results substantiate the necessity of the verification layer.", st_lede)]
story += [Paragraph("5.1  Configurations under test", st_h2)]
story += [cards([
    (MUTED, "Config A / Baseline", "Standalone. The model answers from parametric memory only; no retrieval, no verification."),
    (BLUE, "Config B / LLM+RAG", "The model answers from retrieved village records and documents, with no check on what it writes."),
    (MAGENTA, "Config C / VERIFIED", "RAG plus claim decomposition, cross-encoder verification, correction and abstention, with telemetry."),
])]
story += [Paragraph("5.2  Results", st_h2)]
story += [KeepTogether([fig_benchmarks(), caption("Figure 5.1 \u2014 Accuracy and hallucination rate (left) and average latency (right) by configuration.")])]
story += [data_table([["Evaluation configuration", "Factual accuracy", "Hallucination rate", "Retrieval recall@3", "Avg latency", "Public safety status"],
                      ["Config A: Standalone LLM", "58.4%", "41.6%", "N/A (parametric)", "0.82 s", chip("UNSAFE FOR PUBLIC USE", RED)],
                      ["Config B: LLM + RAG", "84.2%", "15.8%", "91.2%", "1.18 s", chip("RESIDUAL HALLUCINATION", AMBER)],
                      ["Config C: RAG + NLI Telemetry", "98.1%", "0.0% (grounded)", "94.6%", "1.44 s", chip("PRODUCTION CERTIFIED", GREEN)]],
                     [118, 62, 72, 72, 52, CW - 376], center_cols=(1, 2, 3, 4), first_col_bold=True)]
story += [Spacer(1, 8), Paragraph("What the numbers show", st_h3)]
story += bullets([
    "<b>RAG alone</b> (A \u2192 B) adds <b>25.8 points</b> of accuracy and cuts hallucination from 41.6% to 15.8%.",
    "<b>Verification</b> (B \u2192 C) adds a further <b>13.9 points</b> of accuracy and removes the remaining 15.8 points of hallucination.",
    "The price is <b>+0.26 s</b> of latency over RAG alone (+0.62 s over the baseline), plus a 3.4-point higher recall@3.",
])
story += [callout("Confidence note", "A result of 0 out of 250 does not prove the true rate is zero. By the \u201crule of three\u201d, zero observed events in 250 trials "
                                     "is consistent, at 95% confidence, with a true rate of up to about <b>1.2%</b> (3 \u00F7 250). Report the figure as "
                                     "\u201c0 of 250 observed\u201d and enlarge the test set before making stronger claims.", "warn"), Spacer(1, 4)]
story += [CondPageBreak(200), Paragraph("5.3  Policy constants at a glance", st_h2)]
story += [data_table([["Policy", "Value", "Effect"],
                      ["Supported gate", "P<sub>entail</sub> \u2265 0.75 and P<sub>contra</sub> \u2264 0.15", "Claim is delivered as written"],
                      ["Contradiction gate", "P<sub>contra</sub> &gt; 0.35", "Claim is suppressed and corrected from the record"],
                      ["Abstain gate", "max(P<sub>entail</sub>, P<sub>contra</sub>) &lt; 0.50", "Insufficient context: safe abstention"],
                      ["Zero Guessing floor", "Retrieval similarity &lt; 0.65", "System abstains instead of risking misinformation"],
                      ["Degraded-mode trigger", "Cross-encoder GPU latency &gt; 800 ms", "Fall back to BM25 keyword matching on verified records"],
                      ["CDC sync convergence", "&lt; 100 ms (ingestion ceiling 120 ms)", "Time from commit to searchable in Qdrant"],
                      ["Detection window", "Rolling 24 hours", "Telemetry aggregation period on the live dashboard"]],
                     [118, 190, CW - 308], first_col_bold=True)]
story.append(PageBreak())

# ---- Build
doc = Doc(OUT, pagesize=A4, title="Real-Time Live Updates & Verification Telemetry Architecture",
          author="AI-Grounded Civic Infrastructure", subject="System Design Specification v2026",
          leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM)
cover_frame = Frame(0, 0, W, H, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="cover")
body_frame = Frame(LM, BM, CW, H - TM - BM, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="body")
doc.addPageTemplates([PageTemplate("Cover", [cover_frame], onPage=draw_cover),
                      PageTemplate("Body", [body_frame])])
doc.multiBuild(story, canvasmaker=NumberedCanvas)
print("built", OUT)