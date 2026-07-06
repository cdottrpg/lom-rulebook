from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

# ══════════════════════════════════════════════════════════════════════════════
# Encoding safeguard: detect mojibake (UTF-8 bytes read as cp1252)
# If you see mojibake (corrupted accented chars or A-tilde combos) in the PDF, run _fix_all_encoding.py in this folder.
# ══════════════════════════════════════════════════════════════════════════════
def _check_encoding():
    """Scan source for mojibake patterns in non-comment lines. Warns if found."""
    import __main__
    try:
        with open(__main__.__file__, 'r', encoding='utf-8') as _f:
            _lines = _f.readlines()
    except Exception:
        return
    _problems = []
    for _lineno, _line in enumerate(_lines, 1):
        if _line.lstrip().startswith('#'):
            continue  # skip comments
        for _i, _ch in enumerate(_line):
            if ord(_ch) == 0x00E2 and _i + 2 < len(_line):
                # Try W1252 reversal: 3 chars -> 1 original char
                try:
                    _b = bytes(ord(_line[_i+k]) for k in range(3))
                    _r = _b.decode('utf-8')
                    if len(_r) == 1:
                        _problems.append(f"L{_lineno}: corrupted char near …{_line[max(0,_i-5):_i+15].strip()!r}…")
                        break
                except Exception:
                    pass
            elif ord(_ch) in (0x00C3, 0x00C2) and _i + 1 < len(_line):
                try:
                    _b = bytes(ord(_line[_i+k]) for k in range(2))
                    _r = _b.decode('utf-8')
                    if len(_r) == 1:
                        _problems.append(f"L{_lineno}: corrupted char near …{_line[max(0,_i-5):_i+10].strip()!r}…")
                        break
                except Exception:
                    pass
        if len(_problems) >= 3:
            break
    if _problems:
        import warnings
        warnings.warn(
            "\n[!]  MOJIBAKE DETECTED in content! The file has encoding corruption.\n"
            "   Run this to fix:  python fix_encoding.py\n"
            "   First problem: " + _problems[0]
        )
_check_encoding()

# ── Page-number marker for self-correcting TOC ──────────────────────────────
# Usage: after content changes, run the build TWICE. First pass captures page
# numbers; second pass uses them in the TOC.
# ══════════════════════════════════════════════════════════════════════════════
import json, os

_TOC_CACHE_PATH = os.path.join(os.path.dirname(__file__), '_toc_cache.json')

class _PageNum(Flowable):
    """Zero-height flowable that records the current page number when drawn."""
    _marks = {}
    def __init__(self, label):
        Flowable.__init__(self)
        self.label = label
        self.width = 0
        self.height = 0
    def wrap(self, aW, aH):
        return (0, 0)
    def draw(self):
        _PageNum._marks[self.label] = self.canv.getPageNumber()

def _load_page_cache():
    """Load cached page numbers from disk. Returns dict or empty if nonexistent."""
    try:
        with open(_TOC_CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_page_cache(marks):
    """Save page numbers to disk for the next build."""
    with open(_TOC_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(marks, f, indent=2)

_PAGE_CACHE = _load_page_cache()

def _get_page(label):
    """Return cached page number for a chapter label, or '?' if unknown."""
    p = _PAGE_CACHE.get(label)
    return str(p) if p is not None else "?"
# ══════════════════════════════════════════════════════════════════════════════

# ─── Color Palette (Black/charcoal bg, amber-gold accents, white text on dark) ─
GOLD       = colors.HexColor("#7A5C00")   # dark gold: rules, borders, subsection titles
DARK_GOLD  = colors.HexColor("#5A4200")   # deeper dark gold: secondary borders
DEEP_NAVY  = colors.HexColor("#111111")   # near-black: cover bg, header bars
DARK_BG    = colors.HexColor("#222222")   # dark gray: table category rows
MID_NAVY   = colors.HexColor("#1A1A1A")   # near-black: table header rows
LIGHT_BLUE = colors.HexColor("#1A1A1A")   # near-black: section titles on white bg
CREAM      = colors.HexColor("#FFFFFF")   # white: text on dark backgrounds
DARK_TEXT  = colors.HexColor("#1C1C1C")   # near-black: body text on white
SILVER     = colors.HexColor("#BBBBBB")   # light gray: grid lines, footer
RED_ACCENT = colors.HexColor("#8B2020")   # dark red: warnings
PURPLE_ACC = colors.HexColor("#444444")   # dark gray: notes
GREEN_ACC  = colors.HexColor("#1A1A1A")   # black
ALT_ROW    = colors.HexColor("#FBF8EE")   # faint warm tint: alt table rows

# ─── Styles ───────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles['BookTitle'] = ParagraphStyle(
        'BookTitle',
        fontName='Times-Bold',
        fontSize=36,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=8,
        leading=44,
    )
    styles['Subtitle'] = ParagraphStyle(
        'Subtitle',
        fontName='Times-Italic',
        fontSize=16,
        textColor=CREAM,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles['ChapterTitle'] = ParagraphStyle(
        'ChapterTitle',
        fontName='Times-Bold',
        fontSize=22,
        textColor=GOLD,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6,
        leading=26,
        borderPad=4,
    )
    styles['SectionTitle'] = ParagraphStyle(
        'SectionTitle',
        fontName='Times-Bold',
        fontSize=14,
        textColor=colors.HexColor("#5A4200"),   # dark gold — visible & rich on white
        spaceBefore=6,
        spaceAfter=2,
        leading=15,
    )
    styles['SubSection'] = ParagraphStyle(
        'SubSection',
        fontName='Times-Bold',
        fontSize=12,
        textColor=GOLD,
        spaceBefore=6,
        spaceAfter=2,
        leading=15,
    )
    styles['Body'] = ParagraphStyle(
        'Body',
        fontName='Times-Roman',
        fontSize=10,
        textColor=DARK_TEXT,
        spaceBefore=1,
        spaceAfter=2,
        leading=13,
        alignment=TA_JUSTIFY,
    )
    styles['BodyBold'] = ParagraphStyle(
        'BodyBold',
        fontName='Times-Bold',
        fontSize=10,
        textColor=DARK_TEXT,
        spaceBefore=2,
        spaceAfter=4,
        leading=14,
    )
    styles['Bullet'] = ParagraphStyle(
        'Bullet',
        fontName='Times-Roman',
        fontSize=10,
        textColor=DARK_TEXT,
        spaceBefore=1,
        spaceAfter=1,
        leading=13,
        leftIndent=16,
        bulletIndent=4,
    )
    styles['BulletBold'] = ParagraphStyle(
        'BulletBold',
        fontName='Times-Bold',
        fontSize=10,
        textColor=DARK_TEXT,
        spaceBefore=1,
        spaceAfter=2,
        leading=13,
        leftIndent=16,
        bulletIndent=4,
    )
    styles['SmallBullet'] = ParagraphStyle(
        'SmallBullet',
        fontName='Times-Roman',
        fontSize=9,
        textColor=DARK_TEXT,
        spaceBefore=1,
        spaceAfter=1,
        leading=12,
        leftIndent=28,
        bulletIndent=16,
    )
    styles['Flavor'] = ParagraphStyle(
        'Flavor',
        fontName='Times-Italic',
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        spaceBefore=4,
        spaceAfter=3,
        leading=13,
        alignment=TA_JUSTIFY,
        leftIndent=20,
        rightIndent=20,
    )
    styles['TableHeader'] = ParagraphStyle(
        'TableHeader',
        fontName='Times-Bold',
        fontSize=9,
        textColor=CREAM,
        alignment=TA_CENTER,
    )
    styles['TableCell'] = ParagraphStyle(
        'TableCell',
        fontName='Times-Roman',
        fontSize=9,
        textColor=DARK_TEXT,
        alignment=TA_LEFT,
        leading=12,
    )
    styles['TableCellCenter'] = ParagraphStyle(
        'TableCellCenter',
        fontName='Times-Roman',
        fontSize=9,
        textColor=DARK_TEXT,
        alignment=TA_CENTER,
        leading=12,
    )
    styles['TableSubHeader'] = ParagraphStyle(
        'TableSubHeader',
        fontName='Times-Bold',
        fontSize=9,
        textColor=DARK_TEXT,
        alignment=TA_CENTER,
        backColor=colors.HexColor('#D4D0C8'),
        leading=12,
    )
    styles['Warning'] = ParagraphStyle(
        'Warning',
        fontName='Times-Bold',
        fontSize=10,
        textColor=RED_ACCENT,
        spaceBefore=4,
        spaceAfter=4,
        leading=14,
        leftIndent=10,
    )
    styles['BoxText'] = ParagraphStyle(
        'BoxText',
        fontName='Times-Roman',
        fontSize=9,
        textColor=DARK_TEXT,
        spaceBefore=2,
        spaceAfter=2,
        leading=13,
    )
    styles['PageNum'] = ParagraphStyle(
        'PageNum',
        fontName='Times-Roman',
        fontSize=8,
        textColor=SILVER,
        alignment=TA_CENTER,
    )
    return styles

S = make_styles()

# ─── Helper builders ─────────────────────────────────────────────────────────
def h_rule(color=GOLD, thickness=1):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=2, spaceBefore=2)

def thin_rule():
    return HRFlowable(width="100%", thickness=0.5, color=SILVER, spaceAfter=2, spaceBefore=2)

def chapter(title):
    # Extract a short label for page-number tracking
    if title.startswith("Appendix"):
        label = title.split(':')[0]
    elif title == "Table of Contents":
        label = "Table of Contents"
    elif title == "Glossary of Terms":
        label = "Glossary of Terms"
    else:
        label = title.split(':')[0].strip()
    return [
        h_rule(GOLD, 2),
        Paragraph(title, S['ChapterTitle']),
        h_rule(GOLD, 1),
        Spacer(1, 3),
        _PageNum(label),
    ]

def section(title):
    return [thin_rule(), Paragraph(title, S['SectionTitle'])]

def subsection(title):
    return [Paragraph(title, S['SubSection'])]

def body(text):
    return Paragraph(text, S['Body'])

def bullet(text):
    return Paragraph(f"• {text}", S['Bullet'])

def bbullet(text):
    return Paragraph(f"• {text}", S['BulletBold'])

def sbullet(text):
    return Paragraph(f"– {text}", S['SmallBullet'])

def flavor(text):
    return Paragraph(f'"{text}"', S['Flavor'])

def sp(n=6):
    return Spacer(1, n)

def table_style(header_bg=MID_NAVY, alt_bg=colors.HexColor("#FBF8EE")):
    return TableStyle([
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('TEXTCOLOR', (0,0), (-1,0), CREAM),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,1), (-1,-1), 'Times-Roman'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, alt_bg]),
        ('GRID', (0,0), (-1,-1), 0.5, SILVER),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ])

# ─── Reinforced abilities splitter ──────────────────────────────────────────
REINFORCED_SEP = "\n<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"

def split_reinforced(ability_text):
    """Split ability text into (main_ability, reinforced_ability).
    
    Returns (main_text, reinforced_text) where reinforced_text may be empty.
    Strips '(Reinforced)' from ability names in the reinforced block.
    """
    idx = ability_text.find(REINFORCED_SEP)
    if idx == -1:
        return ability_text, ""
    main_text = ability_text[:idx]
    reinforced_text = ability_text[idx + len(REINFORCED_SEP):]
    # Remove "(Reinforced)" from ability names (format: "Name (Reinforced):")
    # Use a safer replacement that doesn't introduce tag imbalance in source
    reinforced_text = reinforced_text.replace(" (Reinforced):", ":")
    return main_text, reinforced_text


AB_COL_W = [0.75*inch, 5.6*inch]

def ability_table_style():
    """Return the standard TableStyle used for ability and reinforced boxes."""
    return TableStyle([
        ('BACKGROUND', (0,0), (0,-1), MID_NAVY),
        ('TEXTCOLOR', (0,0), (0,-1), CREAM),
        ('FONTNAME', (0,0), (0,-1), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('FONTNAME', (1,0), (1,-1), 'Times-Roman'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, SILVER),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (1,0), (1,-1), colors.white),
    ])

def render_ability_boxes(main_text, reinforced_text, story):
    """Append the ability table, and a reinforced table if present."""
    # Main ability box
    ab_row = [[Paragraph("Ability", S['TableHeader']), Paragraph(main_text, S['TableCell'])]]
    ab_t = Table(ab_row, colWidths=AB_COL_W)
    ab_t.setStyle(ability_table_style())
    story.append(ab_t)

    # Reinforced box (separate, below)
    if reinforced_text:
        story.append(sp(1))
        re_row = [[Paragraph("Reinforced\nAbilities", S['TableHeader']),
                   Paragraph(reinforced_text, S['TableCell'])]]
        re_t = Table(re_row, colWidths=AB_COL_W)
        re_t.setStyle(ability_table_style())
        story.append(re_t)

    # Separator after the ability block (match original h_rule after each entry)
    story.append(h_rule(GOLD, 0.5))

    story.append(h_rule(GOLD, 0.5))


def warning_box(text):
    """Return a red-bordered callout box with a bold WARNING header."""
    box_data = [
        [Paragraph("<b><font color='#8B2020'>⚠ IMPORTANT — TRACK YOUR POINT VALUES</font></b>", S['Warning'])],
        [Paragraph(text, S['BoxText'])],
    ]
    box = Table(box_data, colWidths=[6.3*inch])
    box.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.5, RED_ACCENT),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF5F5')),
        ('TOPPADDING', (0,0), (0,0), 6),
        ('BOTTOMPADDING', (0,0), (0,0), 2),
        ('TOPPADDING', (0,1), (-1,-1), 2),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return box

# ─── Page callbacks ───────────────────────────────────────────────────────────
def draw_outlined_text(canvas, text, x, y, font, size, fill_color, stroke_color, stroke_width=0.6, align='center', page_width=None):
    """Draw text with a stroke outline for dramatic effect."""
    canvas.saveState()
    canvas.setFont(font, size)
    canvas.setFillColor(fill_color)
    canvas.setStrokeColor(stroke_color)
    canvas.setLineWidth(stroke_width)
    canvas.setLineJoin(1)  # round joins
    # mode 2 = fill then stroke
    canvas._textRenderMode = 2
    if align == 'center' and page_width:
        canvas.drawCentredString(x, y, text)
    elif align == 'right':
        canvas.drawRightString(x, y, text)
    else:
        canvas.drawString(x, y, text)
    canvas.restoreState()

def cover_page(canvas, doc):
    w, h = letter
    canvas.saveState()

    # ── White background ──────────────────────────────────────────────────────
    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # ── Outer gold border (thick) ─────────────────────────────────────────────
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(3.5)
    canvas.rect(0.38*inch, 0.38*inch, w - 0.76*inch, h - 0.76*inch, fill=0, stroke=1)

    # ── Inner dark-gold border (thin) ─────────────────────────────────────────
    canvas.setStrokeColor(DARK_GOLD)
    canvas.setLineWidth(0.8)
    canvas.rect(0.52*inch, 0.52*inch, w - 1.04*inch, h - 1.04*inch, fill=0, stroke=1)

    # ── Decorative corner ticks ───────────────────────────────────────────────
    tk = 0.22 * inch
    b = 0.52 * inch
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(2)
    for (px, py) in [(b, b), (w-b, b), (b, h-b), (w-b, h-b)]:
        sx = tk if px < w/2 else -tk
        sy = tk if py < h/2 else -tk
        canvas.line(px, py, px+sx, py)
        canvas.line(px, py, px, py+sy)

    cx = w / 2

    # ── "GURPS:" ──────────────────────────────────────────────────────────────
    draw_outlined_text(canvas, "POWERED BY GURPS", cx, h - 1.9*inch,
                       'Times-Italic', 14,
                       fill_color=DARK_GOLD,
                       stroke_color=colors.black,
                       stroke_width=0.4, align='center', page_width=w)

    # ── "PATHWAYS" ────────────────────────────────────────────────────────
    draw_outlined_text(canvas, "PATHWAYS", cx, h - 2.6*inch,
                       'Times-Bold', 44,
                       fill_color=GOLD,
                       stroke_color=colors.black,
                       stroke_width=1.0, align='center', page_width=w)

    # Gold rule
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.5)
    canvas.line(cx - 1.6*inch, h - 2.9*inch, cx + 1.6*inch, h - 2.9*inch)

    # Subtitle lines
    canvas.setFont('Times-Italic', 13)
    canvas.setFillColor(colors.black)
    canvas._textRenderMode = 0
    canvas.drawCentredString(cx, h - 3.2*inch, "A Powered by GURPS Rulebook")
    canvas.drawCentredString(cx, h - 3.44*inch, "for the World of")

    # ── "LORD OF THE MYSTERIES" ───────────────────────────────────────────────
    draw_outlined_text(canvas, "LORD OF THE MYSTERIES", cx, h - 4.0*inch,
                       'Times-Bold', 26,
                       fill_color=GOLD,
                       stroke_color=colors.black,
                       stroke_width=0.7, align='center', page_width=w)

    # Second rule
    canvas.setStrokeColor(DARK_GOLD)
    canvas.setLineWidth(1)
    canvas.line(cx - 2.0*inch, h - 4.3*inch, cx + 2.0*inch, h - 4.3*inch)

    # ── Flavour text ──────────────────────────────────────────────────────────
    flavor_lines = [
        "Beyond the Fog lies a world of divine hierarchies both ancient and terrible.",
        "Fallen deities whose shattered power seeps into pathways for mortals to drink.",
        "Orthodox gods who watch their faithful from realms of cold authority.",
        "Evil gods who hunger in the dark between prayers.",
        "And the Outer Gods — vast, nameless, incomprehensible —",
        "whose attention alone can break a mind.",
        "",
        "To become a Beyonder is to step into that hierarchy.",
        "To climb it is to risk becoming something that is no longer human.",
    ]
    canvas.setFont('Times-Italic', 12.5)
    canvas.setFillColor(colors.HexColor("#222222"))
    canvas._textRenderMode = 0
    fl_y = h - 4.72*inch
    for line in flavor_lines:
        if line:
            canvas.drawCentredString(cx, fl_y, line)
        fl_y -= 18

    # Third rule
    rule3_y = fl_y - 0.12*inch
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.5)
    canvas.line(cx - 1.5*inch, rule3_y, cx + 1.5*inch, rule3_y)

    # ── Credits ───────────────────────────────────────────────────────────────
    credits = [
        "Based on the Chinese web novel series by Cuttlefish That Loves Diving",
        "Powered by GURPS",
    ]
    canvas.setFont('Times-Roman', 8.5)
    canvas.setFillColor(colors.HexColor("#444444"))
    cred_y = rule3_y - 0.25*inch
    for line in credits:
        canvas.drawCentredString(cx, cred_y, line)
        cred_y -= 13

    canvas.restoreState()

def normal_page(canvas, doc):
    w, h = letter
    canvas.saveState()
    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    # Header bar
    canvas.setFillColor(DEEP_NAVY)
    canvas.rect(0, h-0.55*inch, w, 0.55*inch, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Times-Italic', 9)
    canvas.drawString(0.6*inch, h-0.32*inch, "Powered by GURPS: Pathways — Lord of the Mysteries")
    canvas.setFont('Times-Roman', 9)
    canvas.drawRightString(w-0.6*inch, h-0.32*inch, f"Page {doc.page}")
    # Gold line under header
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1)
    canvas.line(0.5*inch, h-0.56*inch, w-0.5*inch, h-0.56*inch)
    # Footer
    canvas.setFillColor(DEEP_NAVY)
    canvas.rect(0, 0, w, 0.4*inch, fill=1, stroke=0)
    canvas.setStrokeColor(GOLD)
    canvas.line(0.5*inch, 0.4*inch, w-0.5*inch, 0.4*inch)
    canvas.restoreState()

# Output folder
import os
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Build document ──────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        os.path.join(OUTPUT_DIR, "Mr.Worms LOM TTRPG Rulebook v6.9d.pdf"),
        pagesize=letter,
        rightMargin=0.65*inch,
        leftMargin=0.65*inch,
        topMargin=0.9*inch,
        bottomMargin=0.65*inch,
    )

    story = []

    # ── COVER — drawn entirely on canvas via cover_page() callback ────────────
    story.append(Spacer(1, 1))  # minimal spacer; canvas draws everything
    story.append(PageBreak())

    # ── TABLE OF CONTENTS ─────────────────────────────────────────────────────
    story += chapter("Table of Contents")
    toc_data = [
        ["Ch.", "Title", "Contents", "Page"],
        ["1",     "Introduction",        "The World of Loen, The Beyonder System Overview, How to Use This Book",                          _get_page("Chapter 1")],
        ["2",     "Core Rules",          "The Success Roll, Attributes, Secondary Characteristics, Quick Contests, Skill Defaults",        _get_page("Chapter 2")],
        ["3",     "Character Creation",  "Point Budget, Attributes, Advantages, Disadvantages, Skills, Complete Skill List",               _get_page("Chapter 3")],
        ["4",     "Spirituality",        "SPI Attribute, SPI by Pathway, Spiritual Intuition, Spiritual Perception, Spirit Vision, Ritualistic Magic, Divination Arts", _get_page("Chapter 4")],
         ["5",     "Combat",              "Initiative, Maneuvers, Active Defenses, Ranged Combat, Damage & Injury, Healing & Recovery, Spirit Body Damage, Fright Checks", _get_page("Chapter 5")],
         ["6",     "The Beyonder System", "Beyonders, Sequence Ladder, Digestion, CoR, Advancement, Rampagers, Society, Mystical Items", _get_page("Chapter 6")],
        ["6.5",   "Divination Arts",     "Divination Arts Skill, Methods & Tools, Performing a Divination, Awareness & Countermeasures, Anti-Divination Techniques", _get_page("Chapter 6.5")],
        ["7",     "Ritualistic Magic",   "Core Philosophy, Primary Skill, Ritual Resolution, Power Sources, Effect Categories, Failure & Consequences, Sequence & Rituals, Sample Rituals", _get_page("Chapter 7")],
        ["7.5",    "Summoning Spiritual Creatures", "Incantations, Rituals, Contracts, Creatures",          _get_page("Chapter 7.5")],
        ["7.6",    "Spirit Vision Guide", "Ether Body Colors, Astral Projection Colors, Pathway Differences, Using Spirit Vision",         _get_page("Chapter 7.6")],
        ["8",     "Equipment & Starting Wealth",  "Currency Conversion, Starting Wealth, Weapons, Equipment, Legal Licenses, Hired Allies",          _get_page("Chapter 8")],
        ["9",     "Sequence 9 Potion Effects",  "All 22 Pathways — Stats, Skills & Abilities Upon First Consumption",                             _get_page("Chapter 9")],
        ["10",    "Sequence 8 Potion Effects",  "All 22 Pathways — Stats, Skills & Abilities at Sequence 8",                                      _get_page("Chapter 10")],
        ["11",    "Sequence 7 Potion Effects",  "All 22 Pathways — Stats, Skills & Abilities at Sequence 7",                                      _get_page("Chapter 11")],
        ["12",    "Sequence 6 Potion Effects",  "All 22 Pathways — Stats, Skills & Abilities at Sequence 6",                                      _get_page("Chapter 12")],
        ["13",    "Boon Granting",              "What Is a Boon, Requirements, The Boon Granting Ritual, Consequences & Risks",                 _get_page("Chapter 13")],
        ["14",    "Non-Standard Pathways",      "Boon-Granted Paths from Outer Deities — Dancer, Patient, Shaman, Dreamless, Tramp, Villain, Scrooge, Broker, Initiator, Astronomy Aficionado", _get_page("Chapter 14")],
        ["15",    "Non-Standard Sequence 8",    "Secretary, Reporter, Sex Addict, Alms Monk, Musician — Stats, Skills & Abilities", _get_page("Chapter 15")],
         ["App. A","Quick Reference Tables",     "Core Mechanic, Character Creation Summary, Combat, Spiritual Skills, CoR & Digestion",    _get_page("Appendix A")],
        ["App. B","The Political World",        "Nations, Factions, Economy, The Great Game, Year 1349 Timeline",                                          _get_page("Appendix B")],
        ["App. C","Orthodox Churches & Secret Organizations",       "Seven Orthodox Churches, Enforcement Divisions, Church Relations, Secret Organizations",          _get_page("Appendix C")],
        ["",      "Glossary of Terms",  "Quick-reference glossary of setting-specific and mechanical terms",                                    _get_page("Glossary of Terms")],
    ]
    toc_data[0] = [Paragraph(c, S['TableHeader']) for c in toc_data[0]]
    for i in range(1, len(toc_data)):
        row = toc_data[i]
        toc_data[i] = [
            Paragraph(str(row[0]), S['TableCellCenter']),
            Paragraph(row[1], S['BodyBold']),
            Paragraph(row[2], S['TableCell']),
            Paragraph(row[3], S['TableCellCenter']),
        ]
    t = Table(toc_data, colWidths=[0.55*inch, 1.45*inch, 3.9*inch, 0.4*inch])
    t.setStyle(table_style())
    story.append(t)
    story.append(PageBreak())

    # ── QUICK START FOR NEW PLAYERS ──────────────────────────────────────────
    story += chapter("Quick Start for New Players")
    story.append(body(
        "If you have never played a tabletop roleplaying game or used GURPS before, start here. "
        "This page gives you everything you need to begin. The rest of the book is reference material "
        "for when you need to look something up."
    ))
    story.append(sp(3))

    story += section("The Core Mechanic (Chapter 2)")
    story.append(body(
        "Roll <b>3d6</b>. If the total is <b>equal to or under</b> your skill or stat number, "
        "you succeed. That is the only rule you need to memorise."
    ))
    story.append(bullet("<b>Critical Success:</b> Roll 3 or 4 — brilliant result"))
    story.append(bullet("<b>Critical Failure:</b> Roll 17 or 18 — disaster"))
    story.append(bullet("<b>Combat Critical:</b> Crit on an attack roll = double damage"))
    story.append(sp(2))

    story += section("Making a Character (Chapter 3)")
    story.append(body(
        "You have <b>70 points</b> to build your character. Four core stats start at 9:"
    ))
    story.append(bullet("<b>ST</b> (Strength) — HP, melee damage, carrying capacity"))
    story.append(bullet("<b>DX</b> (Dexterity) — agility, aim, physical skills"))
    story.append(bullet("<b>IQ</b> (Intelligence) — knowledge, social skills, perception"))
    story.append(bullet("<b>HT</b> (Health) — stamina (FP), endurance, survival"))
    story.append(body(
        "Spend points to raise them. <b>Advantages</b> are special traits (talent, training, luck). "
        "<b>Disadvantages</b> are flaws that give you extra points."
    ))
    story.append(sp(2))

    story += section("Skills (Chapter 3)")
    story.append(body(
        "Skills are what your character knows how to do. Each skill is based on a stat "
        "(DX, IQ, etc.) and has a difficulty: Easy, Average, Hard, or Very Hard."
    ))
    story.append(body(
        "<b>Why buy them?</b> Without training, you roll at a harsh default (e.g. Guns at DX-4 = "
        "target number 5 — you almost never hit). Spending a few points raises you to 12, 14, or "
        "higher — now you are reliably effective. Your Sequence potion also grants free skill "
        "bonuses (see Sequence chapters), so your Beyonder comes pre-equipped with relevant training."
    ))
    story.append(sp(2))

    story += section("Secondary Attributes (Chapter 3)")
    story.append(body("Derived automatically from your core stats:"))
    story.append(bullet("<b>HP</b> (Hit Points) = ST — how much damage you can take"))
    story.append(bullet("<b>FP</b> (Fatigue Points) = HT — energy for special moves and spells"))
    story.append(bullet("<b>Will</b> = IQ — mental resistance and courage"))
    story.append(bullet("<b>Per</b> (Perception) = IQ — noticing things"))
    story.append(bullet("<b>Basic Speed</b> = (HT+DX)/4 — who acts first in combat"))
    story.append(bullet("<b>Basic Move</b> = Speed (drop fractions) — how far you move per second"))
    story.append(bullet("<b>SPI</b> (Spirituality) — starts at 0 for mortals; see below"))
    story.append(sp(2))

    story += section("Sequence 9 Potions (Chapters 4, 6 & 9)")
    story.append(body(
         "This is the heart of the game. A <b>Sequence 9 potion</b> is the first step onto a "
         "<b>Pathway</b> (a supernatural class: Seer, Hunter, Sailor, Warrior, etc. — each Pathway is named after its Sequence 0 god, e.g. the Seer belongs to the Fool Pathway)."
    ))
    story.append(body("When you drink one:"))
    story.append(bullet("Your <b>SPI</b> jumps from 0 to as high as +9 for spiritual pathways"))
    story.append(bullet("You gain <b>stat boosts, skill bonuses, and a unique ability</b>"))
    story.append(bullet("You begin the <b>Acting Method</b> — behave like your potion's role to digest it safely"))
    story.append(body(
        "There are <b>22 Pathways</b> across three categories: "
        "<b>Mystical</b> (high SPI — Seer, Sleepless, Monster), "
        "<b>Reality-leaning</b> (low SPI — Hunter, Warrior, Savant), "
        "and <b>Balanced</b> (mid SPI — Sailor, Apothecary). "
        "Your first potion choice defines your entire character."
    ))
    story.append(sp(2))

    story += section("How the Game Flows (Chapter 2)")
    story.append(body(
        "1. The GM describes the scene and situation.<br/>"
        "2. You say what your character does.<br/>"
        "3. If the outcome is uncertain, the GM says \"roll X\" — usually a skill or stat.<br/>"
        "4. Roll 3d6. Equal to or under your target number = success.<br/>"
        "5. The GM narrates what happens next."
    ))
    story.append(sp(3))

    story.append(sp(3))

    story += chapter("Chapter 1: Introduction — The Fog and What Lies Beyond")
    story.append(flavor(
        "Above the gray city of Backlund, gaslit streets wind between factories belching coal smoke "
        "and Gothic spires. The newspapers speak of revolution, empire, and science. They do not speak "
        "of the Beyonders — those who have drunk from the pathways of ancient deities and walk among mortals "
        "wearing human faces."
    ))
    story.append(sp(3))

    story += section("The World of Loen")
    story.append(body(
        "Lord of the Mysteries is set in a world equivalent to the Victorian/Edwardian era of early industrial "
        "capitalism — steam engines, gas lamps, newspapers, revolvers, and class warfare. But beneath this "
        "mundane surface runs a hidden current of profound supernatural power: the Beyonder system, wherein "
        "mortals who drink alchemical potions — derived from the distilled essence of fallen deities — gain "
        "supernatural abilities and walk the path toward divinity itself."
    ))
    story.append(body(
        "The primary setting is the Kingdom of Loen, centered on its teeming capital Backlund. "
        "The city is divided sharply by class: the wealthy West Borough with its parks and mansions; "
        "the middle-class Midtown with its shops and offices; and the dangerous East Borough with its "
        "slums, factories, and dockyards. Characters typically begin in East Borough or Midtown, scrabbling "
        "for survival before the supernatural finds them."
    ))
    story.append(sp(3))

    story += section("The Beyonder System")
    story.append(body(
        "In the hidden world of Beyonders, humans consume carefully crafted potions to walk the path "
        "of supreme ascension, unlocking occult powers beyond ordinary comprehension. "
        "Twenty-two pathways guide this journey, each beginning at Sequence 9. The lower the sequence, "
        "the greater the Beyonder's power. "
        "Those who descend all the way to Sequence 0 attain abilities that rival the gods themselves, "
        "a transcendence so rare and extraordinary that it is known simply as the path of the divine."
    ))
    story.append(body("To advance, a Beyonder must:"))
    story.append(bullet("Acquire the correct potion formula for the next sequence"))
    story.append(bullet("Gather the required ingredients"))
    story.append(bullet("Brew or purchase the completed potion"))
    story.append(bullet("Consume it and succeed at a <b>Potion Consumption Roll</b> — failure means death"))
    story.append(bullet("Act in accordance with the pathway's nature to safely digest the potion"))
    story.append(sp(3))
    story.append(body(
        "This rulebook uses GURPS 4th Edition as its mechanical foundation, adding custom "
        "attributes and rules for the Beyonder progression system as well as changing GURPS rules to "
        "accommodate the setting more faithfully."
    ))

    story += section("What Is a Roleplaying Game?")
    story.append(body(
        "If you have never played a tabletop roleplaying game (TTRPG) before, here is what you need to know. "
        "This book is not a board game with a fixed board and pieces. It is a set of tools for telling a "
        "collaborative story — one where you are a player, not just a spectator."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>You play a character.</b> You create a person in this world — a factory worker, a reporter, a "
        "street thief — and decide what they say and do, just like an actor playing a role in a play. "
        "Your character's abilities are listed on a <b>character sheet</b>: numbers that say how strong, "
        "smart, or spiritually sensitive they are, and what skills they have learned. You do not need to "
        "memorise these numbers — the sheet is your reference."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>The Game Master (GM) runs everything else.</b> One person at the table — the GM — plays the "
        "role of the world itself. They describe the foggy streets of Backlund, play the shopkeepers and "
        "villains you meet, and decide what happens when you take risks. The GM is not your enemy. Their "
        "job is to make the story exciting and fair."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>The dice decide uncertainty.</b> When your character attempts something where failure is "
        "interesting — picking a lock, dodging a bullet, lying to a detective — you roll dice to see "
        "if you succeed. This book uses three six-sided dice (3d6). You add or subtract modifiers based "
        "on how hard the task is and how skilled your character is, then roll. Equal to or under your "
        "target number = success."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>There is no 'winning'.</b> The goal is not to beat the game. The goal is to tell a compelling "
        "story together. Your character might fail, get hurt, or even die — and those moments often make "
        "the best stories. The rules exist to keep things fair and surprising, not to restrict what you "
        "can try."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>If you are a first-time player:</b> Do not try to learn every rule before you start. Learn "
        "what your character can do, learn how to roll a success check, and trust your GM to handle the "
        "rest. The rules in this book will make more sense once you have seen them in action."
    ))
    story.append(sp(3))

    story += section("How to Use This Book")
    story.append(body(
        "This book is a complete rulebook. You will need the GURPS Basic Set Characters and Campaigns "
        "(4th Edition) for full rules. This book provides everything specific to the LOTM setting: "
        "the new SPI attribute, Beyonder mechanics, setting-appropriate templates, and a curated skill and "
        "equipment list. Standard GURPS rules apply unless this book explicitly overrides them."
    ))
    story.append(body(
        "<b>Campaign Tone:</b> Start gritty and grounded. Characters begin as ordinary mortals — barely "
        "scraping by in a harsh industrializing city — and only encounter the supernatural after several "
        "sessions of investigation. The horror of discovering Beyonders exists should be earned, not assumed. "
        "The setting operates at <b>Tech Level 5</b> (Early Industrial Age): steam engines, railways, revolvers, "
        "gas lamps, telegraphs, and early medicine. Magic and industry exist side by side, but most people "
        "only see one of them."
    ))


    story.append(PageBreak())
    story += chapter("Chapter 2: Core Rules")

    story += section("How the Game Works")
    story.append(body(
        "A session of Pathways plays out as a conversation between the Game Master and the players. "
        "Here is the basic loop that drives the game:"
    ))
    story.append(sp(2))
    story.append(body(
        "<b>1. The GM sets the scene.</b> \"You step off the train at Backlund Central Station. Coal smoke "
        "hangs in the air. A newsboy shouts about the latest murder in East Borough. A woman in black "
        "glances at you from across the platform, then disappears into the crowd.\""
    ))
    story.append(sp(2))
    story.append(body(
        "<b>2. You say what your character does.</b> \"I want to follow that woman.\" "
        "\"I'll buy a newspaper and keep watch from the bench.\" "
        "\"I check if anyone else is watching her.\" You are in control of your character's choices — "
        "the world responds to what you do."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>3. The GM tells you what happens — and when to roll.</b> If your action is something your "
        "character could simply do (walk across the street, pick up an object, ask a question), it just "
        "happens. If the outcome is uncertain and the stakes are interesting — picking a locked door, "
        "spotting a hidden follower, lying to a suspicious cop — the GM calls for a <b>success roll</b>."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>4. Roll 3d6 and check your target number.</b> Your character sheet tells you the relevant "
        "number — a skill like Stealth 12, or an attribute like Perception 10. Roll three six-sided dice, "
        "add them up. If the total is equal to or less than your target number, you succeed. The "
        "difference between your roll and your target is your <b>margin of success</b> — the bigger, the better."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>5. The GM narrates the result.</b> Success means you do what you intended, possibly with extra "
        "benefits. Failure means something goes wrong — you slip, you get caught, you learn the wrong "
        "information. Sometimes failure is more interesting than success. Either way, the story moves forward."
    ))
    story.append(sp(3))
    story.append(body(
        "<b>Example:</b> Your character tries to follow the woman through a crowded market without being "
        "noticed. The GM says \"Roll Stealth — 3d6, target 12.\" You roll a 7 — success by 5! The GM "
        "says: \"You weave through the crowd effortlessly. She never looks back. You see her slip into a "
        "doorway marked with a brass compass — a séance parlor.\" This is how the entire game flows: "
        "describe, act, roll, narrate, repeat."
    ))
    story.append(sp(3))

    story += section("The Success Roll")
    story.append(body(
        "All skill and attribute checks use the same mechanic: roll 3d6 and compare to your target number. "
        "Roll equal to or under your skill/attribute to succeed. Margins matter — the degree of success or "
        "failure often determines quality of outcome."
    ))
    story.append(bullet("<b>Critical Success:</b> Roll of 3 or 4 (always succeeds brilliantly)"))
    story.append(bullet("<b>Critical Success in Combat:</b> A critical success on an attack roll deals double damage."))
    story.append(bullet("<b>Success by 0–2:</b> Barely succeeded"))
    story.append(bullet("<b>Success by 3–4:</b> Clean success"))
    story.append(bullet("<b>Success by 5+:</b> Exceptional result"))
    story.append(bullet("<b>Failure by 1–2:</b> Barely failed"))
    story.append(bullet("<b>Critical Failure:</b> Roll of 17 or 18, or fail by 10+"))
    story.append(sp(3))

    story += section("The Four Buyable Attributes")
    story.append(body(
        "All characters are defined by six core stats, but only four of them can be raised with character "
        "points. In this campaign, all mortal characters begin with every attribute at <b>9</b> and receive "
        "no points back for this baseline. Points are spent on top of the base 9. Raising attributes follows "
        "an <b>exponential cost curve</b> — each level costs more than the level before it."
    ))
    story.append(body(
        "See the <b>Attribute Cost Table</b> in <b>Chapter 3: Character Creation</b> for the full point costs."
    ))
    story.append(Paragraph(
        "* Spirituality (SPI) is a separate spiritual stat — it begins at 0 for all mortals and ",
        ParagraphStyle('note', fontName='Times-Italic', fontSize=9, textColor=PURPLE_ACC)
    ))
    story.append(Paragraph(
        "  cannot be raised by points. Only Beyonder potions, supernatural events, or certain rituals",
        ParagraphStyle('note', fontName='Times-Italic', fontSize=9, textColor=PURPLE_ACC)
    ))
    story.append(Paragraph(
        "  can increase it. See Chapter 4 for full rules.",
        ParagraphStyle('note', fontName='Times-Italic', fontSize=9, textColor=PURPLE_ACC)
    ))
    story.append(sp(3))

    story += section("Attribute Scale Reference")
    scale_data = [
        ["Score", "Descriptor", "Examples"],
        ["6–7", "Impaired", "Severe disability; below functional average"],
        ["8", "Below Average", "Noticeable weakness; many common tasks are difficult"],
        ["9", "Average", "Typical person; where all mortal characters begin"],
        ["10", "Above Average", "High side of able-bodied; good adventurer baseline"],
        ["11", "Notable", "Brawny / Deft / Brilliant / Resilient — top 15% of population"],
        ["12", "Exceptional", "Highest likely on street; strongly defines a character"],
        ["13", "Remarkable", "Celebrated talent; smartest person in a large city"],
        ["14", "World-Class", "Historical record-holders; one-in-a-million individuals"],
        ["15+", "Transcendent", "Beyond ordinary human limits; seen in specific pathways and sequences"],
    ]
    scale_data[0] = [Paragraph(c, S['TableHeader']) for c in scale_data[0]]
    for i in range(1, len(scale_data)):
        scale_data[i] = [Paragraph(c, S['TableCellCenter']) if j == 0 else Paragraph(c, S['TableCell'])
                         for j, c in enumerate(scale_data[i])]
    sc_t = Table(scale_data, colWidths=[0.65*inch, 1.2*inch, 4.45*inch])
    sc_t.setStyle(table_style())
    story.append(sc_t)
    story.append(sp(3))

    story += section("What the Numbers Mean")
    story.append(body(
        "If you are new to GURPS, here is how to read the numbers on your character sheet in plain English."
    ))
    story.append(sp(1))
    skill_mean_data = [
        ["Your Roll Target", "What It Means in Play"],
        ["6 or less", "Almost impossible for an untrained person. Only attempt if you have no other choice."],
        ["7–8", "Poor odds. 1 in 6 to 1 in 4 chance. A desperate gambit."],
        ["9", "About a 50/50 chance. Average person doing something unfamiliar."],
        ["10", "Slightly better than even. Things might go your way."],
        ["11–12", "Solid odds (63–74%). A trained professional at work."],
        ["13–14", "Very reliable (84–91%). You are good at this — visibly so."],
        ["15–16", "Expert territory (95–98%). You rarely fail at routine tasks."],
        ["17–18", "Master level (99%+). Failure is a genuine surprise."],
    ]
    skill_mean_data[0] = [Paragraph(c, S['TableHeader']) for c in skill_mean_data[0]]
    for i in range(1, len(skill_mean_data)):
        skill_mean_data[i] = [Paragraph(c, S['TableCell']) for c in skill_mean_data[i]]
    story.append(Table(skill_mean_data, colWidths=[1.5*inch, 4.8*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "Think of it this way: every point matters. Raising your Stealth from 11 to 12 might not sound "
        "like much, but it takes your success rate from 63% to 74% — a meaningful difference every time "
        "you hide in the shadows. And because GURPS uses margins of success, a higher skill also means "
        "you succeed <i>by more</i> when you do roll well."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Modifiers change your target number.</b> If the GM says \"it is dark, -2 to Stealth\", and your "
        "Stealth is 12, you now need to roll 10 or less. That changes a 74% chance to a 50% chance. "
        "This is why conditions matter — darkness, cover, distractions, and tools all affect your odds."
    ))
    story.append(sp(3))

    story += section("Secondary Characteristics")
    story.append(body("Derived from primary attributes at their starting values of 9:"))
    sec_data = [
        ["Characteristic", "Base Formula", "Cost to Modify"],
        ["HP (Hit Points)", "= ST (9)", "±2 pts per level"],
        ["Will", "= IQ (9)", "±5 pts per level"],
        ["Perception (Per)", "= IQ (9)", "±5 pts per level"],
        ["FP (Fatigue Points)", "= HT (9)", "±3 pts per level"],
        ["Spirituality", "= SPI (0)", "Fixed at 0; see Chapter 4"],
         ["CoR", "Current: 0 / Max: Will", "Tracked in play; never bought"],
        ["Basic Speed", "= (HT + DX) / 4 = 4.50", "±5 pts per 0.25"],
        ["Basic Move", "= Basic Speed rounded down = 4", "±5 pts per level"],
        ["Digestion %", "0% (mortals N/A)", "Tracked through acting"],
    ]
    sec_data[0] = [Paragraph(c, S['TableHeader']) for c in sec_data[0]]
    for i in range(1, len(sec_data)):
        sec_data[i] = [Paragraph(c, S['TableCell']) for c in sec_data[i]]
    sec_t = Table(sec_data, colWidths=[1.5*inch, 2.0*inch, 2.8*inch])
    sec_t.setStyle(table_style())
    story.append(sec_t)
    story.append(sp(3))

    story += subsection("Burning FP & SPI to Modify Rolls")
    story.append(body(
        "You can push yourself beyond normal limits by spending Fatigue or Spirituality. "
        "This represents a surge of effort — straining your muscles or focusing your spiritual energy."
    ))
    story.append(body(
        "<b>FP -> Physical Rolls.</b> Spend 1 FP to gain +1 on any roll based on ST, DX, or HT "
        "(attack rolls, dodging, climbing, lifting, etc.). You may use this <b>after</b> seeing the "
        "result. Max +5 per roll."
    ))
    story.append(body(
        "<b>SPI -> Mystical Rolls.</b> Spend 1 SPI to gain +1 on any SPI-based or supernatural skill "
        "roll (Ritualistic Magic, Spiritual Perception, Occultism vs. Beyonder phenomena, etc.). "
        "You may use this <b>after</b> seeing the result. There is no cap — you may spend as much SPI as you have."
    ))
    story.append(body(
        "You cannot spend both FP and SPI on the same roll."
    ))
    story.append(sp(3))

    story += section("Quick Contests")
    story.append(body(
        "When two characters directly oppose each other — one trying to deceive while the other "
        "tries to detect the lie, one grappling while the other tries to break free — both sides "
        "roll against their relevant skill or attribute. The winner is the one who succeeds by "
        "the larger margin. Ties go to the defender (the one resisting the action)."
    ))
    qc_data = [
        ["Situation", "Attacker Rolls", "Defender Rolls"],
        ["Deception vs. detection",     "Fast-Talk or Acting", "Detect Lies or Per"],
        ["Grapple vs. escape",          "Wrestling",           "ST or Escape"],
        ["Intimidation vs. resistance", "Intimidation",        "Will"],
        ["Ritual effect vs. target",    "Ritualistic Magic",   "Will or HT"],
        ["Pursuit on foot",             "Running",             "Running"],
        ["Beyonder ability vs. target", "Ability roll",        "Will or HT (as specified)"],
    ]
    qc_data[0] = [Paragraph(c, S['TableHeader']) for c in qc_data[0]]
    for i in range(1, len(qc_data)):
        qc_data[i] = [Paragraph(c, S['TableCell']) for c in qc_data[i]]
    story.append(Table(qc_data, colWidths=[2.2*inch, 1.8*inch, 2.3*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>If both succeed:</b> the one with the higher margin wins. "
        "<b>If both fail:</b> nothing happens — try again next round if the situation allows. "
        "<b>If one succeeds and one fails:</b> the one who succeeded wins outright. "
        "<b>Ties always go to the defender.</b>"
    ))
    story.append(sp(4))

    story += section("Skill Defaults")
    story.append(body(
        "You can attempt most skills even without training. This is called using the <b>default</b>. "
        "Defaults are always worse than trained use — they represent someone fumbling through "
        "something they have never formally learned."
    ))
    story.append(sp(2))
    sd_data = [
        ["Skill Difficulty", "Untrained Default"],
        ["Easy",      "Attribute - 4"],
        ["Average",   "Attribute - 5"],
        ["Hard",      "Attribute - 6"],
        ["Very Hard", "No default — cannot attempt untrained"],
    ]
    sd_data[0] = [Paragraph(c, S['TableHeader']) for c in sd_data[0]]
    for i in range(1, len(sd_data)):
        sd_data[i] = [Paragraph(c, S['TableCellCenter']) for c in sd_data[i]]
    story.append(Table(sd_data, colWidths=[1.8*inch, 4.5*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Example:</b> A character with IQ 9 (the campaign baseline) tries to pick a lock "
        "(Lockpicking, IQ/Average) without any training. Their default is IQ - 5 = 4. They need "
        "to roll 4 or under on 3d6. That is very unlikely — training matters."
    ))
    story.append(body(
        "Some skills have no default at all — Very Hard skills and any skill the GM rules requires "
        "specialist knowledge before you can even attempt it (surgery, ritual magic, operating a "
        "steam locomotive). If a skill has no default, failure is automatic and the GM will say so "
        "before you waste the attempt."
    ))
    story.append(sp(3))

    story += chapter("Chapter 3: Character Creation")

    story.append(body(
        "Characters begin as ordinary mortals on the verge of encountering the supernatural. "
        "They are not heroes — yet. They are factory workers, street thieves, journalists, and soldiers "
        "who will soon stumble into a world that should not exist."
    ))
    story.append(sp(3))

    story += section("How Character Creation Works")
    story.append(body(
        "GURPS 4th Edition uses a unified point-buy system. Every character is built from the same "
        "currency — Character Points — spent on four things: <b>Attributes</b>, <b>Advantages</b>, "
        "<b>Disadvantages</b> (which give points back), and <b>Skills</b>. There are no classes, no "
        "levels, and no pre-set templates you are locked into. You spend points where they matter for "
        "your concept and leave the rest."
    ))
    story.append(sp(3))
    story.append(body(
        "The standard GURPS process, in order, is:"
    ))
    story.append(bullet("<b>1. Choose a concept.</b> Know what your character does and how they survive."))
    story.append(bullet("<b>2. Set Attributes.</b> ST, DX, IQ, HT, and SPI. These are your raw capabilities — expensive to raise, but they underpin everything else."))
    story.append(bullet("<b>3. Buy Advantages.</b> Innate gifts, unusual training, and social assets. Budget carefully."))
    story.append(bullet("<b>4. Take Disadvantages.</b> Flaws, obligations, and burdens. They give points back and create story hooks. Optional — up to -40 pts worth."))
    story.append(bullet("<b>5. Buy Skills.</b> The bulk of your points go here. Skills are what you actually do in play."))
    story.append(bullet("<b>6. Record Secondary Characteristics.</b> HP, FP, Basic Speed, Basic Move, Perception, and Will are all derived automatically from your attributes."))
    story.append(sp(3))

    story += subsection("Pathways — Attribute Rules")
    story.append(body(
        "In a standard GURPS campaign, attributes default to 10 and the full point cost applies from "
        "the first level. <b>Pathways campaigns use a different baseline.</b> All starting characters "
        "are ordinary people — not exceptional by birth — and their four buyable attributes (ST, DX, IQ, HT) "
        "begin at <b>9</b>. You do not receive any points back for this lower starting value. It is simply "
        "the human norm for this setting."
    ))
    story.append(sp(3))
    story.append(body(
        "Raising attributes follows an <b>exponential cost curve</b> — each level costs more than the "
        "level before it. The first raise (9 to 10) costs the base rate. Each subsequent raise doubles "
        "the cost of the previous raise. This makes high attributes genuinely expensive, encouraging "
        "broad competence over min-maxing a single stat."
    ))
    story.append(sp(2))
    attr_cost_data = [
        ["Attribute", "9->10", "10->11", "11->12", "12->13", "13->14"],
        ["ST (Strength)",   "10 pts", "20 pts", "40 pts", "80 pts", "160 pts"],
        ["DX (Dexterity)",  "20 pts", "40 pts", "80 pts", "160 pts", "320 pts"],
        ["IQ (Intelligence)","20 pts","40 pts", "80 pts", "160 pts", "320 pts"],
        ["HT (Health)",     "10 pts", "20 pts", "40 pts", "80 pts", "160 pts"],
    ]
    attr_cost_data[0] = [Paragraph(c, S['TableHeader']) for c in attr_cost_data[0]]
    for i in range(1, len(attr_cost_data)):
        attr_cost_data[i] = [Paragraph(attr_cost_data[i][j],
            S['TableCellCenter'] if j >= 1 else S['TableCell']) for j in range(6)]
    story.append(Table(attr_cost_data, colWidths=[1.3*inch]+[0.7*inch]*5,
                       style=table_style()))
    story.append(sp(3))
    story.append(body(
        "<b>Example — DX 11:</b> 9->10 costs 20 pts, 10->11 costs 40 pts. Total: <b>60 pts</b> for DX 11."
    ))
    story.append(body(
        "<b>Example — ST 12:</b> 9->10 costs 10 pts, 10->11 costs 20 pts, 11->12 costs 40 pts. "
        "Total: <b>70 pts</b> for ST 12."
    ))
    story.append(body(
        "A character who leaves an attribute at 9 pays nothing and receives no refund — "
        "9 is simply the starting point, not a discount."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Spirituality (SPI)</b> is separate. All mortals begin at <b>SPI 0</b>, and it <b>cannot</b> "
        "be raised with character points. SPI increases only through Beyonder potions, supernatural events, "
        "or certain rituals. The amount of SPI granted depends on the pathway's spiritual affinity — mysticism-leaning "
        "pathways (e.g., Seer, Sleepless, Monster) grant as much as +9, while reality-leaning pathways "
        "(e.g., Hunter, Warrior, Savant) grant as little as +1. See Chapter 4 for full SPI rules."
    ))
    story.append(sp(3))

    story += section("Point Budget")
    budget_data = [
        ["Category", "Points", "Notes"],
        ["Starting Total", "70 pts", "All characters begin with 70 points to spend"],
        ["Attributes", "0 pts (fixed)", "All attributes start at 9; no refund given"],
        ["Advantages", "10–15 pts typical", "Define your character's edge; budget carefully"],
        ["Disadvantages", "0 to -40 pts", "Maximum -40 pts; not required — take only what fits your character"],
        ["Skills", "~50 pts typical", "Core of your character's competencies"],
    ]
    budget_data[0] = [Paragraph(c, S['TableHeader']) for c in budget_data[0]]
    for i in range(1, len(budget_data)):
        budget_data[i] = [Paragraph(budget_data[i][j], S['TableCellCenter'] if j == 1 else S['TableCell'])
                          for j in range(3)]
    b_t = Table(budget_data, colWidths=[1.4*inch, 1.2*inch, 3.7*inch])
    b_t.setStyle(table_style())
    story.append(b_t)
    story.append(sp(3))

    story += section("Step 1: Attributes")
    story.append(body(
        "All attributes begin at 9. Players may raise any attribute by spending points at the costs listed "
        "in the <b>Pathways — Attribute Rules</b> table above. Keep your campaign's starting point total "
        "in mind — attribute raises are expensive and every point spent here comes directly from your skill budget."
    ))
    story.append(sp(3))

    story += section("Step 2: Advantages")
    story.append(body(
        "Advantages define what makes your character special. Choose 1–2 that strongly reinforce your concept. "
        "Budget carefully — advantages are expensive and every point you spend here comes from skills."
    ))

    story += subsection("Combat Advantages")
    adv_combat = [
        ["Advantage", "Cost", "Effect"],
        ["Combat Reflexes", "15 pts", "+1 to all active defenses, +6 to recover from stun, never freeze in surprise"],
        ["Danger Sense", "15 pts", "GM warns of threats just before they strike (surprise is negated)"],
        ["Hard to Kill", "2 pts/level", "+1/level to HT rolls to avoid death; can take 1–5 levels"],
        ["Hard to Subdue", "2 pts/level", "+1/level to remain conscious when reduced to 0 or negative HP"],
        ["High Pain Threshold", "10 pts", "Ignore shock penalties from injury; +3 on HT rolls to avoid knockdown"],
        ["Lifting ST", "3 pts/level", "Extra ST only for lifting/carrying purposes; does not affect damage"],
    ]
    adv_combat[0] = [Paragraph(c, S['TableHeader']) for c in adv_combat[0]]
    for i in range(1, len(adv_combat)):
        adv_combat[i] = [Paragraph(adv_combat[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(adv_combat, colWidths=[1.4*inch, 0.8*inch, 4.1*inch],
                        style=table_style()))
    story.append(sp(3))

    story += subsection("Mental & Social Advantages")
    adv_mental = [
        ["Advantage", "Cost", "Effect"],
        ["Charisma", "5 pts/level", "+1/level to reaction rolls and Influence skills (Leadership, Panhandling, Public Speaking, Savoir-Faire, Sex Appeal, Streetwise) [max 4 levels]"],
        ["Contact", "1–10 pts", "Reliable source of information or aid (varies by skill and frequency)"],
        ["Church Organisation Informant", "5–15 pts", "A representative of a church enforcement body (Nighthawks, Mandated Punishers, Machinery Hivemind, etc.) has chosen you as an informant. Receive help from authorities when in minor legal trouble or when caught using Beyonder powers without harm to innocents. Earn contribution points for important information or assistance, exchangeable for money or Beyonder formulas/ingredients. 5 pts: newly recruited, must prove your worth. 10–15 pts: trusted informant; the organisation's representative trusts your judgement."],
        ["Official Beyonder", "15 pts", "You operate under the sanction of a recognised church or organisation. Benefits: Revolver +2, Ritualistic Magic +1, Hidden Lore (Beyonders) +3, Occultism +2, Hermes Language (Broken). You have Legal Enforcement Powers as a sanctioned investigator. Drawback: Duty (to your organisation) — you can be called upon for assignments and must follow institutional protocol."],
        ["Eidetic Memory", "5 pts", "+5 to remember things after one reading; near-perfect recall"],
        ["Empathy", "15 pts", "Sense emotions; +3 to social skill rolls"],
        ["Language Talent", "10 pts", "All language skills cost half the normal points"],
        ["Reputation", "varies", "Known for something specific — positive reactions from relevant groups"],
        ["Voice", "10 pts", "+2 to all rolls to influence others through speech"],
        ["Alertness", "5 pts/level", "+1 per level to all Per rolls. Notice more of your surroundings — active and passive perception both benefit."],
        ["Healer", "10 pts", "+2 to all rolls to diagnose, treat, and heal; +3 to First Aid specifically; HT rolls to avoid or recover from disease at +2."],
        ["Single-Minded", "5 pts", "+3 to any extended concentration task (research, crafting, lockpicking, etc.) when you can focus without interruption."],
        ["Versatile", "5 pts", "+1 to defaults skill rolls — any time you use a skill at default, you are effectively one level better."],
        ["Intuition", "5 pts", "Once per session, the GM may give you a meaningful hunch about a decision. Ask the GM: 'Is this a good/bad idea?' The GM must answer honestly."],
        ["Lightning Calculator", "5 pts", "Perfect mental arithmetic; quick estimates at no penalty; numerical puzzles and mental maths at +2."],
        ["Absolute Direction", "5 pts", "Always know which way is north; never become lost in natural terrain. +3 to Navigation and Body Sense rolls."],
        ["Language (specify)", "varies", "Individual language proficiency. See the Languages section for cost tables based on proficiency (Native/Accented/Broken) and type (Common vs Mystical)."],
    ]
    adv_mental[0] = [Paragraph(c, S['TableHeader']) for c in adv_mental[0]]
    for i in range(1, len(adv_mental)):
        adv_mental[i] = [Paragraph(adv_mental[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(adv_mental, colWidths=[1.4*inch, 0.8*inch, 4.1*inch],
                        style=table_style()))
    story.append(sp(3))

    story += subsection("Languages")
    story.append(body(
        "The world of Loen is linguistically rich. Common languages carry no mystical weight — they are "
        "the everyday speech of nations. Mystical languages, by contrast, resonate with the supernatural "
        "forces of the Spirit World and are essential for rituals, charms, and Beyonder abilities. "
        "Points listed are for <b>Spoken + Written</b> at the given level. "
        "<b>Spoken-only or written-only</b> costs half. "
        "<b>Language Talent</b> halves all costs (rounded up)."
    ))
    story.append(sp(2))

    story += subsection("Common Languages")
    com_lang = [
        ["Language", "Region / Origin"],
        ["Loen",        "Loen Kingdom — the lingua franca of the Northern Continent"],
        ["Feysac",      "Feysac Empire — derived from Ancient Feysac"],
        ["Intis",       "Intis Republic — derived from Ancient Feysac"],
        ["Balam (Dutan)","East and West Balam, Southern Continent — distinct origin from Ancient Feysac but structurally similar"],
        ["Highland",    "Mountain regions of the Northern Continent — various dialects"],
        ["Rorsted",     "Rorsted Archipelago — derived from Ancient Feysac"],
    ]
    com_lang[0] = [Paragraph(c, S['TableHeader']) for c in com_lang[0]]
    for i in range(1, len(com_lang)):
        com_lang[i] = [Paragraph(com_lang[i][0], S['TableCell']),
                       Paragraph(com_lang[i][1], S['TableCell'])]
    story.append(Table(com_lang, colWidths=[1.2*inch, 5.1*inch], style=table_style()))
    story.append(sp(1))
    lang_cost_data = [
        ["Proficiency", "Cost", "Effect on Skill Rolls"],
        ["Native",     "6 pts", "Fluent. No penalty to language-dependent skill rolls. Pass as a native speaker."],
        ["Accented",   "4 pts", "Noticeable accent. -2 to language-dependent skill rolls."],
        ["Broken",     "2 pts", "Simple ideas only. -3 to language-dependent skill rolls. Cannot read complex texts."],
    ]
    lang_cost_data[0] = [Paragraph(c, S['TableHeader']) for c in lang_cost_data[0]]
    for i in range(1, len(lang_cost_data)):
        lang_cost_data[i] = [Paragraph(lang_cost_data[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(lang_cost_data, colWidths=[1.2*inch, 1.0*inch, 4.1*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Mystical Languages")
    story.append(body(
        "Mystical languages carry inherent supernatural power. Speaking them can shake natural forces, "
        "activate charms, and perform rituals. They are exponentially harder to learn than common tongues "
        "because each word is dense with meaning and spiritual resonance."
    ))
    story.append(sp(2))
    mys_lang = [
        ["Language", "Origin / Notes"],
        ["Ancient Hermes", "Created by the ancient sage Hermes in the Second Epoch, based on Jotun and Dragonese. Direct, powerful — but lacks concealment, making it dangerous for the unprotected. Used for sacrifice and prayer."],
        ["Hermes", "The improved, safer descendant of Ancient Hermes. Better concealment and protection. Essential knowledge for all Beyonders."],
        ["Elvish", "Ancient language of the elves. Every word is rich in meaning; sentences are very short. Can shake natural forces. Used for sacrifice, prayer, and spellcasting."],
        ["Dragonese", "Ancient language of dragons. Can shake natural forces. Used for sacrifice, prayer, and spellcasting."],
        ["Jotun (Giant's)", "Ancient language of giants. Can shake natural forces. Still in daily use in the City of Silver (Forsaken Land of the Gods). Basis of Ancient Feysac."],
        ["Ancient Feysac", "Common tongue of the Fourth Epoch and root of all modern Northern Continent languages. Derived from Jotun. Has minor mystical properties but cannot shake natural forces. Considered a mystical language due to its origin and ritual use."],
    ]
    mys_lang[0] = [Paragraph(c, S['TableHeader']) for c in mys_lang[0]]
    for i in range(1, len(mys_lang)):
        mys_lang[i] = [Paragraph(mys_lang[i][0], S['TableCell']),
                       Paragraph(mys_lang[i][1], S['TableCell'])]
    story.append(Table(mys_lang, colWidths=[1.4*inch, 4.9*inch], style=table_style()))
    story.append(sp(1))
    mys_cost_data = [
        ["Proficiency", "Cost", "Effect on Skill Rolls"],
        ["Native",     "30 pts", "Fluent. No penalty. Can perform rituals, read ancient texts, and channel mystical forces through the language."],
        ["Accented",   "20 pts", "Functional but imperfect. -2 to language-dependent skill rolls. Rituals using the language at -2."],
        ["Broken",     "10 pts", "Recognise common words and phrases. -3 to language-dependent skill rolls. Cannot perform rituals in the language."],
    ]
    mys_cost_data[0] = [Paragraph(c, S['TableHeader']) for c in mys_cost_data[0]]
    for i in range(1, len(mys_cost_data)):
        mys_cost_data[i] = [Paragraph(mys_cost_data[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(mys_cost_data, colWidths=[1.2*inch, 1.0*inch, 4.1*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Language Talent</b> (10 pts) halves all language costs. "
        "<b>Multilingual</b> (3 pts) grants fluency in two common languages without point cost — "
        "it does not apply to mystical languages."
    ))
    story.append(sp(3))

    story += subsection("Appearance")
    story.append(body(
        "How your character looks can have a measurable impact on social interactions. "
        "The following levels of Appearance affect reactions from others:"
    ))
    app_data = [
        ["Level", "Cost", "Reaction Modifier"],
        ["Attractive", "+1 pt", "+1 to reaction rolls"],
        ["Handsome / Beautiful", "+4 pts", "+2 to reaction rolls"],
        ["Very Handsome / Very Beautiful", "+8 pts", "+3 to reaction rolls"],
        ["Unattractive", "-4 pts", "-1 to reaction rolls"],
        ["Ugly", "-8 pts", "-2 to reaction rolls"],
        ["Hideous", "-16 pts", "-4 to reaction rolls"],
        ["Monstrous", "-20 pts", "-5 to reaction rolls"],
        ["Horrific", "-24 pts", "-6 to reaction rolls"],
    ]
    app_data[0] = [Paragraph(c, S['TableHeader']) for c in app_data[0]]
    for i in range(1, len(app_data)):
        app_data[i] = [Paragraph(app_data[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(app_data, colWidths=[2.0*inch, 0.8*inch, 3.5*inch], style=table_style()))
    story.append(body(
        "<i>Note: Appearance point costs have been adjusted for the Pathways setting "
        "and differ from standard GURPS values.</i>"
    ))
    story.append(sp(3))

    story += subsection("Mundane Advantages")
    story.append(body(
        "Mundane advantages are available to any character — mortal or Beyonder alike. They represent "
        "natural gifts, fortunate circumstances, and trained excellence."
    ))
    story.append(sp(2))
    story += subsection("Social & Reputation")
    soc_adv = [
        ["Advantage", "Cost", "Effect / When It Triggers"],
        ["Acute Social Awareness",  "5 pts",  "+2 to all Body Language and Detect Lies rolls. You read a room before you enter it."],
        ["Class Mobility",          "5 pts",  "Move believably across two social classes. +2 to Savoir-Faire in either; NPCs rarely question your presence."],
        ["Connections: Church Lay Staff", "5 pts", "Recognized civilian assistant to one Orthodox Church. Access to facilities; some protection from routine Nighthawk scrutiny."],
        ["Connections: Press Credentials","3 pts","Recognized press identity. Opens doors otherwise closed; plausible reason to be anywhere in a city."],
        ["Fearsome Reputation",     "5 pts",  "Known in criminal circles. Relevant NPCs start cautious; Intimidation in these circles is at +2."],
        ["Local Legend",            "5 pts",  "Well-known in one neighbourhood (specify). +2 to social rolls there; people look out for you."],
        ["Mentor",                  "5 pts",  "Senior figure offers intermittent guidance. Once per session consult for info, a contact, or a skill roll at their level."],
        ["Multilingual",            "3 pts",  "Fluent in two additional languages. No penalty to language-dependent social skills in those languages."],
        ["Natural Leader",          "5 pts",  "When you issue a direct command under pressure, allies may reroll their first Fright Check or morale roll with +1. Once per scene."],
        ["Police Informant",        "5 pts",  "Arrangement with local constabulary. Minor legal trouble can often be redirected. Discreet — exposure would be dangerous."],
        ["Respectable Address",     "3 pts",  "Lodgings in a creditable neighbourhood. +1 to social rolls with middle/upper class NPCs who would otherwise look down on you."],
        ["Street Credibility",      "3 pts",  "Trusted in the working-class underground. Call in small favours from dock workers, factory hands, and street operators once per session."],
        ["Fearlessness",            "2 pts/level", "+1 per level to Fright Checks; also grants immunity to intimidation from beings with fewer levels of Fearlessness than you. Vital in a world of horrors."],
        ["Fit",                     "5 pts",  "+1 to all HT rolls; recover FP at twice the normal rate"],
        ["Very Fit",                "15 pts", "+2 to all HT rolls; lose FP at half the normal rate; recover FP at twice the normal rate"],
        ["Wealth: Comfortable",     "5 pts", "Good income; start with £5. Status 1 → +1 reaction from those impressed by wealth."],
    ]
    soc_adv[0] = [Paragraph(c, S['TableHeader']) for c in soc_adv[0]]
    for i in range(1, len(soc_adv)):
        soc_adv[i] = [Paragraph(soc_adv[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(soc_adv, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Legal & Firearms")
    legal_adv = [
        ["Advantage", "Cost", "Effect / When It Triggers"],
        ["Hunting License",      "5 pts",  "Legal in Loen for hunting rifle only. Costs £5 to obtain in-game. Valid in rural/suburban areas — carrying in city limits draws police attention."],
        ["General Weapon Certificate", "15 pts", "Full civilian firearm permit. Costs £50 to obtain in-game. Allows carry of any non-military weapon in cities; required for pistols, rifles, shotguns in urban areas."],
        ["Legal Enforcement Powers", "5 pts", "Official authority to investigate, detain, and carry weapons in the line of duty. Works within jurisdiction only; may vary by city or organization."],
    ]
    legal_adv[0] = [Paragraph(c, S['TableHeader']) for c in legal_adv[0]]
    for i in range(1, len(legal_adv)):
        legal_adv[i] = [Paragraph(legal_adv[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(legal_adv, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Professional & Technical")
    prof_adv = [
        ["Advantage", "Cost", "Effect / When It Triggers"],
        ["Black Market Access",     "5 pts",  "Reliable source for illegal or restricted goods. Once per session attempt to acquire a specific item outside legal channels."],
        ["Experienced Investigator","5 pts",  "Once per investigation scene ask the GM one yes/no question about observable evidence without a skill roll."],
        ["Former Military Officer", "10 pts", "Leadership and Tactics at +1; military contacts; entitled to officer courtesies in formal settings."],
        ["Industrial Expertise",    "5 pts",  "Deep familiarity with a specific industry (specify). +2 to all relevant skill rolls; NPCs in that industry trust your knowledge."],
        ["Medical Training (Informal)","5 pts","Use Physician at IQ-2 without purchasing the skill; First Aid rolls gain +1."],
        ["Navigator's Eye",         "5 pts",  "Never become lost in any city previously visited; rural navigation rolls at +2."],
        ["Photographic Instinct",   "3 pts",  "Photography rolls at +2; instinctively know what to capture as evidence."],
        ["Safecracker",             "5 pts",  "+3 to Lockpicking for combination locks and mechanical safes specifically."],
        ["Underworld Lawyer",       "5 pts",  "Once per session cite an obscure legal technicality convincingly enough to delay, redirect, or dismiss a legal problem."],
    ]
    prof_adv[0] = [Paragraph(c, S['TableHeader']) for c in prof_adv[0]]
    for i in range(1, len(prof_adv)):
        prof_adv[i] = [Paragraph(prof_adv[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(prof_adv, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Physical & Innate")
    phys_adv = [
        ["Advantage", "Cost", "Effect / When It Triggers"],
        ["Alcohol Tolerance",  "1 pt",  "Never suffer social penalties from moderate drinking; Carousing rolls to appear sober at +3."],
        ["Cold Resistance",    "2 pts", "No penalties from cold weather up to freezing; hypothermia rolls at +2."],
        ["Controlled Breathing","3 pts","Hold breath for HT × 3 seconds without a roll; HT rolls to resist airborne toxins at +2."],
        ["Fast Healer",        "5 pts", "Recover 1 additional HP per day of rest. Injuries that would leave others bedridden leave you functional in half the time."],
        ["Hard Stomach",       "2 pts", "No HT rolls required for disgusting environments — gore, corpses, foul conditions."],
        ["Iron Jaw",           "3 pts", "Knockdown rolls from blows to the head at +2; never bite through your own tongue under shock."],
        ["Light Sleeper",      "2 pts", "Perception rolls while sleeping at +4; never caught completely unaware at night."],
        ["Low-Profile Build",  "3 pts", "Physical appearance is unremarkable. All attempts to identify you from description are at -2."],
        ["Night Eyes",         "5 pts", "Reduce all darkness penalties by 2; in dim gaslight or moonlight suffer no penalty at all."],
        ["Perfect Balance",    "20 pts", "+6 to avoid knockdown; +2 to Acrobatics, Climbing, Piloting"],
        ["Great Balance",      "10 pts", "+2 to avoid knockdown; +1 to Acrobatics, Climbing, Piloting"],
        ["Rapid Recovery",     "5 pts", "Stun durations halved; recover from knockdown in half normal time."],
        ["Flexibility",        "5 pts", "+3 to Climbing and Escape; ignore up to -3 close-quarters penalties."],
        ["Double-Jointed",     "15 pts","+5 to Climbing and Escape; ignore up to -5 close-quarters penalties; any body part bends any way."],
        ["Acute Vision",       "2 pts", "+2 to Vision rolls; notice details at a distance, read lips, spot hidden objects."],
        ["Acute Hearing",      "2 pts", "+2 to Hearing rolls; detect faint sounds, eavesdrop through walls, identify speech in noise."],
        ["Resistant (specify)", "3 or 5 pts", "HT rolls to resist a specific category at +3 (3 pts) or +8 (5 pts). Common choices: Disease, Poison, Temperature Extremes."],
        ["Outdoorsman", "10 pts/level", "+1 per level to all Outdoor skills (Camouflage, Fishing, Naturalist, Navigation, Survival, Tracking, Weather Sense). Max 4 levels."],
    ]
    phys_adv[0] = [Paragraph(c, S['TableHeader']) for c in phys_adv[0]]
    for i in range(1, len(phys_adv)):
        phys_adv[i] = [Paragraph(phys_adv[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(phys_adv, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Supernatural Advantages")
    story.append(body(
        "Supernatural advantages are most commonly seen in Beyonders, where pathway progression unlocks "
        "abilities beyond mortal reach. However, in rare cases, ordinary humans may possess one or two "
        "of these traits naturally — a born seer, a child with uncanny perception, or someone marked by "
        "fate before they ever drink a potion."
    ))
    story.append(sp(2))
    story += subsection("Perception & Detection")
    sup_perc = [
        ["Advantage", "Cost", "Effect / When It Triggers"],
        ["Aura Sensitivity",    "5 pts",  "Sense the emotional weight of places. In locations where violence, grief, or supernatural events occurred, receive a vague impression without rolling."],
        ["Death Sense",         "10 pts", "Passive awareness of recent death within 30 meters (within 24 hours). Sense its direction without rolling; can sense whether a person is dying."],
        ["Divine Touchstone",   "10 pts", "An Orthodox deity has taken minor notice of you. Once per session ask the GM a yes/no question your character senses as an impression."],
        ["Dreamsight",          "10 pts", "Dreams contain genuine information. Once per session the GM may offer a cryptic dream-image related to current events; sharing it grants +1 to one investigation roll."],
        ["Ether Body Awareness","5 pts",  "Know immediately when a supernatural effect is targeting your soul, not just your body — even without Spirit Vision."],
        ["Fate Sensitivity",    "10 pts", "Once per session when making a decision with major consequences, ask the GM: 'Does this feel wrong?' The GM must answer honestly."],
        ["Ghost Proximity Sense","5 pts", "Passive. Sense when a spirit is within 10 meters — a cold certainty. No details; no roll required."],
        ["Pathway Resonance",   "10 pts", "Unexplained affinity with one specific Pathway (specify). +3 to rolls to identify items, individuals, or rituals associated with it."],
        ["Ritual Intuition",    "5 pts",  "Sense when a ritual is being performed within 50 meters. Notice the spiritual disturbance without rolling — even without knowing its type."],
        ["Soul Reading (Untrained)","10 pts","Once per scene the GM may offer one true impression about a target's emotional condition or hidden motive. Cannot be triggered deliberately."],
    ]
    sup_perc[0] = [Paragraph(c, S['TableHeader']) for c in sup_perc[0]]
    for i in range(1, len(sup_perc)):
        sup_perc[i] = [Paragraph(sup_perc[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(sup_perc, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Resistance & Resilience")
    sup_res = [
        ["Advantage", "Cost", "Effect / When It Triggers"],
        ["Anchored Soul",       "10 pts", "All attempts to alter your mental identity — possession, compulsion, pathway side effects — are at -2 against you."],
         ["Cleansed Spirit",     "5 pts",  "CoR gained from passive exposure are halved. Active corruption from deliberate acts is unaffected."],
        ["Cold Iron Tolerance", "3 pts",  "Unaffected by the mild spiritual discomfort iron causes to sensitive individuals. Rare in those with significant spiritual heritage."],
        ["Faithful Grounding",  "5 pts",  "Genuine faith acts as an anchor. Fright Checks in church buildings, shrines, or during prayer are at +3."],
        ["Incorruptible Will",  "10 pts", "+3 to all Will rolls to resist Beyonder abilities, evil god whispers, and ritual compulsion. Does not apply to mundane social pressure."],
         ["Spiritual Fortitude", "5 pts",  "Maximum CoR equal Will + 3 rather than just Will."],
        ["Warded Dreams",       "5 pts",  "All supernatural attempts to enter, read, or alter your dreams require an additional success by 3 or more to take effect."],
    ]
    sup_res[0] = [Paragraph(c, S['TableHeader']) for c in sup_res[0]]
    for i in range(1, len(sup_res)):
        sup_res[i] = [Paragraph(sup_res[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(sup_res, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Unusual Gifts")
    sup_gift = [
        ["Advantage", "Cost", "Effect / When It Triggers"],
        ["Luck",                "10 pts", "1 reroll per session — may reroll any one failed roll."],
        ["Beckoning Luck",      "20 pts", "2 rerolls per session — reroll any failed roll, usable at any time. If the re-roll also fails there is no additional effect — and fate may balance later."],
        ["Born Under a Named Star","15 pts","Seers and Diviners who read your fate always notice something unusual. You register as 'marked' in ways they cannot fully interpret."],
        ["Mystical Item",       "5–15 pts", "A single mystical item you already possess, defined with the GM. Cost scales with power: a minor charm (5 pts), a useful tool (10 pts), or a significant piece of equipment (15 pts). The item should match one of the 22 pathways' domains. If lost or destroyed, rename this advantage to 'Mystical Item (Lost)' — no refund."],
        ["Charmed Object",      "5 pts",  "One item you own provides +1 to one specific skill when used (specify item and skill). Lost permanently if the item is destroyed."],
         ["Dead Language Fluency","5 pts", "Read and speak one dead language (Ancient Hermes, Ancient Loen, etc.) without having formally learned it. Origin unexplained."],
        ["Familiar Presence",   "5 pts",  "Animals and spirits are unusually calm near you. Domestic animals never startle; non-hostile spirits observe rather than act against you."],
        ["Sequence Knowledge",  "15 pts", "You know the formula for your next Sequence 8 potion — main ingredients, supplementary ingredients, and basic preparation method. This knowledge arrives instinctively once you reach Sequence 9. It does not grant the ingredients, a pre-prepared potion, or an Acting Method. Covers only the immediate next sequence."],
        ["Knows the Acting Method", "15 pts", "You innately understand the Acting Method for your Pathway. Doubles your digestion speed — all Digestion Gain Per Session is doubled (e.g. Exemplary +15–20% becomes +30–40%)."],
        ["Marked by Ritual",    "10 pts", "A lasting spiritual imprint (define with GM). Grants +2 to one type of SPI roll but may attract unusual attention."],
        ["Spirit Tongue",       "10 pts", "Communicate basic intent to ghosts and lingering spirits without the Language of the Dead ability. Limited to yes/no exchanges."],
        ["Uncanny Survivor",    "10 pts", "Once per campaign arc, when you would die on a death roll, succeed automatically instead. The GM decides the cost."],
        ["Sanctity",            "5 pts",  "Your connection to the divine is unusually clear. +2 to Theology and Religious Ritual; once per session, the GM must answer one factual question about Church doctrine or history honestly."],
    ]
    sup_gift[0] = [Paragraph(c, S['TableHeader']) for c in sup_gift[0]]
    for i in range(1, len(sup_gift)):
        sup_gift[i] = [Paragraph(sup_gift[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(sup_gift, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))

    story.append(sp(2))
    story += subsection("Seven Orthodox Gods Blessings")
    story.append(body(
        "The Seven Orthodox Churches bless their faithful with supernatural favor. "
        "Each blessing costs <b>75 points</b> and represents divine intervention:"
    ))
    
    bless_data = [
        ["Deity", "Blessing Effect (Passive & Permanent)"],
        ["Goddess of Evernight", "Dream Lucidity, Concealment. Most divination fails against you."],
        ["Lord of Storms", "Underwater Breathing. Stay underwater 10 hrs; +3 HT vs pressure."],
        ["Earth Mother", "Bury in soil to regenerate. Fatal wounds heal; revive from death."],
        ["God of Combat", "Herculean strength & catlike reflexes. +3 ST, +3 DX, +3 HT."],
        ["God of Knowledge and Wisdom", "Expert in mysticism. +5 to all occult/knowledge skills."],
        ["Eternal Blazing Sun", "Possession impossible. Burn evil near you (1d6/round)."],
        ["God of Steam & Machinery", "Beyonder item affinity. Rapid ID; curses negated."],
    ]
    bless_data[0] = [Paragraph(c, S['TableHeader']) for c in bless_data[0]]
    for i in range(1, len(bless_data)):
        bless_data[i] = [Paragraph(bless_data[i][j], S['TableCell']) for j in range(2)]
    story.append(Table(bless_data, colWidths=[2.0*inch, 4.3*inch], style=table_style()))
    
    story.append(sp(2))
    story.append(body(
        "<b>Requirement:</b> Character must be a confirmed believer in the corresponding Church. "
        "Losing faith (GM discretion) temporarily suspends blessings until reconciliation."
    ))

    story += section("Step 3: Disadvantages")
    story.append(body(
        "You may take up to <b>-40 points</b> of disadvantages (no minimum — they are entirely optional). These aren't penalties — they "
        "are character definition. The best disadvantages create story hooks and force interesting decisions. "
        "Up to 5 additional points of quirks (minor personality traits at -1 pt each) are allowed."
    ))
    story.append(sp(3))

    story += subsection("Mundane Disadvantages")
    story.append(body("These represent ordinary human flaws, social conditions, and personal struggles available to any character."))
    story.append(sp(2))
    story += subsection("Core Disadvantages")
    disadv_data = [
        ["Disadvantage", "Value", "When It Triggers"],
        ["Wealth: Poor",       "-15",       "Start with 5 soli; boarding house; barely afford basic food. Status −1 → −1 reaction from status-conscious NPCs."],
        ["Wealth: Dead Broke", "-25",       "Start with £0; no home; beg or steal for every meal. Status −2 → −2 reaction from status-conscious NPCs."],
        ["Wealth: Struggling","-10",       "Start with 15 soli; modest room; occasional luxuries"],
        ["Curious (12)",       "-5",        "Must roll vs. 12 or investigate any mystery encountered"],
        ["Greed (12)",         "-15",       "Must roll vs. 12 or take any opportunity for significant profit"],
        ["Overconfidence (12)","-5",        "Believes they can handle situations they cannot"],
        ["Bad Temper (12)",    "-10",       "Must roll vs. 12 to avoid angry outbursts when provoked"],
        ["Bully (12)",         "-10",       "Must roll vs. 12 to resist intimidating or humiliating someone weaker when the opportunity arises"],
        ["Obsession (12)",     "-5 to -10", "Consuming long-term goal dominates life and decisions"],
        ["Nightmares (12)",    "-5",        "Disturbed sleep; wake unrefreshed — lose 1 FP each morning"],
        ["Code of Honor",      "-5 to -15", "Personal code limits actions; must be followed even at cost"],
        ["Sense of Duty",      "-2 to -15", "Must help/protect certain groups even at personal risk"],
        ["Social Stigma",      "-5 to -20", "Society discriminates: Criminal Record -5, Servant Class -5"],
        ["Secret",             "-5 to -30", "Dangerous hidden truth; exposure has severe consequences"],
    ]
    disadv_data[0] = [Paragraph(c, S['TableHeader']) for c in disadv_data[0]]
    for i in range(1, len(disadv_data)):
        disadv_data[i] = [Paragraph(disadv_data[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(disadv_data, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Social & Background")
    disadv_soc = [
        ["Disadvantage", "Value", "Trigger / Notes"],
        ["Blacklisted",         "-10 pts",      "A specific industry, org, or church has your name. Employment or access there fails automatically without disguise."],
        ["Blood Feud",          "-5 to -15 pts","A family, gang, or faction holds a grievance. Their agents appear as recurring threats (scale reflects their power)."],
        ["Creditor's Target",   "-10 pts",      "You owe a dangerous debt. Periodic pressure, threats, or interference; cannot ignore it without severe consequences."],
        ["Drafted",             "-5 pts",       "Technically in a military reserve or conscript pool. Mobilisation orders can arrive at any time, legally compelling service."],
        ["Ex-Convict",          "-10 pts",      "Social Stigma in formal settings; increased police scrutiny; certain employment and legal protections unavailable."],
        ["Famous Face",         "-5 pts",       "Recognizable in the city. Disguise attempts at -2; surveillance harder; strangers approach you, sometimes dangerously."],
        ["Fugitive (Minor)",    "-10 pts",      "Open local warrant on a non-capital charge. Cannot approach police, visit courts, or enter government buildings without risk."],
        ["Fugitive (Serious)",  "-20 pts",      "Serious criminal charges outstanding. Significant arrest risk on sight in major cities; cannot use real name officially."],
        ["Illegitimate Birth",  "-5 pts",       "-1 to social rolls in formal/upper-class settings where this is known; inheritance and legal rights are complicated."],
        ["Orphan with Dependents","-10 pts",    "Support younger siblings or a sick relative. Regular financial drain; their safety is a lever enemies can use."],
        ["Refugee Status",      "-10 pts",      "No legal right of permanent residence. No papers, no safety net; deportation is a real threat; police encounters are dangerous."],
        ["Wanted by Church",    "-15 pts",      "An Orthodox Church has marked you. Not just the police — Nighthawks or equivalent Beyonder enforcers may be looking."],
        ["Duty (specify)",      "-2 to -20 pts","Regular, enforced obligation to an organization or individual. Value reflects frequency and danger: -5 for light duty (roll 6 or less), -10 for hazardous duty (roll 9 or less), -15 for extremely hazardous (roll 12 or less; appears weekly). Specify organization and nature at creation."],
    ]
    disadv_soc[0] = [Paragraph(c, S['TableHeader']) for c in disadv_soc[0]]
    for i in range(1, len(disadv_soc)):
        disadv_soc[i] = [Paragraph(disadv_soc[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(disadv_soc, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Personal & Psychological")
    disadv_pers = [
        ["Disadvantage", "Value", "Trigger / Notes"],
        ["Absent-Mindedness",    "-15 pts",      "-3 to skill rolls requiring concentration or organisation in everyday life; must roll vs. IQ to remember to do something if interrupted or distracted. In combat, may forget to reload, change tactics, or use special abilities (GM's discretion)."],
        ["Addiction: Laudanum",  "-10 pts",      "Must use daily or suffer -2 to all rolls from withdrawal; supply costs drain income."],
        ["Addiction: Tobacco",   "-3 pts",       "Minor withdrawal irritability (-1 to Will) if unable to smoke for a full day."],
        ["Chronic Insomnia",     "-5 pts",       "Lose 1 FP each morning that cannot be recovered through rest; rolls requiring sustained concentration at -1."],
        ["Class Resentment",     "-5 pts",       "Must roll vs. Will-2 or express hostility when in prolonged contact with the resented class."],
        ["Compulsive Gambling",  "-10 pts",      "Regular income loss; prone to debt; requires Will roll at -2 to leave a game while ahead."],
        ["Duty-Bound",           "-5 to -10 pts","An obligation takes priority over personal safety. Must regularly sacrifice time, money, or risk to fulfil it."],
        ["Glass Jaw",            "-5 pts",       "All knockdown rolls from head strikes at -2; concussion effects last longer."],
        ["Glory Hound",          "-5 pts",       "Must roll vs. Will or ensure your role in any success is publicly known, even when discretion would be wiser."],
        ["Grief-Stricken",       "-5 pts",       "In situations that echo a specific loss, Will rolls to act clearly are at -2. Can be gradually resolved through play."],
        ["Guilt",                "-5 pts",       "-1 to Will in situations that echo the original act; may be exploited by people who know the truth."],
        ["Impulsive",            "-10 pts",      "Must roll vs. IQ-2 to pause and plan; failure means you act on the first reasonable impulse in any urgent situation."],
        ["Reckless",             "-5 pts",       "-1 to any roll where caution would be smarter; must roll vs. Will to back down from a physical challenge."],
        ["Reputation: Troublemaker","-5 pts",    "Employers, landlords, and officials treat you with pre-emptive suspicion; -2 to first reactions in formal settings."],
        ["Social Anxiety",       "-5 pts",       "-2 to social skill rolls in groups of 6+; -3 when addressing strangers of higher status."],
        ["Stubborn",             "-5 pts",       "Must roll vs. Will-3 to reverse your stated position in the same scene, even when clearly wrong."],
        ["Superstitious (mundane)","-3 pts",     "If warding routine is disrupted, -1 to all rolls for the day; will go out of their way to observe superstitions."],
        ["Reluctant Killer",     "-5 pts",       "-4 to hit recognizable people with deadly force (-2 if face hidden); cannot Aim. If you kill a recognizable person, become morose for 3d days — Will rolls required to use violence again."],
        ["Cannot Harm Innocents", "-10 pts",     "Will not use deadly force when innocent bystanders might be affected, or against enemies not using deadly force on you. Non-deadly force is acceptable."],
        ["Cannot Kill",          "-15 pts",      "Unwilling to kill anyone, even through omission, or to allow comrades to kill. If responsible for a death, react as Reluctant Killer (-5)."],
        ["Self-Defence Only",    "-15 pts",      "Use violence only to protect yourself or those in your care, to the minimum degree necessary; no pre-emptive strikes."],
        ["Total Non-Violence",   "-30 pts",      "Will not use violence against intelligent creatures, even in self-defense. May defend against animals."],
        ["Workaholic",           "-5 pts",       "Cannot relax; always finds something productive to do. -2 to social rolls in leisure settings; rolls to take a day off at Will-3."],
        ["Callous",              "-5 pts",       "-3 to social skill rolls when warmth or empathy is required. You may still act kindly — but it is an effort and it shows."],
        ["Kleptomania",          "-10 pts",      "Compelled to steal small objects when the opportunity arises and no consequences are obvious. Roll vs. Will to resist when the situation makes theft easy."],
        ["Skinny",               "-5 pts",       "-2 to ST for purposes of knockback and grappling; +2 to rolls to escape bonds or fit into tight spaces. Clothing is hard to find off the rack."],
        ["Shyness",              "-5 to -10 pts","-1 to -2 to social skill rolls depending on severity and audience. Mild (-5): -1 in groups of 6+; Severe (-10): -2 in groups of 3+."],
        ["Laziness",             "-10 pts",      "Must roll vs. Will to undertake any sustained effort not immediately necessary or personally interesting. Unemployment is a real risk."],
        ["Clueless",             "-10 pts",      "-3 to all social skill rolls; generally miss social cues and subtlety. You do not understand subtext, sarcasm, or implication."],
        ["Unfit",                "-5 pts",       "-1 to all HT rolls; recover FP at half normal rate. Unfit for sustained physical exertion."],
        ["Vow (specify)",        "-5 to -15 pts","A solemn promise that restricts your actions. Common examples: Poverty (give away all wealth beyond subsistence) -10, Partial Silence (limited speech) -5, Vegetarian -5."],
        ["Charity",              "-10 pts",      "Cannot ignore genuine need. Must roll vs. Will to avoid helping anyone who asks for assistance you can reasonably provide. May be exploited."],
        ["Loner",                "-5 pts",       "Must roll vs. Will to spend extended time in groups larger than 3-4 people. Seek solitude when stressed; -1 to social rolls in crowds."],
        ["Bloodlust",            "-10 pts",      "Must go for killing blows in combat. IQ roll necessary to accept a surrender or take a prisoner. Downed foes get an extra shot to make sure."],
    ]
    disadv_pers[0] = [Paragraph(c, S['TableHeader']) for c in disadv_pers[0]]
    for i in range(1, len(disadv_pers)):
        disadv_pers[i] = [Paragraph(disadv_pers[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(disadv_pers, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Supernatural Disadvantages")
    story.append(body(
        "These disadvantages are most commonly found in Beyonders dealing with the side effects of their "
        "potions, but in rare cases may appear in ordinary people who have been touched or broken by the "
        "hidden world."
    ))
    story.append(sp(2))
    story += subsection("Core Supernatural Disadvantages")
    disadv_sup = [
        ["Disadvantage", "Value", "When It Triggers"],
        ["Weirdness Magnet",     "-15",       "Strange supernatural events are drawn to you constantly"],
        ["Paranoia (12)",        "-10",       "Must roll vs. 12 or assume strangers are threats; common potion side effect"],
        ["Hallucinations (12)",  "-10",       "Periodic false sensory experiences; visions, voices, phantom presences"],
        ["Compulsion (pathway)", "-5 to -15", "Uncontrollable urge tied to pathway nature; triggered by stress"],
        ["Delusion (minor)",     "-5",        "Firmly believes something false about the supernatural world"],
        ["Coldblooded",          "-10",       "Morality erodes upon advancement. Roll Will when suppressing evil desires (murder, lust, theft, etc.). Define with the GM which desires apply to your character."],
        ["Compulsive Behavior (Indulge Evil Desires) SC 6", "-15", "When an opportunity to commit an evil act (murder, torture, betrayal, etc.) presents itself, roll 3d6 ≤ 6 or indulge fully. Conscience offers no resistance."],
    ]
    disadv_sup[0] = [Paragraph(c, S['TableHeader']) for c in disadv_sup[0]]
    for i in range(1, len(disadv_sup)):
        disadv_sup[i] = [Paragraph(disadv_sup[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(disadv_sup, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Exposure & CoR")
    disadv_exp = [
        ["Disadvantage", "Value", "Trigger / Notes"],
        ["Aura Leak",            "-10 pts", "Spiritual body radiates faintly even suppressed. Beyonders with Spiritual Perception detect you automatically within 20 meters."],
        ["Bleed-Through Visions","-10 pts", "Spirit Vision activates involuntarily in emotionally charged locations. Roll vs. Will or be briefly incapacitated by the vision."],
        ["CoR Brand",     "-10 pts", "A visible or spiritually legible mark from prior CoR exposure. Church Beyonders who examine you react with suspicion or investigation."],
        ["Dream Invaded",        "-10 pts", "Dreams are accessible to outside entities without effort. You are unaware of visitors unless they choose to reveal themselves."],
        ["Ether Body Damage",    "-10 pts", "Prior spirit body damage (see Spirit Body Damage, Chapter 5) that never fully healed. All SPI-based rolls at -1; Spirit Vision on you reveals the damage immediately."],
        ["Fate Debt",            "-15 pts", "You owe fate something. The GM holds a narrative debt to be called in at a dramatically significant moment. Beckoning Luck never applies."],
        ["Unlucky",              "-10 pts", "Once per session the GM may inconvenience you by making your life slightly more difficult. This is a weaker Fate Debt that triggers every session and remains until bought off or resolved through the assistance of a powerful fate-related Beyonder or ritual."],
        ["Pathway Resonance (Hostile)","-10 pts","One specific Pathway resonates badly with you (specify). Beings of that Pathway react with instinctive hostility; their abilities against you at +1."],
        ["Residual Contamination","-10 pts","Spiritual residue from a forbidden item or ritual. Seers and Spiritual Perception users detect 'something wrong' about you."],
        ["Soul Scar",            "-5 pts",  "Under extreme spiritual stress (Fright Check failure by 5+, witnessing Seq. 5+ abilities), old pain resurfaces: -1 to all rolls for the scene."],
        ["Thinned Veil",         "-10 pts", "Boundary between your senses and the spiritual world is unusually permeable. Concentration in spiritually active environments at -2."],
    ]
    disadv_exp[0] = [Paragraph(c, S['TableHeader']) for c in disadv_exp[0]]
    for i in range(1, len(disadv_exp)):
        disadv_exp[i] = [Paragraph(disadv_exp[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(disadv_exp, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Compulsions & Obsessions")
    disadv_comp = [
        ["Disadvantage", "Value", "Trigger / Notes"],
        ["Bound to a Place",     "-10 pts", "Spiritually tethered to a location (specify). Leaving for more than one week causes growing unease: -1 to Will per additional week, cumulative."],
        ["Compulsion: Collection (pathway)","-5 to -10 pts","Compelled to collect specific items (bones, keys, mirrors, etc.). Roll vs. Will-2 when presented with a collectible you do not own."],
        ["Compulsion: Confess",  "-5 pts",  "Under significant stress, must tell someone a true secret. Roll vs. Will-2 or confess something genuine to the nearest trusted person."],
        ["Compulsion: Preserve the Dead","-10 pts","Cannot pass a neglected corpse without properly covering or acknowledging it. Roll vs. Will-3 to continue without addressing them first."],
        ["Drawn to Ritual Sites","-5 pts",  "Pulled toward places where rituals have been performed. When within blocks of a ritual site, compelled to investigate even without obvious reason."],
        ["Evil Eye Fear",        "-5 pts",  "Avoid eye contact with strangers; periodically perform warding rituals. If interrupted from a warding routine, -1 to Will rolls for the day."],
        ["Honest to Spirits",    "-5 pts",  "Cannot deliberately lie in the presence of ghosts or entities you know to be spiritually present. Instinctive, not a rational choice."],
        ["Pathway Pull",         "-10 pts", "A specific Pathway exerts a narrative pull before you drink a potion. Compelled to follow situations that lead toward it even when wisdom says otherwise."],
    ]
    disadv_comp[0] = [Paragraph(c, S['TableHeader']) for c in disadv_comp[0]]
    for i in range(1, len(disadv_comp)):
        disadv_comp[i] = [Paragraph(disadv_comp[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(disadv_comp, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Mental & Perceptual")
    disadv_ment = [
        ["Disadvantage", "Value", "Trigger / Notes"],
        ["Chronophobia (Temporal)","-10 pts","Irrational terror of something time-related (clocks stopping, mirrors, specific hours). Triggered: immediate Fright Check at -3."],
        ["Dead-Eyed",            "-5 pts",  "-2 to first-impression social rolls with strangers; animals are skittish around you; children sometimes cry."],
        ["Unsettling Appearance", "-4 pts",  "-1 to all reaction rolls. Your presence instinctively disturbs or repels others — a common consequence of Abyss and Chained Pathway potions."],
        ["Entity Fixation",      "-10 pts", "-1 to all rolls when a specific entity type is present nearby; -2 to any roll that requires you to ignore them."],
        ["Fear of Silence",      "-5 pts",  "In complete silence — underground, at sea, in empty buildings — must roll vs. Will-2 or feel compelled to speak or make noise."],
        ["Haunted",              "-10 pts", "A specific ghost follows you. Other spiritual beings notice it; it may interfere with rituals; can be used as leverage by those who know."],
        ["Memory Bleed",         "-10 pts", "Someone else's genuine memories intrude periodically — an unrelated person from your past, or someone whose spiritual body overlapped yours."],
        ["Perceptual Splitting",  "-10 pts", "At moments of high spiritual activity, senses temporarily separate from your body. All physical rolls at -2 during an episode (1d seconds)."],
        ["Phobia: Sacred Symbols","-10 pts", "A specific church's symbols, prayers, or holy items cause genuine fright. Fright Check at -2 on direct exposure; -1 in consecrated buildings."],
        ["Spiritually Loud",     "-5 pts",  "Spiritual presence registers as larger than your actual Sequence would suggest. Perceived as more powerful than you are — a curse as much as a blessing."],
        ["Threshold Blindness",  "-5 pts",  "One specific entity type or supernatural phenomenon you cannot perceive with any spiritual skill, regardless of roll results (specify at creation)."],
        ["Phobia (specify)",     "-5 to -15 pts","Irrational fear of a specific thing (cities, spiders, crowds, etc.). Fright Check at -2 when exposed; -1 to all rolls while the phobic stimulus is present and unavoidable. Severity depends on how common the trigger is."],
    ]
    disadv_ment[0] = [Paragraph(c, S['TableHeader']) for c in disadv_ment[0]]
    for i in range(1, len(disadv_ment)):
        disadv_ment[i] = [Paragraph(disadv_ment[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(disadv_ment, colWidths=[1.6*inch, 0.8*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += section("Step 4: Skills")
    story.append(body(
        "Skills represent your character's learned abilities. Each skill has a controlling attribute "
        "and a difficulty. Your skill level equals the controlling attribute plus any levels you have "
        "purchased with points."
    ))
    story.append(sp(2))
    story.append(body(
        "You buy skills by spending points up a ladder. The ladder costs are cumulative totals — "
        "you pay the <b>difference</b> to move from one step to the next. The ladder is the same "
        "for every skill regardless of difficulty; difficulty only shifts where on the ladder you "
        "start relative to your attribute."
    ))
    story.append(sp(1))
    story.append(body(
        "Skill costs follow a <b>near-exponential curve</b> — each level after the third costs twice "
        "as much as the level before it. The first level costs 1 pt, the second costs 1 pt (+1), the "
        "third costs 2 pts (+2), the fourth costs 4 pts (+4), and so on. This makes broad competence "
        "cheap but mastery extremely expensive — a single skill pushed to Attribute+3 costs 8 pts, "
        "while four skills at Attribute+0 cost only 1 pt each."
    ))
    story.append(sp(2))
    story.append(body("<b>The point ladder (cumulative totals spent):</b>"))
    ladder_data = [
        ["Total Pts Spent", "1", "2", "4", "8", "16", "32", "64", "128", "256"],
        ["Incremental cost", "1 pt", "+1 pt", "+2 pts", "+4 pts", "+8 pts", "+16 pts", "+32 pts", "+64 pts", "+128 pts"],
    ]
    ladder_data[0] = [Paragraph(c, S['TableHeader']) for c in ladder_data[0]]
    ladder_data[1] = [Paragraph(c, S['TableCellCenter']) for c in ladder_data[1]]
    story.append(Table(ladder_data, colWidths=[1.1*inch]+[0.62*inch]*9, style=table_style()))
    story.append(sp(3))
    story.append(body(
        "Difficulty determines where your first point of investment lands relative to your attribute:"
    ))
    skill_cost_data = [
        ["Difficulty", "1 pt", "2 pts", "4 pts", "8 pts", "16 pts", "32 pts", "64 pts", "128 pts"],
        ["Easy",      "Attr+0", "Attr+1", "Attr+2", "Attr+3", "Attr+4", "Attr+5", "Attr+6", "Attr+7"],
        ["Average",   "Attr-1", "Attr+0", "Attr+1", "Attr+2", "Attr+3", "Attr+4", "Attr+5", "Attr+6"],
        ["Hard",      "Attr-2", "Attr-1", "Attr+0", "Attr+1", "Attr+2", "Attr+3", "Attr+4", "Attr+5"],
        ["Very Hard", "Attr-3", "Attr-2", "Attr-1", "Attr+0", "Attr+1", "Attr+2", "Attr+3", "Attr+4"],
    ]
    skill_cost_data[0] = [Paragraph(c, S['TableHeader']) for c in skill_cost_data[0]]
    for i in range(1, len(skill_cost_data)):
        skill_cost_data[i] = [Paragraph(c, S['TableCellCenter']) for c in skill_cost_data[i]]
    story.append(Table(skill_cost_data, colWidths=[0.85*inch]+[0.62*inch]*8,
                        style=table_style()))
    story.append(sp(3))
    story.append(body(
        "<b>Example — Research (IQ/Hard), IQ 9:</b>"
    ))
    story.append(bullet("Spend 1 pt: Research 7 (IQ 9 - 2)"))
    story.append(bullet("Spend 1 more pt (2 total): Research 8 (IQ 9 - 1)"))
    story.append(bullet("Spend 2 more pts (4 total): Research 9 (IQ 9 +0)"))
    story.append(bullet("Spend 4 more pts (8 total): Research 10 (IQ 9 +1)"))
    story.append(bullet("Spend 8 more pts (16 total): Research 11 (IQ 9 +2)"))
    story.append(sp(2))
    story.append(body(
        "<b>Example — Brawling (DX/Easy), DX 9:</b>"
    ))
    story.append(bullet("Spend 1 pt: Brawling 9 (DX 9 +0) — already useful"))
    story.append(bullet("Spend 1 more pt (2 total): Brawling 10"))
    story.append(bullet("Spend 2 more pts (4 total): Brawling 11"))
    story.append(sp(3))
    story.append(body("<b>Skill Buying Strategy:</b> For most characters, aim for:"))
    story.append(bullet("3–4 <i>signature</i> skills at 11–13 (your specialty and defining competence)"))
    story.append(bullet("5–8 <i>competent</i> skills at 9–10 (useful secondary abilities)"))
    story.append(bullet("4–6 <i>dabbling</i> skills at 8 (basic familiarity, defaults)"))
    story.append(body("Don't spread too thin — better to be exceptional at a few things than mediocre at many."))
    story.append(sp(3))

    story += subsection("Complete Skill List by Category")
    skills_table_data = [
        ["Skill", "Attr / Difficulty", "Notes"],
        # COMBAT
        ["— COMBAT SKILLS —", "", ""],
         ["Guns (Pistol)", "DX/Easy", "Derringers, semi-automatic pistols"],
         ["Guns (Revolver)", "DX/Easy", "Revolvers of all calibres"],
        ["Guns (Rifle)", "DX/Easy", "Rifles, muskets, carbines"],
        ["Guns (Shotgun)", "DX/Easy", "Scatter weapons"],
        ["Fast-Draw (Pistol)", "DX/Easy", "Quick weapon draw from holster"],
        ["Brawling", "DX/Easy", "Untrained street fighting"],
        ["Boxing", "DX/Average", "Trained fisticuffs with technique"],
        ["Knife", "DX/Easy", "Combat knife use"],
        ["Axe/Mace", "DX/Average", "Heavy blunt/edged weapons"],
        ["Bayonet", "DX/Average", "Rifle-mounted blade"],
        ["Wrestling", "DX/Average", "Grappling and takedowns"],
        ["Throwing", "DX/Average", "Thrown weapons in general"],
        ["Thrown Weapon (Knife)", "DX/Easy", "Throwing knives specifically"],
        ["Gunner (Machine Gun)", "DX/Easy", "Vehicle-mounted machine guns, heavy weapon emplacements"],
        ["Gunner (Cannon)", "DX/Easy", "Artillery pieces, ship cannons, field guns"],
        ["Shortsword", "DX/Average", "Light one-handed blades; includes sabre, cutlass"],
        ["Broadsword", "DX/Average", "Heavy one-handed blades; includes longsword"],
        ["Polearm", "DX/Average", "Long hafted weapons; spears, halberds, pikes"],
        ["Shield", "DX/Easy", "Block and parry with any shield type"],
        # SOCIAL
        ["— SOCIAL SKILLS —", "", ""],
        ["Fast-Talk", "IQ/Average", "Con, deceive, talk your way out"],
        ["Intimidation", "Will/Average", "Threaten and coerce others"],
        ["Diplomacy", "IQ/Hard", "Negotiate peacefully; reach compromise"],
        ["Public Speaking", "IQ/Average", "Address crowds effectively"],
        ["Acting", "IQ/Average", "Disguise emotions; theatrical performance"],
        ["Leadership", "IQ/Average", "Command and inspire others"],
        ["Detect Lies", "Per/Hard", "Spot deception and falsehood"],
        ["Interrogation", "IQ/Average", "Extract information under pressure"],
        ["Observation", "Per/Average", "Notice and remember details"],
        ["Psychology", "IQ/Hard", "Understand and predict people"],
        ["Savoir-Faire", "IQ/Easy", "Social graces (specify class)"],
        ["Sex Appeal", "HT/Average", "Attract, seduce, or distract through charisma"],
        ["Panhandling", "IQ/Easy", "Beg for money or favours on the street"],
        ["Disguise", "IQ/Average", "Change appearance convincingly"],
        ["Forgery", "IQ/Hard", "Create fake documents"],
        ["Holdout", "IQ/Average", "Conceal objects on your person"],
        # KNOWLEDGE
        ["— KNOWLEDGE SKILLS —", "", ""],
        ["Research", "IQ/Average", "Find information in libraries"],
        ["Writing", "IQ/Average", "Compose documents, reports"],
        ["History", "IQ/Hard", "Historical knowledge"],
        ["Literature", "IQ/Hard", "Literary and cultural knowledge"],
        ["Occultism", "IQ/Average", "General supernatural lore"],
        ["Hidden Lore", "IQ/Average", "Specific secret knowledge (specify type)"],
        ["Thaumatology", "IQ/Very Hard", "Deep magic theory"],
        ["Theology", "IQ/Hard", "Religious doctrine and practice"],
        ["Religious Ritual", "IQ/Hard", "Conduct religious ceremonies"],
        ["Appraisal", "IQ/Average", "Value items and artifacts"],
        ["Merchant", "IQ/Average", "Trade, negotiation, market knowledge"],
        ["Criminology", "IQ/Average", "Crime investigation methods"],
        ["Explosives (Demolition)", "IQ/Average", "Prepare and set explosives to destroy targets"],
        ["Diagnosis", "IQ/Hard", "Identify ailments and conditions"],
        ["Physician", "IQ/Hard", "Medical treatment and surgery"],
        ["Surgery", "IQ/Very Hard", "Invasive medical procedures; requires Physician"],
        ["Pharmacy", "IQ/Hard", "Drug and remedy preparation"],
        ["Law (specify)", "IQ/Hard", "Legal knowledge; specializations include Military, Criminal, Civil"],
        ["Connoisseur (specify)", "IQ/Average", "Expert knowledge of quality/value in a specific field (antiques, art, wine, etc.)"],
        ["Streetwise", "IQ/Average", "Urban underworld knowledge"],
        ["Gambling", "IQ/Average", "Games of chance"],
        ["Area Knowledge", "IQ/Easy", "Specific region (specify)"],
        ["Current Affairs", "IQ/Easy", "Recent events (specify topic)"],
        ["Cryptography", "IQ/Hard", "Create and break codes, ciphers, and hidden messages"],
        ["Alchemy", "IQ/Very Hard", "Transform substances; prepare elixirs, alchemical potions, and magical compounds"],
        ["Ritualistic Magic", "IQ/Very Hard", "Perform supernatural rituals: divination, summoning, binding, enchanting; the core Beyonder skill"],
        # THIEF
        ["— THIEF SKILLS —", "", ""],
        ["Pickpocket", "DX/Hard", "Steal from people's person"],
        ["Lockpicking", "IQ/Average", "Open locks without key"],
        ["Stealth", "DX/Average", "Move silently, avoid detection"],
        ["Shadowing", "IQ/Average", "Follow without being noticed"],
        ["Traps", "IQ/Average", "Detect, disarm, set traps"],
        # PHYSICAL
        ["— PHYSICAL SKILLS —", "", ""],
        ["Climbing", "DX/Average", "Scale surfaces and walls"],
        ["Knot-Tying", "DX/Easy", "Bind, secure, and rig ropes; escape bonds at -2"],
        ["Acrobatics", "DX/Hard", "Tumbling, balance, gymnastics"],
        ["Aerobatics", "DX/Hard", "Aerial maneuvers, stunts, and diving"],
        ["Running", "HT/Average", "Sprint and long-distance endurance"],
        ["Swimming", "HT/Easy", "Move through water"],
        ["Jumping", "DX/Easy", "Leap distances"],
        ["Lifting", "HT/Average", "Hoist heavy loads"],
        ["Hiking", "HT/Average", "Long-distance foot travel; pace and endurance overland"],
        ["First Aid", "IQ/Easy", "Emergency medical care"],
        # CRAFT
        ["— CRAFT & TECHNICAL —", "", ""],
        ["Mechanic", "IQ/Average", "Repair machines (specify type)"],
        ["Engineering", "IQ/Hard", "Design and analyse mechanical systems, structures, and blueprints"],
        ["Armoury (any)", "IQ/Average", "Repair and maintain weapons"],
        ["Electrician", "IQ/Average", "Work with electrical systems"],
        ["Inventor!", "IQ/Wildcard", "Wildcard skill covering all invention, engineering, and mechanical tasks"],
        # SPIRITUAL
        ["— SPIRITUAL SKILLS (SPI-based) —", "", "SPI skills cannot be raised with character points — they improve only through Sequence progression and pathway bonuses."],
        ["Spiritual Intuition", "SPI/Hard", "Sense fate-changes and danger through spirit"],
        ["Spiritual Perception", "SPI/Average", "Detect hidden spirits and supernatural phenomena"],
        ["Divination Arts", "SPI/Hard", "Perform focused divination: pendulum, coin, dowsing, dream interpretation, scrying, tarot"],
        # KNOWLEDGE (continued)
        # SURVIVAL
        ["— SURVIVAL & OTHER —", "", ""],
        ["Survival", "Per/Average", "Live off land (specify terrain)"],
        ["Urban Survival", "Per/Average", "Survive in urban environments"],
        ["Scrounging", "Per/Easy", "Find useful items in unlikely places"],
        ["Navigation", "IQ/Average", "Find your way; chart courses"],
        ["Tracking", "Per/Average", "Follow trails and quarry"],
        ["Seamanship", "IQ/Easy", "Work aboard ships"],
        ["Camouflage", "IQ/Easy", "Hide yourself or objects"],
        ["Tactics", "IQ/Hard", "Military and combat planning"],
        ["Fortune Telling", "IQ/Average", "Read cards, palms; mundane methods"],
        ["Astrology", "IQ/Hard", "Interpret celestial patterns for divination, navigation, and fate-reading"],
         ["Cogitation", "Will/Hard", "A focused mental state that allows Beyonders to stabilise their spirituality, resist mental interference, and prepare for divination or spirit-related abilities. Replaces Meditation for Beyonder purposes."],
        ["Carousing", "HT/Easy", "Drink and socialize effectively"],
        ["Weather Sense", "IQ/Average", "Predict weather from natural observation"],
        ["Boating (Sailboat)", "DX/Average", "Sail and maneuver sailing vessels"],
        ["Boating (Unpowered)", "DX/Average", "Row and handle small unpowered boats"],
        # INVESTIGATION & DETECTION
        ["— INVESTIGATION & DETECTION —", "", ""],
        ["Body Language", "Per/Average", "Read physical cues; posture, expression, tells"],
        ["Forensics", "IQ/Hard", "Scientific crime scene investigation"],
        ["Intelligence Analysis", "IQ/Hard", "Evaluate and interpret gathered information"],
        ["Search", "Per/Average", "Systematically locate hidden objects or people"],
        ["Lip Reading", "Per/Average", "Understand speech without hearing it"],
        ["Cartography", "IQ/Average", "Read, draw, and interpret maps"],
        # PERFORMANCE & ARTS
        ["— PERFORMANCE & ARTS —", "", ""],
        ["Performance", "IQ/Average", "General stage and platform performance"],
        ["Singing", "HT/Easy", "Vocal performance; also used by Bards for Beyonder abilities"],
        ["Musical Instrument", "IQ/Hard", "Play a specific instrument (specify)"],
        ["Dancing", "DX/Average", "Formal and social dance"],
        ["Artist (Drawing)", "IQ/Hard", "Illustration and portraiture"],
        ["Artist (Painting)", "IQ/Hard", "Painted works on canvas or paper"],
        ["Ventriloquism", "IQ/Hard", "Project voice to deceive listeners"],
        ["Poetry", "IQ/Average", "Write verse; also aids public speaking"],
        # ACADEMIC
        ["— ACADEMIC —", "", ""],
        ["Accounting", "IQ/Hard", "Financial records and business maths"],
        ["Administration", "IQ/Average", "Bureaucratic management and procedure"],
        ["Economics", "IQ/Hard", "Markets, trade, and financial systems"],
        ["Philosophy", "IQ/Hard", "Formal logic and ethical reasoning"],
        ["Linguistics", "IQ/Hard", "Study of language structure; accelerates language learning"],
        ["Anthropology", "IQ/Hard", "Cultures, customs, and social structures"],
        ["Archaeology", "IQ/Hard", "Excavation and analysis of ancient sites"],
        ["Sociology", "IQ/Hard", "Broad study of human society and groups"],
        ["Astronomy", "IQ/Hard", "Celestial bodies and their movements"],
        ["Mathematics (Applied)", "IQ/Hard", "Practical maths for engineering and science"],
        ["Chemistry", "IQ/Hard", "Compounds, reactions, and substances"],
        ["Physics", "IQ/Very Hard", "Natural laws governing matter and energy; requires Mathematics"],
        ["Teaching", "IQ/Average", "Instruct and educate others effectively"],
        ["Speed-Reading", "IQ/Average", "Read and comprehend text at high speed"],
        # TRADE & CRAFT
        ["— TRADE & CRAFT —", "", ""],
        ["Carpentry", "IQ/Easy", "Work with wood; build and repair structures"],
        ["Masonry", "IQ/Easy", "Stonework and brick construction"],
        ["Sewing", "DX/Easy", "Stitch, repair, and make garments"],
        ["Leatherworking", "DX/Easy", "Craft and repair leather goods and harnesses"],
        ["Smith (Iron)", "IQ/Average", "Forge and work iron tools and parts"],
        ["Cooking", "IQ/Average", "Prepare food; basic herbalism uses this as default"],
        ["Jeweler", "IQ/Hard", "Work with precious metals and gems"],
        ["Machinist", "IQ/Average", "Operate and maintain machine tools"],
        ["Photography", "IQ/Average", "Operate cameras; develop images in darkroom"],
        ["Freight Handling", "IQ/Average", "Dock and warehouse logistics"],
        # ANIMALS & OUTDOORS
        ["— ANIMALS & OUTDOORS —", "", ""],
        ["Animal Handling (any)", "IQ/Average", "Control and care for animals (specify type)"],
        ["Riding (Horse)", "DX/Average", "Ride and direct a mounted animal at speed"],
        ["Falconry", "IQ/Average", "Train and hunt with birds of prey"],
        ["Fishing", "Per/Easy", "Catch fish; read water conditions"],
        ["Gardening", "IQ/Easy", "Cultivate plants in managed spaces"],
         ["Farming", "IQ/Easy", "Cultivate crops and manage farmland"],
        ["Naturalist", "IQ/Hard", "Broad knowledge of plants, animals, and ecology"],
        ["Herbal Medicine", "IQ/Very Hard", "Natural therapeutic use of plants; requires Naturalist"],
        ["Herb Lore", "IQ/Very Hard", "Magical/occult plant knowledge; preparation of mystical herbal remedies and poisons"],
        ["Veterinary", "IQ/Hard", "Medical diagnosis and treatment for animals"],
        # UNDERWORLD & COVERT
        ["— UNDERWORLD & COVERT —", "", ""],
        ["Filch", "DX/Average", "Swipe items from surfaces without notice"],
        ["Sleight of Hand", "DX/Hard", "Conceal and manipulate objects in plain sight"],
        ["Escape", "DX/Hard", "Free oneself from bonds and confinement"],
        ["Counterfeiting", "IQ/Hard", "Replicate currency or official seals"],
        ["Smuggling", "IQ/Average", "Move contraband past inspections"],
        ["Poisons", "IQ/Hard", "Know, prepare, and apply toxins; also detect them"],
        # MILITARY & NAVAL
        ["— MILITARY & NAVAL —", "", ""],
        ["Soldier", "IQ/Average", "General military knowledge, drill, and doctrine"],
        ["Strategy", "IQ/Hard", "Large-scale military and operational planning"],
        ["Forward Observer", "IQ/Average", "Direct artillery or ranged fire from a distant position"],
        ["Shiphandling (Ship)", "IQ/Hard", "Command and navigate a large sailing or steam vessel"],
        ["Navigation (Sea)", "IQ/Average", "Determine course by stars and charts at sea"],
        ["Navigation (Land)", "IQ/Average", "Orienteer and chart routes overland"],
    ]
    skills_table_data[0] = [Paragraph(c, S['TableHeader']) for c in skills_table_data[0]]
    for i in range(1, len(skills_table_data)):
        row = skills_table_data[i]
        if row[1] == "":
            # Category header
            skills_table_data[i] = [
                Paragraph(f"<b>{row[0]}</b>", ParagraphStyle('CatHdr', fontName='Times-Bold',
                    fontSize=9, textColor=CREAM)),
                Paragraph("", S['TableCell']),
                Paragraph("", S['TableCell']),
            ]
        else:
            skills_table_data[i] = [
                Paragraph(row[0], S['TableCell']),
                Paragraph(row[1], S['TableCellCenter']),
                Paragraph(row[2], S['TableCell']),
            ]
    sk_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), MID_NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), CREAM),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,1), (-1,-1), 'Times-Roman'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.4, SILVER),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ])
    for i, row in enumerate(skills_table_data):
        if i > 0 and isinstance(row[1], Paragraph) and row[1].text == "":
            sk_style.add('BACKGROUND', (0,i), (-1,i), DARK_BG)
            sk_style.add('TEXTCOLOR', (0,i), (-1,i), GOLD)
            sk_style.add('SPAN', (0,i), (-1,i))
            sk_style.add('FONTNAME', (0,i), (-1,i), 'Times-Bold')
        elif i % 2 == 0 and i > 0:
            sk_style.add('BACKGROUND', (0,i), (-1,i), colors.HexColor("#EEF3F8"))
    sk_t = Table(skills_table_data, colWidths=[1.7*inch, 1.1*inch, 3.5*inch])
    sk_t.setStyle(sk_style)
    story.append(sk_t)
    
    story.append(PageBreak())
    story += section("Study Points (Optional Rule)")
    story.append(body(
        "Between adventures, a character may spend downtime to learn or improve mundane skills "
        "by converting time and money into <b>study points</b> — character points that can only "
        "be spent on the skill being studied."
    ))
    story.append(sp(2))

    story += subsection("Earning Study Points")
    story.append(body(
        "Pick one skill and a study method. Meet the requirements below to earn 1 character point "
        "locked to that skill."
    ))
    sp_data = [
        ["Difficulty", "With a Tutor", "Self-Study"],
        ["Easy",      "6 hrs + 4s", "12 hrs + 1s"],
        ["Average",   "12 hrs + 8s", "24 hrs + 2s"],
        ["Hard",      "24 hrs + £1", "48 hrs + 4s"],
        ["Very Hard", "48 hrs + £2", "Not possible"],
    ]
    sp_data[0] = [Paragraph(c, S['TableHeader']) for c in sp_data[0]]
    for i in range(1, len(sp_data)):
        sp_data[i] = [Paragraph(c, S['TableCell']) for c in sp_data[i]]
    story.append(Table(sp_data, colWidths=[1.2*inch, 2.0*inch, 2.0*inch], style=table_style()))
    story.append(sp(1))
    story.append(body(
        "<b>Tutor:</b> Must have the skill at Attribute+2 or higher. Max 3 students at a time."
    ))
    story.append(body(
        "<b>Self-study:</b> Requires a book, manual, or practice space (included in the cost)."
    ))
    story.append(sp(3))

    story += subsection("Spending Study Points")
    story.append(body(
        "Study points follow the same exponential ladder as normal character points "
        "(see Step 4: Skills earlier in this chapter). Each +1 in a skill costs "
        "twice as many CP as the previous +1:"
    ))
    sp_ladder = [
        ["Cumulative CP", "Easy", "Average", "Hard", "Very Hard"],
        ["1",     "Attr+0",  "Attr-1",  "Attr-2",  "Attr-3"],
        ["2",     "Attr+1",  "Attr+0",  "Attr-1",  "Attr-2"],
        ["4",     "Attr+2",  "Attr+1",  "Attr+0",  "Attr-1"],
        ["8",     "Attr+3",  "Attr+2",  "Attr+1",  "Attr+0"],
    ]
    sp_ladder[0] = [Paragraph(c, S['TableHeader']) for c in sp_ladder[0]]
    for i in range(1, len(sp_ladder)):
        sp_ladder[i] = [Paragraph(c, S['TableCell']) for c in sp_ladder[i]]
    story.append(Table(sp_ladder, colWidths=[1.2*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch], style=table_style()))
    story.append(sp(1))
    story.append(body(
        "<b>Example — Average skill:</b> Tomás (DX 10) wants Guns (Pistol) — DX/Average, "
        "default DX-5 = 5. He hires a tutor: 12 hrs + 8s earns 1 study CP -> Guns-9 (Attr-1). "
        "He studies 12 more hours (8s) for 1 more CP -> Guns-10 (Attr+0). Another 24 hours "
        "(16s) for 2 more CP -> Guns-11 (Attr+1) — the cap."
    ))
    story.append(sp(3))

    story += subsection("Limits")
    story.append(bullet("A skill cannot exceed <b>Attribute+1</b> through study alone."))
    story.append(bullet("Beyonder potion-granted skills (Chapters 9–11) cannot be studied."))
    story.append(bullet("No more than <b>two skills</b> may be studied per downtime period."))
    story.append(sp(3))

    story.append(sp(6))
    story += section("Character Creation Summary")
    story.append(bullet("70 point budget | All attributes fixed at 9 | No points refunded for baseline"))
    story.append(bullet("Attributes cost exponentially — each level doubles the previous: ST: 10 pts -> 20 pts -> 40 pts… | DX/IQ: 20 pts -> 40 pts -> 80 pts… | HT: 10 pts -> 20 pts -> 40 pts…"))
    story.append(bullet("SPI is fixed at 0 for mortals — cannot be raised with points; increased only by Beyonder potions."))
    story.append(bullet("Advantages: 10–15 pts typical | Disadvantages: 0 to -40 pts maximum (not required)"))
    story.append(bullet("Skills: ~50 pts typical | Skill Level = Attribute + Levels Purchased"))
    story.append(sp(3))
    
    story += chapter("Chapter 4: Spirituality — The Sixth Sense of the Soul")

    story.append(flavor(
        "In the world of Loen, every soul has weight. Spirituality is not faith — it is the measurable "
        "substance of one's connection to the supernatural order. Seers read it in auras, tracing faint "
        "threads of fate in the people around them. And ordinary mortals, if they are sensitive enough, feel it "
        "as a prickling at the back of the neck when something wrong walks past."
    ))
    story.append(sp(3))

    story += section("The Spirituality (SPI) Attribute")
    story.append(body(
        "SPI represents a character's connection to the spiritual world, the strength of their soul, "
        "and their capacity to perceive and manipulate supernatural forces. It differs meaningfully "
        "from related attributes:"
    ))
    spi_compare = [
        ["Attribute", "Represents", "Example"],
        ["IQ", "Mental processing, logic, learning speed", "High IQ = fast learner, logical thinker"],
        ["Will", "Mental fortitude, resisting influence", "High Will = resistant to mind control"],
        ["SPI", "Spiritual perception, fate sensitivity, supernatural connection",
         "High SPI = senses changes in fate, sees intangible things"],
    ]
    spi_compare[0] = [Paragraph(c, S['TableHeader']) for c in spi_compare[0]]
    for i in range(1, len(spi_compare)):
        spi_compare[i] = [Paragraph(c, S['TableCell']) for c in spi_compare[i]]
    story.append(Table(spi_compare, colWidths=[0.7*inch, 2.3*inch, 3.3*inch],
                        style=table_style()))
    story.append(sp(3))
    story.append(body(
        "<b>SPI cannot be raised by spending character points.</b> It is not a buyable attribute. "
        "All mortals begin at <b>SPI 0</b>, fixed. SPI increases only through Beyonder potions, "
        "supernatural events, or certain rituals."
    ))
    story.append(sp(2))
    story.append(body(
        "Not all Beyonders are created equal in spiritual power. The amount of SPI a Sequence 9 "
        "potion grants depends on the pathway's spiritual affinity, as established in the novels and wiki. "
         "Pathways confirmed to have <b>high spirituality</b> — the <b>Seer</b> (Fool), <b>Secrets Supplicant</b> "
         "(Hanged Man), <b>Sleepless</b> (Darkness), <b>Mystery Pryer</b> (Hermit), and <b>Monster</b> "
         "(Wheel of Fortune) — receive significantly more SPI than other pathways. Pathways with strong spiritual abilities at Sequence 9 "
         "receive moderate bonuses (+2 to +6). Reality-leaning pathways receive a baseline <b>+1 SPI</b>, "
        "representing the minimal spiritual awakening of becoming a Beyonder. The <b>Prisoner</b> (Chained) "
        "is a unique exception — its spirituality is actively constrained by the potion itself, granting "
        "<b>0 SPI</b> at Sequence 9."
    ))
    story.append(sp(3))

    story += section("Spiritual Skills in Detail")

    story += subsection("1. Spiritual Intuition (SPI/Hard)")
    story.append(body(
        "Sense changes in fate and detect danger through your spirit before it manifests physically. "
        "This is the soul's early-warning system — not rational thought, but a deep <i>knowing</i>."
    ))
    si_data = [
        ["Roll Result", "Effect"],
        ["Success", "Vague feeling of wrongness or impending danger"],
        ["Success by 3+", "Know approximate direction of the threat"],
        ["Success by 5+", "Specific premonition (ambush, poison, betrayal)"],
        ["Critical Success", "Brief mental vision of the exact danger"],
    ]
    si_data[0] = [Paragraph(c, S['TableHeader']) for c in si_data[0]]
    for i in range(1, len(si_data)):
        si_data[i] = [Paragraph(c, S['TableCell']) for c in si_data[i]]
    story.append(Table(si_data, colWidths=[1.5*inch, 4.8*inch], style=table_style()))
    story.append(sp(3))
    story.append(body("<b>Modifiers:</b> +2 meditative state; -2 distracted/in combat; -4 magically concealed"))
    story.append(sp(3))

    story += subsection("2. Spiritual Perception (SPI/Average)")
    story.append(body(
        "Passively sense spiritual disturbances, detect hidden spirits, and notice supernatural phenomena. "
        "The GM rolls this secretly when supernatural events occur nearby."
    ))
    sp_data = [
        ["Roll Result", "Effect"],
        ["Success", "Notice a 'spiritual weight' or unnatural presence in the area"],
        ["Success by 3+", "Pinpoint the location of the spiritual disturbance"],
        ["Success by 5+", "Identify type of entity (ghost, Beyonder, cursed item)"],
        ["Critical Success", "Detailed information: sequence level, pathway, emotional state"],
    ]
    sp_data[0] = [Paragraph(c, S['TableHeader']) for c in sp_data[0]]
    for i in range(1, len(sp_data)):
        sp_data[i] = [Paragraph(c, S['TableCell']) for c in sp_data[i]]
    story.append(Table(sp_data, colWidths=[1.5*inch, 4.8*inch], style=table_style()))
    story.append(sp(3))
    story.append(body("<b>Modifiers:</b> +2 graveyard/ritual site; -2 industrial/polluted area; -4 entity hiding; +6 Seer"))
    story.append(sp(3))

    story += subsection("3. Spirit Vision")
    story.append(body(
        "See the non-physical aspects of beings — their Ether Body (health), Spirit Body (emotions), and auras. "
        "<b>Cost:</b> 1 SPI per minute."
    ))
    sv_data = [
        ["Aura Layer", "Color Meanings"],
        ["Health (Ether Body)", "White/bright = healthy; Dark/thin = sick; Red patches = fever; Black spots = curse or illness"],
        ["Emotions (Astral Body)",
         "Red = anger/passion; Orange = comfort; Yellow = happiness; Green = calm/peace; "
         "Blue = cold logic; Purple = high spirituality; Dark = sorrow/depression"],
    ]
    sv_data[0] = [Paragraph(c, S['TableHeader']) for c in sv_data[0]]
    for i in range(1, len(sv_data)):
        sv_data[i] = [Paragraph(c, S['TableCell']) for c in sv_data[i]]
    story.append(Table(sv_data, colWidths=[1.4*inch, 4.9*inch], style=table_style()))
    story.append(sp(3))

    story.append(body(
        "Spirit Vision's clarity improves with the user's SPI and Sequence, not through skill points. "
        "As a Beyonder ability, its effectiveness scales naturally:"
    ))
    story.append(bullet("<b>Low Sequence (Seq 9–7):</b> Basic auras — vague colours, hard to distinguish detail. SPI typically 0–8, with spiritually-attuned pathways (e.g. Hermit) reaching higher."))
    story.append(bullet("<b>Mid Sequence (Seq 6–4):</b> Clear auras; identify health status and strong emotions. Can estimate the Sequence level of other Beyonders. SPI typically 6–14."))
    story.append(bullet("<b>High Sequence (Seq 3+):</b> Transcendent perception; can analyze soul structure and destiny threads. SPI typically 12+."))
    story.append(sp(3))

    story += subsection("4. Ritualistic Magic (IQ/Very Hard)")
    story.append(body(
        "Perform supernatural rituals to achieve magical effects: summoning, binding, enchanting, "
        "divination, and prayer. The most powerful and dangerous spiritual skill."
    ))
    story.append(body(
        "<i>See <b>Chapter 7: Ritualistic Magic</b> for the complete ritual system — "
        "resolution procedures, modifiers, power sources, effect categories, failure tables, "
        "and sequence considerations.</i>"
    ))
    story.append(sp(2))

    story += subsection("5. Divination Arts (SPI/Hard)")
    story.append(body(
        "Perform focused divination using spiritual techniques: pendulum, coin, dowsing, dream "
        "interpretation, mirror scrying, tarot, and other methods of obtaining hidden knowledge. "
        "Faster and cheaper than full ritual divination, but limited to questions that can be "
        "answered through spiritual insight alone."
    ))
    story.append(body(
        "<i>See <b>Chapter 6.5: Divination Arts</b> for the complete system — methods, "
        "procedures, modifiers, awareness, and countermeasures.</i>"
    ))
    story.append(sp(2))

    story += section("Spirituality Recovery")
    story.append(body(
        "Spirituality (SPI) is a finite resource. Once spent on abilities, rituals, and skills, it "
        "must be carefully restored through rest."
    ))
    story.append(sp(2))

    story.append(body("<b>Rest:</b>"))
    story.append(body(
        "A character who rests — sitting quietly, sleeping, or engaging in no strenuous physical or "
        "spiritual activity — recovers <b>1 SPI per hour</b>. This is the standard and only recovery rate. "
        "Combat, ritual casting, or heavy physical exertion interrupts rest and halts recovery."
    ))
    story.append(sp(3))

    # ─────────────────────────────────────────────────────────────────────────────
    # SPI Threshold Penalties
    # ─────────────────────────────────────────────────────────────────────────────
    story += subsection("SPI Threshold Penalties")
    story.append(body(
        "As SPI is depleted, the spirit body weakens. Track SPI loss against your maximum SPI "
        "value just like HP:"
    ))
    story.append(sp(1))

    spi_threshold_data = [
        ["SPI Level", "Effect"],
        ["SPI to 1", "Normal function; no penalties"],
        ["<= 1/3 Max SPI", "Spiritual Attrition: -3 to all SPI-based skill rolls and Beyonder ability checks"],
        ["0 SPI", "Spiritual Exhaustion: All Beyonder abilities deactivate; cannot activate any SPI-cost abilities; Spirit Vision shuts off"],
         ["Below 0 SPI", "Soul Debt: +1 CoR per 1 point below 0 (e.g. SPI -4 = +4 CoR). See CoR (Chapter 6)."],
    ]
    spi_threshold_data[0] = [Paragraph(c, S['TableHeader']) for c in spi_threshold_data[0]]
    for i in range(1, len(spi_threshold_data)):
        spi_threshold_data[i] = [Paragraph(c, S['TableCell']) for c in spi_threshold_data[i]]
    story.append(Table(spi_threshold_data, colWidths=[1.3*inch, 5.0*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "Unlike HP depletion, there is no risk of death from SPI loss. SPI recovers at 1 per hour "
        "of rest (see Spirituality Recovery, above). CoR from soul debt are permanent "
        "and require special rituals (Chapter 6) to remove."
    ))
    story.append(sp(3))

    story.append(body(
        "<i>See <b>Chapter 6.5: Divination Arts</b>, Section IV, for the complete rules on "
        "detecting, resisting, and countering divination — including passive awareness, "
        "detection mechanics, active anti-divination techniques, items, and Sequence immunity.</i>"
    ))
    story.append(sp(3))

    story += chapter("Chapter 5: Combat — Violence in the Fog")

    story.append(flavor(
        "Gunfights in Backlund's alleys are brief and brutal. A revolver shot at close range ends arguments "
        "permanently. Beyonders fight differently — with inhuman speed, supernatural senses, and abilities "
        "that make conventional tactics useless. Learn to fight, or learn to run."
    ))
    story.append(sp(3))

    story += section("Initiative and Turn Order")
    story.append(body(
        "Combat is simultaneous in fiction but sequential in play. Turn order is determined at the "
        "start of each combat and stays fixed for the entire fight unless a character's Basic Speed "
        "changes (from injury or supernatural effects)."
    ))
    init_data = [
        ["Priority", "Rule"],
        ["1st",  "Highest Basic Speed acts first."],
        ["Tie",  "Highest DX breaks the tie."],
        ["Still tied", "Roll 1d6 — higher result goes first. Stays fixed for the fight."],
        ["Surprise", "Surprised characters skip their first turn entirely and cannot defend on it."],
    ]
    init_data[0] = [Paragraph(c, S['TableHeader']) for c in init_data[0]]
    for i in range(1, len(init_data)):
        init_data[i] = [Paragraph(init_data[i][j],
            S['TableCellCenter'] if j == 0 else S['TableCell']) for j in range(2)]
    story.append(Table(init_data, colWidths=[1.0*inch, 5.3*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Basic Speed reminder:</b> Basic Speed = (HT + DX) / 4. At starting attributes of 9, "
        "all characters begin at Basic Speed 4.50. Raising DX or HT raises your speed. "
        "Combat Reflexes does not raise Basic Speed but grants a +1 to all active defenses and "
        "prevents freezing on surprise — a strong pick for any fighter."
    ))
    story.append(sp(3))

    story += section("The Combat Round")
    story.append(body(
        "Each combat round represents approximately 1 second. On your turn, you choose one <b>maneuver</b>. "
        "When attacked, you may attempt one or more <b>active defenses</b>."
    ))
    story.append(sp(3))

    story += section("Maneuvers (Choose One Per Turn)")
    maneuver_data = [
        ["Maneuver", "Movement", "Description"],
        ["Move", "Full Move", "Move up to your full Basic Move in meters. May face any direction."],
        ["Ready", "Step", "Reload a weapon, draw an item, drink a vial, or prepare equipment."],
        ["Aim (Ranged)", "Step", "Add weapon's ACC to your next ranged Attack. +1 per additional Aim (max ACC+2). Canceled by any Active Defense or injury."],
        ["Do Nothing", "None", "If Stunned: -4 to Active Defense. Otherwise rest to recover FP."],
        ["Concentrate", "Step*", "Channel powers or skills requiring focus. Roll Will-3 if injured or defending."],
        ["Wait", "—", "Define a trigger; if it occurs, perform your chosen maneuver immediately."],
        ["Regular Attack", "Step", "Make one melee or ranged attack. Step 1 meter before or after."],
        ["All-Out Attack (Determined)", "Step", "Pay 2 FP. +4 to hit melee, +1 to hit ranged. Cannot defend next turn."],
        ["All-Out Attack (Strong)", "Step", "Pay 2 FP. +2 to damage. Cannot defend next turn."],
        ["All-Out Attack (Double)", "Step", "Pay 2 FP. Two separate attacks (roll twice). Cannot defend next turn."],
        ["Charge Attack", "Full Move", "Move full distance, then attack. -4 to hit. Cannot defend next turn."],
        ["All-Out Defense (Increased)", "Step", "Pay 2 FP. +2 to one active defense until next turn. Cannot attack."],
        ["All-Out Defense (Double)", "Step", "Pay 2 FP. Use two different defenses vs. one attack. Cannot attack."],
        ["Feint", "Step", "Roll a Quick Contest of your Melee skill vs. opponent's Melee, Cloak, Shield, or DX. If you succeed (or succeed by more), subtract your margin of success/victory from their active defense on your next Attack, All-Out Attack, or Move and Attack this turn."],
    ]
    maneuver_data[0] = [Paragraph(c, S['TableHeader']) for c in maneuver_data[0]]
    for i in range(1, len(maneuver_data)):
        maneuver_data[i] = [Paragraph(maneuver_data[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(3)]
    story.append(Table(maneuver_data, colWidths=[1.7*inch, 0.7*inch, 3.9*inch],
                        style=table_style()))
    story.append(sp(3))

    story += subsection("Extra Effort Options (Costs FP)")
    story.append(bullet("<b>[Free Action]</b> [Giant Step] Pay 1 FP: Take an extra step before or after attack"))
    story.append(bullet("<b>[Free Action]</b> [Strong Blow] Pay 1 FP: +2 damage. Regular melee attacks only."))
    story.append(bullet("<b>[Free Action]</b> [Heroic Charge] Pay 2 FP: Ignore Charge Attack penalties (-4 to hit)"))
    story.append(bullet("<b>[Free Action]</b> [Feverish Defense — Variant Rule] Pay 1 FP: +2 to one defense roll. Cannot defend next turn."))
    story.append(sp(3))

    story += section("Attack Options")
    story.append(body(
        "Unlike full maneuvers (which define your entire action for a turn), <b>Attack Options</b> are "
        "modifiers you can apply <i>to an attack</i> within an Attack, All-Out Attack, or Move and Attack "
        "maneuver. You may combine multiple attack options on the same attack."
    ))
    story.append(bullet(
        "<b>Rapid Strike:</b> Split a melee Attack maneuver into <i>two</i> separate attacks against "
        "the same or different targets. Both attacks suffer -6 to skill. Additional rapid strikes "
        "in the same maneuver stack the penalty."
    ))
    story.append(bullet(
        "<b>Deceptive Attack:</b> Take a -2 penalty to your melee attack roll for every -1 you wish "
        "to impose on the target's active defense against that attack. Maximum penalty is half your "
        "skill (rounded down). Can be combined with Rapid Strike (apply to each attack separately)."
    ))
    story.append(sp(3))

    story += section("Active Defenses")
    story.append(body(
        "When you know you are being attacked, you may attempt one active defense "
        "(unless you took an All-Out Attack maneuver). Each type may be used multiple times per round, "
        "but Parry accumulates a -4 cumulative penalty after the first (-2 for fencing weapons)."
    ))
    story.append(body(
        "<b>Free Actions:</b> Retreat, Acrobatic Dodge, and Dive! are <b>free actions</b> — they do "
        "not cost your maneuver and can be taken alongside any active defense. Each can be used "
        "once per round unless stated otherwise."
    ))
    def_data = [
        ["Defense", "Formula", "Notes"],
        ["Dodge", "Basic Speed (drop fractions) + 3", "Universal; no weapon required. May be used repeatedly."],
        ["Parry (Armed)", "Weapon Skill ÷ 2 + 3", "Weapon must be ready. Cumulative -4 per additional parry (-2 fencing, -1 rapier)."],
        ["Parry (Unarmed)", "Brawling or DX ÷ 2 + 3", "Brawling parries weapons at -3. Boxing uses Boxing ÷ 2 + 3 and ignores that penalty. Cannot parry ranged attacks."],
        ["Block", "Shield Skill ÷ 2 + 3", "Once per round. Add shield's DB to your Block score."],
    ]
    def_data[0] = [Paragraph(c, S['TableHeader']) for c in def_data[0]]
    for i in range(1, len(def_data)):
        def_data[i] = [Paragraph(c, S['TableCell']) for c in def_data[i]]
    story.append(Table(def_data, colWidths=[0.9*inch, 1.5*inch, 3.9*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Defense Modifiers")
    story.append(bullet("Attacked from side: -2 to defense"))
    story.append(bullet("Attacked from rear: -4 to defense"))
    story.append(bullet("<b>[Free Action]</b> [Retreat] Step back 1 hex: +3 Dodge / +1 Block / +1 Parry vs. 1 melee attack per round"))
    story.append(bullet("<b>[Free Action]</b> [Acrobatic Dodge] Roll vs. Acrobatics: success gives +2 Dodge; failure gives -2 Dodge. Stacks with Retreat."))
    story.append(bullet("<b>[Free Action]</b> [Dive!] +3 Dodge vs. ranged only. Spend 1 turn getting back up (Change Posture)."))
    story.append(sp(3))

    story += subsection("Shields")
    story.append(body(
        "Shields are uncommon in Backlund's streets, but surface in the hands of riot police, Nighthawk "
        "patrols, and prepared adventurers. A shield must be Readied (one turn) to provide its benefits. "
        "While Readied, its <b>DB</b> (Defense Bonus) adds to all active defenses (Dodge, Parry, and Block) "
        "against attacks from the front or shield side. Cover DR represents how much damage the shield "
        "itself absorbs when struck — if damage exceeds Cover DR, the remainder passes through to the "
        "blocking arm (treat as arm hit) or the torso if using the shield for cover (treat as torso hit)."
    ))
    story.append(sp(2))
    shield_data = [
        ["Shield Type", "DB", "Cover DR", "HP", "Weight", "Cost", "Notes"],
        ["Light\n(buckler, target)", "+1", "3", "15", "2 kg", "£2", "Worn on forearm; frees hand; -1 to Block vs. ranged"],
        ["Medium\n(round, heater)", "+2", "5", "20", "5 kg", "£5", "Standard shield; common among watchmen and soldiers"],
        ["Heavy\n(tower, riot)", "+3", "7", "30", "10 kg", "£8", "Full body cover when crouching; Move -1 while Readied"],
        ["Improvised\n(lid, crate side)", "+1", "2", "12", "varies", "—", "-2 to Block; Shatters on damage exceeding Cover DR"],
    ]
    shield_data[0] = [Paragraph(c, S['TableHeader']) for c in shield_data[0]]
    for i in range(1, len(shield_data)):
        shield_data[i] = [Paragraph(c, S['TableCellCenter']) for c in shield_data[i]]
    story.append(Table(shield_data, colWidths=[1.1*inch, 0.4*inch, 0.6*inch, 0.4*inch, 0.6*inch, 0.5*inch, 3.7*inch],
                       style=table_style()))
    story.append(sp(1))
    story.append(bullet(
        "<b>Breaking a shield:</b> Once Cover DR is exceeded, any excess damage reduces the shield's HP. "
        "At 0 HP the shield is destroyed. A shield can be targeted directly (size penalty -5 for light, "
        "-4 for medium, -3 for heavy)."
    ))
    story.append(bullet(
        "<b>Shield as cover:</b> A Readied shield can be used to block a doorway or arrow slit on your "
        "turn. Treat it as having Cover DR equal to its listed value × 1.5 for this purpose. HP remains the same."
    ))
    story.append(bullet(
        "<b>Shield Bash:</b> Use the shield as an improvised weapon: damage = thr-2 cr for light, "
        "thr-1 cr for medium, thr cr for heavy. Skill defaults to Shield/DX or Brawling-2."
    ))
    story.append(sp(3))

    story += subsection("Melee Skills: Brawling, Boxing & Wrestling")
    story.append(sp(2))
    
    story += subsection("Brawling (DX/Easy)")
    story.append(body(
        "Brawling covers untrained street fighting — punches, kicks, elbows, knees, headbutts, and shoves. "
        "Default: DX-2 if untrained. "
        "All Brawling attacks use <b>Thrust (thr)</b> damage. "
        "Parry: Either hand at (Brawling ÷ 2 + 3). Innately ambidextrous for parrying — no penalty for using either hand."
    ))
    brawl_moves = [
        ["Attack", "Roll", "Damage", "Notes"],
        ["Punch", "Brawling", "thr-1 cr", "Most common attack"],
        ["Kick", "Brawling-2", "thr cr", "Longer reach, slower"],
        ["Elbow", "Brawling-2", "thr-2 cr", "Close range, quick"],
        ["Knee", "Brawling-2", "thr-1 cr", "Close range, quick"],
        ["Headbutt", "Brawling-3", "thr-2 cr", "Close range, risky"],
        ["Shove", "Brawling-2", "Special", "Knock down: target rolls DX or fall"],
    ]
    brawl_moves[0] = [Paragraph(c, S['TableHeader']) for c in brawl_moves[0]]
    for i in range(1, len(brawl_moves)):
        brawl_moves[i] = [Paragraph(brawl_moves[i][j],
            S['TableCellCenter'] if j == 1 else S['TableCell']) for j in range(4)]
    brawl_t = Table(brawl_moves, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 2.6*inch])
    brawl_t.setStyle(table_style())
    story.append(brawl_t)
    story.append(sp(2))
    
    story += subsection("Boxing (DX/Average)")
    story.append(body(
         "Boxing is trained fisticuffs with proper technique — jabs, crosses, hooks, and uppercuts. "
         "Boxers can parry attacks with their hands: <b>Parry = Boxing ÷ 2 + 3</b>. "
         "Unlike Brawling, Boxing parries weapons without penalty. "
         "<b>Damage Bonus:</b> +1 to all Boxing attacks at DX+1; +2 at DX+2 (max +2 without Trained by a Master)."
     ))
    box_moves = [
        ["Attack", "Roll", "Damage", "Notes"],
        ["Jab", "Boxing", "thr cr", "Quick, leading hand"],
        ["Cross", "Boxing", "thr+1 cr", "Power shot, rear hand"],
        ["Hook", "Boxing-1", "thr+1 cr", "Side attack, arcs around guard"],
        ["Uppercut", "Boxing-2", "thr+2 cr", "Upward strike, vulnerable to counter"],
    ]
    box_moves[0] = [Paragraph(c, S['TableHeader']) for c in box_moves[0]]
    for i in range(1, len(box_moves)):
        box_moves[i] = [Paragraph(box_moves[i][j],
            S['TableCellCenter'] if j == 1 else S['TableCell']) for j in range(4)]
    box_t = Table(box_moves, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 2.6*inch])
    box_t.setStyle(table_style())
    story.append(box_t)
    story.append(sp(2))
    
    story += subsection("Wrestling (DX/Average)")
    story.append(body(
        "Wrestling covers grappling, takedowns, pins, and escapes. "
        "Wrestlers can parry melee attacks with their hands at -3 to skill: <b>Parry = (Wrestling-3) ÷ 2 + 3</b>. "
        "All grappling rolls are Quick Contests of DX or Wrestling. "
        "<b>Grappling ST Bonus:</b> For grappling only (not strikes), add +1 ST at DX+1, +2 ST at DX+2 "
        "(max +2 without Wrestling Master advantage). Applies to grapples, break free, takedowns, pins, and chokes."
    ))
    wrest_moves = [
        ["Maneuver", "Roll", "Opposed Roll", "Notes"],
        ["Grapple", "Wrestling", "DX or Escape", "Initiate grapple; both roll DX"],
        ["Takedown", "Wrestling-1", "DX or Wrestling", "Knock down; target falls prone"],
        ["Pin", "Wrestling-2", "DX or Wrestling", "Immobilize; target cannot act"],
        ["Escape", "Escape-2", "DX or Wrestling", "Break free from grapple or pin"],
    ]
    wrest_moves[0] = [Paragraph(c, S['TableHeader']) for c in wrest_moves[0]]
    for i in range(1, len(wrest_moves)):
        wrest_moves[i] = [Paragraph(wrest_moves[i][j],
            S['TableCellCenter'] if j == 1 else S['TableCell']) for j in range(4)]
    wrest_t = Table(wrest_moves, colWidths=[1.3*inch, 1.1*inch, 1.3*inch, 2.5*inch])
    wrest_t.setStyle(table_style())
    story.append(wrest_t)
    story.append(sp(2))
     
    # Summary table for all three melee skills
    story += subsection("Summary: Melee Skill Comparison")
    summary_data = [
        ["Skill", "Damage Bonus", "Parry Formula", "Special Notes"],
        ["Brawling (DX/E)", "None (thr only)", "Brawling/2 + 3", "Default DX-2; innately ambidextrous for parrying"],
        ["Boxing (DX/A)", "+1 at DX+1, +2 at DX+2", "Boxing/2 + 3", "Default DX-5; trained fisticuffs; parries weapons without penalty"],
        ["Wrestling (DX/A)", "None (grapple only)", "(Wrestling-3)/2 + 3", "No default; ST bonus for grappling; parry at -3"],
    ]
    summary_data[0] = [Paragraph(c, S['TableHeader']) for c in summary_data[0]]
    for i in range(1, len(summary_data)):
        summary_data[i] = [Paragraph(c, S['TableCell']) for c in summary_data[i]]
    summary_t = Table(summary_data, colWidths=[1.2*inch, 1.5*inch, 1.5*inch, 2.3*inch])
    summary_t.setStyle(table_style())
    story.append(summary_t)
    story.append(sp(3))
    
    story += section("Ranged Combat")
    story.append(body(
        "Shooting works like melee — roll 3d6 against your Guns skill — but distance, visibility, "
        "and movement impose penalties that make accurate fire genuinely difficult. The setting "
        "runs on TL5+1 weapons: revolvers, rifles, and early semi-automatics. A hit at close "
        "range from a revolver is lethal for ordinary mortals."
    ))
    story.append(sp(2))
    story += subsection("Range Penalties")
    range_data = [
        ["Distance to Target", "Penalty"],
        ["Up to 2 meters (close — arm's reach)", "+0"],
        ["3–5 meters (short)",  "-1"],
        ["6–10 meters",         "-2"],
        ["11–20 meters",        "-3"],
        ["21–50 meters",        "-4"],
        ["51–100 meters",       "-5"],
        ["100+ meters",         "-6 or worse (GM discretion)"],
    ]
    range_data[0] = [Paragraph(c, S['TableHeader']) for c in range_data[0]]
    for i in range(1, len(range_data)):
        range_data[i] = [Paragraph(range_data[i][j],
            S['TableCellCenter'] if j == 1 else S['TableCell']) for j in range(2)]
    story.append(Table(range_data, colWidths=[3.2*inch, 3.1*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Other Ranged Modifiers")
    ranged_mod_data = [
        ["Condition", "Modifier"],
        ["Target is stationary",             "+0"],
        ["Target walking (up to 3 meters/sec)","-1"],
        ["Target running (4+ meters/sec)",    "-2"],
        ["Shooter moved this turn",          "-2"],
        ["Shooter used Aim last turn",       "+ weapon's Acc (see weapon table)"],
        ["Shooter used Aim for 3+ turns",    "+ weapon's Acc +2 (max Acc +2 total)"],
        ["Target is prone",                  "-2 ranged (but -4 in melee)"],
        ["Darkness or heavy fog",            "-3 to -9 depending on severity"],
        ["Target has cover (half body)",     "-2 to hit, +2 DR on covered areas"],
    ]
    ranged_mod_data[0] = [Paragraph(c, S['TableHeader']) for c in ranged_mod_data[0]]
    for i in range(1, len(ranged_mod_data)):
        ranged_mod_data[i] = [Paragraph(ranged_mod_data[i][j],
            S['TableCellCenter'] if j == 1 else S['TableCell']) for j in range(2)]
    story.append(Table(ranged_mod_data, colWidths=[3.5*inch, 2.8*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Dodging ranged attacks:</b> You may Dodge normally. If you did not know the shot was "
        "coming (no visible wind-up, fired from concealment), you cannot defend at all — the bullet "
        "arrives before you can react. This is why Danger Sense and Spiritual Intuition are valuable."
    ))
    story.append(body(
        "<b>Guns and reloading:</b> Most revolvers hold 5–6 shots. Rifles hold 1 (single-shot) to "
        "5–10 (magazine). Reloading takes one Ready maneuver per round for revolvers "
        "(speed-loaders halve this). Running out of ammunition mid-fight is a real tactical concern."
    ))
    story.append(sp(3))

    story += section("Damage & Injury")
    story.append(body(
        "Damage reduces HP. When HP reaches 0 or below, roll 3d6 <b>against your HT</b> each turn or fall "
        "unconscious. Death occurs at -HP (negative of your full HP total) — roll vs. <b>HT</b> to survive. "
        "At -5×HP, death is automatic with no roll."
    ))
    damage_data = [
        ["HP Level", "Effect"],
        ["HP to 1", "Normal function; no penalties"],
        ["1/3 HP remaining", "Reeling: -1 to all rolls"],
        ["0 HP", "Roll 3d6 <= HT or fall unconscious; roll each turn to remain conscious"],
        ["-HP", "Roll vs. HT or die; must roll vs. HT each turn while below this threshold"],
        ["-5×HP", "Dead — no roll required"],
    ]
    damage_data[0] = [Paragraph(c, S['TableHeader']) for c in damage_data[0]]
    for i in range(1, len(damage_data)):
        damage_data[i] = [Paragraph(c, S['TableCell']) for c in damage_data[i]]
    story.append(Table(damage_data, colWidths=[1.3*inch, 5.0*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Spirit Body Damage")
    story.append(body(
        "Some Beyonder abilities and supernatural effects deal damage directly to the spirit body "
        "rather than the physical body. Spirit body damage bypasses physical Damage Resistance (DR) "
        "entirely — but the <b>target chooses how to absorb it</b>."
    ))
    story.append(sp(1))
    story.append(body("<b>Choosing a Pool:</b>"))
    story.append(bullet(
        "When an effect deals spirit body damage, the target chooses which of three pools it reduces: "
        "<b>HP</b>, <b>FP</b>, or <b>SPI</b>."
    ))
    story.append(bullet("Choose <b>before</b> the damage is rolled."))
    story.append(bullet("One pool per instance — you cannot split a single hit across multiple pools."))
    story.append(bullet("You <b>may</b> choose a pool already at 0 (risking death, unconsciousness, or Soul Debt)."))
    story.append(sp(1))
    story.append(body("<b>Damage Application:</b>"))
    story.append(bullet(
        "Wounding multipliers apply normally to the chosen pool (Cut ×1.5, Imp ×2, etc.). "
        "Damage-type multipliers (e.g. skull ×4, vitals ×3) stack with wounding multipliers when applied to HP."
    ))
    story.append(bullet("Physical DR does not protect against spirit body damage."))
    story.append(bullet("Spiritual DR (if any) does apply, but is extremely rare."))
    story.append(sp(1))
    story.append(body("<b>Threshold Penalties by Pool:</b>"))
    story.append(bullet(
        "<b>HP ≤ 0:</b> Standard GURPS death/dying rules."
    ))
    story.append(bullet(
        "<b>FP below 0:</b> -1 to <b>all</b> rolls per 1 FP below 0. "
        "If FP drops below -1×MaxFP, you fall unconscious."
    ))
    story.append(bullet(
        "<b>SPI ≤ 1/3 Max:</b> Spiritual Attrition — -3 to all SPI-based skill rolls and Beyonder ability checks."
    ))
    story.append(bullet(
        "<b>SPI = 0:</b> Spiritual Exhaustion — all Beyonder abilities deactivate; Spirit Vision shuts off."
    ))
    story.append(bullet(
        "<b>SPI below 0:</b> Soul Debt — +1 CoR per 1 point below 0."
    ))
    story.append(sp(1))
    story.append(body("<b>Damage Expression:</b> Spirit body damage is given either as:"))
    story.append(bullet(
        "<b>Flat dice:</b> e.g. \"2d6-3 to spirit body\" — roll damage, then choose a pool and subtract from it."
    ))
    story.append(bullet(
        "<b>Weapon-based:</b> e.g. \"thrust at ST-2\" — calculate the wielder's thrust damage, "
        "reduce by the penalty, then apply to the chosen pool."
    ))
    story.append(sp(1))
    story.append(body("<b>Recovery</b> follows each pool's normal rate:"))
    story.append(bullet("HP → natural healing, First Aid, magic."))
    story.append(bullet("FP → 1 per 10 minutes of rest; sleep restores all FP."))
    story.append(bullet("SPI → 1 per hour of rest (see Spirituality Recovery, Chapter 4)."))
    story.append(bullet("CoR from Soul Debt are permanent and require special rituals (Chapter 6) to remove."))
    story.append(sp(1))
    story.append(body(
        "<b>Non-Beyonders (SPI 0):</b> Can only choose HP or FP — they have no spirituality to sacrifice."
    ))
    story.append(sp(3))

    story += subsection("Optional — Hit Locations")
    story.append(body(
        "When attacking, you may call a specific body part before rolling. Take the listed "
        "penalty to your attack roll. On a hit, the wounding modifier is applied to penetrating "
        "damage (stacks with the damage-type multiplier)."
    ))
    story.append(sp(1))

    hitloc_data = [
        ["Target", "Penalty", "×", "Special Effect on Hit"],
        ["Torso", "+0", "×1", "Default location. No special effect."],
        ["Arm", "-2", "×1", "Drop held item if damage >= 3; crippled at > ½ HP of limb (~ HP/3)"],
        ["Leg", "-2", "×1", "Knock prone if damage >= 3; crippled at > ½ HP of limb (~ HP/3)"],
        ["Hand", "-4", "×1", "Drop held item; crippled easily (> HP/6)"],
        ["Neck", "-5", "Cr ×1.5 / Cut ×2 / Imp ×2", "Knockdown roll at -5; choke possible if damage > HP/2"],
        ["Face", "-5", "×1", "Knockdown at -5; risk of blindness or disfigurement"],
        ["Skull", "-7", "×4", "Knockdown at -10; DR 2 (skull bone, stacks with helmet)"],
        ["Vitals", "-3", "×3 (imp/pi only)", "Extra shock (adds +1 turn to stun duration); bleeding risk"],
        ["Eye", "-9", "×4", "Blind at > HP/10; bypasses head DR (not eye protection)"],
    ]
    hitloc_data[0] = [Paragraph(c, S['TableHeader']) for c in hitloc_data[0]]
    for i in range(1, len(hitloc_data)):
        hitloc_data[i] = [Paragraph(c, S['TableCellCenter']) if j <= 1 else Paragraph(c, S['TableCell']) for j, c in enumerate(hitloc_data[i])]
    story.append(Table(hitloc_data, colWidths=[0.7*inch, 0.6*inch, 0.9*inch, 4.1*inch], style=table_style()))
    story.append(sp(2))

    story.append(body(
        "<b>Crippling:</b> A limb or extremity struck for more than ½ its HP is crippled — "
        "unusable until healed. Arm/leg crippling: drop held items or reduce Move to 1. "
        "Recovers when the limb returns to positive HP. First Aid (skill 12+) removes "
        "permanent damage risk."
    ))
    story.append(sp(3))

    story += subsection("Optional — Wounding Multipliers")
    story.append(body(
        "Damage type determines the multiplier applied to damage that gets through DR:"
    ))
    story.append(sp(1))

    wound_data = [
        ["Damage Type", "×", "Examples"],
        ["Crushing", "×1", "Fists, clubs, maces, falling"],
        ["Cutting", "×1.5", "Swords, axes, claws, fangs"],
        ["Impaling", "×2", "Spears, arrows, rapiers, fangs"],
        ["Piercing (small)", "×0.5", "Daggers, small-calibre pistols"],
        ["Piercing", "×1", "Revolvers, rifles"],
        ["Large Piercing", "×1.5", "Hunting rifles, anti-material weapons"],
        ["Burning", "×1", "Fire, flame spells, lasers"],
        ["Toxic", "×1", "Poison (ignores DR)"],
    ]
    wound_data[0] = [Paragraph(c, S['TableHeader']) for c in wound_data[0]]
    for i in range(1, len(wound_data)):
        wound_data[i] = [Paragraph(c, S['TableCellCenter']) if j <= 1 else Paragraph(c, S['TableCell']) for j, c in enumerate(wound_data[i])]
    story.append(Table(wound_data, colWidths=[1.4*inch, 0.5*inch, 4.4*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "Hit location wounding multipliers stack with damage-type multipliers. "
        "Example: a cutting hit to the Neck (Cut ×2) with a sword (Cut ×1.5) applies "
        "×3 total to penetrating damage."
    ))
    story.append(sp(3))

    story += subsection("Optional — Major Wound Threshold")
    story.append(body(
        "Any single attack that deals more than <b>half your HP</b> (round up) counts as a Major Wound. "
        "Make an immediate <b>HT roll</b>:"
    ))
    story.append(sp(1))

    mw_data = [
        ["Result", "Effect"],
        ["Success", "-4 to all rolls for 1 turn from shock and pain"],
        ["Failure", "Stunned for 1d6 seconds (roll HT each turn to recover early)"],
        ["Fail by 5+", "Knocked down and unconscious for 1d hours"],
    ]
    mw_data[0] = [Paragraph(c, S['TableHeader']) for c in mw_data[0]]
    for i in range(1, len(mw_data)):
        mw_data[i] = [Paragraph(c, S['TableCellCenter']) for c in mw_data[i]]
    story.append(Table(mw_data, colWidths=[1.2*inch, 5.1*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "This adds drama to big hits without multiplying damage. At HP 9, a single 5-damage strike "
        "triggers a Major Wound — dangerous but survivable."
    ))
    story.append(sp(3))

    story += section("Healing & Recovery")
    story.append(body(
        "HP and FP recover at different rates. Neither comes back instantly. Pushing yourself "
        "when depleted is dangerous — FP loss bleeds into HP once you hit zero FP, and a "
        "character at low HP who keeps acting risks going unconscious mid-scene."
    ))
    story.append(sp(2))

    story += subsection("Fatigue Points (FP)")
    story.append(body(
        "FP are used by All-Out maneuvers, Extra Effort, and rituals. They recover quickly "
        "compared to HP."
    ))
    fp_data = [
        ["Method", "FP Recovered", "Time Required"],
        ["Rest (sitting, no strenuous activity)", "1 FP", "Per 10 minutes"],
        ["Sleep",                                 "All FP", "8 hours"],
        ["At 0 FP",        "Every point of FP spent below 0 also costs 1 HP", "Immediate"],
        ["At 1/3 FP or below", "-1 to all rolls; Move and Dodge halved",      "Until above threshold"],
    ]
    fp_data[0] = [Paragraph(c, S['TableHeader']) for c in fp_data[0]]
    for i in range(1, len(fp_data)):
        fp_data[i] = [Paragraph(c, S['TableCell']) for c in fp_data[i]]
    story.append(Table(fp_data, colWidths=[2.2*inch, 2.4*inch, 1.7*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Hit Points (HP)")
    story.append(body(
        "HP are restored through three distinct mechanisms: natural recovery, external healing, "
        "and regeneration. Each follows different rules and time scales."
    ))
    story.append(sp(2))

    hp_data = [
        ["Method", "HP Recovered", "Time Required / Notes"],
        ["Natural Recovery (HT roll success)", "1 HP (2 HP w/ Very Rapid Healing)", "Per day; rest & food required"],
        ["Natural Recovery (20–29 HP)",         "2× base rate",                     "Per day; scales proportionally"],
        ["Natural Recovery (30–39 HP)",         "3× base rate",                     "Per day; scales proportionally"],
        ["First Aid",                           "1 HP + stops bleeding",            "1 minute; once per wound"],
        ["Physician (skill 12+)",               "1 HP (2 HP on critical success)",  "Per day of bed rest; requires equipment"],
        ["Healing advantage",                   "2 HP (costs 1 FP)",                "Concentration + IQ roll"],
    ]
    hp_data[0] = [Paragraph(c, S['TableHeader']) for c in hp_data[0]]
    for i in range(1, len(hp_data)):
        hp_data[i] = [Paragraph(c, S['TableCell']) for c in hp_data[i]]
    story.append(Table(hp_data, colWidths=[2.0*inch, 2.0*inch, 2.3*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "Natural Recovery does not normally restore FP unless specific modifiers or high-level "
        "supernatural abilities are applied."
    ))
    story.append(sp(2))

    story += subsection("Regeneration")
    story.append(body(
        "Regeneration is a passive advantage that automatically restores HP without rolls or "
        "active intervention. The rate depends on the level purchased:"
    ))
    regen_data = [
        ["Regeneration Level", "Rate"],
        ["Slow", "1 HP per 12 hours"],
        ["Regular", "1 HP per hour"],
        ["Fast", "1 HP per minute"],
        ["Very Fast", "1 HP per second"],
        ["Extreme", "10 HP per second"],
    ]
    regen_data[0] = [Paragraph(c, S['TableHeader']) for c in regen_data[0]]
    for i in range(1, len(regen_data)):
        regen_data[i] = [Paragraph(c, S['TableCell']) for c in regen_data[i]]
    story.append(Table(regen_data, colWidths=[1.6*inch, 4.7*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "Like Natural Recovery, standard Regeneration restores <b>HP only</b>, though modifiers "
        "such as <b>Heals FP Only</b> or <b>Restores Either FP or HP</b> can change this. "
        "Regeneration includes <b>Rapid Healing</b> benefits but operates independently of the "
        "daily HT roll used for Natural Recovery."
    ))
    story.append(body(
        "At 0 HP or below, a character with any level of Regeneration still makes HT rolls to "
        "avoid unconsciousness — but each tick of Regeneration may lift them above the threshold "
        "before they fail."
    ))
    story.append(sp(3))

    story += section("Fright Checks")
    story.append(body(
        "When characters witness supernatural phenomena, they must make a <b>Fright Check</b>: "
        "roll 3d6 vs. Will with the modifier listed below. Add the result to any margin of failure "
        "to determine the effect from the Fright Effects table."
    ))
    fright_data = [
        ["Trigger", "Will Modifier"],
        ["Minor supernatural event (strange sounds, moved objects)", "+2"],
        ["Beyonder using powers (visible supernatural ability)", "+0"],
        ["Encountering a monster or undead creature", "-2 to -6"],
        ["Witnessing a supernatural death", "-4"],
        ["Outer God influence or manifestation", "-8 or worse"],
    ]
    fright_data[0] = [Paragraph(c, S['TableHeader']) for c in fright_data[0]]
    for i in range(1, len(fright_data)):
        fright_data[i] = [Paragraph(fright_data[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(2)]
    story.append(Table(fright_data, colWidths=[3.8*inch, 1.5*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Fright / Awe / Confusion — Effects Table")
    story.append(body(
        "When a Fright Check (or equivalent Awe/Confusion check) is failed, roll <b>3d6 + margin of failure</b> "
        "and consult the table. Which column applies depends on the trigger:"
    ))
    story.append(bullet("<b>Fright</b> — terrifying or grotesque supernatural phenomena (horrors, violence, corruption)."))
    story.append(bullet("<b>Awe</b> — overwhelming divine or profound beauty/truth (angelic presence, revelations)."))
    story.append(bullet("<b>Confusion</b> — incomprehensible or paradoxical stimuli (time loops, non-Euclidean spaces, abstract information overload)."))
    story.append(body("All three use the same roll; only the effects differ."))
    story.append(sp(3))
    fright_effects = [
        ["Roll", "Fright", "Awe", "Confusion"],
        ["4–9",
         "Stunned 1 sec; roll vs. Will each sec to recover.",
         "Stunned 1 sec; roll vs. Will each sec to recover.",
         "Stunned 1 sec; roll vs. IQ each sec to recover."],
        ["10–11",
         "Stunned 1d–2d sec; roll vs. Will to recover.",
         "Stunned 1d–2d sec; roll vs. Will to recover.",
         "Stunned 1d–2d sec; roll vs. IQ to recover."],
        ["12",
         "Retching for (25 − HT) sec; roll vs. Will to recover.",
         "Ecstasy for (25 − Will) sec; roll vs. Will to recover.",
         "Dazed for (25 − IQ) sec; roll vs. IQ to recover."],
        ["13–15",
         "Acquire a <b>quirk</b>: mild phobia or superstition.",
         "Acquire a <b>quirk</b>: fascination or devotion to the trigger.",
         "Acquire a <b>quirk</b>: persistent confusion or memory tic."],
        ["16–21",
         "New −10 pt disadvantage: Delusion, Phobia, or Cowardice.",
         "New −10 pt disadvantage: Fanaticism, Vow (worship), or Truthfulness.",
         "New −10 pt disadvantage: Indecisive, Confused, or Short Attention Span."],
        ["22–23",
         "New −15 pt disadvantage: Severe Phobia or Paranoia.",
         "New −15 pt disadvantage: Extreme Fanaticism or self-sacrificing Vow.",
         "New −15 pt disadvantage: Dementia (age-related confusion) or Deep Sleeper."],
        ["24–29",
         "Major physical trauma: hair turns white, age 3d6 years, or lose 1 HT permanently.",
         "Physical marking: faint glow, stigmata, or lose 1 HT from rapture.",
         "Brain fog: lose 1 IQ permanently; -2 to all skill rolls for 1d6 days."],
        ["30–34",
         "Catatonia or coma for 1d6 days; lose 1d6 FP permanently.",
         "Stupor of wonder for 1d6 days; lose touch with mundane reality.",
         "Fugue state for 1d6 days; cannot form new memories during episodes."],
        ["35+",
         "Permanent loss of −1 IQ and −1 Will from sheer horror.",
         "Permanent loss of −1 IQ and −1 Per from overwhelming awe.",
         "Permanent loss of −1 IQ and −1 DX from fractured cognition."],
    ]
    fright_effects[0] = [Paragraph(c, S['TableHeader']) for c in fright_effects[0]]
    for i in range(1, len(fright_effects)):
        fright_effects[i] = [Paragraph(fright_effects[i][j],
            S['TableCellCenter'] if j==0 else S['TableCell']) for j in range(4)]
    story.append(Table(fright_effects, colWidths=[0.6*inch, 2.1*inch, 2.1*inch, 2.1*inch], style=table_style()))
    story.append(sp(3))

    story += chapter("Chapter 6: The Beyonder System")

    story.append(flavor(
        "Every pathway leads somewhere. Every potion costs something. "
        "The question is never whether you will change — only whether you will remain yourself when you do."
    ))
    story.append(sp(3))

    story += section("What Is a Beyonder?")
    story.append(body(
        "There are multiple Pathways for Beyonders to take, all starting from Sequence 9. Beyonders gain "
        "power from specific potions or boons, but must endure the side effects — paranoia, hallucinations, "
        "altered perception — that ensue upon consuming or being bestowed with them. There is always a chance "
        "they will succumb to these side effects and lose control, becoming monsters themselves. In cases "
        "where Beyonders grow very old or sustain serious injury, using their abilities risks triggering "
        "that same loss of control."
    ))
    story.append(sp(3))

    story += section("The Sequence Ladder")
    seq_data = [
        ["Sequence", "Power Level", "Notes"],
        ["9 (Weakest)", "Newly awakened", "Just drank the potion; adjusting to powers; most vulnerable to corruption"],
        ["8", "Developing", "Beginning to master abilities; still human in most ways"],
        ["7", "Competent", "Noticeably superhuman; regarded with fear by mortals"],
        ["6", "Powerful", "Major supernatural threat; equal to military forces"],
        ["5", "Formidable", "Can affect whole districts; known to major powers"],
        ["4", "Mighty", "Demigod level; nations take notice"],
        ["3", "Near-Divine", "Comparable to legendary historical figures"],
        ["2", "Transcendent", "Forces of nature; reshape cities"],
        ["1", "Extraordinary", "World-shaping power; few exist in living memory"],
        ["0 (Strongest)", "God-Equivalent", "True divinity; these are the deities whose pathways you walk"],
    ]
    seq_data[0] = [Paragraph(c, S['TableHeader']) for c in seq_data[0]]
    for i in range(1, len(seq_data)):
        seq_data[i] = [Paragraph(seq_data[i][j],
            S['TableCellCenter'] if j==0 else S['TableCell']) for j in range(3)]
    story.append(Table(seq_data, colWidths=[1.0*inch, 1.1*inch, 4.2*inch], style=table_style()))
    story.append(sp(3))

    story += section("The Digestion System")
    story.append(body(
        "After consuming a potion, a Beyonder must <i>digest</i> it — safely incorporating its power "
        "over time. Digestion is tracked as a percentage from 0% to 100%. The primary method is the "
        "<b>Acting Method</b>: the Beyonder engrosses themselves in the 'role' of the potion, embodying "
        "its nature deeply and consistently. Most Beyonders must wait years between potions to minimise "
        "the risk of losing control. From <b>Sequence 5 onward</b>, advancement also requires a ritual "
        "in addition to the potion — without it, the likelihood of losing control becomes near-certain."
    ))
    story.append(sp(3))
    dig_data = [
        ["Acting Quality", "Digestion Gain Per Session"],
        ["Exemplary (fully embodies pathway nature)", "+15–20%"],
        ["Good (follows most requirements)", "+10–15%"],
        ["Adequate (follows some requirements)", "+5–10%"],
        ["Poor (barely follows pathway)", "+0–5%"],
        ["None (ignores pathway nature entirely)", "0% or loses progress"],
    ]
    dig_data[0] = [Paragraph(c, S['TableHeader']) for c in dig_data[0]]
    for i in range(1, len(dig_data)):
        dig_data[i] = [Paragraph(dig_data[i][j],
            S['TableCellCenter'] if j==1 else S['TableCell']) for j in range(2)]
    story.append(Table(dig_data, colWidths=[3.0*inch, 3.3*inch], style=table_style()))
    story.append(sp(3))

    story += section("CoR — Corruption")
    story.append(body(
        "<b>CoR</b> measures how close a Beyonder is to losing their humanity and sanity. "
        "Maximum CoR equals the character's Will score. Reaching maximum CoR means the character becomes "
        "an NPC monster or irreversibly mad Beyonder — removed from play."
    ))
    cp_data = [
        ["Action", "CoR Gained"],
        ["Using powers while drained of Spirituality", "1 CoR per use"],
        ["Seeing or Hearing things you're not supposed to", "1–3 CoR per session"],
        ["Witnessing higher-Sequence powers (Seq 6 or above)", "1–4 CoR"],
        ["Using forbidden rituals", "2–5 CoR"],
        ["Advancing sequence without full digestion", "10+ CoR"],
        ["Ritual magic critical failure", "1d CoR"],
    ]
    cp_data[0] = [Paragraph(c, S['TableHeader']) for c in cp_data[0]]
    for i in range(1, len(cp_data)):
        cp_data[i] = [Paragraph(c, S['TableCell']) for c in cp_data[i]]
    story.append(Table(cp_data, colWidths=[3.0*inch, 3.3*inch], style=table_style()))
    story.append(sp(3))
    story.append(Paragraph(
        "[!] At maximum CoR: The character is permanently lost. The GM takes full control. "
        "The other characters now have a new enemy.",
        S['Warning']
    ))
    story.append(sp(3))

    story += section("Potion Consumption Roll")
    story.append(body(
        "When a Beyonder drinks a potion to advance to the next Sequence, they must make a "
        "<b>Potion Consumption Roll (PCR)</b>. This is a raw 3d6 roll — no stat or skill applies. "
        "Only the drinker's digestion of their current potion matters."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Roll 3d6 <= 10 + Digestion Modifier.</b>"
    ))
    story.append(sp(2))
    story.append(body("The Digestion Modifier depends on how fully the current potion has been digested:"))
    pcr_data = [
        ["Digestion of Current Potion", "Modifier", "Effective Target"],
        ["0%",      "-9", "1 — always fails"],
        ["10%",     "-7", "3"],
        ["20%",     "-5", "5"],
        ["30%",     "-4", "6"],
        ["40%",     "-2", "8"],
        ["50%",     "0",  "10 — even odds"],
        ["60%",     "+2", "12"],
        ["70%",     "+4", "14"],
        ["80%",     "+5", "15"],
        ["90%",     "+7", "17"],
        ["100%",    "+9", "19 — always succeeds"],
    ]
    pcr_data[0] = [Paragraph(c, S['TableHeader']) for c in pcr_data[0]]
    for i in range(1, len(pcr_data)):
        pcr_data[i] = [Paragraph(c, S['TableCellCenter']) for c in pcr_data[i]]
    story.append(Table(pcr_data, colWidths=[2.0*inch, 1.0*inch, 2.0*inch],
                        style=table_style()))
    story.append(sp(3))
    story.append(body("<b>Results:</b>"))
    story.append(bullet("<b>Success:</b> The potion integrates. The Beyonder gains the new Sequence's abilities."))
    story.append(bullet(
        "<b>Failure:</b> The potion overwhelms the drinker. The character is lost — they transform "
        "into an NPC <b>Rampager</b> (see below) immediately, permanently under the GM's control."
    ))
    story.append(sp(2))
    story.append(body(
        "From <b>Sequence 5 onward</b>, advancement also requires a preparation ritual before the potion "
        "can be consumed at all. The ritual does not modify the PCR — it is a prerequisite to even attempt it."
    ))
    story.append(sp(3))

    story += section("Advancing to the Next Sequence")
    story.append(body("To advance from Sequence 9 to Sequence 8 (and so on), a character must:"))
    story.append(bullet("Obtain the formula for the next-sequence potion (rare, expensive, or dangerous to acquire)"))
    story.append(bullet("Gather the required ingredients (some are supernatural or illegal)"))
    story.append(bullet("Brew the potion or obtain it from another Beyonder"))
    story.append(bullet("Drink it and make a <b>Potion Consumption Roll</b> (see above)"))
    story.append(bullet("From Sequence 5 onward: also perform a prerequisite ritual before attempting the PCR"))
    story.append(sp(3))
    story.append(body(
        "<b>GM Note:</b> Beyonder advancement beyond Sequence 7 should be rare and tied to major "
        "story achievements. Each advance represents a fundamental transformation of the character's "
        "nature, not merely a power upgrade."
    ))
    story.append(sp(3))

    story += section("Rampager — Losing Control")
    story.append(body(
        "No matter the pathway, the higher the Sequence, the greater the insanity and inhuman inclinations "
        "that accumulate. Losing control is not solely linked to the potion's effects — it is also "
        "intricately connected to a Beyonder's emotions and mental health. The key lies in self-control: "
        "resisting the temptations of evil gods and devils, suppressing greed and jealousy, and guarding "
        "against the erosion of desire."
    ))
    story.append(sp(3))
    story.append(body("Losing control progresses through three stages:"))
    ramp_data = [
        ["Stage", "Description"],
        ["Stage 1 — Warning Signs",
         "Auditory and visual hallucinations begin. The Beyonder may dismiss them as exhaustion or stress."],
        ["Stage 2 — Loss of Control",
         "The body and mind are partially out of control. The Beyonder periodically displays terrifying "
         "or strange states they cannot fully explain or suppress."],
        ["Stage 3 — Rampager",
         "Complete breakdown. The Beyonder transforms into a terrifying monster. The transition from "
         "Stage 2 to Stage 3 can happen rapidly — sometimes within moments of the symptoms appearing."],
    ]
    ramp_data[0] = [Paragraph(c, S['TableHeader']) for c in ramp_data[0]]
    for i in range(1, len(ramp_data)):
        ramp_data[i] = [Paragraph(c, S['TableCell']) for c in ramp_data[i]]
    story.append(Table(ramp_data, colWidths=[1.7*inch, 4.6*inch], style=table_style()))
    story.append(sp(3))

    story += section("Beyonders in Society")

    story += subsection("Ordinary People")
    story.append(body(
        "The existence of Beyonders is unknown to most people. Mystical knowledge available to the public "
        "is limited to basic Ritualistic Magic and some Ritualistic Magic involving the Orthodox Deities — "
        "both of which can be learned at Divination Clubs or through public magazines. The authorities "
        "(churches, police, royal family) actively prevent ordinary civilians from becoming involved in "
        "Beyonder matters. However, those who discover the truth and become inadvertently involved may "
        "be offered a position as civilian staff at the local church — or an opportunity to take a "
        "potion and serve as an official Beyonder themselves."
    ))
    story.append(sp(3))

    story += subsection("Official Beyonders")
    story.append(body(
        "Official Beyonders are those who operate under the sanction of a church or other recognized "
        "organisation. They may have climbed through the ranks or been approached after encountering "
        "Beyonder elements. For most church-affiliated police branches, these individuals investigate "
        "and dispatch responses to Beyonder incidents. Their work is well-compensated and carries "
        "institutional protection — but also obligation."
    ))
    story.append(sp(3))

    story += subsection("Wild Beyonders")
    story.append(body(
        "Those who become Beyonders without church sanction are called <b>Wild Beyonders</b>. They must "
        "remain hidden to avoid capture. Many take occupations that benefit from their pathway — a Hunter "
        "working as a bounty hunter, a Spectator as a detective — but being too effective attracts "
        "unwanted attention. Wild Beyonders face two major obstacles: <b>luck</b> and <b>money</b>. "
        "Luck is required to find the correct formula and ingredients; money to purchase them. Without "
        "institutional support, most wild Beyonders are stuck at low sequences indefinitely."
    ))
    story.append(sp(3))

    story += section("Mystical Items & Sealed Artifacts")
    story.append(body(
        "Mystical items are extraordinary objects combined with Beyonder characteristics or ritual power. "
        "Some are dangerous enough to be classified as <b>Sealed Artifacts</b> — items with significant "
        "abilities and equally significant drawbacks. Sealed Artifacts arise in one of two ways: as a "
        "result of the death of an out-of-control Beyonder, or through craftsmanship by a Sequence 6 or "
        "higher Savant Pathway Beyonder. Although their powers adhere to the traits of the 22 pathways, "
        "each Sealed Artifact is unique — shaped by its formation environment, its original owner's "
        "history, and forces no one fully understands."
    ))
    story.append(sp(3))

    story += subsection("Sealed Artifact Grades")
    story.append(body(
        "The seven churches classify Sealed Artifacts into four grades (0–3) based on danger, power, "
        "and sealing method. Grade 0 and 1 artifact codes are shared between churches due to their "
        "danger — but the detailed information is not. Classification was formally established in the "
        "late Fourth Epoch / early Fifth Epoch."
    ))
    story.append(sp(3))
    sealed_data = [
        ["Grade", "Danger", "Power Equivalent", "Church Access Rules"],
        ["Grade 3", "Considerable",
         "Low-Sequence Beyonder (Seq 8–9)",
         "Formal Nighthawk members and above"],
        ["Grade 2", "Dangerous",
         "Mid-Sequence Beyonder (Seq 5–7)",
         "Bishop or Nighthawk team captain and above; 3–5 per cathedral"],
        ["Grade 1", "Highly Dangerous",
         "Saint (Seq 3–4)",
         "Diocesan Bishop or Nighthawk deacon and above; 1–2 per diocese HQ"],
        ["Grade 0", "Extremely Dangerous",
         "Angel (Seq 1–2 equivalent)",
         "Most confidential — not to be inquired, described, or spied upon"],
    ]
    sealed_data[0] = [Paragraph(c, S['TableHeader']) for c in sealed_data[0]]
    for i in range(1, len(sealed_data)):
        sealed_data[i] = [Paragraph(c, S['TableCell']) for c in sealed_data[i]]
    story.append(Table(sealed_data, colWidths=[0.7*inch, 0.9*inch, 1.6*inch, 3.1*inch],
                       style=table_style()))
    story.append(sp(3))

    story += subsection("Charms")
    story.append(body(
        "Charms are mystical items whose power derives from a high-level existence, contained in a "
        "vessel and stabilized by symbols carved on precious metals. They can be used by any holder "
        "via the activation incantation set by the maker — but once used, the charm burns away at the "
        "end of its activation period. The spirituality within diminishes over time; low-grade charms "
        "must be renewed every two weeks."
    ))
    story.append(sp(3))
    charm_data = [
        ["Name", "Domain", "Function"],
        ["Aquatic Affinity Charm", "Tyrant", "Grants affinity with underwater creatures"],
        ["Dream Charm", "Darkness", "Allows the wielder to enter someone else's dream"],
        ["Flaring Sun Charm", "Sun", "Calls forth a blazing pillar of light from the sky"],
        ["Language Comprehension Charm", "White Tower", "Temporarily enhances understanding, reasoning, and communication"],
        ["Requiem Charm", "Darkness", "Soothes ghosts, souls, and zombies; deals with vengeful spirits"],
        ["Shriek Charm", "Chained", "Creates an invisible sound wave that drills into all nearby ears"],
        ["Slumber Charm", "Darkness", "Forcefully puts the target to sleep"],
        ["Teleportation Charm", "Door", "Allows the caster to teleport to a different location"],
        ["Yesterday Once More Charm", "Fool", "See through one's past; borrow the power of a historical self"],
        ["Scholar of Yore Cane", "Fool", "Regain peak strength by borrowing power from History (one use)"],
        ["Fate Siphon", "Error", "Siphon the fate connection between wielder and target briefly"],
        ["Deity's Curse", "Darkness / Wheel of Fortune", "Inflicts a god-level misfortune curse on the target"],
    ]
    charm_data[0] = [Paragraph(c, S['TableHeader']) for c in charm_data[0]]
    for i in range(1, len(charm_data)):
        charm_data[i] = [Paragraph(c, S['TableCell']) for c in charm_data[i]]
    story.append(Table(charm_data, colWidths=[1.8*inch, 1.4*inch, 3.1*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Mystical Ammunition")
    story.append(body(
        "Certain bullets are crafted with Beyonder characteristics or ritual power, granting "
        "extraordinary effects beyond standard ballistics."
    ))
    story.append(sp(3))
    ammo_data = [
        ["Name", "Domain", "Effect"],
        ["Aging Bullets", "Error", "Causes the target to lose vitality rapidly, entering an aged state"],
        ["Control Spirit Bullets", "Fool", "Paralyzes one body part on hit"],
        ["Deceit Bullets", "Error", "Misdirects the target; causes errors in judgment; can deceive rules"],
        ["Demon Hunting Bullets", "Twilight Giant", "Highly effective against corrupted creatures"],
        ["Deprivation Bullets", "Error", "Steals three Beyonder powers from the target, starting from most recent"],
        ["Exorcism Bullets", "Sun", "Purifies ghost-related monsters"],
        ["Parasite Bullets", "Error", "Creates Worms of Time that parasitize the target, allowing shooter control"],
        ["Purifying Bullets", "Sun", "Purifies ghosts"],
    ]
    ammo_data[0] = [Paragraph(c, S['TableHeader']) for c in ammo_data[0]]
    for i in range(1, len(ammo_data)):
        ammo_data[i] = [Paragraph(c, S['TableCell']) for c in ammo_data[i]]
    story.append(Table(ammo_data, colWidths=[1.7*inch, 1.3*inch, 3.3*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Special Medicines")
    story.append(body(
        "Special medicines are extraordinary mixtures prepared using spiritual ingredients or Ritualistic "
        "Magic. They slowly lose their spirituality after preparation and generally have an expiration "
        "date. The following are notable medicines encountered in the Fifth Epoch:"
    ))
    story.append(sp(3))
    med_data = [
        ["Name", "Description"],
        ["Amantha Extract",
         "An aromatic floral essence (Night vanilla, slumber flower, chamomile). Relaxes emotions; "
         "creates instant calm as if gazing into silent darkness."],
        ["Eye of the Spirit Medication",
         "Drago and poplar bark/leaves, sun-dried and decocted, immersed in Lanti Wine. "
         "A helpful agent for psychics and spiritual workers."],
        ["Goddess's Gaze",
         "A dark red liquid. Stimulates the spirit and body's potential; keeps a person functional "
         "in a short period until they can receive proper treatment."],
        ["Holy Night Powder",
         "Slumber flowers, Dragon Blood grass, deep red sandalwood, mint. From the Church of the "
         "Evernight Goddess. Assists Beyonders in guiding their power before ritual magic; builds a "
         "clean spiritual environment. Limit: up to Sequence 7 or a personal silver knife."],
        ["Sedative Agent",
         "A blue fluid. Keeps users awake while feeling deeply calm. Rarely used but highly efficient "
         "for mediumship work."],
        ["Serenity Agent",
         "Maintains calm and rational thought; useful in high-stress supernatural situations."],
        ["Truth Serum (Confession Concoction)",
         "Makes it exceedingly difficult to lie. What the subject utters stems from their innermost desires."],
        ["Healing Agent",
         "Mends most external wounds, alleviates severe injuries, and eliminates minor ailments."],
        ["Berserk Agent",
         "Grants the user extraordinary strength when released; unpredictable if used without preparation."],
        ["Quelaag's Oil",
         "A mix of mint and disinfectant. Helps a person ignore the stench of rotting corpses; "
         "refreshes and clears the mind."],
        ["Sanguine Anesthesia Gas",
         "Causes deep slumber lasting more than three hours."],
        ["Mysticism Smelling Salts",
         "An extremely foul-smelling gas that wakes the user immediately. Can cancel or protect "
         "against sleeping gas effects."],
    ]
    med_data[0] = [Paragraph(c, S['TableHeader']) for c in med_data[0]]
    for i in range(1, len(med_data)):
        med_data[i] = [Paragraph(c, S['TableCell']) for c in med_data[i]]
    story.append(Table(med_data, colWidths=[1.7*inch, 4.6*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Unique Sealed Artifacts")
    story.append(body(
        "The following are individual Sealed Artifacts of note — unique items documented by the "
        "churches or encountered in the field. Each has its own history, abilities, and dangers."
    ))
    story.append(sp(3))

    # ── Gauntlet of the False Baron ──
    story.append(Paragraph(
        "<b>Sealed Artifact 2–17: Gauntlet of the False Baron</b> "
        "<i>(Black Emperor Pathway · Grade 2 · Seq 7 equivalent)</i>",
        S['BodyBold']
    ))
    story.append(sp(1))
    story.append(body(
        "<b>Appearance:</b> A gauntlet of blackened leather reaching mid-forearm, "
        "stitched with silver thread in intricate patterns resembling contract clauses and legal seals. "
        "The stitching occasionally rearranges itself when not observed directly. "
        "The palm bears a faint, warm pressure as if perpetually holding an invisible coin. "
        "Rumoured to have been crafted in the late Fourth Epoch from the Beyonder characteristic "
        "of a Briber who attempted to bribe Death itself — and failed."
    ))
    story.append(sp(2))

    # Ability table
    gauntlet_abilities = [
        ["Ability", "SPI Cost", "Effect"],
        ["Bribe — Weaken",
         "1 SPI",
         "Touch the gauntlet's palm to a target or a held object as an Attack maneuver. "
         "The target suffers -3 to all attack and active defense rolls for 5 turns "
         "(penalty drops by 1 each turn: -3 -> -2 -> -1 -> 0). "
         "If the target cannot be touched directly, a symbolic object thrown at them "
         "(DX roll to land) works at half duration (3 turns, -3 -> -2 -> -1 -> 0)."],
        ["Bribe — Arrogance",
         "1 SPI",
         "As above, but the target rolls IQ at -2 each turn. On a failure, they are "
         "compelled to make a reckless or arrogant action (GM's discretion). "
         "Penalty diminishes by 1 each turn (-2 -> -1 -> 0). Duration: 3 turns."],
        ["Minor Distortion",
         "2 SPI",
         "Snap the gauntlet's fingers as a free action to twist a single incoming ranged "
         "attack (bullet, arrow, thrown weapon) within 10 meters. The attack's trajectory "
         "curves harmlessly away — the attacker must roll again at -4 or miss entirely. "
         "Cannot be used on melee attacks or area effects. "
         "Once per round."],
        ["False Majesty",
         "1 SPI/turn",
         "The gauntlet exudes an aura of command. As a Concentrate maneuver, the wearer "
         "can force a single target within 5 meters to roll Will. On failure, the target "
         "hesitates — they cannot attack the wearer directly on their next turn "
         "(they may defend themselves and act otherwise). Maintained by spending 1 SPI each turn."],
    ]
    gauntlet_abilities[0] = [Paragraph(c, S['TableHeader']) for c in gauntlet_abilities[0]]
    for i in range(1, len(gauntlet_abilities)):
        gauntlet_abilities[i] = [
            Paragraph(gauntlet_abilities[i][0], S['TableCell']),
            Paragraph(gauntlet_abilities[i][1], S['TableCellCenter']),
            Paragraph(gauntlet_abilities[i][2], S['TableCell']),
        ]
    story.append(Table(gauntlet_abilities, colWidths=[1.4*inch, 0.7*inch, 4.2*inch],
                       style=table_style()))
    story.append(sp(2))

    story.append(Paragraph("<b>Drawbacks:</b>", S['BodyBold']))
    story.append(bullet(
        "<b>Corruptive Influence.</b> Each day the gauntlet is worn for more than one hour, "
        "the wearer must roll Will. On failure, they gain a temporary Disadvantage for the rest "
        "of the day: Greed (12), Overconfidence (12), or Trickster Mentality "
        "(always seeking a loophole, -1 to cooperative skill rolls). The GM chooses which. "
        "After 7 cumulative failures, the Disadvantage becomes permanent until the artifact is "
        "relinquished and the wearer undergoes spiritual cleansing."
    ))
    story.append(bullet(
        "<b>Soul's Price.</b> Each use of any ability costs 1 HP in addition to SPI. "
        "The gauntlet draws blood from the wearer's hand — dark veins creep up the arm for "
        "several minutes after use."
    ))
    story.append(bullet(
        "<b>Withdrawal.</b> If the gauntlet is not used for 24 hours, the wearer suffers "
        "a splitting headache (-2 to all IQ and Per rolls) until they use at least one ability. "
        "If 48 hours pass without use, the gauntlet tightens painfully, dealing 1d6-2 "
        "crushing damage to the hand and arm (ignores DR; cannot be healed until used)."
    ))
    story.append(sp(2))
    story.append(Paragraph(
        "<b>Sealing Instructions:</b> Keep in a lead-lined box etched with the Seven "
        "Seals of Contract. The gauntlet must be offered a voluntary sacrifice of one silver "
        "coin per week, placed inside the box. If the offering is missed for three consecutive "
        "weeks, the gauntlet begins whispering temptations to anyone within 10 meters (Will-2 "
        "to resist acting on them).",
        S['Body']
    ))
    story.append(sp(3))

    # ── Echoing Coin of the Serpent ──
    story.append(Paragraph(
        "<b>Sealed Artifact 3–05: Echoing Coin of the Serpent</b> "
        "<i>(Error Pathway · Grade 3 · Seq 8 equivalent)</i>",
        S['BodyBold']
    ))
    story.append(sp(1))
    story.append(body(
        "<b>Appearance:</b> A gold coin the size of a Loen sixpence, stamped with the"
        " profile of a crowned serpent on one side and a labyrinth of concentric circles"
        " on the other. The coin is unnervingly warm to the touch and, when held close"
        " to the ear, emits a faint rhythmic hum — like a distant clock ticking in"
        " reverse. It was discovered in the ruins of a Fourth Epoch swindler's vault,"
        " alongside three identical coins that had all rusted to dust the moment the"
        " vault was opened."
    ))
    story.append(sp(2))

    coin_abilities = [
        ["Ability", "SPI Cost", "Effect"],
        ["Duplicate",
         "1 SPI",
         "Place the coin atop any single non-magical, non-living object no larger than"
         " a loaf of bread and speak the activation incantation (\"As above, so below\")."
         " After 1 minute of concentration, a perfect duplicate of the object appears"
         " beside the original. The duplicate is physically identical but has no spiritual"
         " or Beyonder properties — it cannot replicate Mystical Items, potions,"
         " characteristics, or artifacts. The original is unaffected. Maximum one"
         " duplicate per hour."],
        ["Minor Misfortune",
         "1 SPI",
         "Flick the coin into the air as a free action. While it is spinning, choose a"
         " target within 5 meters. For the next 3 turns, that target suffers -1 to all"
         " rolls (attacks, defenses, skill checks) as minor coincidences go against them"
         " (loose cobblestone, gust of wind, slipping grip). The coin lands and the"
         " effect ends. Usable once per scene."],
        ["Worm's Whim",
         "2 SPI",
         "Press the coin firmly against a non-living surface no larger than a door and"
         " will it to merge. The coin sinks into the material and creates a temporary"
         " passage — a subtle distortion that creatures can pass through as if the wall"
         " were an open archway. The passage lasts 5 minutes or until the coin is"
         " retrieved (which collapses it instantly). The coin cannot be retrieved from"
         " inside the passage and must be collected from the opposite side."],
    ]
    coin_abilities[0] = [Paragraph(c, S['TableHeader']) for c in coin_abilities[0]]
    for i in range(1, len(coin_abilities)):
        coin_abilities[i] = [
            Paragraph(coin_abilities[i][0], S['TableCell']),
            Paragraph(coin_abilities[i][1], S['TableCellCenter']),
            Paragraph(coin_abilities[i][2], S['TableCell']),
        ]
    story.append(Table(coin_abilities, colWidths=[1.2*inch, 0.7*inch, 4.4*inch],
                       style=table_style()))
    story.append(sp(2))

    story.append(Paragraph("<b>Drawbacks:</b>", S['BodyBold']))
    story.append(bullet(
        "<b>Time Debt.</b> Each use of the coin's abilities ages the user by one day"
        " (visible as a momentary grey streak in the hair or a new wrinkle). The aging"
        " is cosmetic and temporary — it fades over 24 hours — but if the coin is used"
        " more than 7 times in a single week, the aging becomes permanent and the user"
        " loses 1 HP permanently until the coin is relinquished for at least a month."
    ))
    story.append(bullet(
        "<b>Coin's Greed.</b> Once per day, if the user attempts to discard, give away,"
        " or destroy the coin, it teleports back into their pocket or purse within"
        " 1d10 minutes. The coin can only be permanently relinquished through a formal"
        " ritual (Ritualistic Magic -2) or by transferring it to a willing new owner"
        " who accepts the burden."
    ))
    story.append(bullet(
        "<b>Echoing Whispers.</b> While in possession of the coin, the user occasionally"
        " hears faint whispers of past owners' conversations — typically lies,"
        " betrayals, or temptations. During moments of stress (combat, chase,"
        " interrogation), the GM may call for a Will-1 roll. On failure, the user"
        " is distracted for one turn (-2 to active defenses or skill rolls)."
    ))
    story.append(sp(2))
    story.append(Paragraph(
        "<b>Sealing Instructions:</b> Place the coin in a bag of lead shot and submerge"
        " it in holy water blessed by a priest of the Evernight Goddess. The container"
        " must be stored in a room without windows or clocks — timekeeping devices of"
        " any kind cause the coin to hum audibly. The water must be changed every new"
        " moon. If the coin begins ticking audibly through the lead, it has successfully"
        " deceived the seal and should be immediately reclassified as Grade 2 or higher.",
        S['Body']
    ))
    story.append(sp(3))

    # ── Candle of Shared Slumber ──
    story.append(Paragraph(
        "<b>Sealed Artifact 2–11: Candle of Shared Slumber</b> "
        "<i>(Darkness Pathway · Grade 2 · Seq 6 equivalent)</i>",
        S['BodyBold']
    ))
    story.append(sp(1))
    story.append(body(
        "<b>Appearance:</b> A tall, tapered candle of deep purple wax flecked with silver"
        " particles that shimmer like distant stars. It stands approximately 30 cm tall"
        " and burns with a pale, smokeless flame that sheds no heat. The candle never"
        " melts or shortens during normal use — it only diminishes when one of its"
        " abilities is activated. When not lit, the wax exudes a faint scent of"
        " night-blooming jasmine and old parchment. The candle was recovered from a"
        " sealed crypt beneath the Cathedral of the Evernight Goddess in Backlund,"
        " where it had been burning for an estimated 800 years without perceptible"
        " consumption."
    ))
    story.append(sp(2))

    candle_abilities = [
        ["Ability", "SPI Cost", "Effect"],
        ["Slumber",
         "1 SPI",
         "Light the candle as a Concentrate maneuver. All living creatures within a"
         " 5-meter radius must roll HT-2 or fall into a deep, dreamless sleep for"
         " 1d10 minutes. Those who succeed are drowsy (-1 to all rolls) for 3 turns."
         " The flame gutters and the candle shortens by 1 cm. Sleeping creatures can"
         " only be awakened by taking damage or by a successful First Aid roll at -4."],
        ["Shared Dream",
         "2 SPI",
         "Light the candle and focus on a willing or unconscious target within 10 meters"
         " as a Concentrate maneuver for 3 turns. The user enters a shared dream with"
         " the target, enabling direct conversation, memory exploration, or the planting"
         " of suggestions. The user may stay in the dream for up to 10 minutes of"
         " real time (which may feel much longer in-dream). The candle shortens by 3 cm."
         " If the target is unwilling, they may resist with a Will-2 roll each turn of"
         " the focusing period."],
        ["Extinguish Memory",
         "3 SPI",
         "Pinch out the candle's flame with bare fingers (deals 1 HP burn damage to the"
         " user — this damage is real and cannot be prevented by DR). Choose a target"
         " within 5 meters. One specific memory the user is aware of is erased from the"
         " target's mind — they lose all recollection of that event, person, or piece"
         " of knowledge. The memory is not destroyed but stored within the candle wax."
         " The candle shortens by 5 cm. Restoring the memory requires re-lighting the"
         " candle from the same wax pool, or a Miracle-level ritual."],
    ]
    candle_abilities[0] = [Paragraph(c, S['TableHeader']) for c in candle_abilities[0]]
    for i in range(1, len(candle_abilities)):
        candle_abilities[i] = [
            Paragraph(candle_abilities[i][0], S['TableCell']),
            Paragraph(candle_abilities[i][1], S['TableCellCenter']),
            Paragraph(candle_abilities[i][2], S['TableCell']),
        ]
    story.append(Table(candle_abilities, colWidths=[1.3*inch, 0.7*inch, 4.3*inch],
                       style=table_style()))
    story.append(sp(2))

    story.append(Paragraph("<b>Drawbacks:</b>", S['BodyBold']))
    story.append(bullet(
        "<b>Dream Bleed.</b> Every time the candle is used, the user must roll Will-0."
        " On failure, fragments of dreams — not their own — intrude upon their sleep"
        " that night. These dreams contain images from the minds of previous users."
        " After 5 such failures, the user begins experiencing waking hallucinations"
        " (glimpses of strangers' memories) during moments of quiet, imposing -1 to"
        " Perception rolls in calm environments."
    ))
    story.append(bullet(
        "<b>Candle's Hunger.</b> The candle must be fed at least one hour of"
        " uninterrupted flame every 7 days, or it begins attracting ghosts and"
        " wandering spirits within a 100-meter radius. These entities are not"
        " hostile per se — they are drawn to the candle's lingering dream energy —"
        " but their presence complicates stealth, sleep, and spiritual work."
    ))
    story.append(bullet(
        "<b>Burns True.</b> The fire of this candle, though cool to objects, burns"
        " living flesh as if it were white-hot iron. Any creature that touches the"
        " flame takes 1d6 burning damage that ignores mundane armour. This damage"
        " is spiritual in nature — the wound aches in moonlight and cannot be healed"
        " by mundane means until the next dawn."
    ))
    story.append(sp(2))
    story.append(Paragraph(
        "<b>Sealing Instructions:</b> The candle must be kept in a bell jar of"
        " lead crystal on an altar draped in black velvet. It must never be exposed"
        " to direct sunlight or the light of a full moon. Once per month, a prayer"
        " to the Evernight Goddess must be recited over it. If the candle begins"
        " burning on its own, it indicates possession by an external intelligence —"
        " the seal has been breached and emergency measures are required.",
        S['Body']
    ))
    story.append(sp(3))

    # ── The Peerless Flagon ──
    story.append(Paragraph(
        "<b>Sealed Artifact 1–04: The Peerless Flagon</b> "
        "<i>(Sun Pathway · Grade 1 · Seq 4 equivalent)</i>",
        S['BodyBold']
    ))
    story.append(sp(1))
    story.append(body(
        "<b>Appearance:</b> A simple ceramic flagon of unglazed earthenware, roughly"
        " 20 cm tall, with a single symbol fired into its side — the Radiant Sun in"
        " full glory with twelve rays. It is extraordinarily heavy for its size"
        " (approximately 7 kg) and always feels slightly warm. When its stopper is"
        " removed, a golden light spills from the opening, illuminating dark spaces"
        " as though a lantern were inside. The flagon predates the Fourth Epoch and"
        " is believed to have been crafted by a Solar High Priest of the Ancient Sun"
        " Church who, in a moment of divine madness, attempted to bottle the dawn."
        " The church officially denies any knowledge of this artifact; unofficially,"
        " it is the subject of three ongoing internal investigations."
    ))
    story.append(sp(2))

    flagon_abilities = [
        ["Ability", "SPI Cost", "Effect"],
        ["Dawn's Draught",
         "2 SPI",
         "Drink from the flagon as a Ready maneuver. The user is immediately healed"
         " of 1d6+2 HP of injury and cured of any mundane poison or disease in their"
         " system. Undead creatures within 5 meters take 1d6 burning damage from the"
         " released radiance. The flagon refills itself at the next sunrise."
         " Maximum one draught per day, even if the flagon is refilled."],
        ["Purifying Flood",
         "3 SPI",
         "Upset the flagon as an Attack maneuver, spilling its contents across a"
         " 3-meter radius. The liquid burns with golden light for 3 turns, dealing"
         " 2d6 burning damage each turn to undead, demons, and corrupted beings"
         " within the area. Living creatures are unaffected but are blinded for 1 turn"
         " if they look directly at the spilled light. The liquid evaporates at the"
         " end of the duration. Usable once per hour — the flagon must slowly"
         " replenish from ambient sunlight."],
        ["Bottled Dawn",
         "5 SPI",
         "Remove the stopper and speak the True Name of the Sun (a three-syllable"
         " word that inflicts 1 HP of spiritual damage to any non-Sun-pathway being"
         " who hears it spoken aloud) as a Concentrate maneuver. A beam of brilliant"
         " golden light fires from the flagon's opening in a straight line 20 meters"
         " long and 1 meter wide. Everything in its path takes 4d6 burning damage"
         " (halved if the target succeeds on HT-3). Against undead, demons, or"
         " Beyonders of the Chained, Abyss, or Death pathways, damage is doubled"
         " and no half-damage is allowed. The flagon cracks noticeably after each"
         " use — after 3 uses of Bottled Dawn, it shatters permanently. The shards"
         " remain dangerous and retain Grade 2 classification."],
    ]
    flagon_abilities[0] = [Paragraph(c, S['TableHeader']) for c in flagon_abilities[0]]
    for i in range(1, len(flagon_abilities)):
        flagon_abilities[i] = [
            Paragraph(flagon_abilities[i][0], S['TableCell']),
            Paragraph(flagon_abilities[i][1], S['TableCellCenter']),
            Paragraph(flagon_abilities[i][2], S['TableCell']),
        ]
    story.append(Table(flagon_abilities, colWidths=[1.2*inch, 0.7*inch, 4.4*inch],
                       style=table_style()))
    story.append(sp(2))

    story.append(Paragraph("<b>Drawbacks:</b>", S['BodyBold']))
    story.append(bullet(
        "<b>Light's Burden.</b> While in possession of the flagon (carried on the"
        " person or within 3 meters for more than 1 hour), the user's eyes glow with"
        " a faint golden light. This imposes -4 to Stealth in darkness and makes the"
        " user memorable (+2 to any roll to identify or recall them). The glow"
        " fades 1d6 hours after the flagon is removed."
    ))
    story.append(bullet(
        "<b>Sun's Judgment.</b> The flagon judges its bearer. Any time the user"
        " knowingly tells a lie, breaks a sworn oath, or commits a cowardly act,"
        " the flagon grows hot (1 HP burn to the hand) and its light dims for"
        " 1 hour — during which time all abilities cost +1 SPI (minimum 1)."
        " After 10 such marks, the flagon refuses to grant any abilities until the"
        " user undertakes a genuine act of heroism (GM's discretion)."
    ))
    story.append(bullet(
        "<b>Burning Thirst.</b> The flagon induces a constant, mild thirst in its"
        " bearer. The user must drink at least twice as much water as normal each"
        " day or suffer from mild dehydration (-1 to HT rolls). Alcohol does not"
        " satisfy this thirst — it makes it worse (doubles the penalty)."
    ))
    story.append(sp(2))
    story.append(Paragraph(
        "<b>Sealing Instructions:</b> The flagon must be wrapped in a shroud of"
        " black silk that has never seen sunlight and stored in a stone vault at"
        " least 10 meters underground. Once per week, the shroud must be replaced"
        " with a fresh one. The old shroud must be burned at noon under an open sky."
        " If the flagon's warmth becomes uncomfortably hot through the shroud, it"
        " is attempting to break containment — a bishop-level exorcism must be"
        " performed within 24 hours.",
        S['Body']
    ))
    story.append(sp(3))



    story += chapter("Chapter 6.5: Divination Arts")

    story.append(flavor(
        "The world is full of obvious things which nobody by any chance ever observes. — Sherlock Holmes, via Klein Moretti"
    ))
    story.append(sp(4))

    story += section("I. The Divination Arts Skill")
    story.append(body(
        "<b>Divination Arts (SPI/Hard)</b> — the focused skill of obtaining hidden knowledge through "
        "spiritual techniques: pendulum swinging, coin tossing, dowsing, dream interpretation, mirror "
        "scrying, tarot reading, and other methods of peering beyond the mundane. "
        "<b>Casting Divination Arts costs 1–2 SPI</b> per use for most standard divinations."
    ))
    story.append(sp(2))
    story.append(body(
        "Divination Arts is <b>narrower</b> than Ritualistic Magic — it covers only divination — "
        "but it is <b>faster, cheaper, and more portable</b>. A Beyonder with Divination Arts can "
        "ask a quick question with a pendulum in moments (costing 1–2 SPI), while Ritualistic Magic "
        "requires full ritual setup even for simple divination. However, complex or large-scale divination "
        "(finding a hidden city, divining the future of a nation) still requires Ritualistic Magic."
    ))
    story.append(sp(2))
    story.append(body("The two skills overlap at the following boundaries:"))
    story.append(bbullet(
        "<b>Simple divination</b> (yes/no, vague direction, basic insight): "
        "Divination Arts is sufficient. Cost: 1–2 SPI."
    ))
    story.append(bbullet(
        "<b>Moderate divination</b> (find a person, glimpse a scene, interpret a dream): "
        "Either skill works. Divination Arts is faster (minutes vs. ritual setup) but may "
        "receive less detail. Cost: 2 SPI."
    ))
    story.append(bbullet(
        "<b>Complex divination</b> (long-range, multiple questions, resisting countermeasures): "
        "Requires Ritualistic Magic or a very high Divination Arts roll (-4 penalty). Cost: 2 SPI."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Default:</b> Divination Arts defaults to Ritualistic Magic-2 and vice versa. "
        "A character with one skill at 12+ can attempt the other at -2."
    ))
    story.append(sp(3))

    story += subsection("Supporting Skills")
    supp_div_data = [
        ["Supporting Skill", "Bonus", "Notes"],
        ["Occultism",              "+1", "Symbolism, mystical traditions, interpreting results"],
        ["Hidden Lore (relevant)", "+1", "Specific knowledge matching the divination's subject"],
        ["Psychology",             "+1", "Reading people through divination results; +1 to dream interpretation"],
         ["Cogitation",             "+1", "Entering the correct mental state for clear divination"],
    ]
    supp_div_data[0] = [Paragraph(c, S['TableHeader']) for c in supp_div_data[0]]
    for i in range(1, len(supp_div_data)):
        supp_div_data[i] = [Paragraph(supp_div_data[i][j],
            S['TableCellCenter'] if j == 1 else S['TableCell']) for j in range(3)]
    story.append(Table(supp_div_data, colWidths=[2.0*inch, 0.7*inch, 3.6*inch], style=table_style()))
    story.append(Paragraph("These bonuses are cumulative but cap at +2 total from supporting skills.",
        ParagraphStyle('note', fontName='Times-Italic', fontSize=9, textColor=PURPLE_ACC)))
    story.append(sp(4))

    story += section("II. Methods & Tools")
    story.append(body(
        "Divination Arts covers a wide range of techniques. Each method has its own strengths:"
    ))
    story.append(sp(2))

    method_data = [
        ["Method", "Best For", "Time", "SPI", "Notes"],
        ["Pendulum",
         "Yes/no questions, quick checks, spiritual dowsing",
         "1 min", "1",
         "The most common method. Requires a weighted object on a chain. The direction of swing indicates yes/no."],
        ["Coin",
         "Binary outcomes, pass/fail checks",
         "30 sec", "1",
         "Simplest method. Toss and interpret based on the spiritual feeling accompanying the result."],
        ["Dowsing Rods",
         "Finding objects, locations, water, hidden passages",
         "5 min", "1–2",
         "Uses L-shaped rods or a Y-branch. The rods cross or dip when over the target."],
        ["Dream Interpretation",
         "Complex questions, symbolic answers, prophetic glimpses",
         "Overnight", "2",
         "The caster sets an intent before sleep. The dream contains a symbolic answer requiring interpretation. +2 if the caster keeps a dream journal."],
        ["Mirror Scrying",
         "Viewing distant places or people, surveillance",
         "10 min", "2",
         "A darkened mirror or bowl of still water. The caster gazes until an image forms. Sensitive to light and noise."],
        ["Crystal Ball",
         "Precise visions, seeing the past/future",
         "15 min", "2",
         "Requires a clear quartz or glass sphere. Provides clear imagery. +1 if the ball has been consecrated."],
        ["Tarot / Cards",
         "Pattern recognition, multiple connected questions",
         "10 min", "2",
         "A spread of cards reveals relationships between factors. Requires a deck with spiritual resonance."],
        ["Bone Oracle",
         "Spirit communication, ancestral guidance",
         "15 min", "2",
         "Toss inscribed bones or lots and read the pattern. Effective for questions about the dead or spirits."],
    ]
    method_data[0] = [Paragraph(c, S['TableHeader']) for c in method_data[0]]
    for i in range(1, len(method_data)):
        method_data[i] = [Paragraph(method_data[i][j],
            S['TableCell'] if j in (1, 4) else S['TableCellCenter']) for j in range(5)]
    story.append(Table(method_data, colWidths=[1.0*inch, 1.4*inch, 0.6*inch, 0.4*inch, 2.9*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "A Beyonder may <b>specialise</b> in one method, gaining +1 when using it. "
        "This counts as a technique (see GURPS Techniques, p. B229). Specialisation does not "
        "penalise other methods — it simply reflects focused practice."
    ))
    story.append(sp(4))

    story += section("III. Performing a Divination")
    story.append(body(
        "A divination attempt follows four steps:"
    ))
    story.append(sp(2))

    story += subsection("Step 1 — State the Question")
    story.append(body(
        "The player states the question clearly. The GM determines the <b>difficulty</b> of the "
        "question — how hard it is to obtain a clear answer:"
    ))
    story.append(sp(2))
    q_data = [
        ["Question Difficulty", "Modifier", "Example"],
        ["Trivial — personal, present, simple", "+2", "\"Is there danger behind this door?\""],
        ["Easy — personal, recent, concrete", "+0", "\"Where did I lose my key?\""],
        ["Moderate — impersonal, distant, vague", "-2", "\"Is the merchant hiding something?\""],
        ["Hard — well-guarded, future, abstract", "-4", "\"Will the Church raid this hideout?\""],
        ["Extreme — divine, fate-bound, cosmic", "-6 or worse", "\"What is the true name of the Hidden One?\""],
    ]
    q_data[0] = [Paragraph(c, S['TableHeader']) for c in q_data[0]]
    for i in range(1, len(q_data)):
        q_data[i] = [Paragraph(q_data[i][j],
            S['TableCell'] if j == 2 else S['TableCellCenter']) for j in range(3)]
    story.append(Table(q_data, colWidths=[1.8*inch, 1.0*inch, 3.5*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Step 2 — Choose Method & Pay SPI")
    story.append(body(
        "Select a divination method (see Section II). Pay the SPI cost. If using ritualistic "
        "divination (full ritual setup), use the Ritualistic Magic rules in Chapter 7 instead."
    ))
    story.append(sp(3))

    story += subsection("Step 3 — Roll & Apply Modifiers")
    story.append(body("Roll Divination Arts, adding all applicable modifiers:"))
    story.append(sp(2))
    div_mod_data = [
        ["Modifier Source", "Modifier"],
        ["Question difficulty", "See Step 1 table"],
        ["Method match (right tool for the question)", "+0 to +2"],
        ["Target link (true name, possession, blood)", "+0 to +4 (same as ritual link rules)"],
        ["Favourable timing (astrological, domain-appropriate)", "+1"],
        ["Unfavourable timing (wrong phase, entity's off-day)", "-1 to -2"],
        ["Interrupted or rushed (half the usual time)", "-2"],
        ["Quiet, dedicated space", "+0 to +1"],
        ["Previous divination about the same subject (cumulative)", "-2 per repeat"],
    ]
    div_mod_data[0] = [Paragraph(c, S['TableHeader']) for c in div_mod_data[0]]
    for i in range(1, len(div_mod_data)):
        div_mod_data[i] = [Paragraph(c, S['TableCellCenter'] if j == 1 else S['TableCell']) for j, c in enumerate(div_mod_data[i])]
    story.append(Table(div_mod_data, colWidths=[3.8*inch, 2.5*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Burning SPI to improve the roll:</b> As with rituals, you may spend additional SPI "
        "(1 SPI = +1, no cap) after seeing your result."
    ))
    story.append(sp(3))

    story += subsection("Step 4 — Interpret the Result")
    story.append(body("The GM interprets the divination based on the roll result:"))
    story.append(sp(2))
    interp_data = [
        ["Roll Result", "Clarity", "GM Gives"],
        ["Success by 5+", "Crystal clear", "Precise answer, additional useful detail, possibly a vision"],
        ["Success by 3–4", "Clear", "Direct answer to the question"],
        ["Success by 0–2", "Vague", "Symbolic or partial answer — requires interpretation (IQ or Occultism roll to fully understand)"],
        ["Failure by 1–4", "Murky", "No useful information. SPI spent. May retry after 1 hour with fresh approach."],
        ["Failure by 5+", "Distorted", "Misleading or inverted answer. The caster believes it is genuine."],
        ["Critical Failure", "Backlash", "Roll on the Critical Failure Table (Chapter 7, Section VI) — treat as a ritual critical failure."],
    ]
    interp_data[0] = [Paragraph(c, S['TableHeader']) for c in interp_data[0]]
    for i in range(1, len(interp_data)):
        interp_data[i] = [Paragraph(c, S['TableCell']) if j == 2 else Paragraph(c, S['TableCellCenter']) for j, c in enumerate(interp_data[i])]
    story.append(Table(interp_data, colWidths=[1.3*inch, 1.0*inch, 4.0*inch], style=table_style()))
    story.append(sp(4))

    # ─────────────────────────────────────────────────────────────────────────────
    # Section IV: Divination Awareness & Countermeasures (moved from Chapter 4)
    # ─────────────────────────────────────────────────────────────────────────────
    story += section("IV. Divination Awareness & Countermeasures")
    story.append(body(
        "In a world where a Seer can glimpse your past with a candle and a lock of hair, "
        "the ability to <b>detect</b> and <b>thwart</b> divination is as vital as any offensive power. "
        "Certain pathways develop innate awareness of being watched through spiritual means, "
        "while others learn active techniques to conceal themselves from prying eyes."
    ))
    story.append(sp(2))

    # ── Quick Reference placed at top for usability ──────────────────────────
    story += subsection("Quick Reference — Resolution Order")
    story.append(body(
        "When a Beyonder is divined, resolve in this order:"
    ))
    story.append(sp(2))
    story.append(bullet("<b>Step 1 — Sequence Immunity:</b> Does the target's Sequence impose a penalty on the diviner's effective skill? (See Sec. 5.) If the penalty makes the roll impossible, the diviner must overcome it via Counter-Countermeasures (Sec. 6)."))
    story.append(bullet("<b>Step 2 — Passive Awareness:</b> Does the target have a pathway ability that grants automatic detection? (See Sec. 1.) If yes, they know immediately and may act."))
    story.append(bullet("<b>Step 3 — Detection Roll:</b> If not automatic, the target may roll SPI/Per (if they have reason to suspect) to sense the divination. (See Sec. 2.)"))
    story.append(bullet("<b>Step 4 — Active Countermeasures:</b> Apply the target's active technique penalties to the diviner's Divination Arts or Ritualistic Magic roll. (See Sec. 3.) All active techniques stack."))
    story.append(bullet("<b>Step 5 — Counter-Countermeasures:</b> Apply any bonuses the diviner has earned — Sequence advantage, direct link, blood sacrifice, or a dedicated ritual. (See Sec. 6.)"))
    story.append(bullet("<b>Step 6 — Resolution:</b> The diviner rolls. On success, the effect goes through (possibly distorted by countermeasures). On failure, the attempt fails and the target may be alerted."))
    story.append(sp(3))

    # ── 1. Passive Awareness ─────────────────────────────────────────────────
    story += subsection("1. Sensing Divination — Passive Awareness")
    story.append(body(
        "When someone attempts to divine you — your location, identity, secrets, or future — you "
        "may feel a spiritual disturbance. The following pathways and sequences gain automatic "
        "awareness or a free roll to detect the attempt:"
    ))
    story.append(body(
        "<b>Note:</b> Beyonders of Seq 4+ (Demigod) always have automatic awareness (see row 8). "
        "The entries below apply primarily to Seq 9–5 characters who have not yet reached "
        "that universal threshold."
    ))
    story.append(sp(2))

    sense_data = [
        ["Pathway", "Seq & Ability", "Detection"],
        ["Fool (Seer)", "Seq 8+ (Clown Intuition)",
         "Sensed as a 'prying gaze' or subtle spiritual pressure. Free Per roll at +2 when someone actively divines them."],
        ["Darkness (Sleepless -> Midnight Poet -> Nightmare)", "Seq 7+ (Nightmare)",
         "Feel the disturbance as a cold touch on their Ether Body. Automatic SPI roll to notice."],
        ["Hanged Man (Secrets Supplicant)", "Seq 7+",
         "Instinctive awareness when their secrets are pried into. +2 to detect divination related to their hidden knowledge."],
        ["Hermit (Mystery Pryer)", "Seq 9+ (Eyes of Mystery Prying)",
         "Always-on spiritual perception. Automatic SPI roll to detect any divination targeting them within 50 meters."],
        ["Justiciar (Arbiter -> Sheriff)", "Seq 8+ (Sheriff)",
         "Sense when a law or rule is being broken spiritually. +2 to detect divination as a form of spiritual trespass."],
        ["Wheel of Fortune (Monster)", "Seq 9+",
         "Passive luck interference. At the GM's discretion, any divination attempt against a Monster may suffer -1 as random chance skews the result. (Passive, unconscious.)"],
        ["Fool / Error / Door", "Seq 5+ (any)",
         "Free Per roll (no bonus) to detect any divination targeting them. +2 if the divination concerns fate, concealment, or secrets. Lord of the Mysteries pathways gain innate divination awareness as part of their authority."],
        ["Any pathway", "Seq 4+ (Demigod)",
         "Automatic awareness. A demigod always knows when someone of weaker Sequence attempts to divine them. Equal or stronger Sequence requires a Quick Contest of SPI vs the diviner's Divination Arts or Ritualistic Magic."],
    ]
    sense_data[0] = [Paragraph(c, S['TableHeader']) for c in sense_data[0]]
    for i in range(1, len(sense_data)):
        sense_data[i] = [Paragraph(c, S['TableCell']) if j != 0 else Paragraph(c, S['TableCellCenter']) for j, c in enumerate(sense_data[i])]
    story.append(Table(sense_data, colWidths=[1.4*inch, 1.5*inch, 3.4*inch], style=table_style()))
    story.append(sp(3))

    # ── 2. Detection Mechanics ───────────────────────────────────────────────
    story += subsection("2. Detection Mechanics")
    story.append(body(
        "When a Beyonder with passive awareness is being divined — or when any Beyonder suspects "
        "they are under observation — the GM calls for a <b>SPI or Per roll</b> (whichever is higher). "
        "This is a free action (once per divination attempt) and does not cost SPI."
    ))
    story.append(sp(2))

    det_data = [
        ["Roll Result", "Outcome"],
        ["Success", "You feel a distinct sense of being watched or pried into. You know the general direction of the diviner (if within 100 meters) and the domain being probed (identity, location, secrets, etc.)."],
        ["Success by 3+", "You sense the diviner's approximate Sequence (±1) and their general Pathway family. You may attempt to trace the connection back to its source (Quick Contest of your SPI vs the diviner's SPI)."],
        ["Critical Success", "You gain a clear vision of the diviner's face and surroundings. You may attempt to feed a false image or piece of information back through the connection — make a Ritualistic Magic or Acting roll contested by the diviner's SPI. On success, they receive your false information as genuine."],
        ["Failure", "You feel nothing unusual. The divination proceeds unnoticed."],
        ["Critical Failure", "You sense nothing, and the diviner is aware that you <i>could</i> have detected them — they know you failed to notice."],
    ]
    det_data[0] = [Paragraph(c, S['TableHeader']) for c in det_data[0]]
    for i in range(1, len(det_data)):
        det_data[i] = [Paragraph(c, S['TableCell']) if j == 1 else Paragraph(c, S['TableCellCenter']) for j, c in enumerate(det_data[i])]
    story.append(Table(det_data, colWidths=[1.3*inch, 5.0*inch], style=table_style()))
    story.append(sp(2))

    det_mod_data = [
        ["Situation", "Modifier"],
        ["Diviner is 2+ Sequences weaker than the target", "+2"],
        ["Diviner is 2+ Sequences stronger than the target", "-2"],
        ["Target carries a protective charm or item", "+1"],
        ["Diviner has the target's true name + personal item", "-2"],
        ["Target is in a warded or sacred space", "+2"],
        ["Diviner and target are of equal Sequence", "+0"],
    ]
    det_mod_data[0] = [Paragraph(c, S['TableHeader']) for c in det_mod_data[0]]
    for i in range(1, len(det_mod_data)):
        det_mod_data[i] = [Paragraph(c, S['TableCellCenter'] if j == 1 else S['TableCell']) for j, c in enumerate(det_mod_data[i])]
    story.append(Table(det_mod_data, colWidths=[4.0*inch, 2.3*inch], style=table_style()))
    story.append(sp(3))

    # ── 3. Active Techniques ─────────────────────────────────────────────────
    story += subsection("3. Active Anti-Divination Techniques")
    story.append(body(
        "Beyonders with sufficient Sequence and the right pathway can actively hide from divination. "
        "Each technique lists its SPI cost, duration, and mechanical effect. All active techniques "
        "<b>stack</b> — their penalties add together when a divination is attempted."
    ))
    story.append(sp(2))

    # 3A
    story += subsection("3A. Spiritual Warding (Universal, Seq 7+)")
    story.append(body(
        "A Beyonder erects a thin film of protective spirituality around themselves. This is the "
        "simplest and most widely known anti-divination technique."
    ))
    story.append(bullet("Cost: 2 SPI"))
    story.append(bullet("Duration: 1 hour, or until the ward is broken"))
    story.append(bullet("Effect: All divination attempts against you are at -2 while the ward holds"))
    story.append(bullet("Bonus: You gain +2 on detection rolls (see Sec. 2 above) while warding is active"))
    story.append(bullet("Limitation: Ward breaks if you suffer injury greater than HP/3 (round down) from a single attack"))
    story.append(sp(2))

    # 3B
    story += subsection("3B. Concealment (Darkness Pathway, Seq 5 — Spirit Warlock)")
    story.append(body(
        "The Evernight Goddess's domain. The Beyonder wraps themselves in the concept of "
        "<b>Concealment</b> — the spiritual equivalent of hiding in plain sight. They become "
        "harder to find, remember, and divine."
    ))
    story.append(bullet("Cost: 2 SPI"))
    story.append(bullet("Duration: 1 hour"))
    story.append(bullet("Effect: All divination against you is at -4"))
    story.append(bullet("Bonus: Anyone trying to recall specific details about you must first win a Quick Contest of Will vs your SPI"))
    story.append(bullet("Extension: You may extend Concealment to one willing target within touch range at +1 SPI per additional target"))
    story.append(sp(2))

    # 3C
    story += subsection("3C. Identity Confusion (Fool Pathway, Seq 6 — Faceless)")
    story.append(body(
        "A Faceless can mask their spiritual aura to match a different person they have "
        "studied or touched. If a divination targets the Faceless's original identity, it "
        "instead picks up the masked aura — leading the diviner to the wrong person."
    ))
    story.append(bullet("Cost: 2 SPI"))
    story.append(bullet("Duration: 1 hour, or until the Faceless changes their masked identity"))
    story.append(bullet("Effect: Any divination attempting to identify you or locate you by your spiritual signature diverts to the person you are impersonating"))
    story.append(bullet("Limitation: You must have met or studied the target whose aura you mimic. A simple description is not enough — you need 10+ minutes of close observation or a personal item."))
    story.append(bullet("Counter: A diviner who critically succeeds on their Divination Arts or Ritualistic Magic roll realises the spiritual signature is a mask and may attempt a Quick Contest of Divination Arts or Ritualistic Magic vs your SPI to pierce it"))
    story.append(sp(2))

    # 3D
    story += subsection("3D. Door Misdirection (Door Pathway, Seq 5 — Traveler)")
    story.append(body(
        "The Traveler introduces a tiny 'error' into the spiritual connection — the divination "
        "goes to the wrong address. The diviner's spell connects to a random location or person "
        "instead of the intended target."
    ))
    story.append(bullet("Cost: 3 SPI"))
    story.append(bullet("Duration: Instant (opposes a single divination attempt)"))
    story.append(bullet("Effect: On a successful SPI roll, the divination is redirected to a random location or person within 1 mile"))
    story.append(bullet("Deception: The diviner does not know their spell was misdirected unless they critically succeed"))
    story.append(bullet("Limitation: Does not work against diviners 2+ Sequences stronger than you"))
    story.append(sp(2))

    # 3E
    story += subsection("3E. Historical Mimicry: Spiritual Blank (Fool Pathway, Seq 3 — Scholar of Yore)")
    story.append(body(
        "The Scholar projects a distracting historical figure or event over their own spiritual signature. "
        "To any divination spell, the Scholar appears as a different person, a location, or simply "
        "a blurred patch of unresolved history."
    ))
    story.append(bullet("Cost: 5 SPI"))
    story.append(bullet("Duration: 1d6 minutes (the projection collapses immediately if you take any hostile action)"))
    story.append(bullet("Effect: Any divination targeting you returns information about the projected historical figure or scene instead of you"))
    story.append(bullet("Penalty: Concentrating to maintain the projection prevents you from taking other complex actions"))
    story.append(bullet("Detection: A demigod of equal or stronger Sequence can perceive the projection as a 'laminated' spiritual layer and may attempt a Quick Contest of Divination Arts or Ritualistic Magic vs your SPI to see through it"))
    story.append(sp(2))

    # 3F
    story += subsection("3F. Self-Divination Interference (Universal, Seq 5+)")
    story.append(body(
        "A Beyonder pre-emptively divines <i>themselves</i>, saturating their spiritual signature "
        "with the result. For the rest of the day, any external divination about the same question "
        "receives a distorted echo of the Beyonder's own self-divination instead."
    ))
    story.append(bullet("Cost: SPI equal to what a divination of that scope would normally cost (see Chapter 6.5, Section III, or Chapter 7, Power Sources)"))
    story.append(bullet("Duration: 24 hours, or until you perform a new self-divination that overwrites the previous one"))
    story.append(bullet("Effect: The external diviner receives a false but plausible result — the echo of your self-divination"))
    story.append(bullet("Deception: The diviner does not know the result is false unless they critically succeed"))
    story.append(sp(3))

    # ── 4. Items & Materials ─────────────────────────────────────────────────
    story += subsection("4. Anti-Divination Items & Materials")
    story.append(body(
        "Certain mystical items and preparations provide passive or active protection against divination:"
    ))
    story.append(sp(2))

    item_data = [
        ["Item", "Effect", "Cost"],
        ["Concealment Pendant\n(Darkness charm)", "+2 to detect divination; worn passively.", "£50 / 5 pts"],
        ["Eyes of the Spirit World\n(Hermit charm)", "When activated (1 SPI), reveals if you are being divined right now. One charge per use.", "£30 / 3 pts per charge"],
        ["Blank Paper Talisman\n(Fool pathway)", "Affix to a surface: the room cannot be divined for 1 hour. One-time use.", "£20 each"],
        ["Mystical Candle of Obscurity", "Burning during a ritual suppresses detection of that ritual by -3 to anyone sensing it. Lasts 1 hour.", "£15"],
        ["Silver Mirror of Reflection", "When placed on an altar, any divination targeting the owner has a 50% chance (1–3 on 1d6) of reflecting back on the diviner.", "£40 + blessing ritual"],
        ["Salt of Spiritual Clarity", "A pinch thrown into the air purifies the spiritual environment. Any active divination targeting the area is interrupted and must restart.", "£5 per pouch (3 uses)"],
    ]
    item_data[0] = [Paragraph(c, S['TableHeader']) for c in item_data[0]]
    for i in range(1, len(item_data)):
        item_data[i] = [Paragraph(item_data[i][j],
            S['TableCellCenter'] if j == 2 else S['TableCell']) for j in range(3)]
    story.append(Table(item_data, colWidths=[1.6*inch, 3.5*inch, 1.2*inch], style=table_style()))
    story.append(sp(3))

    # ── 5. Sequence Immunity ─────────────────────────────────────────────────
    story += subsection("5. Sequence Immunity — When Divination Struggles")
    story.append(body(
        "At certain thresholds of power, a Beyonder becomes extremely difficult to divine. "
        "Instead of outright immunity, these thresholds impose severe penalties — making "
        "success possible only for the exceptionally skilled, the well-prepared, or the lucky."
    ))
    story.append(sp(2))

    imm_data = [
        ["Sequence", "Penalty"],
        ["Seq 5 (Beyonder Threshold)",
         "Divination from Seq 9–7 Beyonders is at -6 unless the diviner has a direct link (true name + blood or hair), which reduces the penalty to -3."],
        ["Seq 4 (Demigod)",
         "Divination from any weaker-Sequence Beyonder is at -10. Equal-Sequence divination is at -3. Only a critical success (3–4) can succeed — the -10 penalty cannot be offset by skill alone."],
        ["Seq 3 (Saint)",
         "Only demigods (Seq 4+) or those with a special connection can attempt to divine you. Weaker Sequences are at -10 and only a critical success (3–4) can succeed — the penalty cannot be offset by skill alone."],
        ["Seq 2 (Angel)",
         "Divination is at -10 and requires the diviner to possess your true honorific name and an intimate possession. The mere attempt may draw your attention — the GM decides when and how."],
        ["Seq 6–9",
         "No passive penalty applies. The Sequence Advantage rule (below) only affects targets at Seq 5+."],
    ]
    imm_data[0] = [Paragraph(c, S['TableHeader']) for c in imm_data[0]]
    for i in range(1, len(imm_data)):
        imm_data[i] = [Paragraph(c, S['TableCell']) if j == 1 else Paragraph(c, S['TableCellCenter']) for j, c in enumerate(imm_data[i])]
    story.append(Table(imm_data, colWidths=[1.4*inch, 4.9*inch], style=table_style()))
    story.append(sp(3))

    # ── 6. Countering Anti-Divination ─────────────────────────────────────────
    story += subsection("6. Countering Anti-Divination")
    story.append(body(
        "Determined diviners are not helpless against a hidden target. The following methods can "
        "pierce or bypass anti-divination techniques:"
    ))
    story.append(sp(2))
    story.append(bullet("<b>Sequence Advantage:</b> If the diviner is 2+ Sequences stronger than the target, they ignore the target's passive Sequence penalty (but active techniques like Concealment or Identity Confusion still apply at half penalty, rounded up)."))
    story.append(bullet("<b>Direct Link:</b> Having the target's true name + an intimate personal item halves all anti-divination penalties (round down)."))
    story.append(bullet("<b>HP Sacrifice:</b> Burning 4+ HP (at 2 HP = 1 SPI rate) when casting a divination ignores -2 of anti-divination penalties for that attempt."))
    story.append(bullet("<b>Anti-Anti-Divination Ritual:</b> A dedicated ritual (base difficulty -4, requires rare materials worth £100+) can temporarily suppress a target's protective techniques for 1d hours. This requires the target's name and a personal item."))
    story.append(bullet("<b>Divine Intervention:</b> A prayer to an orthodox deity whose domain includes divination (the God of Knowledge and Wisdom, the Evernight Goddess) may grant a temporary bypass — but the deity will expect something in return. The GM should set a clear cost (a future service, a sacrifice, or a quest) and may limit this to once per story arc."))
    story.append(sp(3))

    story += chapter("Chapter 7: Ritualistic Magic")

    story.append(flavor(
        "Ritualistic magic is a very dangerous thing... — Emperor Roselle to Klein Moretti"
    ))
    story.append(sp(4))

    story += section("I. Core Philosophy")
    story.append(body(
        "Ritualistic Magic is not spellcasting. It is a structured negotiation with forces "
        "older and stranger than you. Every ritual is built on <b>three pillars</b>:"
    ))
    story.append(sp(2))
    story.append(bbullet(
        "<b>Sacrifice</b> — sparks the interest of the entity you invoke. "
        "The quality and relevance of your offering determines whether they notice."
    ))
    story.append(bbullet(
        "<b>Incantation</b> — specifically describes the existence you call upon. "
        "Correct names, honorifics, and domains matter. Errors invite the wrong thing."
    ))
    story.append(bbullet(
        "<b>Symbols & Formatting</b> — the physical arrangement, drawn sigils, candle "
        "placement, and altar layout convey your intent to the spiritual world."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Low-Sequence Beyonders are not strong enough.</b> Almost all the ritualistic magic "
        "they can perform is the seeking of external powers and help. A Sequence 9 or 8 Beyonder "
        "has limited Spirituality and weak personal authority over symbolism — they must invoke "
        "higher beings to achieve meaningful effects. This is not a weakness of the system; it is "
        "the fundamental nature of ritual work."
    ))
    story.append(body(
        "<b>Praying to Oneself</b> — Ritualistic magic can also be directed inward, drawing power "
        "from your own spirituality without petitioning any god. To do so, craft a "
        "<b>three-line description</b> of your being that precisely identifies your spiritual "
        "location within the Wall of Spirituality. For example: <i>\"Cordu Village's Trickster "
        "King, Aurore Lee's younger brother, An entity known as Lumian Lee...\"</i> "
        "The benefit is total independence from divine constraints — the weakness is that the "
        "result is limited by your personal power. A weak Beyonder gets a weak result."
    ))
    story.append(sp(2))
    story.append(bbullet("<b>Rituals are processes, not buttons.</b> They take time, materials, and preparation."))
    story.append(bbullet("<b>Power must come from somewhere.</b> Your own SPI is finite. This is why you invoke gods, make sacrifices, or gather multiple participants."))
    story.append(bbullet("<b>Sequence determines authority.</b> The lower your Sequence, the weaker your symbolism and personal authority — you must compensate with elaborate ritual, better materials, and invoking higher beings."))
    story.append(bbullet("<b>Every ritual is a risk.</b> The wrong incantation, the wrong timing, or insufficient sacrifice can attract entities you did not intend to contact."))
    story.append(sp(4))

    story += section("II. The Primary Skill")
    story.append(body(
        "<b>Ritualistic Magic (IQ/Very Hard)</b> — your core skill. It has no default and cannot "
        "be substituted. It covers your ability to design, prepare, and execute rituals correctly. "
        "Supporting skills provide complementary bonuses but never replace this skill."
    ))
    story.append(sp(2))
    supp_data = [
        ["Supporting Skill", "Bonus", "Notes"],
        ["Occultism",                          "+1", "General ritual theory, symbol knowledge, mysticism fundamentals"],
        ["Thaumatology",                       "+1", "Theoretical magical framework; stacks with Occultism"],
        ["Hidden Lore (relevant domain)",      "+1", "Specific knowledge of the entity, domain, or spirit world"],
        ["Research",                           "+1", "If caster spent significant time researching this specific effect"],
        ["Professional Skill (Astrology etc)", "+1", "When the ritual's material component or timing falls within that domain"],
    ]
    supp_data[0] = [Paragraph(c, S['TableHeader']) for c in supp_data[0]]
    for i in range(1, len(supp_data)):
        supp_data[i] = [Paragraph(supp_data[i][j],
            S['TableCellCenter'] if j == 1 else S['TableCell']) for j in range(3)]
    story.append(Table(supp_data, colWidths=[2.0*inch, 0.7*inch, 3.6*inch], style=table_style()))
    story.append(Paragraph("These bonuses are cumulative but cap at +3 total from supporting skills.",
        ParagraphStyle('note', fontName='Times-Italic', fontSize=9, textColor=PURPLE_ACC)))
    story.append(sp(4))

    story += section("III. Ritual Resolution — Two Modes")
    story.append(body(
        "Ritualistic Magic can be resolved at two levels of detail depending on the stakes. "
        "<b>Quick Ritual</b> is for routine work (daily divination, simple prayers, minor warding). "
        "<b>Full Ritual</b> is for consequential magic (curses, binding, summoning, cleansing). "
        "Both use the same underlying canon procedure — they just expose different levels of granularity."
    ))
    story.append(sp(2))
    story.append(bbullet("<b>Quick Ritual:</b> Resolve in 4 steps. ~1 minute at the table. 15–30 minutes in-game."))
    story.append(bbullet("<b>Full Ritual:</b> Three phases — Prepare, Conduct, Close. ~5 minutes at the table. 30 min–1 hr in-game."))
    story.append(bbullet("<b>Ceremony:</b> For advancement rituals and large-scale workings. Story-level resolution — no mechanical shortcut."))
    story.append(sp(4))

    story += subsection("A. Quick Ritual")
    story.append(body(
        "Use for routine, low-stakes rituals where the drama is in the outcome, not the setup."
    ))
    story.append(sp(2))

    story += subsection("Step 1 — State Intent")
    story.append(body(
        "The player describes what they want in one or two sentences. The GM confirms the effect "
        "category (Light, Moderate, or Heavy — see Section V) and its base difficulty."
    ))
    story.append(sp(2))

    story += subsection("Step 2 — Determine Power Source")
    story.append(body("The player chooses where the energy comes from. Pick one:"))
    story.append(bbullet(
        "<b>Personal SPI (Praying to Oneself):</b> Pay the SPI cost from your own pool. "
        "Safest method — no entity becomes aware of you. The result is limited by your personal power."
    ))
    story.append(bbullet(
        "<b>Invocation (Deity or Hidden Existence):</b> Borrow power from an external entity. "
        "The GM rolls on the Entity Response Table (Section IV) to determine the entity's reaction. "
        "More powerful than personal SPI but carries risk."
    ))
    story.append(bbullet(
        "<b>Sacrifice or External Source:</b> Use HP, multiple participants, or a catalyst. "
        "See Section IV: Power Sources for details."
    ))
    story.append(sp(2))
    story.append(body(
        "<i>Note: You may also burn additional SPI after the roll to improve it (see \"Burning FP & SPI to "
        "Modify Rolls\" in Chapter 2). This is separate from the ritual's fuel cost.</i>"
    ))
    story.append(sp(2))

    story += subsection("Step 3 — Apply Modifiers")
    story.append(body("Sum the following two modifiers:"))
    story.append(sp(2))

    story.append(body("<b>1. Preparation Quality</b>"))
    prep_quick_data = [
        ["Condition", "Modifier"],
        ["Excellent — sanctified space, domain-matched materials, proper altar, Cogitation + Wall", "+2"],
        ["Adequate — clean space, basic materials, Cogitation + Wall", "+0"],
        ["Poor / None — no preparation, wrong materials, rushed, no Wall", "-2 to -4"],
    ]
    prep_quick_data[0] = [Paragraph(c, S['TableHeader']) for c in prep_quick_data[0]]
    for i in range(1, len(prep_quick_data)):
        prep_quick_data[i] = [Paragraph(c, S['TableCellCenter']) for c in prep_quick_data[i]]
    story.append(Table(prep_quick_data, colWidths=[3.5*inch, 1.5*inch], style=table_style()))
    story.append(sp(2))

    story.append(body("<b>2. Target Link</b>"))
    link_quick_data = [
        ["Link to Target", "Modifier"],
        ["Perfect — true name + intimate possession (blood, hair, photo)", "+4"],
        ["Strong — true name only, or intimate possession only", "+2 to +3"],
        ["Weak — public alias, secondhand item, vague description", "+0 to -1"],
        ["None — no name, no item, no description", "-4"],
    ]
    link_quick_data[0] = [Paragraph(c, S['TableHeader']) for c in link_quick_data[0]]
    for i in range(1, len(link_quick_data)):
        link_quick_data[i] = [Paragraph(c, S['TableCellCenter']) for c in link_quick_data[i]]
    story.append(Table(link_quick_data, colWidths=[3.5*inch, 1.5*inch], style=table_style()))
    story.append(sp(2))

    story += subsection("Step 4 — Roll & Resolve")
    story.append(body(
        "Roll Ritualistic Magic, add the total modifier, and compare to the effect's base difficulty:"
    ))
    eff_quick_data = [
        ["Effect Weight", "Base Difficulty", "Typical SPI Cost"],
        ["Light (divination, minor communication, simple warding)", "+0", "2 SPI"],
        ["Moderate (curse, cleansing, binding, fabrication, enhancement)", "-2", "4–6 SPI"],
        ["Heavy (summoning, soul-anchoring, transference, unraveling)", "-4", "8+ SPI"],
    ]
    eff_quick_data[0] = [Paragraph(c, S['TableHeader']) for c in eff_quick_data[0]]
    for i in range(1, len(eff_quick_data)):
        eff_quick_data[i] = [Paragraph(c, S['TableCell']) for c in eff_quick_data[i]]
    story.append(Table(eff_quick_data, colWidths=[3.2*inch, 1.0*inch, 1.5*inch], style=table_style()))
    story.append(sp(2))

    resolve_data = [
        ["Result", "Outcome"],
        ["Success by 3+", "Effect surpasses intent. Entity pleased (if invoked)."],
        ["Success by 0–2", "Effect works as intended."],
        ["Failure by 1–4", "No effect. SPI and materials spent. Faint spiritual disturbance."],
        ["Failure by 5+", "Partial wrong activation. GM chooses a distorted outcome."],
        ["Critical Failure (17–18)", "Roll on the Critical Failure Table (Section VI)."],
    ]
    resolve_data[0] = [Paragraph(c, S['TableHeader']) for c in resolve_data[0]]
    for i in range(1, len(resolve_data)):
        resolve_data[i] = [Paragraph(c, S['TableCell']) for c in resolve_data[i]]
    story.append(Table(resolve_data, colWidths=[1.8*inch, 4.5*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Burning SPI to improve the roll:</b> After seeing your result, you may spend additional SPI "
        "(1 SPI = +1) using the universal burning mechanic (Chapter 2). There is no cap. This is separate "
        "from the ritual's fuel cost — you can do both."
    ))
    story.append(sp(4))

    story += subsection("B. Full Ritual")
    story.append(body(
        "For important or dangerous rituals. Uses the complete canon procedure compressed into "
        "<b>three phases</b>. The full 12-step reference is preserved at the end of this section "
        "for GMs who want the novel's texture."
    ))
    story.append(sp(3))

    story += subsection("Phase I — Prepare")
    story.append(body("The player declares the following. Each choice feeds into a single Preparation Modifier."))
    story.append(sp(2))
    story.append(bbullet("<b>Target entity:</b> Orthodox god / Hidden existence / Evil god / Yourself"))
    story.append(bbullet("<b>Timing:</b> Does it match the entity's domain? (Night -> Evernight, Noon -> Sun, etc.)"))
    story.append(bbullet("<b>Materials:</b> Domain-appropriate candles (2 ingredients each), essential oils, pure metal dagger, paper, salt"))
    story.append(bbullet("<b>Space:</b> Clean, spiritually cleansed, Wall of Spirituality erected"))
    story.append(bbullet("<b>Sacrifice (if any):</b> HP / none (see Section IV — HP Sacrifice)"))
    story.append(bbullet("<b>Link to target:</b> None / Weak / Strong / Perfect"))
    story.append(sp(2))

    story.append(body("The GM determines the <b>Preparation Modifier</b> from the player's declarations:"))
    prep_full_data = [
        ["Preparation Quality", "Modifier", "What This Looks Like"],
        ["Excellent", "+3", "Sanctified space, rare domain-matched materials, celestial timing, perfect link, high-grade sacrifice"],
        ["Good", "+1 to +2", "Domain-matched candles, proper altar, strong link, clean space, adequate materials"],
        ["Adequate", "+0", "Correct materials, clean space, basic link, Cogitation + Wall erected"],
        ["Poor", "-1 to -2", "Improvised space, generic items, no cleansing, weak link, rushed"],
        ["None", "-4 or worse", "Open street, wrong materials, no link, no Cogitation, no Wall"],
    ]
    prep_full_data[0] = [Paragraph(c, S['TableHeader']) for c in prep_full_data[0]]
    for i in range(1, len(prep_full_data)):
        prep_full_data[i] = [Paragraph(prep_full_data[i][j],
            S['TableCellCenter'] if j == 1 else S['TableCell']) for j in range(3)]
    story.append(Table(prep_full_data, colWidths=[1.3*inch, 0.9*inch, 4.1*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Phase II — Conduct")
    story.append(body(
        "The player narrates the incantation (4-part Hermes structure — see reference below). "
        "The GM may award a <b>Flourish Bonus</b> (+1) for good in-character delivery."
    ))
    story.append(sp(2))
    story.append(body("<b>Effective skill</b> = Ritualistic Magic + Preparation Mod + Flourish Bonus"))
    story.append(body("If invoking an entity, the GM rolls on the <b>Entity Response Table</b> (Section IV) and adds its result to the total."))
    story.append(sp(2))
    story.append(body(
        "<b>Burning SPI to improve the roll:</b> As with Quick Rituals, you may spend additional SPI "
        "(1 SPI = +1, no cap) after seeing your result, separate from the ritual's fuel cost."
    ))
    story.append(sp(3))

    story += subsection("Phase III — Close")
    story.append(body("The player describes the closing procedure. The GM confirms it and resolves the outcome."))
    story.append(sp(2))
    story.append(bullet("Drip a drop of essential oil on each candle."))
    story.append(bullet("Burn the piece of paper used to draw the target symbol."))
    story.append(bullet("Thank the entity (if one was invoked)."))
    story.append(bullet("Extinguish candles <b>right to left</b>, beginning with 'me' and then 'god'."))
    story.append(bullet("Dispel the Wall of Spirituality."))
    story.append(sp(2))
    story.append(body("Then resolve using the same outcome table as Quick Ritual (Step 4)."))
    story.append(sp(4))

    story += subsection("C. The Complete Canon Procedure (Reference)")
    story.append(body(
        "The novel's full procedure is preserved here as a reference. Every step is canon. "
        "Use this for Ceremony-mode rituals or when you want the full texture of the ritual."
    ))
    story.append(sp(2))

    story += subsection("1. Choose Target & Determine Timing")
    story.append(body(
        "Decide whether you are praying to an orthodox god, a hidden existence, or yourself. "
        "For orthodox gods, choose the date and time over which They rule — "
        "the Evernight Goddess at night, the Sun at dawn, the God of Knowledge and Wisdom on "
        "the 7th day of the week, etc. Wrong timing for the entity gives -1 to -2."
    ))
    story.append(body(
        "If invoking a deity or entity, you need Their <b>honorific name</b> or at minimum the "
        "domains They rule over. This determines the incantation structure."
    ))

    story += subsection("2. Prepare Ingredients")
    story.append(body(
        "Assemble materials from the entity's domain. Burning extracts, essential oils, and "
        "herbal powder serves <b>two purposes</b>: (1) it helps you attune your spirituality "
        "and enter Cogitation; (2) it pleases the entity being invoked, increasing the chance "
        "of a response. Each deity has characteristic ingredients — night vanilla and slumber "
        "flowers for the Evernight Goddess; sunflower and amber for the Sun; lavender and mint "
        "for the God of Knowledge and Wisdom."
    ))
    story.append(body(
        "Most ingredients are used to make <b>candles</b>, with 2 related ingredients per candle. "
        "A proper ritual needs 1–3 specially prepared candles."
    ))

    story += subsection("3. Sanctify the Space")
    story.append(body(
        "Use salt and/or pure water to cleanse items. Pronounce an incantation while cleansing — "
        "the penultimate sentence should name the deity (or use your own name as a wild Beyonder). "
        "The most commonly sanctified item is a pure metal dagger."
    ))

    story += subsection("4. Enter Cogitation")
    story.append(body(
        "Focus your mind, draw out your strength. Let your brain go somewhat blank, think of an "
        "object that does not exist in this world, and place all focus on it. Exchange the imagined "
        "object — use something you imagine completely out of thin air. This creates a "
        "<b>Mystic Experience</b>. Essential oils and herbs help the performer enter this state."
    ))

    story += subsection("5. Build the Wall of Spirituality")
    story.append(body(
        "Construct a sealed spiritual environment around the altar using supplementary items "
        "blessed by a Sanctification Ritual (Holy Night Powder, silver dagger, or salt). "
        "The wall protects the ritual space from outside interference and contains spiritual energy."
    ))

    story += subsection("6. Set Up the Altar")
    story.append(body(
        "The altar requires: a <b>pure metal dagger</b> (silver for Evernight/The Fool, brass for "
        "God of Knowledge and Wisdom, iron for darker entities), <b>candles</b> made from domain-"
        "appropriate ingredients, extracts, essential oils, herbal powders, and/or animal materials. "
        "The space must be <b>spiritually clean</b> — no miscellaneous items, no disturbances."
    ))

    story += subsection("7. Light the Candles")
    story.append(body(
        "Candles cannot be lit by ordinary means during a ritual. The correct method: extend your "
        "spirituality, rub it against the wick, and ignite it that way. Light candles "
        "<b>from left to right, beginning with 'god' followed by 'me'</b>. A standard '3-candle' "
        "arrangement has two candles on top (left = entity, right = entity's domain) and one below "
        "('me' — the performer)."
    ))

    story += subsection("8. Apply Oils & Herbs")
    story.append(body(
        "Drop essential oil and/or herbal powders onto candle flames, or light herbs and throw them "
        "into a cauldron. This pleases the entity and helps maintain Cogitation."
    ))

    story += subsection("9. Recite the Incantation")
    story.append(body(
        "The standard incantation has <b>four parts</b>, spoken in <b>Hermes</b>:"
    ))
    story.append(sp(2))
    story.append(bbullet(
        "<b>Part 1 — Invocation:</b> A prayer for someone's power. Replace 'someone' with the "
        "entity's honorific name, symbol, or domain. E.g.: \"The existence that rules the "
        "concealed path and controls fate...\""
    ))
    story.append(bbullet(
        "<b>Part 2 — Grace:</b> \"I pray for the God's loving grace.\""
    ))
    story.append(bbullet(
        "<b>Part 3 — Request:</b> What you pray for. Must be brief — finish in one sentence."
    ))
    story.append(bbullet(
        "<b>Part 4 — Empowerment:</b> Invoke a specific herb or ingredient to empower the request. "
        "E.g.: \"Sun Flower, a herb that belongs to the Sun. Please bestow your powers to my incantation.\""
    ))
    story.append(sp(2))
    story.append(body(
        "As long as the four-part structure is followed and the key meaning is expressed in Hermes, "
        "the rest can be left to the caster's creativity. For <b>Praying to Oneself</b>, "
        "replace the four-part structure with the three-line self-description (see Section IV — Personal Spirituality)."
    ))

    story += subsection("10. Deliver Sacrifice")
    story.append(body(
        "If the ritual requires a sacrifice, present it now. There is no real distinction between "
        "using a knife to sacrifice someone and using a chemical explosion — what matters is that "
        "the entity receives what was promised."
    ))

    story += subsection("11. Draw & Burn the Symbol")
    story.append(body(
        "Draw the symbol of what is desired on a piece of paper. After reciting the incantation, "
        "burn it to seal the intent."
    ))

    story += subsection("12. Complete & Close")
    story.append(body("After the paper has burned:"))
    story.append(bullet("Drip a drop of essential oil on each candle."))
    story.append(bullet("Thank the entity."))
    story.append(bullet("Extinguish candles <b>right to left</b>, beginning with 'me' and then 'god'."))
    story.append(bullet("Dispel the Wall of Spirituality."))
    story.append(sp(2))

    story += subsection("Suspending a Ritual")
    story.append(body(
        "High-level rituals can take hours to half a day. A suspension-style technique allows the "
        "caster to terminate at a defined point, finish other matters, then return and continue. "
        "The caster must understand the mysticism theory and grasp the corresponding technique — "
        "improvising a suspension without the correct knowledge risks failure or terrifying backlash. "
        "At the GM's discretion, suspending a ritual costs -2 to the effective skill."
    ))
    story.append(sp(4))

    story += subsection("Time & Complexity Reference")
    time_data = [
        ["Ritual Complexity", "Base Time", "Rushed", "Extended"],
        ["Light (divination, minor enhancement)", "15 min", "-3 to roll", "+1 to roll"],
        ["Moderate (curses, wards, communication)", "30 min", "-3 to roll", "+1 to roll"],
        ["Heavy (summoning, binding, fabrication)", "1 hour",  "-4 to roll", "+2 to roll"],
        ["Major (soul-touching, large-scale effects)", "3+ hours", "-5 to roll", "+2 to roll"],
    ]
    time_data[0] = [Paragraph(c, S['TableHeader']) for c in time_data[0]]
    for i in range(1, len(time_data)):
        time_data[i] = [Paragraph(c, S['TableCellCenter']) for c in time_data[i]]
    story.append(Table(time_data, colWidths=[2.1*inch, 0.9*inch, 1.3*inch, 2.0*inch], style=table_style()))
    story.append(sp(4))

    story += section("IV. Power Sources")
    story.append(body(
        "Every ritual requires a source of energy. The reason <b>which power source you choose "
        "matters</b> is simple: your personal Spirituality is limited. The bigger the effect, "
        "the more SPI you need — and you may not have enough.",
    ))
    story.append(body(
        "Before rolling, you must declare where the energy comes from. This choice cannot be "
        "changed once the ritual has begun."
    ))
    story.append(sp(2))
    story += subsection("A. Personal Spirituality (Praying to Oneself)")
    story.append(body(
        "You draw entirely on your own SPI. This is the safest method — no entity becomes aware "
        "of you — but it is limited by your personal reserves. The caster pays SPI equal to the "
        "ritual's complexity cost. SPI cannot be reduced below 0."
    ))
    spi_cost_data = [
        ["Complexity", "SPI Cost"],
        ["Simple effect, short duration, single target", "2-3 SPI"],
        ["Moderate effect, hours to days, single target", "4-6 SPI"],
        ["Powerful effect, long duration or wider scope", "7-10 SPI"],
        ["Major effect (territory-scale, permanent, or very powerful)", "11-15+ SPI"],
    ]
    spi_cost_data[0] = [Paragraph(c, S['TableHeader']) for c in spi_cost_data[0]]
    for i in range(1, len(spi_cost_data)):
        spi_cost_data[i] = [Paragraph(c, S['TableCell']) for c in spi_cost_data[i]]
    story.append(Table(spi_cost_data, colWidths=[3.5*inch, 2.8*inch], style=table_style()))
    story.append(body(
        "<b>Burning SPI to improve the roll:</b> This SPI cost is the <i>fuel</i> for the ritual. "
        "Separately, you may spend additional SPI after seeing your roll to boost it (+1 per SPI, no cap) "
        "using the universal burning mechanic (see Chapter 2, \"Burning FP & SPI to Modify Rolls\"). "
        "The two uses of SPI are cumulative."
    ))
    story.append(sp(3))

    story += subsection("B. HP Sacrifice")
    story.append(body(
        "The caster burns HP in addition to or instead of SPI. Every 2 HP spent counts as 1 SPI "
        "toward the ritual cost. This is visible — bleeding, pallor, shaking. Others <i>will</i> notice. "
        "HP sacrifice does not grant a bonus to the roll — it only provides spiritual fuel."
    ))

    story += subsection("C. Multiple Participants")
    story.append(body(
        "A ritual may include multiple trained participants who pool their SPI. The primary caster "
        "leads the ritual and makes the roll; each assistant contributes their SPI to the total "
        "cost. Assistants do not need to have Ritualistic Magic skill themselves, but they must be "
        "Beyonders who can consciously channel their spirituality. Each assistant beyond the first "
        "also grants +1 to the ritual roll (maximum +3)."
    ))
    story.append(body(
        "<b>Large-scale rituals</b> may require dozens or hundreds of participants. "
        "Some methods gather sacrifice on a massive scale — for example, sacrificing an entire "
        "city's worth of souls on a single altar. These are the tools of high-Sequence Beyonders "
        "like Witches casting terrifyingly potent Curses targeting whole groups."
    ))

    story += subsection("D. External Sacrifice")
    story.append(body(
        "Offerings of items, materials, or living beings can be sacrificed to an entity in exchange "
        "for power or favor. The offering is consumed or destroyed in the process. The GM determines "
        "the value of the sacrifice on a three-tier scale: <b>Ordinary</b> (common goods, small animals) "
        "grants +0 to the roll, <b>Meaningful</b> (valuable items, Beyonder materials) grants +2, "
        "and <b>Precious</b> (Sealed Artifacts, sentient sacrifices) grants +4. "
        "Living sacrifice adds +2 per sentient being offered. The sacrificed item is always lost "
        "regardless of success or failure."
    ))
    story.append(sp(2))

    story += subsection("E. Catalysts")
    story.append(body(
        "Certain rare materials can be burned or consumed during the ritual to boost its power. "
        "Catalysts do not replace SPI — they <b>enhance</b> it. A catalyst typically provides "
        "+0 to +2 to the ritual roll, at the GM's discretion based on quality and relevance."
    ))
    story.append(body("Common catalysts include: high-purity essential oils from an entity's domain, alchemically prepared reagents, Beyonder blood, and spiritually resonant gemstones."))
    story.append(sp(2))

    story += subsection("F. Invocation (Deity or Hidden Existence)")
    story.append(body(
        "The caster calls on an orthodox god, a hidden existence, or an evil god. This is the "
        "<b>most common method for low-Sequence Beyonders</b> — your personal authority and SPI "
        "are insufficient, so you borrow power from someone higher. The GM rolls secretly on "
        "the <b>Entity Response Table</b> first, then applies the entity's modifier to the Ritualistic Magic roll."
    ))
    story.append(body(
        "Orthodox deities shift the table result by <b>-2</b> when the request aligns with their "
        "domain and the caster is in good standing (e.g., a Nighthawk praying to the Evernight "
        "Goddess). Hidden existences and evil gods use the table unmodified — they are less "
        "reliable but may answer for lesser requests."
    ))
    entity_data = [
        ["GM Roll (3d6)", "Entity Response"],
        ["3-5",   "Full response. +5 to ritual roll. Entity may add its own conditions or expectations."],
        ["6-8",   "Partial response. +3 to ritual roll. Effect is noticeably weaker or slightly altered."],
        ["9-11",  "Minimal response. +1 to ritual roll. Result barely functions as intended."],
        ["12-14", "No response. Ritual draws only on caster's residual power (treat as 2 SPI personal)."],
        ["15-17", "Distracted or displeased. -2 to ritual roll. Something else may notice instead."],
        ["18",    "Active rejection. Ritual fails automatically. The entity is now aware of the caster."],
    ]
    entity_data[0] = [Paragraph(c, S['TableHeader']) for c in entity_data[0]]
    for i in range(1, len(entity_data)):
        entity_data[i] = [Paragraph(entity_data[i][j],
            S['TableCellCenter'] if j == 0 else S['TableCell']) for j in range(2)]
    story.append(Table(entity_data, colWidths=[1.3*inch, 5.0*inch], style=table_style()))
    story.append(sp(4))

    story += section("V. Effect Categories")
    story.append(body(
        "There is no fixed spell list. Every ritual falls into one of <b>three weights</b> that "
        "determine its base difficulty and SPI cost. The full list of example categories is provided "
        "as a reference — the GM uses common sense to classify any novel request."
    ))
    story.append(sp(2))

    weight_data = [
        ["Weight", "Base Mod", "Typical SPI", "Example Categories"],
        ["Light", "+0", "2 SPI", "Divination (1–2 SPI via Divination Arts, see Ch 6.5), minor communication, simple warding, basic prayer"],
        ["Moderate", "-2", "4–6 SPI", "Enhancement, curse, cleansing, marking, fabrication, concealment, oath-sealing, protection/warding"],
        ["Heavy", "-4", "8+ SPI", "Summoning, binding, unraveling, affliction, transference, soul-anchoring"],
    ]
    weight_data[0] = [Paragraph(c, S['TableHeader']) for c in weight_data[0]]
    for i in range(1, len(weight_data)):
        weight_data[i] = [Paragraph(c, S['TableCellCenter']) for c in weight_data[i]]
    story.append(Table(weight_data, colWidths=[1.0*inch, 0.8*inch, 0.8*inch, 4.0*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Full category reference (all 16 types with their weights):</b>"
    ))
    story.append(sp(1))
    cat_data = [
        ["Weight", "Categories"],
        ["Light (+0)", "Divination (1–2 SPI via Divination Arts), Communication (minor), Warding (simple)"],
        ["Moderate (-2)", "Enhancement, Curse, Cleansing, Marking, Fabrication, Concealment, Oath-Sealing, Protection/Warding"],
        ["Heavy (-4)", "Summoning, Binding, Unraveling, Affliction, Transference, Soul-Anchoring"],
    ]
    cat_data[0] = [Paragraph(c, S['TableHeader']) for c in cat_data[0]]
    for i in range(1, len(cat_data)):
        cat_data[i] = [Paragraph(c, S['TableCell']) for c in cat_data[i]]
    story.append(Table(cat_data, colWidths=[1.2*inch, 5.1*inch], style=table_style()))
    story.append(sp(4))

    story += section("VI. Failure & Consequences")
    story.append(body("Failure always costs. You spent the time, materials, and SPI or HP. The question is only how badly it went wrong — and what noticed you doing it."))
    story.append(sp(2))
    fail_data = [
        ["Result", "Consequence"],

        ["Failure by 1-4",              "No effect. Faint spiritual disturbance — the GM may note it."],
        ["Failure by 5-9",              "Partial, wrong activation. GM chooses a distorted outcome loosely related to intent."],
        ["Failure by 10+",              "Severe misfire. Roll on Critical Failure Table with -2 to the result roll."],
        ["Critical Failure (roll 17-18)","Roll on Critical Failure Table immediately."],
    ]
    fail_data[0] = [Paragraph(c, S['TableHeader']) for c in fail_data[0]]
    for i in range(1, len(fail_data)):
        fail_data[i] = [Paragraph(c, S['TableCell']) for c in fail_data[i]]
    story.append(Table(fail_data, colWidths=[2.0*inch, 4.3*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Critical Failure Table (3d6)")
    crit_data = [
        ["Roll", "Outcome"],
        ["3-4",   "Backlash. Take damage equal to the ritual's SPI cost as injury bypassing DR. Stunned 1d minutes."],
        ["5-6",   "Wrong Attention. Something external noticed the ritual. The GM decides what, and when it acts."],
        ["7-8",   "Distortion. The effect activates in a twisted or reversed form. GM defines how."],
        ["9-10",  "Spiritual Drain. Lose double the SPI cost. Lose 1d SPI from maximum until a full rest. Stunned 1d minutes."],
        ["11-12", "Wrong Arrival. For summoning/communication: something else responds. Otherwise: an unintended entity becomes aware of you."],
         ["13-14", "Corruption. Gain 1 CoR. The ritual still fails."],
         ["15-16", "Shatter. All ward or protection effects on the caster are dispelled. Gain 1 CoR."],
         ["17",    "Soul Exposure. Caster's spiritual self is partially exposed to the entity invoked. Gain 2 CoR. Nightmares for 1d weeks."],
        ["18",    "Catastrophe. The GM invents something terrible. It will be remembered. Possible entity arrival."],
    ]
    crit_data[0] = [Paragraph(c, S['TableHeader']) for c in crit_data[0]]
    for i in range(1, len(crit_data)):
        crit_data[i] = [Paragraph(crit_data[i][j],
            S['TableCellCenter'] if j == 0 else S['TableCell']) for j in range(2)]
    story.append(Table(crit_data, colWidths=[0.6*inch, 5.7*inch], style=table_style()))
    story.append(sp(3))

    story += subsection("Corruption from Ritual Work")
    story.append(body(
        "CoR from ritual failures and dangerous work stack with the main CoR system. "
        "Refer to Chapter 6 for full CoR rules. Additional ritual-specific thresholds:"
    ))
    rcp_data = [
        ["CoR Total", "Additional Ritual Effect"],
        ["3 CoR",  "All ritual rolls at -1 from spiritual instability."],
        ["5 CoR",  "Gain a -5 point mental disadvantage (GM choice, thematically linked to the source)."],
        ["8 CoR",  "Gain a second -5 point mental disadvantage. Passively attracts unwanted spiritual attention."],
        ["10 CoR", "Character is fundamentally altered. May need to retire, become an NPC, or pursue a major story arc."],
    ]
    rcp_data[0] = [Paragraph(c, S['TableHeader']) for c in rcp_data[0]]
    for i in range(1, len(rcp_data)):
        rcp_data[i] = [Paragraph(rcp_data[i][j],
            S['TableCellCenter'] if j == 0 else S['TableCell']) for j in range(2)]
    story.append(Table(rcp_data, colWidths=[0.9*inch, 5.4*inch], style=table_style()))
    story.append(body("Reducing ritual CoR: extended rest away from ritual work removes 1 CoR after a full month of abstinence. Cleansing rituals can also remove CoR on a successful roll."))
    story.append(sp(4))

    story += section("VII. Sequence & Rituals")
    story.append(body(
        "Sequence advancement helps rituals indirectly through growing resources and unlocked abilities, "
        "rather than providing any direct bonus to ritual success."
    ))
    story.append(sp(2))
    story.append(body("Higher Sequence helps rituals in these ways:"))
    seq_effects = [
        ["Factor", "Effect on Rituals"],
        ["SPI pool grows", "You gain more raw spirituality as you advance. Typical maximum SPI: Seq 9 = 3-6, Seq 8 = 5-9, Seq 7 = 8-14. This lets you fuel bigger effects."],
        ["Pathway abilities unlock", "Some Sequences grant specific ritual perks (e.g., Mystery Pryer's Quick Rituals at Seq 9, or the ability to perform certain rituals without full preparation). See your pathway entry."],
        ["Self-powered results strengthen", "The outcome of Praying to Oneself scales with personal power — a higher-Sequence Beyonder produces a stronger result from the same roll. This is Daly's principle: a weak result for the weak, a strong result for the strong."],
    ]
    seq_effects[0] = [Paragraph(c, S['TableHeader']) for c in seq_effects[0]]
    for i in range(1, len(seq_effects)):
        seq_effects[i] = [Paragraph(c, S['TableCell']) for c in seq_effects[i]]
    story.append(Table(seq_effects, colWidths=[1.8*inch, 4.5*inch], style=table_style()))
    story.append(sp(3))

    story.append(body(
        "<b>Example:</b> A Sequence 9 Mystery Pryer invoking the Hidden Sage for a divination: "
        "Ritualistic Magic 14 + invocation roll = effective skill 14-19 (depending on entity response). "
        "A Sequence 7 Hunter attempting the same ritual: Ritualistic Magic 14 + invocation roll = "
        "effective skill 14-19 as well — Sequence does not inherently favour either. The difference "
        "is in the tools available: the Mystery Pryer has a naturally larger SPI pool and pathway "
        "abilities that support divination, while the Hunter must rely on preparation and invocation."
    ))

    story += section("VIII. Sample Rituals")
    story.append(body(
        "The following worked examples show how the system operates in play. Each assumes a caster "
        "with Ritualistic Magic-14. All rolls are against the effective skill after modifiers."
    ))
    story.append(sp(3))

    def ritual_block(title, category, base_diff, time_req, intent, setup, modifiers, eff_skill, spi_cost, on_success, on_fail, on_crit):
        block = []
        block.append(Paragraph(f"<b>{title}</b>", S['SubSection']))
        meta_data = [
            ["Category", "Base Difficulty", "Time"],
            [category, base_diff, time_req],
        ]
        meta_data[0] = [Paragraph(c, S['TableHeader']) for c in meta_data[0]]
        meta_data[1] = [Paragraph(c, S['TableCellCenter']) for c in meta_data[1]]
        block.append(Table(meta_data, colWidths=[2.0*inch, 1.8*inch, 2.5*inch], style=table_style()))
        block.append(sp(2))
        block.append(body(f"<b>Intent:</b> {intent}"))
        block.append(body(f"<b>Setup:</b> {setup}"))
        block.append(sp(2))
        mod_rows = [["Modifier Source", "Value"]] + modifiers
        mod_rows[0] = [Paragraph(c, S['TableHeader']) for c in mod_rows[0]]
        for i in range(1, len(mod_rows)):
            mod_rows[i] = [Paragraph(mod_rows[i][j],
                S['TableCellCenter'] if j == 1 else S['TableCell']) for j in range(2)]
        block.append(Table(mod_rows, colWidths=[3.8*inch, 2.5*inch], style=table_style()))
        block.append(sp(2))
        block.append(body(f"<b>Effective Skill:</b> {eff_skill}"))
        block.append(body(f"<b>SPI Cost:</b> {spi_cost}"))
        block.append(body(f"<b>On Success:</b> {on_success}"))
        block.append(body(f"<b>On Failure:</b> {on_fail}"))
        block.append(body(f"<b>On Critical Failure:</b> {on_crit}"))
        block.append(thin_rule())
        return block

    story += ritual_block(
        "Ritual 1: Luck Enhancement",
        "Enhancement", "-2", "30 minutes",
        "Improve one person's luck for one week, giving them +1 to all social skill rolls.",
        "A quiet dedicated room with candles. The caster has a lock of the target's hair and knows their full name.",
        [
            ["Enhancement base difficulty", "-2"],
            ["Proper dedicated space", "+0"],
            ["True name + intimate possession (hair)", "+4"],
            ["Net modifier", "+2"],
        ],
        "14 + 2 = 16",
        "4 SPI (moderate duration, single target)",
        "The target gains +1 to all social skill rolls for one week. Success by 5+ extends to two weeks or raises the bonus to +2 for one category.",
        "Nothing happens. SPI is spent.",
        "The luck inverts. The target suffers -1 to social rolls for the same duration and will not know why."
    )

    story += ritual_block(
        "Ritual 2: Divination — Seeking a Hidden Location",
        "Divination", "+0", "45 minutes (extended)",
        "Discover the current location of a specific missing person.",
        "A bowl of still water as a scrying focus. The caster has the target's personal journal and writes their full name in their own blood on a slip of paper placed beneath the bowl.",
        [
            ["Divination base difficulty", "+0"],
            ["Proper dedicated space", "+0"],
            ["True name + intimate possession (journal + blood)", "+4"],
            ["Extended ritual (45 min vs 30 min base)", "+1"],
            ["Net modifier", "+5"],
        ],
        "14 + 5 = 19",
        "3 SPI (simple category, single fact)",
        "GM reveals a general location: a city district, near water, underground in a stone room. Success by 5+ gives a recognizable landmark or street name.",
        "A vague symbolic image — possibly misleading, possibly simply incomplete.",
        "The missing person — or something near them — becomes aware that someone is looking for them."
    )

    story += ritual_block(
        "Ritual 3: Summoning a Minor Spirit",
        "Summoning", "-4", "1 hour",
        "Call a low-level local spirit to the ritual space and ask it one question about local events.",
        "A long-used sanctified ritual study. Appropriate offerings: incense, small food items, objects tied to the location's history. Two trained assistants help. The caster invokes rather than using personal SPI.",
        [
            ["Summoning base difficulty", "-4"],
            ["Long-used sanctified space", "+2"],
            ["Appropriate offerings (materials)", "+2"],
            ["Two trained assistants", "+2"],
            ["No true name (category name only)", "+0"],
            ["Net modifier", "+2"],
        ],
        "14 + 2 = 16. GM then rolls secretly on the Entity Response Table.",
        "7 SPI, split among caster and assistants (3/2/2). Power source: Invocation.",
        "A minor spirit manifests. It is not bound. It may answer the question, demand a small offering, answer obliquely, or be hostile — it cannot be commanded.",
        "Nothing comes. The space may feel disturbed for days.",
        "Something answers that was not invited. The GM decides what it is and what it wants."
    )

    story += ritual_block(
        "Ritual 4: Curse of the Unlucky Hand",
        "Curse", "-3", "30 minutes",
        "Inflict persistent bad luck on a merchant rival — causing their business dealings to go subtly wrong for one month.",
        "The caster has a coin the target personally handled and their full name. The ritual uses the caster's own blood (HP sacrifice) to supplement SPI costs. A proper dedicated space.",
        [
            ["Curse base difficulty", "-3"],
            ["Proper dedicated space", "+0"],
            ["True name known", "+3"],
            ["One month duration (longer than one week)", "-1"],
            ["Net modifier", "-1"],
        ],
        "14 - 1 = 13",
        "7 SPI (or 5 SPI + 4 HP sacrifice)",
        "The target suffers -1 to all Commerce, Fast-Talk, and Merchant skill rolls for one month.",
        "The curse does not take hold. The coin grows briefly warm.",
        "Roll on the Critical Failure Table. The target may also feel the attempt — a cold chill, sudden anxiety."
    )

    story += ritual_block(
        "Ritual 5: Oath-Sealing Between Two Parties",
        "Oath-Sealing", "-3", "30 minutes",
        "Bind two willing individuals to a mutual agreement: neither will reveal the location of a safehouse. Consequence of breaking: persistent insomnia (-2 to IQ-based rolls) until amends are made.",
        "Both parties present and verbally agreeing. A small cut from each hand dripped onto a shared paper on which the oath terms are written. A proper ritual space.",
        [
            ["Oath-Sealing base difficulty", "-3"],
            ["Both parties willing", "+0"],
            ["Proper dedicated space", "+0"],
            ["True names of both parties (+ intimate link via blood)", "+4"],
            ["Net modifier", "+1"],
        ],
        "14 + 1 = 15",
        "5 SPI (paid by the officiating caster)",
        "The oath is sealed. Both parties feel a faint pressure. If either breaks it, the insomnia effect activates within 24 hours. Those with Thaumatology can identify a bound individual with a successful skill roll.",
        "The ritual fails silently. Neither party knows. The oath has no spiritual weight.",
        "The oath seals incorrectly — consequences may activate immediately on one random party, or the terms are subtly inverted."
    )

    story += ritual_block(
        "Ritual 6: Fabrication — Warding Talisman",
        "Fabrication", "-3", "3 hours (extended)",
        "Create a small talisman (carved wooden disc) that, when activated, grants DR 2 against one incoming spiritual effect. Single use.",
        "A proper dedicated space. Wood carved from a tree that stood over a gravesite (symbolically appropriate for warding). Protective symbols etched. Triple the base time for additional precision.",
        [
            ["Fabrication base difficulty", "-3"],
            ["Proper dedicated space", "+0"],
            ["Symbolically resonant materials (grave-tree wood)", "+2"],
            ["Extended ritual (triple time)", "+2"],
            ["Single-use object (not permanent)", "+1"],
            ["Net modifier", "+2"],
        ],
        "14 + 2 = 16",
        "6 SPI",
        "The talisman is created. The bearer activates it as a free action when targeted by a spiritual effect, applying DR 2 against it. Success by 5+ grants 2 uses instead of 1.",
        "The talisman is inert. SPI spent. Materials are not reusable.",
        "The talisman is created but inverted — it functions as a beacon for spiritual attention rather than a ward."
    )

    story += ritual_block(
        "Ritual 7: Binding a Spirit to an Object",
        "Binding", "-4", "3 hours (extended)",
        "Bind a specific minor spirit (previously summoned) to a carved stone vessel. Duration: indefinite.",
        "Long-used sanctified space. The spirit's category name and a partial true name. Materials: the carved vessel, silver wire, protective symbols. Two trained assistants. Triple time for safety.",
        [
            ["Binding base difficulty", "-4"],
            ["Long-used sanctified space", "+2"],
            ["Partial true name", "+2"],
            ["Appropriate materials (silver, carved vessel)", "+2"],
            ["Two trained assistants", "+2"],
            ["Extended ritual (triple time)", "+2"],
            ["Indefinite duration", "-3"],
            ["Net modifier", "+3"],
        ],
        "14 + 3 = 17",
        "9 SPI split between caster and assistants (4/3/2)",
        "The spirit is bound. It cannot leave the vessel. It retains its intelligence and will, and it is unhappy. It may communicate with visitors or wait for the vessel to be destroyed.",
        "The spirit is not bound but is present and now irritated. It may leave, attack, or demand compensation.",
        "The binding attempts to trap the caster's own spiritual self in the vessel. Roll Will at -4 to resist. The spirit escapes."
    )

    story.append(sp(4))

    story += subsection("Ritual 8: Standard Sacrificial Ritual")
    story.append(body(
        "The formalized procedure to sacrifice items, materials, or living beings to an entity "
        "in exchange for power or favor. Uses the standard Full Ritual procedure (Section III)."
    ))
    story.append(bullet("<b>Base Difficulty:</b> -2 (minor offering) to -6 (living sacrifice)"))
    story.append(bullet("<b>Setup:</b> Altar with the offering prominently placed. Incantation must name the entity and state the requested exchange."))
    story.append(bullet("<b>Key Modifier:</b> Offering quality (GM discretion): Trivial +0, Meaningful +2, Precious +4. Living sacrifice: +2 per sentient being."))
    story.append(bullet("<b>SPI Cost:</b> 2–4 SPI (the offering itself provides most of the power)"))
    story.append(bullet("<b>On Success:</b> The entity accepts. The offered item is consumed/destroyed. The caster's request is granted or noted."))
    story.append(bullet("<b>On Failure:</b> The offering is consumed but the entity does not respond. SPI is lost."))
    story.append(bullet("<b>Critical Failure:</b> The entity is offended. Roll on Critical Failure Table with +2 to the result."))
    story.append(sp(3))

    story += subsection("Ritual 9: Dualistic Ritual")
    story.append(body(
        "A specialized ritual requiring a male and female participant working in spiritual union. "
        "Used for certain high-risk advancements, blessings, or spiritual communions. Both participants "
        "must be willing and spiritually attuned to each other."
    ))
    story.append(bullet("<b>Base Difficulty:</b> -4"))
    story.append(bullet("<b>Setup:</b> Both participants present at a neutral altar. Matching sets of candles (one per participant). "
                        "Incantation uses first-person plural — the ritual treats both as a single spiritual entity."))
    story.append(bullet("<b>Key Modifier:</b> Both participants share a bond (trust/romance/same pathway) +2. "
                         "Good spiritual attunement +1. Poor attunement -1 to -3."))
    story.append(bullet("<b>SPI Cost:</b> 4–8 SPI, split evenly between participants"))
    story.append(bullet("<b>On Success:</b> The union is recognized by the spirit world. The intended effect manifests as desired."))
    story.append(bullet("<b>On Failure:</b> Spiritual dissonance. Both participants suffer -2 to all spiritual rolls for 1d days."))
    story.append(bullet("<b>Critical Failure:</b> The union inverts — one participant is dominated by the other's spiritual imprint for 1d weeks "
                        "(GM determines consequences)."))
    story.append(sp(3))

    story += subsection("Ritual 10: Bestowment Ritual (Charm Creation)")
    story.append(body(
        "By carving an object with specific symbols and words in a mystical language and praying to an entity "
        "(or to oneself if at Sequence 7 or above) you are able to infuse these objects with the powers from "
        "the domains of the supplier and gain specific one-time use abilities in the case of consumables and "
        "mystical items that have a finite lifespan. The object must either be a plate or bullets of an "
        "appropriate material to the entity's domain, or an appropriate object to the ability requested "
        "(up to the GM); however, in the second case gain an additional -3 disadvantage to the final "
        "Ritualistic Magic roll due to consumables being 'easier'."
    ))
    story.append(body(
        "<b>The steps are as follows:</b>"
    ))
    story.append(bullet(
        "<b>Step 1:</b> Gather all the required tools (jewellery chisels, files) and primary object."
    ))
    story.append(bullet(
        "<b>Step 2:</b> Prepare the plate, bullets or object by rolling Thaumatology. On success, "
        "manage to inscribe the proper symbols, patterns and words upon it. On failure: the object "
        "is turned into scrap that needs to be melted down."
    ))
    story.append(bullet(
        "<b>Step 3:</b> Request a specific ability within the domain of the entity you are praying to "
        "(or if praying to oneself, request abilities that you possess). Depending on the powers "
        "requested, the GM may impose additional disadvantages depending on how much you are asking for. "
        "Roll Ritualistic Magic (IQ/Very Hard) with all applicable modifiers as normal. Depending on "
        "the degree of success, gain an appropriately levelled charm or mystical item. On failure the "
        "object is destroyed. On critical failure, gain additional corruption (up to the GM)."
    ))
    story.append(body(
        "<b>Important:</b> When creating charms or mystical items with abilities equivalent to that of "
        "Sequence 4 or higher, you need to use demigod-level materials in order for their creation to be possible."
    ))
    story.append(body(
        "<b>Pathways and their respective common materials for consumables:</b>"
    ))
    story.append(body(
        "<font color='#C0392B'><b>Pathway</b></font> / <b>Material</b><br/>"
        "<font color='#C0392B'>Fool</font> / Silver, Paper<br/>"
        "<font color='#C0392B'>Error</font> / Silver, Mercury<br/>"
        "<font color='#C0392B'>Door</font> / Silver, Gemstones<br/>"
        "<font color='#C0392B'>Visionary</font> / Gold, Silver<br/>"
        "<font color='#C0392B'>Sun</font> / Gold<br/>"
        "<font color='#C0392B'>White Tower</font> / Bronze<br/>"
        "<font color='#C0392B'>Hanged Man</font> / Lead, Flesh<br/>"
        "<font color='#C0392B'>Darkness</font> / Silver<br/>"
        "<font color='#C0392B'>Death</font> / Copper, Silver, Bone<br/>"
        "<font color='#C0392B'>Twilight Giant</font> / Bronze, Silver, Steel<br/>"
        "<font color='#C0392B'>Demoness</font> / Silver, Bone<br/>"
        "<font color='#C0392B'>Red Priest</font> / Iron<br/>"
        "<font color='#C0392B'>Hermit</font> / Gold, Bronze<br/>"
        "<font color='#C0392B'>Paragon</font> / Copper, Bronze, Brass<br/>"
        "<font color='#C0392B'>Wheel of Fortune</font> / Silver, Mercury<br/>"
        "<font color='#C0392B'>Mother</font> / Tin, Wood<br/>"
        "<font color='#C0392B'>Moon</font> / Silver<br/>"
        "<font color='#C0392B'>Abyss</font> / Iron, Lead<br/>"
        "<font color='#C0392B'>Chained</font> / Iron<br/>"
        "<font color='#C0392B'>Black Emperor</font> / Gold, Iron<br/>"
        "<font color='#C0392B'>Justiciar</font> / Gold, Brass"
    ))
    story.append(body(
        "(For all pathways: materials taken and extracted from beings that possess main ingredients to the "
        "potions of that pathway are amazing additives and will grant an appropriate bonus to the "
        "Thaumatology roll (up to the GM). In the case of high-sequence consumables and mystical items, "
        "appropriate high-sequence materials are necessary.)"
    ))
    story.append(sp(4))

    story.append(PageBreak())

    # ── Chapter 7.5: Summoning Spiritual Creatures ──
    story += chapter("Chapter 7.5: Summoning Spiritual Creatures")
    story.append(sp(2))

    story.append(body(
        "Within the Physical World, Spirit World, Shadow World, Sea of Eternal Unconscious, "
        "Mirror World, and other realms of reality, a variety of different spiritual creatures "
        "exist. By finding or creating a specific three-line incantation and performing a ritual, "
        "one may summon these mystical beings and ask them for favours or create mystical contracts "
        "with them."
    ))
    story.append(sp(3))

    story += subsection("Creating an Incantation")
    story.append(body(
        "In order to summon a mystical being one needs to discover or create a three-line "
        "incantation that points to a specific spiritual creature. The first line should be the "
        "resident realm of the creature (The Unfounded, the Spirit Realm, the Darkness, etc.). "
        "The second and third lines should be accurate descriptors of the creature."
    ))
    story.append(sp(3))

    story += subsection("Summoning Methods")
    story.append(body(
        "There are two ways to summon a spiritual creature: one is by using one's own spirituality "
        "and authority, and the other is by supplicating a higher being for their assistance. "
        "Both methods use a similar principle, but the second requires a complex religious ritual."
    ))
    story.append(sp(3))

    story += subsection("The Summoning Ritual")
    story.append(body(
        "After acquiring or creating the incantation, one needs to set up a basic or complex altar "
        "(depending on whether they will be using the authority of a great being). Then, in an "
        "ancient mystical language (Ancient Hermes, Jotun Dragonese, Elvish), declare: \"I\". Then "
        "in a regular mystical language (Hermes, Ancient Feysac), declare: \"I summon in my name\" "
        "or \"I summon in the name of [insert supplicator's full title or honorific name]\". "
        "Continue and pronounce the summoning incantation."
    ))
    story.append(body(
        "Roll Ritualistic Magic with all applicable modifiers. The GM must roll an additional 3d "
        "for the creature's response — the better the response, the higher the chance they will "
        "peacefully arrive; the worse the response, the lesser the chance that they will arrive, "
        "or they will arrive and attempt to harm the summoner."
    ))
    story.append(sp(3))

    story += subsection("Communication & Requests")
    story.append(body(
        "After successfully summoning the spiritual creature, the summoner may communicate with "
        "the creature in a regular mystical language, or in a regular living language if it is "
        "capable of communicating in it. Simply by summoning the creature, the summoner has already "
        "'paid' spirituality to it — as such, the summoner may request the spiritual creature to "
        "perform a task for them."
    ))
    story.append(sp(3))

    story += subsection("Mystical Contracts")
    story.append(body(
        "If the summoner desires to form a contract, they may do so in one of three ways: "
        "(a) have a greater being oversee the contract's formation, (b) have a being within the "
        "domain of death or the underworld oversee it instead, or (c) have an ability or authority "
        "to create contracts (Certifiers, Spirit Mediums, Spirit Warlocks, Mystery Pryers, "
        "Contractees, Shadow Merchants, etc.). Upon penning a contract in a mystical language, "
        "if both parties consent, it becomes binding and both parties will follow the contract. "
        "Even without using one of the three methods, it is still possible to pen a contract — "
        "however, the possibility that the mystical creature will break it is not off the table."
    ))
    story.append(sp(3))

    story += subsection("Creature Format")
    story.append(body(
        "The abilities, appearance, and other properties of the creature are determined by the GM. "
        "The following format should be used:"
    ))
    story.append(bullet("<b>Name:</b>"))
    story.append(bullet("<b>Appearance:</b>"))
    story.append(bullet("<b>Other Properties:</b>"))
    story.append(bullet("<b>Contract Cost:</b>"))
    story.append(bullet("<b>Attributes:</b>"))
    story.append(bullet("<b>Ability(s) or Function:</b>"))
    story.append(sp(3))

    story += subsection("Example Creature: Bookworm")
    story.append(bullet("<b>Name:</b> Bookworm"))
    story.append(bullet("<b>Appearance:</b> An illusory pale blue worm that has letters from "
                        "different languages coursing under its skin. It has a head with a single "
                        "human-like eye and is around 5 cm in length."))
    story.append(bullet("<b>Other Properties:</b> Capable of speaking in Loenese and Intisian. "
                        "It sounds like a high-pitched but wisdom-filled old man's voice."))
    story.append(bullet("<b>Contract Cost:</b> A piece of rare information that the Bookworm "
                        "does not know yet."))
    story.append(bullet("<b>Attributes:</b> 4 HP"))
    story.append(bullet("<b>Ability — Book Reading (1 SPI):</b> The Bookworm can read through "
                        "a novel-length book in only a couple of minutes."))
    story.append(bullet("<b>Ability — Knowledge Transmission (1 SPI):</b> By the contractor's "
                        "request, the Bookworm will transmit the knowledge from the most recently "
                        "read book by burrowing into the contractor's head. The contractor may "
                        "request specific information from the book, e.g. \"Only provide the pie "
                        "recipes from this cookbook\"."))
    story.append(sp(4))

    story.append(PageBreak())

    story += chapter("Chapter 7.6: Spirit Vision — A Complete Guide")
    story.append(sp(2))
    story.append(body(
        "The spirit sees what the eye cannot. Through Spirit Vision, Beyonders perceive the auras "
        "of life — colors of emotion, threads of health, darkness of corruption. "
        "Activate by expending 1 SPI."
    ))
    story.append(sp(3))

    story += section("A. Astral Projection Colors")
    story.append(body(
        "The Astral Projection lies beneath the Ether Body and reveals emotional state:"
    ))
    
    astral_data = [
        ["Color", "Meaning"],
        ["Red", "Passion, excitement, anger"],
        ["Orange", "Warmth, satisfaction"],
        ["Yellow", "Happiness, extroversion"],
        ["Green", "Calm, peace, balance"],
        ["Blue", "Coldness, stillness, logic"],
        ["White", "Brightness, ambition"],
        ["Dark", "Worry, sorrow, fear"],
        ["Purple", "Spirituality, madness"],
    ]
    astral_data[0] = [Paragraph(c, S['TableHeader']) for c in astral_data[0]]
    for i in range(1, len(astral_data)):
        astral_data[i] = [Paragraph(c, S['TableCell']) for c in astral_data[i]]
    story.append(Table(astral_data, colWidths=[1.0*inch, 5.3*inch], style=table_style()))

    story.append(sp(2))

    story += section("B. Ether Body Colors")
    story.append(body(
        "The Ether Body is the outermost layer — shows physical health:"
    ))
    
    ether_data = [
        ["Body Region", "Color"],
        ["Limbs active", "Red"],
        ["Brain", "Purple"],
        ["Waste systems", "Orange"],
        ["Digestion", "Yellow"],
        ["Heart/reg", "Green"],
        ["Nerves", "Blue"],
        ["Healthy", "White"],
        ["Ill", "Dark/Thin"],
    ]
    ether_data[0] = [Paragraph(c, S['TableHeader']) for c in ether_data[0]]
    for i in range(1, len(ether_data)):
        ether_data[i] = [Paragraph(c, S['TableCell']) for c in ether_data[i]]
    story.append(Table(ether_data, colWidths=[1.3*inch, 3.9*inch], style=table_style()))

    story.append(sp(2))
    story.append(body("A balanced body appears <b>white</b>. Darkness or thinning indicates illness."))

    story.append(sp(2))
    story += section("C. Pathway Differences")
    story.append(body(
        "Not all Beyonders perceive equally. Pathway and Sequence determine what can be seen:"
    ))
    
    path_data = [
        ["Pathway (Seq 9)", "Sequence", "Spirit Vision Ability"],
        ["Seer (Fool)", "9", "Standard: Ether Body + Astral"],
        ["Mystery Pryer (Hermit)", "9", "<b><font color='#C0392B'>Eyes of Mystery Prying:</font></b> See truth, reality, Astral Body"],
        ["Spectator (Visionary)", "9", "Enhanced: Read emotions & thoughts"],
        ["Sleepless (Darkness)", "9", "Limited: Spiritual entities only (no Ether Body analysis)"],
        ["Corpse Collector (Death)", "9", "Passive: See spirits & undead without activation"],
    ]
    path_data[0] = [Paragraph(c, S['TableHeader']) for c in path_data[0]]
    for i in range(1, len(path_data)):
        path_data[i] = [Paragraph(c, S['TableCell']) for c in path_data[i]]
    story.append(Table(path_data, colWidths=[1.2*inch, 0.9*inch, 4.2*inch], style=table_style()))

    story.append(sp(2))
    story += section("D. Reading Spirit Vision")
    story.append(body(
        "<b>Using <font color='#C0392B'>Spirit Vision:</font></b> Activate by expending 1 SPI (1 SPI per minute to maintain). "
        "Make a Perception-based roll to interpret correctly."
    ))
    
    roll_data = [
        ["Roll", "Effect"],
        ["Success", "Identify primary emotion or general health"],
        ["Success by 3+", "Detect specific feelings"],
        ["Success by 5+", "Sense recent events"],
        ["Critical", "Full reading"],
        ["Failure", "Incorrect reading"],
    ]
    roll_data[0] = [Paragraph(c, S['TableHeader']) for c in roll_data[0]]
    for i in range(1, len(roll_data)):
        roll_data[i] = [Paragraph(c, S['TableCell']) for c in roll_data[i]]
    story.append(Table(roll_data, colWidths=[1.3*inch, 4.9*inch], style=table_style()))

    story.append(sp(2))
    story.append(body(
        "<b>Special Forms:</b> Ether Body Awareness (Seer), "
        "<b><font color='#C0392B'>Eyes of Mystery Prying</font></b> (Mystery Pryer), "
        "Enhanced Emotions (Spectator), "
        "Limited Form (Sleepless), "
        "Passive Spirit Vision (Corpse Collector)."
    ))
    

    story.append(PageBreak())

    story += chapter("Chapter 8: Equipment & Starting Wealth")

    story += section("Loen Pound Currency Conversion")
    story.append(body(
        "The Loen Kingdom uses a standard three-tier currency system derived from Victorian British "
        "currency. All prices in this book are given in this system unless otherwise noted."
    ))
    story.append(sp(2))
    currency_data = [
        ["Unit", "Abbreviation", "Subdivision", "Notes"],
        ["Gold Pound", "£ (or £1)", "= 20 Soli (s)", "Highest common denomination; £1, £5, and £10 notes exist"],
        ["Soli (Shilling)", "s (or 1s)", "= 12 Pence (d)", "Silver coin; 1s and 5s coins are most common"],
        ["Penny", "d (or 1d)", "= 4 Farthings (¼d each)", "Copper coin; also ½d and ¼d (farthing) coins"],
    ]
    currency_data[0] = [Paragraph(c, S['TableHeader']) for c in currency_data[0]]
    for i in range(1, len(currency_data)):
        currency_data[i] = [Paragraph(c, S['TableCell']) for c in currency_data[i]]
    story.append(Table(currency_data, colWidths=[1.2*inch, 1.2*inch, 1.5*inch, 3.4*inch], style=table_style()))
    story.append(sp(1))
    story.append(body(
        "<i>Conversion examples: £1 = 20s = 240d. A typical newspaper costs 1d, a pair of shoes 9–10s, "
        "a modest single-room weekly rent 3s10d–4s3d. See the Quick Reference Tables appendix for the currency chart.</i>"
    ))
    story.append(sp(3))

    story += subsection("Feysac Empire Currency")
    story.append(body(
        "The Feysac Empire uses a decimal system (<b>base-10</b>) — significantly simpler than Loen's "
        "three-tier coinage. All prices in this book are given in Loen pounds unless noted, but the "
        "following exchange rate and conversion table can be used for campaigns set in or dealing with "
        "the Feysac Empire."
    ))
    story.append(sp(2))
    feysac_currency = [
        ["Unit", "Abbreviation", "Subdivision", "Notes"],
        ["Gold Hoorn", "gh", "= 10 Feysilver (fs)", "Highest common denomination; minted as coins"],
        ["Feysilver", "fs", "= 10 Kopek (k)", "Silver coin; the everyday workhorse"],
        ["Kopek", "k", "—", "Copper or bronze coin; smallest common unit"],
    ]
    feysac_currency[0] = [Paragraph(c, S['TableHeader']) for c in feysac_currency[0]]
    for i in range(1, len(feysac_currency)):
        feysac_currency[i] = [Paragraph(c, S['TableCell']) for c in feysac_currency[i]]
    story.append(Table(feysac_currency, colWidths=[1.2*inch, 1.2*inch, 1.5*inch, 3.4*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Exchange Rate:</b> 1 Loen Gold Pound = 5.5 Gold Hoorn. "
        "Or inversely, 1 Gold Hoorn ~ 3.6 Soli (roughly 3s 7d)."
    ))
    story.append(sp(2))
    story.append(body("<b>Quick Reference — Loen to Feysac</b>"))
    feysac_conv = [
        ["Loen Price", "Exact Feysac", "Rounded for Play"],
        ["1d (pence)", "2k", "2 kopek"],
        ["1s (soli)", "2 fs 7k", "3 feysilver"],
        ["5s", "1 gh 4 fs", "1 gh 4 fs"],
        ["10s", "2 gh 8 fs", "2 gh 8 fs"],
        ["£1", "5 gh 5 fs", "5½ gh"],
        ["£2", "11 gh", "11 gh"],
        ["£5", "27 gh 5 fs", "27 gh 5 fs"],
        ["£10", "55 gh", "55 gh"],
        ["£50", "275 gh", "275 gh"],
    ]
    feysac_conv[0] = [Paragraph(c, S['TableHeader']) for c in feysac_conv[0]]
    for i in range(1, len(feysac_conv)):
        feysac_conv[i] = [
            Paragraph(feysac_conv[i][0], S['TableCellCenter']),
            Paragraph(feysac_conv[i][1], S['TableCellCenter']),
            Paragraph(feysac_conv[i][2], S['TableCellCenter']),
        ]
    story.append(Table(feysac_conv, colWidths=[1.2*inch, 1.6*inch, 1.6*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Starting Wealth in Feysac:</b> Poor 1 gh 4 fs | Struggling 4 gh 1 fs | "
        "Average 5 gh 5 fs | Comfortable 27 gh 5 fs | Wealthy 275 gh | Very Wealthy 550 gh"
    ))
    story.append(sp(1))
    story.append(body(
        "<i>The half-hoorn (5 fs) is a common coin in daily Feysac trade — similar in feel to Loen's 1-soli piece. "
        "Prices marked in Loen pounds throughout this book can be converted at the table by multiplying by 5.5 "
        "and reading the result as gold hoorn.</i>"
    ))
    story.append(sp(3))

    story += section("Starting Wealth by Economic Status")
    wealth_data = [
        ["Status", "Starting Money", "Reaction Modifier", "Lifestyle"],
        ["Dead Broke (-25 pts)", "£0", "−2", "No home; beg or steal for every meal"],
        ["Poor (-15 pts)", "5 soli", "−1", "Boarding house; barely afford basic food"],
        ["Struggling (-10 pts)", "15 soli", "0", "Modest room; occasional luxuries"],
        ["Average (0 pts)", "£1", "0", "Decent flat; regular meals; some savings"],
        ["Comfortable (+5 pts)", "£5", "+1", "Good lodgings; regular clothing budget"],
        ["Wealthy (+15 pts)", "£50", "+2", "Nice townhouse; fine clothes; a servant"],
        ["Very Wealthy (+25 pts)", "£100", "+3", "Large house; multiple servants; carriage"],
    ]
    wealth_data[0] = [Paragraph(c, S['TableHeader']) for c in wealth_data[0]]
    for i in range(1, len(wealth_data)):
        wealth_data[i] = [Paragraph(wealth_data[i][j],
            S['TableCellCenter'] if j==2 else S['TableCell']) for j in range(4)]
    story.append(Table(wealth_data, colWidths=[1.5*inch, 0.9*inch, 0.65*inch, 3.0*inch], style=table_style()))
    story.append(sp(2))
    story.append(body(
        "Your Wealth level determines your social <b>Status</b>. This affects how NPCs react to you: "
        "<b>+1</b> to reaction rolls per Status level above Average (e.g., Wealthy is Status 2 → +2), "
        "and <b>−1</b> per level below Average (e.g., Poor is Status −1 → −1). "
        "Status 0 (Average) grants no modifier. GMs may limit this modifier based on context — "
        "a shabby dockworker cares little for a noble's title, and a wealthy merchant gets no respect "
        "in a den of cutthroats."
    ))
    story.append(sp(3))

    story += section("Weapons (TL5+1 Victorian Era)")
    weapon_data = [
        ["Weapon", "Damage", "Acc", "Range", "Cost", "Skill"],
         ["Revolver (.38 cal)", "2d pi", "2", "150/1800", "£3", "Guns (Revolver)"],
         ["Revolver (.44 cal)", "2d+2 pi", "2", "175/1900", "£4", "Guns (Revolver)"],
        ["Bolt-Action Rifle", "5d pi+", "4", "500/3500", "£8", "Guns (Rifle)"],
        ["Hunting Rifle", "4d pi", "3", "500/3500", "£8", "Guns (Rifle)"],
        ["Double-Barrel Shotgun", "1d+1 pi", "1", "40/800", "£4", "Guns (Shotgun)"],
        ["Combat Knife", "sw-1 cut / thr imp", "0", "C/1", "10s", "Knife"],
        ["Truncheon/Baton", "sw cr", "0", "C", "5s", "Brawling"],
        ["Hand Axe", "sw+1 cut", "1", "C/1", "8s", "Axe/Mace"],
        ["Broadsword", "sw+1 cut / thr+2 imp", "0", "C", "£3", "Broadsword"],
    ]
    weapon_data[0] = [Paragraph(c, S['TableHeader']) for c in weapon_data[0]]
    for i in range(1, len(weapon_data)):
        weapon_data[i] = [Paragraph(c, S['TableCell']) for c in weapon_data[i]]
    story.append(Table(weapon_data, colWidths=[1.4*inch, 1.0*inch, 0.4*inch, 0.8*inch, 0.5*inch, 2.2*inch],
                        style=table_style()))
    story.append(sp(2))
    story.append(body(
        "<b>Shotgun note:</b> The Double-Barrel Shotgun fires multiple pellets. At close range "
        "(under 20 meters), multiply base damage by the number of pellets (×9 per barrel, "
        "both barrels = ROF 2). Each pellet hits separately — roll each separately or multiply "
        "average damage. Beyond 20 meters, the shot spreads and only 1d-2 pellets hit (roll randomly)."
    ))
    story.append(sp(3))

    story += section("Armour (TL5+1 Victorian Era)")
    armour_data = [
        ["Armour", "DR", "Cost", "Notes"],
        ["Heavy Coat (leather/canvas)", "1", "£2", "Concealable; protects torso and arms"],
        ["Mail Shirt (under coat)", "3/1*", "£10", "DR 3 vs cutting, DR 1 vs other; worn under clothing"],
        ["Bulletproof Vest (early)", "4", "£25", "Bulky, obvious; TL5+1 prototype; stops most pistol rounds"],
    ]
    armour_data[0] = [Paragraph(c, S['TableHeader']) for c in armour_data[0]]
    for i in range(1, len(armour_data)):
        armour_data[i] = [Paragraph(c, S['TableCell']) for c in armour_data[i]]
    story.append(Table(armour_data, colWidths=[1.6*inch, 0.5*inch, 0.7*inch, 3.7*inch],
                        style=table_style()))
    story.append(sp(3))

    story += section("Common Equipment")
    story.append(body(
        "The following table lists common equipment available in Backlund and other Loen towns. "
        "Prices are typical for TL5 urban markets; remote villages may charge 50–100% more."
    ))
    story.append(sp(2))

    def equip_row(cells, style='TableCell'):
        """Build a table row from [item, cost, notes]."""
        return [Paragraph(cells[0], S[style]),
                Paragraph(cells[1], S['TableCellCenter']),
                Paragraph(cells[2], S[style])]

    def equip_header(text, ncols=3):
        """Build a category-header row spanning all columns."""
        return [Paragraph(f"<b>{text}</b>", S['TableSubHeader'])] + \
               [Paragraph("", S['TableSubHeader']) for _ in range(ncols - 1)]

    equip_data = [
        [Paragraph("Item", S['TableHeader']),
         Paragraph("Cost", S['TableHeader']),
         Paragraph("Notes", S['TableHeader'])],
        equip_header("General Tools"),
        ["Lantern (oil)", "3s", "Illuminates 2 m radius; 2 hrs/pint of oil"],
        ["Rope (50 ft hemp)", "2s", "Supports up to 180 kg"],
        ["Rope, 20 ft", "1s", "Light duty; climbing or binding"],
        ["Lock picks (set)", "£1", "Required for Lockpicking skill; full set"],
        ["Lockpick set (basic)", "3s", "Low-quality; -1 to Lockpicking"],
        ["Notebook and pen", "1s", "Record keeping; required for investigative work"],
        ["Pencil case (6 pencils)", "1d", "Spare pencils and eraser"],
        ["Ink bottle (small)", "3d", "Refill for fountain pens; 50 pages' worth"],
        ["Parchment (5 sheets)", "2d", "Formal documents or diagrams"],
        ["Quill & penknife", "1s", "Writing set; penknife usable as tiny blade"],
        ["Compass (brass)", "3s", "Navigation (Land) +1 when exploring unfamiliar terrain"],
        ["Magnifying glass", "3s", "+1 to Search for fine details"],
        ["Small scale (brass)", "5s", "Weighing small goods; Merchant +1 when appraising unknown items"],
        ["Map case (leather)", "2s", "Protects maps and documents from weather"],
        ["Canteen (tin)", "1s", "Holds 1 L of water"],
        ["Chalk bag", "1d", "Chalk for marking; 20 pieces"],
        ["Sand timer (1 min)", "2s", "Short-duration timer"],
        ["Candles (3x)", "1d", "Poor light; 1 m radius dim light each; 2 hrs each"],
        ["Candles (6x, scented)", "2d", "As above; used in rituals"],
        ["Incense sticks (10x)", "1d", "Masking odors; ritual atmosphere"],
        ["Caffeine pills (tin)", "1d", "Stay awake for +2 hrs; fatigue recovery delayed"],
        ["Coffee, ground (bag)", "1d", "Enough for 10 cups; morale booster"],
        ["Whistle (signal)", "2d", "Audible up to 200 m"],
        ["Pocket watch (tin)", "5s", "Keeps time; social status item among commoners"],
        ["Iron lockbox", "8s", "Secure storage; DR 5, HP 10"],
        ["Bedroll", "5s", "Sleeping outdoors; +1 to Survival when rested"],
        ["Trap wire (10 m)", "1s", "Tripwire or snare; -2 to spot if camouflaged"],

        equip_header("Medical & Herbal"),
        ["First aid kit", "5s", "+1 to First Aid; 10 uses before restock"],
        ["Bandages (roll, 5x)", "2d", "Single-use; stops bleeding at -1 to First Aid"],
        ["Antiseptic (bottle)", "1s", "+1 to infection-resistance rolls; 20 doses"],
        ["Herbal salves (3x)", "1s", "+1 to First Aid on burns & rashes"],
        ["Scalpel set", "2s", "Surgery +1; also usable as fine knife"],
        ["Medicine bag (leather)", "10s", "Organizes medical gear; +1 to Physician when treating from it"],
        ["Herbs (assorted, pouch)", "2s", "Herbal Medicine component; 10 doses"],
        ["Medical reference (pamphlet)", "1s", "+1 to Diagnosis when consulted"],
        ["Portable medicine chest", "10s", "Field hospital; +2 to First Aid & Surgery; 50 doses"],
        ["Mortar & pestle", "1s", "Grinding herbs; needed for Herbal Medicine"],
        ["Prayer book (small)", "1s", "Religious comfort; +1 to Religious Ritual"],
        ["Holy book (leather)", "8s", "Full scripture; +1 to Theology; social status with church"],
        ["Holy symbol (wooden)", "2s", "Simple faith focus; -1 to ritual effects vs. quality symbols"],
        ["Holy symbol (quality)", "5s–£5", "Spiritual focus; +1 to Ritualistic Magic & Religious Ritual"],
         ["Rosary (wooden)", "1d", "Cogitation aid; +1 to Cogitation when used"],

        equip_header("Clothing & Protective"),
        ["Heavy boots (leather)", "6s", "Sturdy footwear; +1 to Forced Entry when kicking"],
        ["Dockworker's coat", "8s", "Thick canvas; DR 1 on torso; water-resistant"],
        ["Heavy coat (oilskin)", "10s", "Weatherproof; DR 1 on torso; +1 to Hiking in rain"],
        ["Apron (thick leather)", "5s", "DR 1 on torso front; soaks spills"],
        ["Work gloves (leather)", "1s", "Protects hands; +1 to Lifting vs sharp objects"],
        ["Dark clothing (set)", "5s", "-1 to spot at night; common street wear"],
        ["Dark clothes (quality)", "8s", "As above; blends in at social functions too"],
        ["Spare clothes (servant class)", "5s", "Clean change for social situations"],
        ["Fine clothes (quality)", "£1 10s", "+1 to Savoir-Faire (High Society); status marker"],
        ["Velvet shawl", "12s", "Warmth; +1 to reaction from romantic interests"],
        ["Spectacles (reading)", "5s", "Corrects vision; -3 to Search without them if shortsighted"],

        equip_header("Specialized Equipment"),
        ["Camera (simple box)", "5s", "Single-shot; documentary evidence; -2 to Photography"],
        ["Camera (early folding)", "£2", "Better lens; Photography +1; 12 plates"],
        ["Disguise kit (basic)", "2s", "Makeup and prosthetics; +1 to Disguise; 5 uses"],
        ["Disguise kit (advanced)", "10s", "+2 to Disguise; 10 uses; includes wigs"],
        ["Chemical testing kit", "5s", "+1 to Chemistry when testing samples; 10 tests"],
        ["Crystal ball (glass)", "£2", "Fortune-telling prop; +1 to Fortune-Telling or Psychology"],
        ["Tarot deck (common)", "2s", "Divination tool; +1 to Fortune-Telling"],
        ["Tarot deck (quality)", "10s", "+2 to Fortune-Telling; intricate artwork"],
        ["Ledger book", "2s", "Business records; +1 to Accounting for regular accounts"],
        ["Index cards (box, 100)", "2d", "Reference filing; +1 to Research for organized notes"],
        ["Rare book catalogue", "5s", "Reference; +1 to Connoisseur (Books) when appraising tomes"],
        ["Personal lending ledger", "3s", "Tracking loans; +1 to Merchant when collecting debts"],
        ["Blueprints (rolled, set)", "2d", "Engineering reference; +1 to Engineering for one structure type"],
        ["Timesheet ledger", "1s", "Labour management; +1 to Administration for shift planning"],
        ["False badge (tin)", "2s", "May pass casual inspection; -5 to fool officials"],
        ["Simple Identification Card", "5Gp / 3 pts", "A simple forgery of official identification. Works only for basic inspections (e.g. steam locomotive ticket purchase). There is a real chance the inspector notices the forgery."],
        ["Basic Identification Papers", "30Gp / 5 pts", "Forged selection of multiple identification papers — birth certificate, university degrees, etc. High enough quality to apply for employment. Fails under normal police or official Beyonder scrutiny."],
        ["Press badge", "2s", "Newspaper credentials; +1 to Gather Information in public"],
        ["Grappling hook & rope 15 ft", "4s", "Climbing +1 on walls; supports 135 kg"],
        ["Dolly (hand cart)", "6s", "Move up to 90 kg; Move ×½ when pushing"],
        ["Signal mirror", "2d", "Attract attention up to 1 km in sunlight"],
        ["Chemical light sticks (3x)", "1s", "Cold light; 1 m radius; 1 hr each (TL5 alchemical)"],
        ["Drinking flask (tin, hip)", "2d", "Holds 0.5 L; concealable on person"],
        ["Heavy tankard (pewter)", "1s", "Improvised weapon; 1d-2 cr; +1 to Carousing in pubs"],
    ]
    # Build rows: header row is already Paragraph objects
    for row in equip_data:
        if isinstance(row[0], Paragraph):
            continue  # already formatted (category header)
        row[0] = Paragraph(row[0], S['TableCell'])
        row[1] = Paragraph(row[1], S['TableCellCenter'])
        row[2] = Paragraph(row[2], S['TableCell'])
    def equip_table_style():
        """Table style for Common Equipment: header row + category dividers, no alternating BGs."""
        return TableStyle([
            ('BACKGROUND', (0,0), (-1,0), MID_NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), CREAM),
            ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTNAME', (0,1), (-1,-1), 'Times-Roman'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, SILVER),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ])
    story.append(Table(equip_data,
        colWidths=[2.2*inch, 0.8*inch, 4.3*inch],
        style=equip_table_style()))
    story.append(sp(3))

    story += section("Legal Licenses & Permits")
    story.append(body(
        "The Loen Kingdom maintains a semi-regulated policy on firearms. To legally possess a firearm, "
        "one must apply for one of two documents: a <b>Hunter's License</b> or an <b>All-Purpose Weapon "
        "Usage Certificate</b>. Regardless of which type is held, restricted military firearms — such as "
        "repeaters, steam-pressure guns, or six-barrel machine guns — remain illegal for civilian possession."
    ))
    story.append(sp(2))
    permit_data = [
        ["Permit Type", "Cost", "Point Value", "What It Allows", "Requirements"],
        ["Hunter's License", "£5", "5 pts",
         "Purchase and carry hunting guns (shotguns, hunting rifles) in limited numbers",
         "Straightforward approval — even suburban farmers can qualify; clean record"],
        ["All-Purpose Weapon\nUsage Certificate", "£50", "15 pts",
         "Purchase, store, and carry any civilian firearm (pistols, rifles, shotguns)",
         "City government AND police permission required; must obtain vouches from "
         "3 persons of good moral character and high standing in Backlund"],
        ["Church Enforcement\nBadge (Nighthawk, etc.)", "N/A (issued)", "N/A",
         "Full weapon carry including restricted items; authority to investigate "
         "supernatural incidents",
         "Must be a sworn member of a church enforcement division (Nighthawks, "
         "Mandated Punishers, Inquisitors, etc.); badge supersedes civilian licenses"],
    ]
    permit_data[0] = [Paragraph(c, S['TableHeader']) for c in permit_data[0]]
    for i in range(1, len(permit_data)):
        permit_data[i] = [Paragraph(c, S['TableCell']) for c in permit_data[i]]
    story.append(Table(permit_data, colWidths=[1.3*inch, 0.6*inch, 0.6*inch, 2.3*inch, 2.5*inch], style=table_style()))
    story.append(sp(1))
    story.append(body(
        "<i>Note: Characters may purchase a license purely as equipment (pay the monetary cost) or take it "
        "as an Advantage (pay the point cost and gain the license free of monetary cost, having already "
        "secured it through backstory). The two options are equivalent — a character should not pay both "
        "points and pounds for the same license. Beyonders acting on church authority do not need "
        "civilian licenses; their badge serves as legal authority.</i>"
    ))
    story.append(sp(3))

    story += section("Hired Allies & Services")
    story.append(body(
        "Player characters may wish to hire NPC allies — informants, muscle, experts, or guides. "
        "The following table lists typical daily or weekly rates for common hires in Backlund. "
        "These costs assume a short-term arrangement (1 day to 1 week). Long-term retainers may "
        "be negotiated at a discount."
    ))
    story.append(sp(2))
    hire_data = [
        ["Service", "Daily Rate", "Weekly Rate", "Capabilities"],
        ["Street Informant", "1s", "5s",
         "Local knowledge (East Borough or Docks); +1 to Streetwise; may have criminal contacts"],
        ["Bouncer / Muscle", "2s", "10s",
         "ST 11–12, Brawling-12, Intimidation-10; follows orders in a fight"],
        ["Expert Scholar", "5s", "£1 10s",
         "IQ 12, Research-13, Occultism-12; provides +1 to Research/Occultism for one project"],
        ["Guide (Urban)", "2s", "8s",
         "Area Knowledge (any one district)-12; can navigate back alleys and safe houses"],
        ["Guide (Wilderness)", "3s", "12s",
         "Survival-11, Tracking-11, Area Knowledge (woodlands)-12; hunting skills"],
        ["Consultant Doctor", "5s (+ supplies)", "£2",
         "Diagnosis-12, Surgery-11, Physician-12; treats serious wounds between adventures"],
        ["Private Investigator", "10s", "£3",
         "Criminology-12, Search-11, Stealth-10; conducts discrete investigations"],
        ["Carriage Hire (day)", "3s", "—",
         "Horse-drawn carriage for a full day within city limits; driver included"],
        ["Falsified Identity (Advantage)", "70–100Gp / 20 pts", "—",
         "A fully stolen or falsified identity properly recorded in official government records. Can only be obtained from certain rarely found forgers with extensive government connections. Holds under regular police scrutiny and superficial investigation. Fails if an investigator or official Beyonder peers deeper."],
    ]
    hire_data[0] = [Paragraph(c, S['TableHeader']) for c in hire_data[0]]
    for i in range(1, len(hire_data)):
        hire_data[i] = [Paragraph(c, S['TableCell']) for c in hire_data[i]]
    story.append(Table(hire_data, colWidths=[1.3*inch, 0.8*inch, 0.8*inch, 4.4*inch], style=table_style()))
    story.append(sp(1))
    story.append(body(
        "<i>Note: Hiring an armed ally for dangerous work may require paying a hazard bonus "
        "(+50–100% of daily rate). The GM should adjust rates based on local availability and "
        "the reputation of the hiring party.</i>"
    ))

    story.append(PageBreak())

    story += chapter("Chapter 9: Sequence 9 Potion Effects")

    story.append(body(
        "When a character drinks a Sequence 9 potion they do not simply gain a new power — their body, mind, "
        "and soul are permanently reshaped by the will of the Pathway they have entered. The changes listed "
        "below apply immediately upon consumption. Stat gains and new advantages take effect at the moment "
        "the potion is digested (usually within minutes). Skill gains represent an intuitive awakening: the "
        "Beyonder does not need prior training in the listed skills — they simply know them at the listed level."
    ))
    story.append(sp(4))
    story.append(body(
        "Each entry lists the stat and skill changes that take effect immediately upon digestion, "
        "followed by the pathway's signature ability. All changes are permanent."
    ))
    story.append(sp(2))
    story.append(warning_box(
        "The potion gives you stat bonuses, skill levels, and advantages for <b>free</b>. "
        "If you later want to raise one, just pay the normal point ladder cost for the new level. "
        "That is all — the potion gave you a free head start, nothing more."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Upgrading potion-granted skills & attributes</b>"
    ))
    story.append(body(
        "When you drink a Sequence 9 potion, it gives you certain skills and attribute bonuses "
        "for <b>free</b> — you didn't spend any points on them. They are already on your sheet "
        "at the listed level, fully paid by the potion."
    ))
    story.append(body(
        "If you later want to raise a potion-granted skill or attribute, just pay the normal "
        "point ladder cost for the new level — same as if you had no potion at all. Look up the "
        "cost on the point-cost ladder in <b>Chapter 3: Character Creation</b> and pay it."
    ))
    story.append(body(
        "<b>Exception — SPI-based skills</b> (Spiritual Intuition, Spiritual Perception, Divination Arts) "
        "cannot be raised with character points. They improve only through Sequence progression and pathway bonuses."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Example (skill):</b> A Seer receives Occultism at IQ+2 (Average skill). "
        "They want IQ+3. The ladder says IQ+3 costs <b>16 pts</b>. They pay <b>16 points</b>."
    ))
    story.append(body(
        "<b>Example (attribute):</b> A Sailor receives ST +2 (ST 9 → 11). They want ST 12. "
        "On the point ladder the next level (11 → 12) costs <b>40 pts</b> (see Chapter 3). "
        "They pay <b>40 points</b>."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Disadvantages from potions do not give points back.</b> Some pathway entries "
        "list drawbacks — side effects, compulsions, or changes that look like disadvantages. "
        "These are <b>part of the potion's cost</b>, not a source of bonus points. "
        "You do not add them to your disadvantage total, and you do not get any point refund "
        "for them. They are simply features of your new Beyonder nature."
    ))
    story.append(sp(3))

    story += section("How to Read These Entries")
    story.append(body(
        "Each pathway entry is a block of information. Here is how to read it:"
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Name of the Sequence:</b> The canonical title from the source material (e.g., Seer, Marauder)."
    ))
    story.append(body(
        "<b>Pathway:</b> The divine pathway this Sequence belongs to (e.g., Fool Pathway, Error Pathway)."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Stats:</b> Listed as \"DX +1\" — this means your Dexterity goes up by 1 permanently, "
        "and this improvement is worth 20 character points (paid for by the potion). Some entries list "
        "advantages instead of attribute increases, like \"Eidetic Memory +5 pts\". Some entries also list "
        "drawbacks in a <b>Disadvantages</b> column — these are side effects of the potion and do not give points back."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Skills:</b> Listed as \"Ritualistic Magic/IQ [Very Hard] +3\" — this means you gain "
        "Ritualistic Magic at your IQ attribute <b>plus 3</b>, it is a Very Hard skill (based on IQ), and it is "
        "a new skill you did not have before (you do not need prior training — the potion awakens it). "
        "Both new skills and skill enhancements are listed with their bonus directly."
    ))
    story.append(sp(1))
    story.append(body(
        "<b>Important — how to read the +N bonus:</b> The number after the skill (e.g., +2, +3, +5) "
        "means the <b>final skill level equals your attribute plus that number</b>. It does NOT mean "
        "\"buy N rungs up the ladder from default.\" For example, \"Acrobatics/DX [Hard] +2\" means "
        "your Acrobatics skill is at <b>DX+2</b>, which on the ladder (2^4) costs 16 points — not "
        "the 2 points that \"2 rungs up from default\" would suggest. Always read +N as "
        "\"Attribute + N.\""
    ))
    story.append(sp(2))
    story.append(body(
        "<b>If you already have the skill:</b> The potion may grant a +N bonus to a skill you already "
        "know. In that case, read the bonus as <b>\"skill level + N\"</b> instead of \"Attribute + N.\" "
        "For example, if your character already has Stealth/DX [Average] at level 12, and a potion grants "
        "\"Stealth/DX [Average] +2,\" your Stealth becomes <b>14</b> (not DX+2). The bonus stacks with "
        "your existing proficiency. This only applies when the <b>same skill name and difficulty</b> "
        "match exactly; if you have a different version or difficulty, treat it as a new skill at "
        "Attribute + N."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Ability text:</b> The paragraph(s) after the stats and skills describe what the Sequence "
        "can actually do with its power — special attacks, passive senses, spiritual techniques. Abilities "
        "in <b>bold red</b> are specific named powers you can activate. SPI costs are listed next to "
        "each ability where applicable."
    ))
    story.append(sp(6))

    # ── Pathway data: (title, pathway, stats[], skills[], ability_text)
    seq9_pathways = [

          ("Seer", "Fool Pathway",
          [("SPI", "+9"), ("Eidetic Memory", "continuously grows as the potion digests; allows memorisation of complex ritual steps and divination methods")],
          [("Ritualistic Magic/IQ [Very Hard]", "+3"),
            ("Divination Arts/SPI [Hard]", "+3"),
            ("Spiritual Intuition/SPI [Hard]", "+3"),
            ("Occultism/IQ [Average]", "+2")],
           "<b><font color='#C0392B'>Spirit Vision:</font></b> By expending 1 SPI, the Seer activates Spirit Vision (costs 1 SPI per minute). "
           "While active: sees non-physical entities such as ghosts and spectres; examines the "
           "different parts of a Soul to deduce a target's health and emotional state; detects whether an object "
           "or person carries a magical aura; perceives obstructed objects and faint sounds within roughly "
           "10 meters. <b><font color='#C0392B'>Danger Intuition:</font></b> Passive. The "
           "Seer intuitively detects lethal danger nearby using Spirituality. The GM provides a vague warning "
          "sense whenever mortal danger is near — no roll required."),

         ("Marauder", "Error Pathway",
          [("ST", "+1"), ("DX", "+1"), ("SPI", "+1")],
    [("Knife/DX [Easy]", "+3"),
             ("Shortsword/DX [Average]", "+3"),
            ("Sleight of Hand/DX [Hard]", "+4"),
            ("Pickpocket/DX [Hard]", "+4"),
            ("Observation/Per [Average]", "+2")],
           "<b><font color='#C0392B'>Treasure Sense:</font></b> The Marauder can sense the presence of valuable items "
           "within a 10-meter range — coins, jewellery, artifacts, hidden pouches — but cannot determine their "
           "exact location or what they are. The sense is a vague pull: stronger for higher value, weaker for "
           "trinkets. At the GM's discretion, unusually powerful or ancient items may register as a distinct "
           "\"weight\" in the perception."),

         ("Apprentice", "Door Pathway",
          [("SPI", "+5")],
          [("Running/HT [Average]", "+3"),
             ("Lockpicking/IQ [Average]", "+6"),
            ("Climbing/DX [Average]", "+3"),
           ("Ritualistic Magic/IQ [Very Hard]", "+2")],
          "<b><font color='#C0392B'>Door Opening:</font></b> Apprentices can open things related to Doors. Any mundane lock, bolt, latch, or "
          "physical door can be opened by touch and will (no tool or key required; one second per door, no "
          "roll). Spiritual or warded doors require a Ritualistic Magic roll at no penalty (1 SPI cost). Doors sealed by "
          "High-Sequence Beyonders are beyond this ability. This extends to doors on the human body: an "
           "Apprentice may touch a wound, a joint, or a bodily passage by will — treated as "
           "an attack dealing 1d-1 cut damage that bypasses mundane armor. Make a Brawling roll or a DX-based touch attack to land it on a resisting target. "
          "Additionally, the Apprentice cannot be easily trapped: any time they are physically restrained by "
          "non-supernatural means they receive an immediate free Escape roll at +2 before the situation resolves."),

         ("Spectator", "Visionary Pathway",
            [("SPI", "+2"),
             ("IQ", "+1"),              ("Acute Vision", "+2 to Vision rolls"),
             ("Eidetic Memory", "+5 to remember things after one reading; near-perfect recall")],
          [("Psychology/IQ [Hard]", "+3"),
           ("Body Language/Per [Average]", "+3"),
           ("Observation/Per [Average]", "+2"),
           ("Detect Lies/Per [Hard]", "+2")],
"<b><font color='#C0392B'>Body Language Analysis (1 FP):</font></b> Spectators use their powers of keen observation to analyze "
           "people's expressions, manners, and subconscious actions. For groups of people, this may reveal their surface-level "
           "thoughts and dominant emotions — what they are feeling right now and what is occupying their mind. This is surface "
           "only; deep intentions, lies of omission, and suppressed feelings are not automatically revealed.\n"
           "On a singular target, roll Psychology to deduce and form a mental model of the target. At the GM's discretion, "
           "learn more detailed information about a target's current thoughts and emotions depending on factors such as: "
           "the margin of success, how powerful the target is, time spent observing them, prior information known about them, "
           "etc.\n"
          "Any target who is sharp perceptively (Per 13+) can roll Per to notice the Spectator observing them. "
          "Success by 0–4: they notice something is observing them. Success by 5+ or Critical Success: they also identify "
          "the source of where and what is observing them."),

          ("Bard", "Sun Pathway",
             [("SPI", "+1"),
              ("HT", "+1"), ("Fit", "+1 to all HT rolls; recover FP at twice the normal rate")],
          [("Singing/HT [Easy]", "+4")],
          "<b><font color='#C0392B'>Singing — Buff Effects:</font></b> Through Singing, a Bard imbues effects onto themselves and nearby allies. "
          "On a successful Singing roll (no penalty), the Bard selects ONE of the following "
"effects for all allies within earshot for 10 minutes: <b>(a) Courage —</b> allies ignore Fright Check "
           "penalties up to -3; <b>(b) Strength —</b> allies gain +1 to ST-based rolls; <b>(c) Agility —</b> allies gain "
           "+1 to DX-based rolls; <b>(d) Spiritual Recovery —</b> allies recover 1 SPI at the song's end (Bard cannot benefit from this effect). No SPI cost — "
          "the Bard's voice itself carries the power. At Sequence 9 "
          "a Bard cannot produce effects beyond these through Singing."),

          ("Sailor", "Tyrant Pathway",
            [("ST", "+2"),
             ("SPI", "+1"),
             ("Perfect Balance", "+6 avoid knockdown; +2 Acrobatics, Climbing, Piloting")],
          [("Seamanship/IQ [Easy]", "+3"),
           ("Swimming/HT [Easy]", "+4"),
           ("Navigation (Sea)/IQ [Average]", "+2"),
           ("Weather Sense/IQ [Average]", "+2")],
         "<b><font color='#C0392B'>Phantom Scales (passive):</font></b> Illusory scales beneath the skin grant DR 1 vs. physical impacts. "
         "Anyone grappling or grabbing the Sailor rolls at -2 (slippery as a fish). "
          "<b><font color='#C0392B'>Aquatic Affinity — Diving:</font></b> Without equipment the Sailor freely submerges and acts underwater for "
          "at least 10 minutes, diving to at least 15 meters without protection. Ignore all underwater movement "
          "penalties; hold breath 10 minutes without a roll; dive to 15 m without HT rolls."),

         ("Reader", "White Tower Pathway",
           [("SPI", "+3"),
             ("Eidetic Memory", "+5 to remember things after one reading; near-perfect recall"),
             ("IQ", "+1 (knowledge retention and learning)")],
         [("Research/IQ [Average]", "+3"),
          ("Any one knowledge skill (player's choice)/IQ [Average]", "+3"),
          ("Ritualistic Magic/IQ [Very Hard]", "+2"),
           ("Speed-Reading/IQ [Average]", "+2")],
         "<b><font color='#C0392B'>Reading — Knowledge Wealth:</font></b> A Reader gains a wealth of knowledge through extensive reading combined "
         "with enhanced mental attributes. May attempt an IQ roll (no penalty) to recall any piece of general "
         "knowledge — history, science, mysticism, language — that could plausibly be found in books, even "
         "if the player has not specifically researched it. Critical success produces highly specific detail. "
         "The GM may impose -2 to -4 for very obscure material. The Reader also learns new languages in half "
         "the normal time."),

         ("Secrets Supplicant", "Hanged Man Pathway",
            [("SPI", "+11")],
          [("Ritualistic Magic/IQ [Very Hard]", "+2 — decent knowledge of rituals, especially sacrifices"),
           ("Spiritual Perception/SPI [Average]", "+3 — able to detect hidden and terrifying existences")],
          "<b><font color='#C0392B'>Knowledge (Honorifics):</font></b> Knowledge gained from the potion includes honorific names "
          "for secret existences. Three-part honorific learned: <i>\"The Lord that Created Everything; "
          "The Lord who Reigns Behind the Curtain of Shadows; The Degenerate Nature of all Living Things.\"</i> "
          "Another three-part honorific: <i>\"The Lingering Hero Spirit of The River; The Eyes that Look at Fate; "
          "The Great Soothsayer of Past, Present, and Future.\"</i>",
          [("Paranoia, Hallucinations, or Compulsion (Hanged Man; -10 pts)", "Choose one of these three drawbacks. "
           "Paranoia: you trust no one, always suspect betrayal. Hallucinations: you see and hear things that are not there. "
           "Compulsion (Hanged Man): an irresistible urge to seek out secrets and hidden knowledge, even when dangerous.")]),

         ("Sleepless", "Darkness Pathway",
            [("SPI", "+9"),
            ("Reduced Sleep", "Requires only 3–4 hours of rest per day; otherwise functions as Does Not Sleep")],
          [("Ritualistic Magic/IQ [Very Hard]", "+2")],
           "<b><font color='#C0392B'>Nocturnality (passive):</font></b> +1 to all rolls during the night.\n"
           "<b><font color='#C0392B'>Spirit Vision — Limited Form:</font></b> A Sleepless can activate Spirit Vision to see spiritual entities. "
           "Unlike the Seer, they cannot read the state of different Soul parts or deduce health and emotional "
           "states — it is detection only, not analysis. Expend 1 SPI (costs 1 SPI per minute). On success, sees ghosts, "
           "spectres, and non-physical entities. <b><font color='#C0392B'>Danger Detection in the Dark:</font></b> Passive "
          "Danger Sense that is specifically heightened in low-light and dark environments (+2 to the roll when "
          "in darkness). In any darkness the Sleepless navigates without penalty and suffers no night-based "
          "Perception penalty."),

         ("Corpse Collector", "Death Pathway",
            [("SPI", "+6"),
             ("ST", "+1"), ("HT", "+1"),
             ("Cold Resistance", "No penalties from cold environments; hypothermia rolls at +2"),
             ("Resistant (Decay and Corrosiveness)", "HT rolls to resist corrosiveness (acid, rust) and decay effects at +3"),
            ],
         [("Physician/IQ [Hard]", "+2"),
          ("Surgery/IQ [Very Hard]", "+1")],
           "<b><font color='#C0392B'>Undead Deterrence:</font></b> Mindless undead/spirits (IQ 5−) with SPI ≤ yours "
          "ignore you unless provoked. Intelligent (IQ 6+) or controlled undead may roll Will to act against you. "
          "Controlled undead roll at −2; intelligent undead roll without penalty. No effect on undead with SPI > yours "
          "or created by Seq 5+ Beyonders. "
          "<b><font color='#C0392B'>Undead Detection:</font></b> Corpse Collectors naturally detect undead and spirit "
          "creatures within 15 meters without rolling. They understand the characteristics and weaknesses of many undead beings. "
          "Observation rolls to understand undead beings are at +3. "
           "<b><font color='#C0392B'>Spirit Vision (1 SPI/min, standard):</font></b> The Corpse Collector can activate Spirit Vision to see spiritual entities "
           "and the Ether Body of living beings, enabling limited analysis of health and spiritual conditions.",
           [("Fear of Sunlight and Purification", "−1 to Will, skills, and combat actions under strong holy/purified/sunlight effects. Must roll Will to approach their source. Sunlight/purification/holy attacks gain +1 against you.")]),

         ("Warrior", "Twilight Giant Pathway",
             [("ST", "+3"), ("DX", "+2"), ("HT", "+1"), ("SPI", "+1")],
          [("Broadsword/DX [Average]", "+3"),
           ("Shield/DX [Easy]", "+2"),
           ("Polearm/DX [Average]", "+2"),
           ("Armoury (any)/IQ [Average]", "+2"),
           ("Brawling/DX [Easy]", "+2")],
           "<b><font color='#C0392B'>Combat Mastery (Passive):</font></b> The Warrior has mastery of all kinds of weapons and armour, "
          "with no weapon they cannot use and no fighting style they cannot learn. The Warrior suffers no "
          "default penalty when using any weapon type for the first time — every weapon is treated as known "
          "at effective DX (no default penalty) from the moment it is picked up. Weapons used repeatedly in a session are "
          "treated as known at default +2. <b>Example:</b> A Warrior who picks up a flintlock pistol for the "
          "first time fires it at DX level immediately, but needs several shots before reaching full proficiency "
          "(default +2 after repeated use). They also don and maintain any armour type without penalty and "
          "fight effectively in it regardless of prior experience."),

         ("Assassin", "Demoness Pathway",
            [("ST", "+1"), ("DX", "+2"),
             ("Basic Speed", "+0.25 — reflexes sharpen for precise timing"),
             ("Night Vision", "see in total darkness without penalty"),
             ("Acute Vision", "+2 to vision-based Perception rolls"),
             ("Acute Hearing", "+2 to hearing-based Perception rolls"),
             ("SPI", "+1")],
          [("Acrobatics/DX [Hard]", "+2")],
          "<b><font color='#C0392B'>Feather Fall:</font></b> Assassins can descend from any height without injury. All falls are treated as "
          "controlled regardless of height — the Assassin always lands safely and silently. While descending "
          "they may glide short horizontal distances (up to 1 meter horizontal per 2 meters vertical). Not "
          "sustained flight; cannot maintain altitude. Lands without audible impact — no Perception roll "
          "detects the landing through sound alone. <b><font color='#C0392B'>Shadow Concealment:</font></b> The Assassin's body instinctively "
          "blends with shadows. In any environment with partial shadow or dim lighting, the Assassin is "
          "supernaturally difficult to notice — observers must succeed at a Perception roll at -3 to detect "
          "them while they are stationary, and at -1 while moving slowly. This is a passive physical change, "
           "not a trained skill. Bright, open daylight negates this effect. "
           "<b><font color='#C0392B'>Mighty Blow (3 FP):</font></b> Spend 3 FP and roll the appropriate melee skill. "
           "You gain +3 to hit. On a hit, multiply raw damage dice by 3 (before DR). "
           "This ability cannot be modified by other maneuvers or by burning FP."),

         ("Hunter", "Red Priest Pathway",
            [("ST", "+2"), ("DX", "+2"), ("Per", "+1"), ("Acute Vision", "+2 to vision-based Perception rolls; spot distant details"), ("Acute Hearing", "+2 to hearing-based Perception rolls; detect faint sounds"), ("Danger Sense (partial)", "warning sense for immediate physical danger — less reliable for non-physical threats"), ("SPI", "+1")],
          [("Tracking/Per [Average]", "+4"),
            ("Traps/IQ [Average]", "+4"),
            ("Explosives (Demolition)/IQ [Average]", "+4"),
            ("Survival (any terrain)/Per [Average]", "+2")],
         "<b><font color='#C0392B'>Environment Memory:</font></b> Hunters have an unwavering memory for any alterations made to their surroundings. "
         "Any previously visited location is perfectly recalled, and the Hunter automatically notices any "
         "alteration to a visited location. Natural traps — unstable cliffs, quicksand, deadfall zones — are "
         "detected instinctively without any roll. <b><font color='#C0392B'>Survival Knowledge:</font></b> The Hunter possesses innate knowledge of "
"wild plants and animal organs, including which plants and organs serve as hemostatic agents when injured "
          "and which can be rendered into poisons to coat weapons. Identifying and preparing these requires no roll "
          "in wilderness environments. Hemostatic poultices prepared this way restore 1d HP to a bleeding wound "
          "(requires 1 minute and a First Aid roll at +2); if not bleeding, they restore 2 HP. Only one such "
          "poultice per injury per character."),

         ("Mystery Pryer", "Hermit Pathway",
            [("SPI", "+9")],
          [("Occultism/IQ [Average]", "+3"),
           ("Ritualistic Magic/IQ [Very Hard]", "+4"),
            ("Divination Arts/SPI [Hard]", "+2"),
           ("Thaumatology/IQ [Very Hard]", "+2")],
            "<b><font color='#C0392B'>Eyes of Mystery Prying (1 SPI/min):</font></b> A Mystery Pryer's eyes are "
             "special and allow them to see things that are normally invisible. Always-on passive effects: peer "
             "through attempts to trap them in Dreams or Illusions (all such rolls against them are at -2). "
             "Active use — expend 1 SPI and roll SPI — to activate Spirit Vision: detect if something is a Mystical Item or if "
             "someone is a Beyonder via their Astral Projection, and to examine the full "
            "state of a target's Astral Body, Ether Body, and Body of Heart and Mind: reveals injury, spiritual "
             "corruption, active Beyonder abilities, and potion side effects. <b><font color='#C0392B'>Corruption Exposure:</font></b> When "
             "actively prying into a target who has 5+ CoR, a sealed evil artefact, or an eldritch "
             "entity, the Mystery Pryer must make an immediate Will roll or gain 1 CoR from witnessing "
            "things the mind was not meant to see. The GM may call for additional Will rolls whenever the Pryer "
            "glimpses truly forbidden knowledge.\n"
              "<b><font color='#C0392B'>Spirit Contract (Ritual):</font></b> The Mystery Pryer gains knowledge of how to use "
             "Ritualistic Magic to form contracts with summoned spirits. A Mystery Pryer may maintain up to "
             "<b>2 simultaneous contracts</b> at Sequence 9, doubling to <b>4</b> at Sequence 8. "
             "This remains incredibly dangerous and requires "
             "proper summoning incantations and other safety measures.\n"
             "<b><font color='#C0392B'>Quick Rituals:</font></b> The penalty for rushed rituals is decreased by 3.",
             [("Knowledge Pursuit", "Flat 3d6 roll under 14 — GM decides what information you uncover. "
               "On failure, gain 1 CoR. On critical failure, gain 3 CoR instead. Knowledge revealed is at the GM's "
               "discretion and may include honorific names, partial/full potion formulas, spirit summoning incantations, "
               "spells, curses, mystical and non-mystical ingredients, and more.")]),


         ("Savant", "Paragon Pathway",
           [("IQ", "+2"), ("SPI", "+1")],
         [("Engineering/IQ [Hard]", "+3"),
          ("Mechanic (Steam Engines)/IQ [Average]", "+3"),
          ("Chemistry/IQ [Hard]", "+2"),
          ("Research/IQ [Average]", "+2"),
           ("Inventor!/IQ [Wildcard]", "+2")],
         "<b><font color='#C0392B'>Recall — Total Memory:</font></b> The Savant can recall every piece of knowledge and experience they have "
         "ever encountered. No roll is required — it simply works at any time. Additionally, the Savant "
         "understands the operation of any mechanism, construct, or device within 1 minute of examination "
         "(IQ roll, no penalty) rather than the usual 1 hour. <b><font color='#C0392B'>Rapid Analysis:</font></b> improvised "
         "devices and repairs take half the normal construction time."),

          ("Monster", "Wheel of Fortune Pathway",
              [("SPI", "+12")],
             [("Spiritual Perception/SPI [Average]", "+2"),
              ("Spiritual Intuition/SPI [Hard]", "+1")],
          "<b><font color='#C0392B'>Foresight:</font></b> A Monster is able to hear or see things that others cannot. Occasionally they gain "
          "glimpses of the future — this is the specialty of the Wheel of Fortune Pathway, allowing them to perceive "
          "things that even Pathways with strong Spirit Vision abilities cannot see. Once per session the "
          "Monster receives a spontaneous, unbidden vision of something about to happen (the GM provides a "
          "brief cryptic image or impression). This cannot be triggered on demand — it arrives when fate "
          "deems it relevant. <b><font color='#C0392B'>Danger Premonition:</font></b> Passive Danger Sense that specifically includes "
          "premonitions of bad luck and fate-based traps, not only immediate physical violence.",
             [("Monster Trance", "The Monster occasionally enters a trance-like state (GM's discretion), usually triggered by strong fate currents or significant future events. During a trance, the Monster is unaware of their surroundings and vulnerable.")]),

         ("Planter", "Mother Pathway",
            [("ST", "+3"), ("SPI", "+2"), ("HT", "+1")],
          [("Farming/IQ [Easy]", "+6"),
           ("Gardening/IQ [Easy]", "+6"),
           ("Naturalist/IQ [Hard]", "+4"),
           ("Herbal Medicine/IQ [Very Hard]", "+2"),
           ("Weather Sense/IQ [Average]", "+4")],
         "<b><font color='#C0392B'>Farming Tools Proficiency:</font></b> When fighting with a farming tool, the Planter chooses "
         "the most appropriate skill and gains +2 to the attack roll. For example, a shovel would use either "
         "the Mace skill or the Polearm skill (GM's decision based on how it is wielded)."),

         ("Apothecary", "Moon Pathway",
            [("HT", "+2"), ("SPI", "+4"),
             ("Poison Resistance", "+3 to all HT rolls against poison and toxic substances")],
          [("Pharmacy/IQ [Hard]", "+5"),
           ("Poisons/IQ [Hard]", "+5"),
           ("Physician/IQ [Hard]", "+4"),
           ("Gardening/IQ [Easy]", "+3"),
           ("Herb Lore/IQ [Very Hard]", "+2")],
           "<b><font color='#C0392B'>Spirit Vision — Ether Body:</font></b> The Apothecary can read the Ether Body of living beings, "
           "revealing injuries, illnesses, toxins, and supernatural conditions. Costs 1 SPI per minute.\n\n"
           "<b><font color='#C0392B'>Potion Concoction:</font></b> The Apothecary can brew a variety of alchemical concoctions. "
           "Each potion requires appropriate ingredients (GM discretion on rarity and cost) and a Pharmacy roll at the "
           "listed penalty. An Apothecary may carry up to (SPI) doses of prepared potions at any time. Multiple doses of the "
           "same potion count separately.\n"
           "• <b>Libido Potion (Pharmacy -1):</b> Powdered mummy and aromatic herbs. The drinker gains exceptional stamina "
           "and drive for up to 12 hours. Typically used recreationally or socially; creative players may find other uses.\n"
           "• <b>General Physical Enhancer (Pharmacy -2):</b> Common medicinal herbs, rabbit's foot, honeysuckle extract "
           "(or any Seq 9 supplementary ingredient besides liquor). Grants +1 to ST, HT, DX, and Basic Speed for 5 minutes. "
           "After the duration expires, the user loses 1/3 of their remaining FP (round up) and their FP maximum is halved "
           "(round up) until they sleep for at least 8 hours. If current FP exceeds the new cap, it is reduced to match.\n"
           "• <b>Enhanced Healing Agent (Pharmacy -4):</b> Expensive herbs and rare animal parts costing approximately £20 "
           "per dose. Grants Very Fast Regeneration for 10 seconds. Costs 1/5 of the user's current FP (round up) — e.g., "
           "if current FP is 5/10, after use it becomes 4/10.\n"
           "• <b>Specialised Physical Enhancer (Pharmacy -3):</b> Requires 3 different supplementary ingredients plus a "
           "specific base liquid. Grants +3 to a single attribute for 3 minutes, determined by the base liquid: "
           "hard liquor → ST, soft liquor (wine, etc.) → HT, water → DX. After the duration expires, the user loses "
           "1/3 of their remaining FP (round up) and their FP maximum is halved (round up) until they sleep for at least "
           "8 hours. If current FP exceeds the new cap, it is reduced to match.\n"
           "• <b>Energy Potion (Pharmacy -1):</b> Sugar, honey, coffee powder, and energising herbs. Reduces the user's "
           "maximum FP by 1/4 (round up) and instantly restores their FP to the new maximum. Example: 1 FP out of 12 → "
           "max reduced by 3 to 9, user now has 9 FP. Each subsequent use further reduces maximum FP by 1/4 of the "
           "current maximum. Lost maximum FP returns after 8 hours of uninterrupted sleep."),

         ("Criminal", "Abyss Pathway",
             [("ST", "+2"), ("Per", "+2"), ("SPI", "+1"), ("Will", "-1")],
           [("Guns (Revolver)/DX [Easy]", "+3"),
             ("Knife/DX [Easy]", "+2"),
             ("Brawling/DX [Easy]", "+2"),
             ("Throwing/DX [Average]", "+1"),
             ("Fast-Draw (Revolver)/DX [Easy]", "+2"),
             ("Wrestling/DX [Average]", "+1"),
             ("Boxing/DX [Average]", "+1"),
             ("Streetwise/IQ [Average]", "+1")],
           "<b><font color='#C0392B'>Criminal Proficiency — Universal Weapons:</font></b> Regardless of the weapon — "
           "knightly sword, dagger, longbow, pistol, rifle, machine gun, or a spoon — they can utilise all of them "
           "to kill a target effectively. The Criminal treats any improvised weapon as their Knife or Brawling skill "
           "(whichever is appropriate). They are equally deadly with ranged weapons as with melee — a Criminal can "
           "pick up any firearm and fire it with ease, using the most similar Gun skill available.",
            [("Criminal's Mind", "Roll Will when suppressing evil desires. Define with the GM which new evil desires define your character — murder, lust, theft, etc.")]),

          ("Prisoner", "Chained Pathway",
            [("ST", "+2"), ("HT", "+1"), ("Per", "+2"), ("SPI", "+0"),
             ("Binding (Prisoner)", "Spirituality and desires are Bound; Spiritual Perception and readings of Ether Body "
             "and Astral Projection against them are at -4 when composed. Ether Body and Astral Projection appear "
             "indistinct and calm, making it difficult to detect you are a Beyonder. When not composed or actively "
             "indulging, this trait is temporarily lost."),
            ],
          [("Holdout/IQ [Average]", "+5"),
           ("Lockpicking/IQ [Average]", "+5"),
           ("Escape/DX [Hard]", "+5"),
           ("Explosives (Demolition)/IQ [Average]", "+3"),
           ("Intimidation/Will [Average]", "+2"),
           ("Stealth/DX [Average]", "+1"),
           ("Brawling/DX [Easy]", "+1")],
         "<b><font color='#C0392B'>Knowledge — Criminal Expert:</font></b> Upon advancement, Prisoners gain knowledge that makes them masters "
         "of many criminal techniques: picking locks with wire, digging tunnels with improvised tools, and "
         "killing with seemingly harmless items. Improvised weapons suffer no penalties and are treated as "
         "Brawling or ST. Escape rolls against mundane confinement suffer no penalty or disadvantage regardless "
         "of the restraint type. The Prisoner also has an instinctive awareness of confinement — they always know "
         "within a 10-meter range if a space has a hidden exit or concealed mechanism even before searching "
         "(the GM reveals information regarding this).",
          [("Turbulent Heart", "Roll Will when suppressing desires. Define with the GM which new strong desires define "
          "your character — knowledge, lust, murder, etc.")]),

         ("Arbiter", "Justiciar Pathway",
             [("ST", "+1"), ("DX", "+1"), ("Voice", "+2 to all rolls to influence others through speech"), ("Will", "+1"), ("SPI", "+1")],
          [("Brawling/DX [Easy]", "+2"),
           ("Wrestling/DX [Average]", "+2")],
           "<b><font color='#C0392B'>Authority (1 SPI):</font></b> Arbiters possess a convincing charm and considerable authority, causing people to be "
           "more likely to believe and obey their commands and words. Spend 1 SPI to activate for the scene. "
           "When in conflict against an Arbiter, opponents waver — any NPC opposing the Arbiter in combat or social conflict must succeed at a "
           "Will roll (no modifier) or suffer -1 to attack rolls, defense rolls, and Quick Contests of Will "
           "against the Arbiter for the duration of the scene (or until they leave earshot). On a critical "
           "failure, the penalty increases to -2 and the opponent cannot take direct hostile action against "
           "the Arbiter for 1d turns. Player characters who fail the Will roll feel a strong pull to comply "
           "but are never mechanically forced — the choice remains theirs."),

         ("Lawyer", "Black Emperor Pathway",
            [("IQ", "+1"), ("SPI", "+1")],
          [("Law/IQ [Hard]", "+4"),
           ("Fast-Talk/IQ [Average]", "+3"),
           ("Diplomacy/IQ [Hard]", "+3")],
         "<b><font color='#C0392B'>Eloquence:</font></b> When a Lawyer argues with full conviction, all listeners must succeed at a Will roll "
         "(-3) or find themselves inclined to agree, even if the claim is logically weak. Strong contrary "
         "evidence can override this. On a critical failure of the listener's roll, they may adopt the "
         "Lawyer's position entirely for the rest of the scene."),
    ]

    for entry in seq9_pathways:
        title, pathway, stats, skills, ability = entry[:5]
        disadvantages = entry[5] if len(entry) > 5 else []

        story.append(sp(4))

        # Pathway header
        story += subsection(f"Sequence 9: {title}  ·  {pathway}")
        story.append(sp(2))

        # Build merged stat + disadvantages table (continuous, with divider)
        if stats or skills or disadvantages:
            stat_rows = [[Paragraph("Stat / Advantage", S['TableHeader']), Paragraph("Gain", S['TableHeader'])]]
            for k, v in stats:
                stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            divider_idx = None
            if disadvantages:
                divider_idx = len(stat_rows)
                # Divider row — matches header style (navy bg, cream text, bold)
                stat_rows.append([Paragraph("<b>Drawbacks</b>", S['TableHeader']),
                                  Paragraph("", S['TableHeader'])])
                for k, v in disadvantages:
                    stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            stat_t = Table(stat_rows, colWidths=[1.55*inch, 1.55*inch])
            stat_t.setStyle(table_style())
            if divider_idx is not None:
                stat_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, divider_idx), (-1, divider_idx), MID_NAVY),
                    ('LINEABOVE', (0, divider_idx), (-1, divider_idx), 0.5, GOLD),
                    ('TOPPADDING', (0, divider_idx), (-1, divider_idx), 3),
                    ('BOTTOMPADDING', (0, divider_idx), (-1, divider_idx), 3),
                ]))

            if skills:
                skill_rows = [[Paragraph("Skill", S['TableHeader']), Paragraph("Change", S['TableHeader'])]]
                for k, v in skills:
                    skill_rows.append([
                        Paragraph(k, S['TableCell']),
                        Paragraph(v, S['TableCell']),
                    ])
                skill_t = Table(skill_rows, colWidths=[2.4*inch, 0.85*inch])
                skill_t.setStyle(table_style())

                # Combo: merged stat table + skills table side by side
                combo = Table([[stat_t, skill_t]], colWidths=[3.2*inch, 3.35*inch])
            else:
                combo = Table([[stat_t]], colWidths=[6.4*inch])

            combo.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(combo)
        else:
            story.append(Paragraph("<i>No stat or skill changes at this Sequence.</i>", S['Body']))
        story.append(sp(3))

        # Ability block (with optional Reinforced box)
        main_ab, reinf_ab = split_reinforced(ability)
        render_ability_boxes(main_ab, reinf_ab, story)


    # ──────────────────────────────────────────────────────────────────────────────
    story += chapter("Chapter 10: Sequence 8 Potion Effects")
    story.append(body(
        "Sequence 8 represents a genuine step beyond the human baseline. Powers become more active "
        "and deliberate — no longer passive impressions or minor enhancements, but abilities that "
        "can change situations. Each entry below lists the correct canonical name from the source "
        "material, the pathway, key stat and skill changes, and abilities."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Reading these entries:</b> See <b>Chapter 9</b> for instructions on how to read a pathway entry. "
        "The same rules for potion-granted skills and attributes from Chapter 9 apply here."
    ))
    story.append(sp(2))

    seq8_pathways = [
        
            ("Clown", "Fool Pathway",
             [("ST", "+1"), ("DX", "+2"), ("SPI", "+2"),
            ("Perfect Balance", "+6 avoid knockdown; +2 Acrobatics, Climbing, Piloting")],
            [("Acrobatics/DX [Hard]", "+5"),
             ("Acting/IQ [Average]", "+5"),
             ("Throwing/DX [Average]", "+3"),
             ("Spiritual Intuition/SPI [Hard]", "+3")],
          "<b><font color='#C0392B'>Clown Agility:</font></b> The Clown's supernatural agility allows impossible acrobatics and contortions. "
         "They can land safely from any fall and move in ways that appear mechanically impossible. "
           "<b><font color='#C0392B'>Paper Daggers (1 SPI):</font></b> Turn sheets of paper as hard and sharp as steel, throwing them as flying daggers "
           "or holding them as knives. A paper dagger deals sw-1 cut and can pierce stone and bone. "
           "Paper daggers last for one attack only, then crumble to ordinary paper. "
           "<b><font color='#C0392B'>Clown Intuition:</font></b> Once per scene, when an enemy within 5 meters would successfully hit "
          "the Clown with a melee or ranged attack, the Clown may make one free Dodge or Step before "
          "the attack resolves. The GM may also grant a vision \"flash\" through walls or around corners "
          "once per session at their discretion — this reveals whether individuals are behind closed doors "
           "but not detailed information.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Spirit Vision (Reinforced):</font></b> Range increased to 15 m. Can now read surface emotional state and "
           "basic health of a target (injured, healthy, poisoned) without a roll.\n"
           "<b><font color='#C0392B'>Danger Intuition (Reinforced):</font></b> The vague warning now provides a rough direction and "
           "general distance of the threat (close / medium / far)."),

         ("Trickmaster", "Door Pathway",
          [("SPI", "+2")],
          [],
         "<b><font color='#C0392B'>Spellcasting (1 SPI):</font></b> All spells require a gesture and a word to cast. "
         "Most have a range of 10 m. The Trickmaster's magic is about performing tricks, not dealing damage — "
         "combat applications are secondary to deception and escape.\n"
         "<b><font color='#C0392B'>Flash:</font></b> A blinding white burst in a 3 m cone. "
         "HT or blinded 1d seconds (dazzled -1 vision on success).\n"
         "<b><font color='#C0392B'>Electric Shock:</font></b> A jolt through a held object (1 m touch) or as a 5 m ray. "
         "1d-3 burning (surge). HT or stunned 1 second.\n"
         "<b><font color='#C0392B'>Freezing:</font></b> Frost and thin ice from palm contact or a 10 m ray (arrow-speed). "
         "1d-3 crushing (cold). HT or -1 DX for 1d rounds.\n"
         "<b><font color='#C0392B'>Burning:</font></b> By rubbing their fingers, ignite flammable objects within 3 m. "
         "In combat, the same gesture projects a 3 m ray dealing 1d-3 burning that may ignite exposed combustibles.\n"
         "<b><font color='#C0392B'>Wind:</font></b> A sustained gust within 15 m. -2 to ranged attacks through it, "
         "extinguishes small flames, fills sails — variable effect at GM's call.\n"
         "<b><font color='#C0392B'>Fog:</font></b> A 5 m-radius bank of thick mist at 15 m range. "
         "-4 to vision-based rolls. Lasts 1 minute.\n"
         "<b><font color='#C0392B'>Tumble:</font></b> Treacherous footing in a 3 m radius at 10 m range. "
         "DX-2 or fall. Single target: DX-4 or fall.\n"
         "<b><font color='#C0392B'>Loud Noise:</font></b> A bang, roar, or explosion sound from a point within 30 m. "
         "Per-2 for 1 round; can mask conversation or trigger distractions.\n"
         "<b><font color='#C0392B'>Black Curtain:</font></b> Conjure a 3 m × 3 m sheet of lightless darkness. "
         "Blocks all sight through it (including darkvision and magical sight below Sequence 6). "
         "Lasts 1 minute. Shaped on conjuring (wall, dome, screen); cannot move after placement.\n"
         "<b><font color='#C0392B'>Escape Trick:</font></b> Instantly reposition 5 m in any direction using flash, "
         "curtain, or noise as cover. Observers lose track of you for 1 round.\n"
         "<b><font color='#C0392B'>Gas Transfer:</font></b> Instantly move toxic gases, smoke, or airborne poisons "
         "from a 2 m-radius area to another within 15 m. The gas persists for its remaining duration "
         "or 1 minute, whichever is shorter.\n"
          "<b><font color='#C0392B'>Object Manipulation (Bounce):</font></b> Move or bounce objects up to 2.5 kg "
           "within 5 m at Move 5 (no fine manipulation). An object may be thrown as an improvised weapon "
           "at DX+0, dealing thrust-2 crushing.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Door Opening (Reinforced):</font></b> The Trickmaster can now open spiritual or warded doors "
           "without a Ritualistic Magic roll (no penalty, automatic success for standard magical barriers). "
           "The bodily-door attack deals 1d+1 cut instead of 1d-1. The free Escape bonus against mundane "
           "restraints increases to +4."),


          ("Swindler", "Error Pathway",
             [("DX", "+1"), ("IQ", "+1"), ("Charisma +1", "+1 to reaction rolls and Influence skills"), ("SPI", "+2")],
            [("Fast-Talk/IQ [Average]", "+5"),
             ("Acrobatics/DX [Hard]", "+2"),
             ("Observation/Per [Average]", "+2")],
            "<b><font color='#C0392B'>Mental Disruption:</font></b> A Swindler can cause certain hallucinations to be experienced by a target. "
           "Pay 1 SPI, target rolls Will-3. Effects last up to 1 hour — the target continues experiencing "
           "the hallucination until the duration expires or they succeed on a Will-3 roll to break free (one attempt per hour). "
           "<b><font color='#C0392B'>Reminder:</font></b> Swindlers can steal spiritual materials from a 2m distance as long as it interacts with the spirit world.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Treasure Sense / Superior Observation (Reinforced):</font></b> The Marauder's Treasure Sense upgrades to Superior Observation. "
           "Range increases to 20 m. The Swindler can now read a target's micro-expressions and small movements — "
           "grant +2 to Detect Lies, Body Language, and Observation rolls against any visible target within range.\n"
           "<b><font color='#C0392B'>Theft (Stealing) (Reinforced):</font></b> Reminder distance increases to 5 m. The Swindler can also steal "
           "small non-material items (keys, amulets, vials) that are partially in contact with the spirit world."),

            ("Telepathist", "Visionary Pathway",
             [("IQ", "+1"), ("SPI", "+2"),
             ("Incisive Vision", "+4")],
         [("Psychology/IQ [Hard]", "+2"),
          ("Detect Lies/Per [Hard]", "+3"),
          ("Acting/IQ [Average]", "+3")],
           "<b><font color='#C0392B'>Mind Reading (1 SPI):</font></b> Roll Psychology vs Will. "
           "Reads surface thoughts and dominant emotions only. Will 13+ and Mind Shield = immune. "
           "On success, read undetected. On failure, target may sense something. "
           "After a successful read, roll Psychology to predict the target's next immediate actions. "
           "1 SPI/minute. Broken by line of sight, exhaustion, or injury.\n"
"<b><font color='#C0392B'>Enhanced Body Language Analysis:</font></b> "
"The Telepathist passively reads a target's deeper emotional states, spiritual condition, and hidden auras "
           "with no SPI cost and no roll required. This always-on ability detects hidden emotions, spiritual corruption, "
           "and Beyonder influence on the target's mind.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Body Language Analysis (Reinforced):</font></b> The Spectator's ability is now always-on at no cost. "
           "The Telepathist no longer needs to spend FP to read surface emotions and thoughts of a group — "
           "it happens automatically within 10 m. Against a single studied target, the Psychology roll for deep "
           "analysis gains +2 and requires only 1 minute of observation instead of the usual time."),

           ("Light Suppliant", "Sun Pathway",
            [("DR 2 (vs. fire/light)", "resistance to fire and light damage"), ("SPI", "+8")],
         [("Ritualistic Magic/IQ [Very Hard]", "+3 (Sun domain only — can summon pure beam of Fiery Light)")],
           "<b><font color='#C0392B'>Sunshine (3 SPI):</font></b> The Light Suppliant creates a light like the scorching Sun at noon "
           "in a 5-meter radius centred on themselves (or a point within 10 meters). "
           "Undead and ghosts in the area take 2d6 burning damage (HT/2 to halve). "
           "Living creatures in the area must roll HT or be blinded for 1d3 turns; "
           "those who succeed are merely dazzled (-1 to vision-based Per rolls) for 1 turn. "
            "The light persists for 1 minute and illuminates the area as full daylight. "
           "<b><font color='#C0392B'>Blessing (2 SPI):</font></b> The Light Suppliant blesses themselves and all allies within 5 meters. "
           "For the next 10 minutes, blessed targets gain +3 to all resistance rolls against Fear, Cold, Darkness, and Death effects "
           "(including supernatural abilities with those tags). Additionally, their weapon attacks deal +2 damage against undead creatures, "
           "and they are immune to passive fear/despair auras from low-level undead. "
          "<b><font color='#C0392B'>Daytime (2 SPI):</font></b> A Light Suppliant can allow the surrounding ten meters "
          "to receive Light, and this produced Light will naturally spread to further distances. Lasts 5 minutes. "
          "<b><font color='#C0392B'>Night Vision (1 SPI):</font></b> They can light two 'miniature Suns' in their eyes "
           "to see through Darkness and thus achieve Night Vision. "
           "<b><font color='#C0392B'>Evil Detection:</font></b> The Light Suppliant passively senses the presence of undead creatures and "
          "evil entities within roughly 10 meters, without any roll or activation. This is always on "
          "and cannot be suppressed — it manifests as an instinctive feeling of wrongness or revulsion. "
            "<b><font color='#C0392B'>Holy Water:</font></b> Through Ritualistic Magic (Sun domain), the Light Suppliant imbues a flask of water "
           "with Sun authority. Holy Water lasts until the next sunrise. On contact with a wraith, spirit, or undead creature, "
           "it deals 1d6 corrosion damage (ignores non-magical DR). On a living creature, it deals 1d-1 damage (no corrosion effect). "
          "As a full-round action, the Light Suppliant may attempt an Exorcism by splashing Holy Water on a possessed target "
           "or haunted area — roll Ritualistic Magic vs. the possessing entity's Will; on success, the entity is driven out. "
           "Holy Water may also purify cursed objects by immersion for 1 minute (Ritualistic Magic roll, -2 for powerful curses).\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Singing — Buff Effects (Reinforced):</font></b> The Light Suppliant's songs are more potent. "
           "Duration doubles to 20 minutes. Effects upgrade: Courage ignores Fear up to -5; Strength gives +2 ST-based rolls; "
           "Agility gives +2 DX-based rolls; Spiritual Recovery restores 2 SPI instead of 1."),

           ("Folk of Rage", "Tyrant Pathway",
              [("ST", "+2"), ("DX", "+2"), ("DR 2 (physical)", "scales thicken"), ("Amphibious", "full Basic Move swimming; no skill penalties underwater; still requires air"), ("SPI", "+1")],
         [],
         "<b><font color='#C0392B'>Wrath:</font></b> Accumulate 4 wrath by hitting or being hit (crits give +2 wrath). "
         "Intoxication generates +1 wrath/turn passively. At 4 wrath, choose one: \n"
         "<b><font color='#C0392B'>Rampage:</font></b> On your turn, make 3 separate attack rolls at -0/-2/-4 cumulative penalty (first at no penalty, second at -2, third at -4). Wrath resets. Suffer -2 active defense until next turn. \n"
         "<b><font color='#C0392B'>Raging Blow:</font></b> A single devastating strike at +3 to hit, +3 damage, ignoring 2 DR. "
          "Critical hit forces a knockdown roll. Wrath resets. Lose 1 FP.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Phantom Scales (Reinforced):</font></b> The Sailor's illusory scales thicken into DR 2 (physical) as noted in the stat block. "
           "Grappling penalty increases to -4 — the Folk of Rage is extremely slippery.\n"
           "<b><font color='#C0392B'>Aquatic Affinity (Reinforced):</font></b> Upgraded to full Amphibious (per stat block). "
           "Can now stay submerged for 30 minutes without air and dive to 30 m without protection."),

           ("Student of Ratiocination", "White Tower Pathway",
             [("IQ", "+2"), ("Fluid Intellect", "IQ - 2 to unfamiliar IQ rolls; can attempt VH skills"), ("SPI", "+2")],
           [("Observation/Per [Average]", "+2"),
            ("Ritualistic Magic/IQ [Very Hard]", "+4")],
            "No special abilities at this Sequence — the Student of Ratiocination's power is pure cognitive enhancement.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Reading — Knowledge Wealth (Reinforced):</font></b> The Reader's recall improves. "
           "The IQ roll for general knowledge gains +2. Obscure material penalties are reduced by 2 (minimum -0). "
           "Language learning time is reduced to 1/3 normal (instead of 1/2)."),

        ("Listener", "Hanged Man Pathway",
           [("SPI", "+3"), ("Acute Hearing", "+2 to Hearing rolls; detect faint sounds, eavesdrop through walls, identify speech in noise")],
         [("Ritualistic Magic/IQ [Very Hard]", "+3"),
          ("Occultism/IQ [Average]", "+3"),
          ("Hidden Lore (Supernatural Beings)/IQ [Average]", "+3"),
           ("Spiritual Perception/SPI [Average]", "+2")],
        "<b><font color='#C0392B'>Listening (Passive):</font></b> Listeners always hear both ordinary people and even Low-Mid Sequence Beyonders within a radius of 80 meters. "
        "The closer they are to the sound of a source, the more they will be affected and receive more discernable information from it. "
        "This applies vice versa if further away. Cannot be turned off at this sequence. \n"
        "At GM's discretion, roll 3d6 if you have passively listened to something from a higher/powerful source. "
        "GM decides on what to roll against depending on severity and how close you are in proximity to the source. "
         "Failure against check: Gain 1-3 CoR depending on severity and proximity. "
        "Critical Failure: Listen to the ravings of the True Creator or another existence on the same level. \n"
        "<b><font color='#C0392B'>Listening (Active):</font></b> Listeners who intentionally focus on a single source with their Listening "
        "are now in a state of active listening. Spend 1 SPI, roll 3d6: if below 13 you will listen to your targeted source "
        "and receive clear information from them. 14+ will result in hearing the True Creator or another existence on the same level. "
         "What you gain depends on the source, range of success, and how clear the intent is.\n"
         "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
         "<b><font color='#C0392B'>Knowledge (Honorifics) (Reinforced):</font></b> The Listener gains two additional honorific names "
         "for other secret existences. The GM chooses or creates these based on the campaign. "
         "All Spiritual Perception rolls gain +2 from constant exposure to esoteric whispers.\n"
         "<b><font color='#C0392B'>Spiritual Perception (Reinforced):</font></b> The passive range of spiritual awareness expands to 50 m. "
         "The Listener can automatically detect active Beyonder abilities within this range (no roll required for obvious effects)."),

         ("Midnight Poet", "Darkness Pathway",
            [("SPI", "+3")],
           [("Brawling/DX [Easy]", "+3"),
           ("Guns (any)/DX [Easy]", "+2"),
            ("Climbing/DX [Average]", "+2"),
           ("Ritualistic Magic/IQ [Very Hard]", "+2")],
          "<b><font color='#C0392B'>Nocturnality (passive):</font></b> +1 to all rolls during the night.\n"
          "<b><font color='#C0392B'>Midnight Poem — Spell Effects:</font></b> By reciting a poem about the night or the Evernight Goddess "
         "(one full round), the Midnight Poet manifests one of the effects below. All spells cost 2 SPI. "
        "Roll Ritualistic Magic for all spells. "
         "<b><font color='#C0392B'>Tranquilize:</font></b> Target feels deeply calm and peaceful. "
         "They suffer -2 to all aggressive or hostile actions (attacks, intimidation, etc.) for 1d6 turns. "
         "Will roll (-2) to resist. \n"
          "<b><font color='#C0392B'>Lullaby:</font></b> Puts all who hear the Lullaby to sleep (within earshot, ~20m radius). "
          "Only Beyonders with strong spiritual perception or Cogitation abilities may resist — roll either Spiritual Perception/SPI (Hard) "
          "or Will (-2), whichever is higher. Ordinary mortals and spiritually weak beings fall asleep automatically with no roll. "
          "Sleep lasts 1d minutes unless shaken awake. Those who resist fall serene and find it hard to evoke or express emotions "
          "(-1 to all emotional reaction rolls and social skill rolls) for 1 minute. \n"
         "<b><font color='#C0392B'>Pacify:</font></b> Target loses all desire to act — goes limp and unresponsive. "
         "Cannot take offensive actions; can still defend. Lasts 1d3 turns. Will roll (-3) to resist. \n"
         "<b><font color='#C0392B'>Fear:</font></b> Target is filled with supernatural dread. "
         "Suffers -2 to all rolls and must succeed on a Will (-2) roll each turn to approach the Midnight Poet. "
          "Lasts 1d6 turns. Will roll (-2) to resist entirely.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Nocturnality (Reinforced):</font></b> The bonus during night increases to +2 (instead of +1). "
           "In total darkness (no moon or stars), the bonus becomes +3.\n"
           "<b><font color='#C0392B'>Danger Detection in the Dark (Reinforced):</font></b> The bonus in low-light environments increases to +4. "
           "The Midnight Poet now senses danger in darkness up to 20 m away with pin-point direction."),

          ("Gravedigger", "Death Pathway",
            [("DX", "+2"), ("SPI", "+3")],
          [("Occultism/IQ [Average]", "+4"),
           ("Hidden Lore (Spirits)/IQ [Average]", "+3"),
           ("Ritualistic Magic/IQ [Very Hard]", "+2")],
          "<b><font color='#C0392B'>Spirit Communication:</font></b> The Gravedigger can communicate with nearby spirits and command them to do "
          "simple actions — grasping, immobilizing targets, or revealing hidden information. Range 10 ft, duration 1 "
          "minute per use. Costs 1 SPI per use. To immobilize a target, the spirit makes a ST contest vs. the target's ST; "
          "if the spirit wins, the target is grappled (per GURPS grappling rules) for the duration. Use spirit's ST "
          "(typically 8–12 for ordinary spirits; GM sets for powerful spirits). "
           "<b><font color='#C0392B'>Eye of Death (1 FP):</font></b> Activate to examine an Undead or Spirit creature. "
           "GM reveals one specific vulnerability (e.g. \"weak to fire,\" \"cannot withstand holy water\"). "
           "For the rest of the scene: +2 to hit, +2 damage, ignore 2 DR against that creature. "
           "<b><font color='#C0392B'>Spirit Vision (Enhanced):</font></b> The Gravedigger's Spirit Vision is enhanced — they can now examine different parts of "
           "a Soul to deduce a target's health and emotional state, detect magical auras, and perceive spirits passively.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Undead Deterrence (Reinforced):</font></b> Now affects undead with SPI ≤ yours + 2. "
           "Controlled undead roll at -4 instead of -2 to act against you.\n"
           "<b><font color='#C0392B'>Undead Detection (Reinforced):</font></b> Range increases to 25 m. "
           "The Gravedigger can identify the specific type of undead (ghost, zombie, wraith, etc.) without a roll."),

           ("Pugilist", "Twilight Giant Pathway",
             [("ST", "+3"), ("HT", "+1"), ("DR 1 (all)", "resistance to all physical damage"), ("High Pain Threshold", "+3 to HT rolls to avoid knockdown/stun; no shock penalty from injury"), ("SPI", "+1")],
          [("Brawling/DX [Easy]", "+5"),
           ("Wrestling/DX [Average]", "+3"),
           ("Intimidation/Will [Average]", "+2")],
         "<b><font color='#C0392B'>Iron Body:</font></b> The Pugilist's iron-hard body can resist supernatural forces. "
            "When taking damage from a spell, Beyonder ability, or other supernatural source, the Pugilist may "
            "spend 1–3 FP as a reactive free action to reduce the incoming damage by 2 per FP spent (applied "
            "after any resistance roll, before DR). The Pugilist decides how much FP to spend after seeing "
            "the damage roll but before the damage is applied.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Combat Mastery (Reinforced):</font></b> The Warrior's universal weapon proficiency upgrades. "
           "The Pugilist treats any weapon as known at effective DX immediately (no warm-up needed), matching the "
           "Weapon Master's instant proficiency but limited to melee weapons only. Ranged weapons still need one "
           "use to reach full proficiency (as the Warrior's original ability)."),

           ("Instigator", "Demoness Pathway",
             [("DX", "+1"),
              ("Per", "+1"),
               ("Charisma +2", "+2 to reaction rolls and Influence skills"),
               ("SPI", "+1")],
          [("Fast-Talk/IQ [Average]", "+4"),
           ("Psychology/IQ [Hard]", "+4"),
           ("Acting/IQ [Average]", "+3")],
            "<b><font color='#C0392B'>Instigation — Passive:</font></b> The Instigator senses the emotions, desires, and "
            "hidden malice of anyone within 10 meters — roll Per (no modifier). On success, hidden intent, suppressed anger, and unacted "
           "grievances are revealed. Social situations are read instinctively; on a successful Per roll the Instigator knows "
           "who is the weakest link in a room.\n"
           "<b><font color='#C0392B'>Instigation — Active:</font></b> The Instigator must speak to or gesture at the target to surface "
           "their deepest suppressed desires and grievances. If using only gestures (no speech), "
           "the Instigator rolls at -4. "
           "Roll Fast-Talk (at -6) vs. target's Will. "
           "On success, the target acts on that desire within 1d minutes, believing the impulse is entirely "
           "their own.\n"
           "<b><font color='#C0392B'>Crowd Effect:</font></b> Igniting one individual is enough. Instigated targets become vectors "
           "themselves, drawing others into escalating conflict. The Instigator need not remain present once "
           "the spark is lit.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Feather Fall (Reinforced):</font></b> The Instigator can now glide up to 2 m horizontal per 3 m vertical, "
           "and may arrest a fall from any height instantly as a free action (no SPI cost).\n"
           "<b><font color='#C0392B'>Shadow Concealment (Reinforced):</font></b> Penalty to detect the Instigator in shadows increases to -5 "
           "(from -3) when stationary, and -2 (from -1) when moving slowly."),

          ("Provoker", "Red Priest Pathway",
            [("ST", "+1"), ("DX", "+1"), ("SPI", "+1"), ("Per", "+1"),
            ("Fast Healer (Limited)", "recovers 1 extra HP per 2 days of rest")],
         [],
         "<b><font color='#C0392B'>Spirit Vision (1 SPI per minute, standard):</font></b> The Provoker activates Spirit Vision with a simple gesture — quickly and "
         "discreetly. No concentration or obvious ritual required.\n"
         "<b><font color='#C0392B'>Provocation:</font></b>\n"
         "<b><font color='#C0392B'>Vague Insult:</font></b> These insults can target an individual or multiple people and are made up "
         "from general terms and insulting words, such as, but not limited to: \"Fuck you\", \"Idiot\", \"Dogshit\". "
          "Target must succeed at a Will roll (-2) to resist being provoked. Failing will cause the target to only "
          "target the Provoker for 1 turn.\n"
          "<b><font color='#C0392B'>Detailed Insult:</font></b> The Provoker uses a specific observation as a base for constructing "
          "an insult, for example: \"That's the first warm reception you've had in years.\" "
          "Target must succeed at a Will roll (-4) to resist being provoked. Failing will cause the target to only "
          "target the Provoker for 2 turns. The Provoker can target up to 2 subjects at once, but there must be a "
          "correlation between the subjects and the core of the insult.\n"
          "<b><font color='#C0392B'>Unique Insult:</font></b> This must be based on something that is a part of the target, and they "
          "know it — that is why it hurts their ego especially. Target must succeed at a Will roll (-6) to resist "
          "being provoked. Failing will cause the target to only target the Provoker for 3 turns.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Environment Memory (Reinforced):</font></b> The Provoker can now sense alterations within 20 m (double the original range). "
           "Natural traps are detected automatically at 5 m without any roll.\n"
           "<b><font color='#C0392B'>Survival Knowledge (Reinforced):</font></b> Hemostatic poultices now restore 1d+1 HP to a bleeding wound "
           "(or 3 HP if not bleeding). The Provoker can identify poisonous plants and animal organs "
           "instinctively regardless of terrain type."),

              ("Melee Scholar", "Hermit Pathway",
                [("DX", "+2"), ("ST", "+1"), ("Combat Reflexes", "+1 to all active defenses, +6 to recover from stun, never freeze in surprise"), ("SPI", "+1")],
           [("Occultism/IQ [Average]", "+4"),
            ("Shortsword/DX [Average]", "+3"),
            ("Broadsword/DX [Average]", "+2"),
            ("Ritualistic Magic/IQ [Very Hard]", "+3"),
            ("Hidden Lore (any)/IQ [Average]", "+3")],
           "<b><font color='#C0392B'>Combat Prying (2 SPI):</font></b> Pry into the mystery of combat and learn from a target. "
           "You gain a permanent +1 in the relevant skill.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Eyes of Mystery Prying (Reinforced):</font></b> The always-on passive penalty to Dream/Illusion rolls against you "
           "increases to -3. Active use costs 1 SPI as before but now also reveals a target's combat-relevant weaknesses "
           "(e.g., low HP, low defense, specific damage vulnerability) when examining their Ether Body.\n"
           "<b><font color='#C0392B'>Quick Rituals (Reinforced):</font></b> Penalty for rushed rituals is decreased by 4 (from 3)."),

             ("Archaeologist", "Paragon Pathway",
              [("IQ", "+1"), ("ST", "+1"), ("HT", "+1"), ("Fluid Intellect", "IQ - 2 to unfamiliar IQ rolls; can attempt VH skills"), ("SPI", "+1")],
          [("Ritualistic Magic/IQ [Very Hard]", "+1"),
           ("History/IQ [Hard]", "+3"),
           ("Survival (any)/Per [Average]", "+2"),
           ("Occultism/IQ [Average]", "+3")],
         "<b><font color='#C0392B'>Artifact Lore:</font></b> The Archaeologist can identify the age, origin, and "
         "purpose of any historical or mystical artifact by sight and touch (IQ roll, no penalty). "
         "Common items are identified automatically. Rare or Sealed Artifacts require a History or "
         "Occultism roll at -2 to -6 depending on obscurity.\n"
          "<b><font color='#C0392B'>Ruin Navigation:</font></b> The Archaeologist instinctively navigates ancient ruins, "
           "underground structures, and forgotten sites without penalty. Traps, hidden passages, and "
           "structural hazards in such places are detected on a Perception roll at +2.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Recall — Total Memory (Reinforced):</font></b> The Savant's perfect recall now extends to tactile and "
           "spatial memory — the Archaeologist can recall the exact feel of an object touched once and the "
           "precise layout of any space visited. The IQ roll to understand a mechanism drops to 30 seconds "
           "(from 1 minute).\n"
           "<b><font color='#C0392B'>Rapid Analysis (Reinforced):</font></b> Improvised devices and repairs take 1/4 normal construction time (from 1/2)."),

          ("Robot", "Wheel of Fortune Pathway",
            [("SPI", "+3"),
             ("IQ", "+1"),
             ("DX", "+2"),
            ("Divination Affinity", "+2 to all Divination and Anti-Divination rolls"),
            ("Danger Sense", "GM warns of threats just before they strike; surprise is negated")],
          [("Mathematics (Applied)/IQ [Hard]", "+4"),
           ("Brawling/DX [Easy]", "+2"),
           ("Guns (any)/DX [Easy]", "+2")],
          "<b><font color='#C0392B'>Danger Calculation:</font></b> "
           "The Robot can roughly guess which direction danger is coming from, "
           "even without making a roll. This instinctive sense of imminent threats "
            "and their origin complements the passive Danger Sense advantage.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Foresight (Reinforced):</font></b> The Monster's once-per-session vision increases to twice per session. "
           "The Robot can also attempt to trigger a vision deliberately once per day by "
           "concentrating for 1 minute (SPI roll at -4; success provides a vague glimpse).\n"
           "<b><font color='#C0392B'>Danger Premonition (Reinforced):</font></b> The passive sense now includes supernatural threats "
           "(curses, fate-based traps, spiritual attacks) and provides a 2-second warning before danger strikes, "
           "enough to take a Defensive maneuver."),

             ("Doctor", "Mother Pathway",
             [("SPI", "+2"), ("Ancient Hermes", "Fluent — can speak, read, and write this dead mystical language")],
          [("Physician/IQ [Hard]", "+5"),
            ("Surgery/IQ [Very Hard]", "+3"),
           ("Pharmacy/IQ [Hard]", "+3"),
           ("First Aid/IQ [Easy]", "+3"),
           ("Diagnosis/IQ [Hard]", "+3")],
          "<b><font color='#C0392B'>Soul Suture (1 SPI):</font></b> The Doctor's signature ability. By spending 1 SPI and making a "
           "Physician roll (no penalty), the Doctor repairs spiritual and physical damage, healing "
           "1d6+2 HP in a conscious, stable target over 10 minutes of focused treatment. Cannot be "
           "used in combat or on an actively moving target. Critical success heals 2d6+2 HP. Soul "
           "Suture affects living targets only — it cannot deal damage and cannot be used offensively.\n"
           "<b><font color='#C0392B'>Spirit Vision (Enhanced):</font></b> Spirit Vision now activates automatically at no SPI cost "
           "when examining a patient — the Doctor sees their Ether Body, spiritual injuries, and "
           "emotional state. All Spirit Vision skill rolls and Diagnosis rolls gain +2 while "
           "evaluating or treating a patient.\n"
           "<b><font color='#C0392B'>Soothe (2 SPI):</font></b> When a target within arm's reach has just failed a SPI roll that "
            "caused CoR gain, the Doctor may spend 2 SPI and make a Physician roll (-2 penalty) "
            "to soothe the spiritual wound, reducing the net CoR gain by 1. Must be used within "
           "1 minute of the event.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Farming Tools Proficiency (Reinforced):</font></b> The Planter's tool bonus increases to +4. "
           "Additionally, the Doctor can apply First Aid or perform emergency procedures with any "
           "tool at hand — improvised medical tools suffer no penalty."),

             ("Beast Tamer", "Moon Pathway",
              [("ST", "+2"), ("DX", "+1"), ("Empathy (animals)", "sense animal emotions and intent"), ("SPI", "+2")],
         [("Animal Handling (any)/IQ [Average]", "+5")],
         "<b><font color='#C0392B'>Animal Senses:</font></b> They can read the thoughts of, utilize the senses of, communicate to, "
         "and control Animals, gradually Taming them and making them into their assistants. "
         "No SPI cost. Range: within 50m. Can control up to (IQ÷2) animals at once through concentration.\n"
          "<b><font color='#C0392B'>Passive — Tamed Animal Potion Boost:</font></b> Animals tamed by a Beast Tamer gain +4 to "
           "rolls involving drinking potions.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Spirit Vision — Ether Body (Reinforced):</font></b> The Apothecary's Spirit Vision now also "
           "reads the health and emotional state of animals within 50 m at no SPI cost. "
           "When examining a patient (animal or human), the Physician bonus increases to +3.\n"
           "<b><font color='#C0392B'>Potion Concoction (Reinforced):</font></b> The penalty for all potions is reduced by 1. "
           "The Beast Tamer can carry up to SPI × 1.5 doses (round up)."),

             ("Unwinged Angel (Coldblooded)", "Abyss Pathway",
              [("ST", "+2"), ("SPI", "+1"), ("Will", "-1")],
         [],
          "<b><font color='#C0392B'>Abyss Power Roll:</font></b> The Unwinged Angel's spells are innate demonic abilities, not conscious spiritual expenditures. "
          "Instead of paying SPI, each spell requires a designated FP cost to activate. "
          "You may also sacrifice 1 HP to fuel any spell.\n"
          "<b><font color='#C0392B'>Spell Selection:</font></b> At the start of each day, the Unwinged Angel rolls 3d6. "
          "Less than 8: pick 3 spells. Between 8 and 14: pick 2 spells. Greater than 14: pick only 1 spell.\n"
          "<b><font color='#C0392B'>Spell-Like Abilities (Resisted by HT):</font></b>\n"
           "<b><font color='#C0392B'>Crown of Contempt (1 FP):</font></b> A dark aura visibly pulses outward like a wave of cold. Anyone within 5 meters who fails HT is pushed back 1 meter and suffers -2 to their next attack roll.\n"
           "<b><font color='#C0392B'>Poisonous Flames (2 FP):</font></b> Sickly-colored fire conjured from the palms. Melee touch attack. 1d6 toxic damage on contact, then 1d6-2 for 2 turns. Cannot be smothered. Ignores 1 DR.\n"
          "<b><font color='#C0392B'>Toxic Black Smoke (1 FP):</font></b> Black cloud exhaled toward a chosen point within 10 meters, filling a 3-meter radius. 1d6-2 toxic damage per turn to anyone inside. Lasts 3 turns.\n"
          "<b><font color='#C0392B'>Slowness (1 FP):</font></b> The killer raises both arms and presses their palms sharply downward. The target visibly sinks, dragging as though moving through deep water. -1 Basic Speed, -1 Basic Move for 1d6 turns.\n"
          "<b><font color='#C0392B'>Rending Grasp (2 FP):</font></b> The killer's hand blackens visibly as they reach for the target. On contact, 1d6 FP is torn away — observers see a faint luminescence pulled from the victim toward the killer's hand.\n"
          "<b><font color='#C0392B'>Fevered Haze (2 FP):</font></b> The killer exhales a shimmer of unnatural heat. Targets within 2 meters who fail HT suffer -2 DX and -1 Basic Move for 1d3 turns, visibly unsteady.\n"
          "<b><font color='#C0392B'>Fracture (2 FP):</font></b> A visible crack of dark energy crosses the air toward the target. Their next successful attack deals half damage — the blow lands visibly weaker than it should.\n"
          "<b><font color='#C0392B'>Curses (Resisted by Will. Requires verbal utterance):</font></b>\n"
          "<b><font color='#C0392B'>Mirror of Inadequacy (2 FP):</font></b> A single cutting observation that collapses the target's confidence. -2 to all rolls for 1d6 turns on a failed Will roll.\n"
          "<b><font color='#C0392B'>Spiritual Covetousness (1 FP):</font></b> Awakens a maddening hunger in the target for something they already possess. On a failed Will roll, they spend their next turn protecting or hoarding rather than acting offensively.\n"
          "<b><font color='#C0392B'>Hollow Craving (1 FP):</font></b> Floods the target with a desperate want for something they lack. -1 Will and -1 Perception for 1d3 turns as attention fractures.\n"
          "<b><font color='#C0392B'>Sever the Bond (2 FP):</font></b> One target perceives a chosen ally as a threat or rival for 1 turn — cannot assist, aid, or defend them. On a critical fail, may act against them.\n"
          "<b><font color='#C0392B'>Drain (1 FP):</font></b> The target's body overconsumes its own energy. Lose 2 FP immediately.\n"
          "<b><font color='#C0392B'>Stoke the Coal (1 FP):</font></b> Inflames the target's existing frustration until it becomes unbearable. -2 to all rolls requiring patience or restraint. Must make a Will roll to avoid reacting aggressively to their nearest ally's next action.\n"
             "<b><font color='#C0392B'>Leaden Soul (2 FP):</font></b> The target's movement becomes impossibly heavy. -1 Basic Speed, -1 Basic Move. Must succeed on a Will roll each turn to take any action beyond defending. Lasts 1d3 turns.\n"
             "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
             "<b><font color='#C0392B'>Criminal Proficiency (Reinforced):</font></b> The Criminal's universal weapon talent expands. "
             "The Unwinged Angel now treats all improvised weapons as Brawling +2 (instead of just Brawling). "
             "Any firearm is fired at effective DX+1 immediately. Poison-use rolls gain +2.",
             [("Bloodlust", "Must go for killing blows in combat. IQ roll to accept surrender or take prisoners."),
             ("Callous", "-3 to social skill rolls when warmth or empathy is required."),
             ("Compulsive Behavior (Indulge Evil Desires) SC 6", "When an opportunity to commit an evil act (murder, torture, betrayal, etc.) presents itself, roll 3d6 ≤ 6 or indulge fully."),
             ("Unsettling Appearance", "-1 to all reaction rolls due to unsettling appearance")]),

           ("Lunatic", "Chained Pathway",
            [("ST", "+2"), ("HT", "+1"), ("SPI", "+1"), ("Berserk (voluntary)", "can choose to sacrifice rationality for power; not forced involuntarily"), ("DR 2 (physical)", "resistance to physical damage"), ("Rapid Healing", "+5 to daily HT rolls to recover HP"), ("Divination/Spirit Channel Resistance", "body and soul are Bound; Divination and Spirit Channeling targeting the Lunatic are at -4")],
         [("Brawling/DX [Easy]", "+4"),
          ("Intimidation/Will [Average]", "+3"),
          ("Survival (any)/Per [Average]", "+2"),
          ("Wrestling/DX [Average]", "+2")],
         "<b><font color='#C0392B'>Lunatic's Curse:</font></b> From this Sequence onward, the Chained Pathway Beyonder begins to be "
         "affected by supernatural Curses that accumulate from within. At Sequence 8, the Lunatic "
         "loses control more easily than most Beyonders — all CoR thresholds for losing "
         "control are reduced by 2. In exchange: when injured below half HP, the Lunatic automatically "
         "enters an empowered state (uncontrolled) — ST +3, HT +2, ignore all pain effects, and "
         "attack everything nearby. This state lasts until the fight ends or they succeed on a "
         "Will-4 roll. Escape Mastery from Sequence 9 is fully retained and operates against "
           "spiritual restraints as well as mundane ones at +2.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Knowledge — Criminal Expert (Reinforced):</font></b> The Prisoner's criminal mastery sharpens. "
           "Improvised weapons gain +1 to damage (in addition to no penalty). "
           "Escape rolls against supernatural confinement (spiritual bonds, curses that restrain) are rolled at "
           "full skill without penalty. The hidden-exit awareness expands to 20 m range."),

            ("Sheriff", "Justiciar Pathway",
             [("IQ", "+1"), ("Per", "+2"),              ("Eidetic Memory", "+5 to remember things after one reading; near-perfect recall"), ("SPI", "+1")],
            [("Guns (any)/DX [Easy]", "+3"),
             ("Shortsword/DX [Average]", "+2"),
             ("Brawling/DX [Easy]", "+2"),
            ("Criminology/IQ [Average]", "+3"),
            ("Tracking/Per [Average]", "+2")],
         "<b><font color='#C0392B'>Evil Sense:</font></b> Passive. The Sheriff automatically senses the presence of things related to "
          "Evil, Disorder, and Madness within 25 meters. \"Unprotected\" refers to entities not warded by "
          "anti-divination, mind shielding, or similar concealment. The sense is directional (the Sheriff knows "
          "the rough direction of the source) but does not provide precise location through walls. "
          "High-Sequence Beyonders (Seq 5+) or those using active concealment may roll Will vs. the Sheriff's Per "
          "to hide from this sense.\n"
          "<b><font color='#C0392B'>Jurisdiction:</font></b> The Sheriff claims a region as their own by asserting authority, not by spending spirituality. "
          "Make an <b>Intimidation or Administration roll</b> contested by the Will of the region's inhabitants (use the highest Will among them). "
          "On success, the Sheriff gains jurisdiction — a conceptual anchor that lasts until they designate a new jurisdiction. "
          "On failure, the inhabitants resist the Sheriff's authority; may retry after 24 hours. "
          "Jurisdiction works as an extension of Sheriff's powers. \n"
        "<b>Rules for Jurisdiction:</b> \n"
        "1. You must know the region very well. \n"
        "2. You may not designate a region bigger than a small town. \n"
        "3. You may not designate a region smaller than one room. \n"
        "4. Designated region must have at least one human inhabitant other than yourself. \n"
        "5. Exception to Rule 2: If granted an official post/ownership/governance over a region, "
        "the jurisdiction may be up to 5x the size. \n"
        "<b>This works in 3 stages:</b> \n"
        "<b>Stage 0 — No trust from people/new to jurisdiction:</b> No Benefits despite designating jurisdiction. \n"
        "<b>Stage 1 — Mixed:</b> Depending on the % of people who support you and trust you. These effects materialize: \n"
        "• Grants Combat Reflexes while inside the region. \n"
        "• Sense Extension — Grants extension to your otherworldly senses such as Evil Sense, Death Sense, etc. \n"
        "• Region Assistance — Grants +2 to persuasive rolls for inhabitants that support you in your jurisdiction. \n"
        "<b>Stage 2 — Full Support of all residents:</b> Along with all previous things, you now gain +1 to all your stats as long as you're in range of your jurisdiction. "
         "Grants Danger Sense while inside the region.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Authority (Reinforced):</font></b> The Arbiter's authority strengthens. The Will penalty for opponents "
           "increases to -2 (from -1) within the Sheriff's Jurisdiction area. The activation cost remains 1 SPI for the scene."),

              ("Barbarian", "Black Emperor Pathway",
               [("ST", "+3"), ("HT", "+1"), ("Will", "+2"), ("SPI", "+1")],
          [("Brawling/DX [Easy]", "+3"),
           ("Wrestling/DX [Average]", "+3")],
          "<b><font color='#C0392B'>Physical Enhancement:</font></b> A Barbarian's physical strength and constitution "
          "break the 'rules' of a normal human body. ST and HT-based rolls gain +2 in situations involving "
          "feats of raw force, endurance, or breaking through physical barriers.\n"
            "<b><font color='#C0392B'>Mental Resistance:</font></b> Barbarians possess a high resistance to psychological "
            "influences — mind control and fear-based effects against them "
            "suffer -4. This is passive and always active. Problems that cannot be solved by the law will "
           "be solved by force.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Eloquence (Reinforced):</font></b> The Lawyer's silver tongue now works through intimidation "
           "as effectively as persuasion. The Barbarian may substitute Intimidation for Fast-Talk when using "
           "Eloquence — listeners still roll Will at -3, but the argument may be a growled threat rather than "
           "a smooth logical claim. Strong evidence is still required to override the effect."),

    ]

    for entry in seq8_pathways:
        title, pathway, stats, skills, ability = entry[:5]
        disadvantages = entry[5] if len(entry) > 5 else []

        story.append(sp(4))
        story += subsection(f"Sequence 8: {title}  ·  {pathway}")
        story.append(sp(2))

        # Build merged stat + disadvantages table (continuous, with divider)
        if stats or skills or disadvantages:
            stat_rows = [[Paragraph("Stat / Advantage", S['TableHeader']), Paragraph("Gain", S['TableHeader'])]]
            for k, v in stats:
                stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            divider_idx = None
            if disadvantages:
                divider_idx = len(stat_rows)
                # Divider row — matches header style (navy bg, cream text, bold)
                stat_rows.append([Paragraph("<b>Drawbacks</b>", S['TableHeader']),
                                  Paragraph("", S['TableHeader'])])
                for k, v in disadvantages:
                    stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            stat_t = Table(stat_rows, colWidths=[1.55*inch, 1.55*inch])
            stat_t.setStyle(table_style())
            if divider_idx is not None:
                stat_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, divider_idx), (-1, divider_idx), MID_NAVY),
                    ('LINEABOVE', (0, divider_idx), (-1, divider_idx), 0.5, GOLD),
                    ('TOPPADDING', (0, divider_idx), (-1, divider_idx), 3),
                    ('BOTTOMPADDING', (0, divider_idx), (-1, divider_idx), 3),
                ]))

            if skills:
                skill_rows = [[Paragraph("Skill", S['TableHeader']), Paragraph("Change", S['TableHeader'])]]
                for k, v in skills:
                    skill_rows.append([
                        Paragraph(k, S['TableCell']),
                        Paragraph(v, S['TableCell']),
                    ])
                skill_t = Table(skill_rows, colWidths=[2.4*inch, 0.85*inch])
                skill_t.setStyle(table_style())

                # Combo: merged stat table + skills table side by side
                combo = Table([[stat_t, skill_t]], colWidths=[3.2*inch, 3.35*inch])
            else:
                combo = Table([[stat_t]], colWidths=[6.4*inch])

            combo.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(combo)
        else:
            story.append(Paragraph("<i>No stat or skill changes at this Sequence.</i>", S['Body']))
        
        story.append(sp(3))

        # Ability block (with optional Reinforced box)
        main_ab, reinf_ab = split_reinforced(ability)
        render_ability_boxes(main_ab, reinf_ab, story)

    story.append(PageBreak())



    story += chapter("Chapter 11: Sequence 7 Potion Effects")
    story.append(body(
        "Sequence 7 represents significant advancement beyond the baseline Beyonder. Powers become "
        "formidable and specialised — each pathway's unique nature fully manifests. Each entry below "
        "lists the correct canonical name from the source material, the pathway, key stat and skill "
        "changes, and abilities."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Reading these entries:</b> See <b>Chapter 9</b> for instructions on how to read a pathway entry. "
        "The same rules for potion-granted skills and attributes from Chapter 9 apply here."
    ))
    story.append(sp(2))

    seq7_pathways = [

        # ── Fool Pathway ──

           ("Magician", "Fool Pathway",
            [("DX", "+1"),
             ("SPI", "+2"),
             ("Per", "+1")],
           [("Sleight of Hand/DX [Hard]", "+4")],
           "<b><font color='#C0392B'>Damage Transfer (1 SPI):</font></b> "
           "Free action when you take damage to a vital hit location (skull, vitals, spine). "
           "Transfer the wound to a non-vital area (arm, leg, hand) — the damage still applies "
           "but no longer counts as a vital hit. Each wound can only be transferred once. "
           "If the damage would have been instantly fatal, it becomes a major wound instead. "
           "Cannot transfer wounds to objects or other creatures.\n"
            "<b><font color='#C0392B'>Flaming Jump (1 SPI):</font></b> "
           "One Ready maneuver to focus on any flame within 30m, then step into any fire "
           "source (candle, torch, campfire) and emerge from a different flame within range. "
           "You are immune to ordinary fire damage during the jump. This works on Beyonder "
           "flames (Pyromaniac, Witch's Black Flames) as well — if one exists within range, "
           "you may use it as a destination. Cannot be used in areas cut off from the Spirit World.\n"
           "<b><font color='#C0392B'>Air Bullet (1 SPI):</font></b> "
           "Snap fingers or mimic a gunshot as an Attack maneuver. Fires an invisible compressed-air "
           "projectile that deals 2d-1 pi damage (range 15/30). Uses Sleight of Hand or DX to hit. "
           "No physical ammunition needed — the bullet is pure spirituality. Damage improves to "
           "2d pi once the potion is fully digested (GM discretion).\n"
            "<b><font color='#C0392B'>Paper Figurine Substitute (3 SPI):</font></b> "
            "Requires a pre-prepared paper figurine on your person. When you would take damage "
            "from any source (attack, spell, curse, fall), you may activate this as a free action. "
            "The figurine transforms into a copy of you and swaps places — the attack hits the "
            "figurine (which is destroyed) instead. You reappear up to 2m away in a safe "
            "location of your choice.\n"
           "<b><font color='#C0392B'>Flame Controlling (1 SPI):</font></b> "
           "Free action. Manipulate flames within 30m — ignite flammable materials, shape "
           "existing fire, extinguish small flames (candle to campfire size), or direct fire "
           "to move as you wish. In combat: make a ranged attack (DX or Sleight of Hand) "
           "to hurl a flame jet at a target within 30m, dealing 1d6 burn. Cannot create fire "
           "from nothing unless the potion is fully digested (GM discretion).\n"
           "<b><font color='#C0392B'>Illusion Creation (1 SPI):</font></b> "
           "One Concentrate maneuver. Create a multi-sensory illusion (sight, sound, smell) "
           "within 20m that is nearly indistinguishable from reality. The illusion can move "
           "and act within its area for up to 1 minute (maintain as free action). Observers "
           "may disbelieve by rolling IQ-2 or Per-2; on success they see through the illusion "
           "as transparent and ghostly. Critical failure means they fully believe it.\n"
           "<b><font color='#C0392B'>Underwater Breathing (1 SPI):</font></b> "
           "Creates an invisible 5m air pipe to the surface. Lasts 10 minutes. The air pipe "
           "is intangible — cannot be cut or blocked by mundane means. Pipe length increases "
           "to 10m once the potion is fully digested.\n"
           "<b><font color='#C0392B'>Bone Softening (Free):</font></b> "
           "Passive. +4 to Escape rolls against handcuffs, ropes, chains, and confined spaces. "
           "No SPI cost. The Magician can dislocate joints painlessly and reshape their hands "
           "to slip through gaps smaller than their head.\n"
           "<b><font color='#C0392B'>Paper Weaponry (1 SPI):</font></b> "
           "Upgrade from Paper Daggers. Turn any sheet of paper into a functional bladed weapon "
           "(knife, sword, axe, or improvised blade) for 1 minute. The weapon's damage matches "
           "its type (knife: thr-1 cut / sw-2 imp; short sword: sw+1 cut / thr+1 imp; "
           "etc.) and counts as a Beyonder weapon of the Magician's Sequence for the purpose "
           "of harming spirits and incorporeal beings. Unlike Paper Daggers, the weapon lasts "
           "for multiple attacks until the duration expires. Can also form simple tools "
           "(lockpicks, keys, scissors) that function at their mundane equivalent.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Clown Agility (Reinforced):</font></b> The Magician's acrobatic ability improves further. "
           "Clown Intuition triggering range expands to 8 m. The free Dodge/Step may be taken against any attack, "
           "not just successful hits — the Magician may also use it proactively once per scene to evade "
           "an Area of Effect attack.\n"
           "<b><font color='#C0392B'>Spirit Vision (Reinforced):</font></b> Range expands to 20 m. "
           "The Magician can now read the Ether Body of a target to determine exact HP remaining, "
           "SPI remaining, and whether they are under any active Beyonder effect."),

        # ── Error Pathway ──

         ("Cryptologist", "Error Pathway",
           [("IQ", "+1"), ("SPI", "+2"),
            ("Eidetic Memory", "+5 to remember things after one reading; near-perfect recall")],
           [("Cryptography/IQ [Hard]", "+4"),
            ("Forensics/IQ [Hard]", "+3"),
            ("Occultism/IQ [Average]", "+3"),
            ("Intelligence Analysis/IQ [Hard]", "+3"),
            ("Thaumatology/IQ [Very Hard]", "+2"),
            ("Spiritual Intuition/SPI [Hard]", "+2")],
           "<b><font color='#C0392B'>Decryption (IQ / 1 SPI):</font></b> Requires concentration and a physical item "
           "or scene to study. Roll IQ (or Ritualistic Magic for mystical subjects). "
           "Success: the GM reveals information based on margin of success. "
           "Failure: no insight; SPI still spent. Critical Failure: a false conclusion.\n"
           "Facts come in four strengths:\n"
           "  <b>Trace</b> — vague hint (2 Trace = 1 Standard)\n"
           "  <b>Standard</b> — clear observation\n"
           "  <b>Sharp</b> — decisive fact (counts as 2 Standard)\n"
           "  <b>Undeniable</b> — automatic, no roll (e.g. seeing a gun aimed at you)\n"
            "<b><font color='#C0392B'>Beyonder Knowledge (Passive):</font></b> The Cryptologist has deep knowledge of:\n"
            "• Mystical objects, sealed artifacts, and how items can absorb potions or characteristics\n"
            "• Rituals — standard rituals, the dualistic ritual, the standard sacrificial ritual, the "
            "standard bestowment ritual, and the Artificial Sleepwalking Ritual\n"
            "No roll for common knowledge within these domains; obscure or protected secrets require "
             "Occultism or Thaumatology to recall.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Superior Observation (Reinforced):</font></b> Range expands to 30 m. "
           "The Cryptologist can read micro-expressions at a glance — Detect Lies and Body Language rolls "
           "against any visible target within range gain +3 (from +2).\n"
           "<b><font color='#C0392B'>Mental Disruption (Reinforced):</font></b> The Will penalty for the target's save increases to -4. "
           "The Cryptologist may target up to 2 individuals simultaneously by spending 2 SPI total.\n"
           "<b><font color='#C0392B'>Reminder / Theft (Reinforced):</font></b> Reminder distance increases to 10 m. "
           "The Cryptologist can now steal spiritual materials that are actively guarded (held in a "
           "target's hand or within a locked container) as long as the container interacts with the spirit world."),

        # ── Door Pathway ──

           ("Astrologer", "Door Pathway",
            [("SPI", "+3")],
           [("Astrology/IQ [Hard]", "+3"),
            ("Ritualistic Magic/IQ [Very Hard]", "+2"),
             ("Spiritual Intuition/SPI [Hard]", "+2")],
           "<b><font color='#C0392B'>Crystal Ball Focus (Passive):</font></b> When using a crystal ball, gain +2 to Ritualistic Magic (divination) rolls.\n"
          "<b><font color='#C0392B'>Interference (1 SPI):</font></b> The Astrologer senses and can disrupt divination and "
          "Spiritual Intuition attempts that try to read or sense the future through the spirit world. By stirring their "
          "spirituality, they create an anti-divination warding. Roll SPI vs the opponent's Spiritual Intuition or "
          "Ritualistic Magic roll. Success: opponent's divination becomes blurry and messy — IQ-2 to interpret. "
          "Success by 3: the divination is completely blocked. Failure: unable to interfere; you feel like something is watching you.\n"
          "<b><font color='#C0392B'>Door Opening (2 SPI):</font></b> Touch range. Upgrades the Seq 8 Door ability to bring one "
          "additional person through a door or spatial obstacle. Both must be touching you or each other in a chain. "
          "The door must be real (not illusory) and large enough to admit the group. "
          "Usable once per scene unless the Astrologer concentrates for 1 minute to reopen.\n"
          "<b><font color='#C0392B'>Peephole (1 SPI):</font></b> Creates a palm-sized, invisible peephole through up to 1 meter "
           "of wood, stone, or brick. Lasts 1 minute. You see through it as if standing at the wall's surface.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Trickmaster Spellcasting (Reinforced):</font></b> All Trickmaster spells have their ranges "
           "doubled. Flash and Fog radii increase by 2 m. Escape Trick's reposition distance increases to 10 m. "
           "Gas Transfer range increases to 30 m.\n"
           "<b><font color='#C0392B'>Door Opening (Reinforced):</font></b> The Seq 8 Door Opening upgrade is further enhanced — "
           "the Astrologer may now bring up to 3 additional people through a door (from 1). The ability "
           "can be used twice per scene (from once) before needing 1 minute of concentration to refresh."),

        # ── Visionary Pathway ──

           ("Psychiatrist", "Visionary Pathway",
            [("IQ", "+1"),
             ("HT", "+1"),
              ("Per", "+1"),
              ("Night Vision 5", "see clearly in darkness up to 50 meters — dragon-touched eyes"),
               ("Acute Smell +2", "sharper sense of smell; detect subtle scents and emotional cues"),
               ("DR 2 (dragon scales)", "tough hide from the Mind Dragon; stacks with worn armour"),
               ("SPI", "+2")],
          [("Psychology/IQ [Hard]", "+4"),
           ("Detect Lies/Per [Hard]", "+3"),
           ("Acting/IQ [Average]", "+3"),
            ("Diplomacy/IQ [Hard]", "+3"),
            ("Body Language/Per [Average]", "+2")],
           "<b><font color='#C0392B'>Frenzy (2 SPI):</font></b> Roll Psychology vs Will. On success, target Frenzies for 1d6 turns: "
            "-2 to non-aggressive actions, must attack nearest creature. Deals 1d6-1 FP (min 1). If already unstable "
            "or at 0 FP, roll Will or gain 1 CP.\n"
             "<b><font color='#C0392B'>Awe (2 SPI):</font></b> Project Mind Dragon presence. All within 20 meters roll Will "
            "or freeze in panic for MoF turns (min 1, max 4), -2 to defenses. Hostile action breaks it on that target. "
            "+2 to save if warned.\n"
            "<b><font color='#C0392B'>Psychological Cue (2 SPI):</font></b> After 1 hour of conversation and a medium "
            "(candle, pendant, oil), roll Psychology vs Will. Target unconsciously follows a simple arrangement for 24h. "
            "If the arrangement would significantly harm person/reputation/livelihood or violate a core value, "
             "target gets a new Will+2 save when triggered. May self-cue to enter the Sea of Collective Subconscious "
             "(a shared psychic realm of all unconscious minds; see Glossary).\n"
            "<b><font color='#C0392B'>Placate (1 SPI):</font></b> Roll Psychology (no resistance if willing, else vs Will). "
            "On success, choose one: reduce CP by 1; remove fear/rage/despair; or give a losing-control target "
            "a new Will+2 save. If actively losing control, target saves at <=11 on 3d6. GM adjusts for sequence/severity.\n"
            "<b><font color='#C0392B'>Telepathy (1 SPI):</font></b> Upgrade from Mind Reading — reads "
            "<b>deeper</b> thoughts (not just surface), works on <b>Will 13+</b> (at -2, not immune), "
            "and enables <b>two-way</b> communication. Requires a medium (candlelight, hydrosols, crystal). "
               "Roll Psychology vs Will-1. Target unaware unless crit fail.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Enhanced Body Language Analysis (Reinforced):</font></b> The Telepathist's always-on reading "
           "now penetrates Mind Shield up to level 2 — targets with Mind Shield 1-2 roll a Quick Contest of "
           "Will vs the Psychiatrist's Psychology to block surface readings. Range expands to 20 m.\n"
           "<b><font color='#C0392B'>Mind Reading (Reinforced):</font></b> The Telepathist's active Mind Reading now costs 0 SPI if "
           "the Psychiatrist succeeds by 5+ (instead of always costing 1 SPI/minute). The Psychology roll "
           "to predict a target's next action after a successful read gains +3."),

        # ── Sun Pathway ──

           ("Solar High Priest", "Sun Pathway",
             [("ST", "+2"),
              ("SPI", "+2"),
              ("Disease & Poison Resistance", "+2 to HT vs. disease, poison, and environmental hazards"),
              ("Fit", "+1 to all HT rolls; recover FP at twice the normal rate"),
              ("DR 1 (fire/light)", "stacks with Seq 8 — total DR 3 vs. fire and light")],
           [("Theology/IQ [Hard]", "+3"),
            ("Ritualistic Magic/IQ [Very Hard]", "+2 (Sun domain)"),
            ("Religious Ritual/IQ [Hard]", "+2")],
           "<b><font color='#C0392B'>Theurgical Abilities — Sun Domain (Purification & Exorcism):</font></b>\n"
           "The Solar High Priest's body becomes considerably stronger, gaining resistance to ailments, "
           "poison, and harsh environments. Spell and sacrifice abilities within the Sun domain are greatly "
           "enhanced. Purification and Exorcism operate within the category of Evil (including depraved "
           "auras) and extend to undead as incompatible presences — though with moderately reduced effect "
           "on undead that are not intrinsically Evil.\n\n"
           "<b><font color='#C0392B'>Sun Halo (2 SPI):</font></b> A golden halo forms around the head. All allies within "
           "20 meters ignore Fright Check penalties up to -5 and have Evil energies actively Purified. "
           "Lasts 5 minutes; +1 SPI per additional minute.\n\n"
           "<b><font color='#C0392B'>Sun Holy Water (3 SPI + Ritualistic Magic):</font></b> Consecrates water into Sun Holy "
           "Water. On contact with wraiths, spirits, or undead: 2d6+2 corrosion damage (ignores non-magical DR); "
           "1d-1 on living targets. Full-round action: splash to Exorcise a possessed target — roll Ritualistic "
           "Magic vs. entity's Will. Can also purify cursed objects (1 min immersion; -2 for powerful curses). "
           "Lasts until next sunrise.\n\n"
           "<b><font color='#C0392B'>Holy Oath (3 SPI):</font></b> Silently recite ancient words. For 3 minutes: +2 to "
           "ST-based rolls, +2 to DX-based rolls, +1d6 fire damage on attacks, all attacks gain the Holy tag. "
           "Self only.\n\n"
           "<b><font color='#C0392B'>Holy Light Summoning (4 SPI):</font></b> Calls a holy beam of Light from the sky onto "
           "a point within 30 meters. Undead and Evil entities: 3d6 burning damage (ignores non-magical DR). "
           "Other targets: 1d6 burning. Targets with 5+ CP take +1d. Success by 3+ on Ritualistic Magic "
           "sustains for a second round at no cost. Area illuminated as full daylight for 1 minute.\n\n"
           "<b><font color='#C0392B'>Cleave of Purification (2 SPI):</font></b> Imbues attacks, weapon, or bullets with "
           "Purification. For 5 attacks or 1 minute: bypasses DR of incorporeal targets; on hit, target rolls "
           "HT or suffers -2 to all rolls for 1d rounds. +3 to Purify wraiths outright.\n\n"
           "<b><font color='#C0392B'>Horror Immunity (1 SPI):</font></b> Target becomes immune to Fear for 10 minutes — "
           "including passive auras and active psychic attacks from Evil entities. Self-cast or touch. "
           "+1 SPI per additional target.\n\n"
           "<b><font color='#C0392B'>Fire of Light (3 SPI):</font></b> Dense golden holy Flames erupt at a point within "
           "20 meters, filling a 5-meter radius. Living targets: roll HT or take 2d6 holy fire per round. "
           "Undead and Evil entities: double damage, HT-2 or Purified each round. Lasts 3 rounds. Cannot be "
           "smothered by ordinary means.\n\n"
           ),

        # ── Tyrant Pathway ──

          ("Seafarer", "Tyrant Pathway",
            [("ST", "+1"), ("DX", "+1"), ("IQ", "+1"),
             ("SPI", "+1"),
             ("Eidetic Memory", "+5 to remember things after one reading; near-perfect recall"),
             ("Amphibious (Enhanced)", "acts and moves freely underwater for 30+ minutes without equipment"),
             ("Perfect Balance (Enhanced)", "never loses footing on any sea vessel regardless of conditions"),
             ("Absolute Direction", "Always know which way is north; never become lost at sea or on land. +3 to Navigation and Body Sense rolls.")],
         [("Navigation (Sea)/IQ [Average]", "+5"),
           ("Seamanship/IQ [Easy]", "+4"),
            ("Throwing/DX [Average]", "+4"),
          ("Weather Sense/IQ [Average]", "+4"),
          ("Swimming/HT [Easy]", "+3"),
          ("Mathematics (Applied)/IQ [Hard]", "+2")],
         "<b><font color='#C0392B'>Aquatic Affinity — Enhanced:</font></b> All skill rolls gain +1 while at sea or aboard a vessel. Passive. No bonus on land.\n"
         "<b><font color='#C0392B'>Navigator's Precision:</font></b> Accurately judges distance to any located target. May throw weapons "
         "at full skill with eyes closed or in total darkness after locating the target. A vessel with a Seafarer aboard cannot become "
         "lost under natural conditions.\n"
         "<b><font color='#C0392B'>Water Spells:</font></b> Water conjured by any spell can be dispersed by the Seafarer as a free action.\n"
          "<b><font color='#C0392B'>Suffocation Film (2 SPI):</font></b> Roll Ritualistic Magic vs the target's HT. On success, a "
          "film of water forms over the target's face within 10 meters. The film is extremely hard to remove — "
          "ST-3 each round to make progress. Target suffocates per normal GURPS rules. On failure, no effect; "
          "SPI is still spent.\n"
          "<b><font color='#C0392B'>Azure Wave (2 SPI):</font></b> One round of concentration, then roll Ritualistic Magic. On "
          "success, a water wave sweeps a 10-meter cone from the Seafarer's position. Targets in the cone roll "
          "DX-2 or are knocked prone and pushed 1d meters back. Failure by 5+ also causes loss of next action. "
          "On a failed Ritualistic Magic roll, the wave sputters — no effect; SPI still spent.\n"
         "<b><font color='#C0392B'>Restorative Waters (1 SPI):</font></b> Apply conjured water to a wound. Roll Physician at IQ+0. "
         "Success restores 1d-2 HP (minimum 1). Cannot be used in combat without Concentrate maneuver.\n"
         "<b><font color='#C0392B'>Aqueous Cleanse (1 SPI):</font></b> Aqueous light cleanses surfaces of filth, blood, mundane poisons, "
         "and minor spiritual contamination on contact.\n"
          "<b><font color='#C0392B'>Wrath — Retained:</font></b> Folk of Rage ability fully retained. Additionally: "
          "roar (1 SPI) at a target within 20 meters — Will-2 or target enters uncontrolled berserk rage for "
          "1d rounds. Player characters resist at Will, no modifier.\n"
         "<b><font color='#C0392B'>Singing of the Storm — New:</font></b> Range increases to 30 meters, Will penalty becomes -3 "
          "for 1d rounds. At sea: 50 meters, Will-4.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Phantom Scales (Reinforced):</font></b> DR increases to 4 (physical, stacks with worn armor) "
           "and extends to cover the throat and eyes (no chink/eye weak spots). Duration extends to 25 minutes.\n"
           "<b><font color='#C0392B'>Sea Affinity (Reinforced):</font></b> The Swim skill bonus increases to +4. "
           "The Seafarer can hold breath for 5 minutes per point of HT (instead of 3) and "
           "ignores depth pressure penalties up to 50 m.\n"
           "<b><font color='#C0392B'>Battle Cry (Reinforced):</font></b> All allies within 15 m gain +2 to Will "
           "against Fear checks for the scene (from +1). Fright Check range expands to 15 m.\n"
           "<b><font color='#C0392B'>Bravery (Reinforced):</font></b> The Seafarer and all allies within 5 m are immune "
           "to Fright Checks from first-time supernatural exposure (ghosts, sea monsters, etc.)."),

        # ── White Tower Pathway ──

          ("Detective", "White Tower Pathway",
            [("IQ", "+1"), ("DX", "+1"), ("SPI", "+2")],
          [("Criminology/IQ [Average]", "+5"),
           ("Forensics/IQ [Hard]", "+5"),
           ("Intelligence Analysis/IQ [Hard]", "+4"),
           ("Ritualistic Magic/IQ [Very Hard]", "+2"),
            ("Guns (Pistol)/DX [Easy]", "+3"),
             ("Brawling/DX [Easy]", "+3")],
            "<b><font color='#C0392B'>Reconstruction (1 SPI):</font></b> Requires a physical item that was present at the "
           "target event. The Detective peers into the spirit world's record of the past. "
           "Roll Ritualistic Magic. Success: instant full-sensory flash (sight, sound, smell) of the scene "
           "from the item's perspective — duration is scene-dependent (GM discretion). "
           "Success by 3+: clearer vision; may spot one hidden detail the GM chooses to reveal. "
           "Critical Success: vision includes emotional and spiritual impressions of those present. "
             "Failure: no effect; SPI is still expended.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Recall (Reinforced):</font></b> +4 to remember any fact the Detective has "
           "personally encountered (from +2). The touch-based memory recovery extends to objects the Detective "
           "touched within the past 24 hours (instead of 1 hour).\n"
           "<b><font color='#C0392B'>Eye of the Mind (Reinforced):</font></b> The IQ-based skill roll for obscure "
           "or deliberately hidden material suffers only -3 (from -5). The Detective may use Eye of the Mind "
           "to analyze a scene in a single minute per item of interest.\n"
           "<b><font color='#C0392B'>Ratiocination (Reinforced):</font></b> When using Ratiocination to "
           "reconstruct a conclusion from scattered clues, the Detective gains +3 to the roll. "
           "The time required drops from 1d6 minutes to 1d3 minutes."),

        # ── Hanged Man Pathway ──

            ("Shadow Ascetic", "Hanged Man Pathway",
             [("SPI", "+3"),
             ("Per", "+1")],
           [("Ritualistic Magic/IQ [Very Hard]", "+2 (additional)"),
            ("Stealth/DX [Average]", "+3"),
            ("Occultism/IQ [Average]", "+2 (additional)")],
           "<b><font color='#C0392B'>Shadow Lurking (1 SPI):</font></b> "
           "Conceal yourself within any shadow large enough to cover your body. "
           "While Lurking, you are invisible and inaudible to mundane senses — "
           "observers roll Per-2 to notice any signs of your presence. "
           "You may move between connected shadows (within the same room or "
           "adjacent area) as a Move maneuver. Attacking or using SPI-cost "
           "abilities instantly breaks concealment. Duration: up to 1 minute "
           "(extend at 1 SPI per minute).\n"
           "<b><font color='#C0392B'>Shadow Shaping (1 SPI):</font></b> "
           "Shape shadows within 10m into melee weapons (knife, sword, chain) "
           "or simple animal forms (shadow hound, serpent). Weapons deal damage "
           "matching their type (e.g. knife: thr-1 cut; shortsword: sw+1 cut) "
            "but as <b>shadow corrosion</b> — they bypass non-magical DR and "
            "damage the spirit body alongside the physical body (see Spirit Body Damage, Chapter 5). Animal forms "
           "have ST 8, HT 10, DX 10, Move 6, and follow simple commands (attack, "
           "guard, fetch). They deal 1d-2 corrosion damage on a successful hit. "
           "Duration: 1 minute. One shape at a time.\n"
           "<b><font color='#C0392B'>Shadow Chrysalis (2 SPI):</font></b> "
           "Requires Shadow Lurking. Target one creature within 10m — their "
           "own shadow rises and envelops them in a black cocoon. Quick Contest "
           "of ST vs your SPI: if the target loses, they are held immobile for "
           "1d3 turns. Each turn, the target may attempt a new ST roll to break "
           "free (at -2 if your SPI exceeds their ST). While trapped, the target "
           "takes 1d-2 corrosion damage per turn from the shadow's degenerating "
           "touch.\n"
           "<b><font color='#C0392B'>Summon Shadow (2 SPI):</font></b> "
           "Ritualistic Magic roll to summon a shadow creature from the Shadow "
           "World. On success, a shadow servitor manifests within 10m and follows "
           "your mental commands for up to 1 minute (ST 12, HT 12, DX 10, Move 8, "
           "DR 3 vs physical, immune to mind-affecting). It attacks for 1d6 "
           "corrosion damage or performs complex tasks. On a failed roll, the "
           "summoning still works but the creature is hostile — it attacks the "
           "nearest creature (possibly you) for 1d3 turns before dissolving. "
           "Critical failure: a stronger shadow entity notices you (GM discretion).\n"
           "<b><font color='#C0392B'>Listening Control (Passive):</font></b> "
           "The Shadow Ascetic can now toggle the Listener's passive Listening "
           "on and off as a free action. When active, range is reduced from 80m "
           "to 40m and the GM applies +2 to any interference rolls (reducing "
            "the risk of hearing higher entities).\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Listening (Reinforced):</font></b> When toggled active, passive Listening range "
           "is 80 m (from 50 m) with no penalty to interference rolls. Active Listening range increases to "
           "30 m and the Shadow Ascetic may listen to 2 simultaneous conversations.\n"
           "<b><font color='#C0392B'>Spiritual Perception (Reinforced):</font></b> +3 to detect spiritual entities "
           "and auras (from +2). The passive range expands to 80 m (from 50 m). "
           "A successful roll reveals the entity's general emotional state (hostile, indifferent, fearful).\n"
           "<b><font color='#C0392B'>Anonymize (Reinforced):</font></b> The duration extends to 1 hour per SPI spent "
           "(from 30 minutes). The Ascetic may also Anonymize 1 additional person within 2 m at no extra SPI cost."),

        # ── Darkness Pathway ──

         ("Nightmare", "Darkness Pathway",
           [("SPI", "+3"), ("IQ", "+1")],
         [],
         "<b><font color='#C0392B'>Silent Midnight Poem (1 SPI):</font></b> Can now chant Midnight Poems without opening the mouth.\n"
         "<b><font color='#C0392B'>Nightmare State (1 SPI):</font></b> The Nightmare's body falls asleep while the Soul Body moves freely "
         "within city range to enter dreams. While in this state, vision is tainted and all Observation rolls suffer -3. "
         "The Nightmare sees glowing orbs that belong to the dream of someone.\n"
         "<b><font color='#C0392B'>Dream Shaping (1 SPI):</font></b> Shapes the dream of a target, guiding them into revealing certain things "
         "or truths. Can be used for interrogation: all Interrogation, Detect Lies, and Observation rolls gain +3 during this state. "
         "Target rolls Will -2; on critical failure the target divulges their biggest secret.\n"
         "<b><font color='#C0392B'>Dream Invasion (2 SPI):</font></b> Forcefully drags a target into a dream. Target rolls Spiritual Intuition -5; "
         "on failure they are unaware they are in a dream; on critical failure they suffer -1 to all actions in the dream. "
         "Range: 20 meters if done quickly, 100 meters with 2 turns of preparation. The Nightmare can coax the target into sleeping "
         "to reduce casting cost by 1 SPI. Once used, both the Nightmare and the target fall into the dream. The Nightmare can coax "
         "up to 10 people into sleeping, but can only enter the dream of 1 target.\n"
         "<b><font color='#C0392B'>Nightmare Limbs (1 SPI):</font></b> Generates tentacles from the back for close combat. These tentacles "
         "are made of flesh and blood — if destroyed, the Nightmare takes 1d6-2 damage. Tentacles have the Nightmare's HP -2. "
          "When used, they deal 1d6+1 damage.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Nocturnality (Reinforced):</font></b> At night or in darkness, DX and IQ bonuses "
           "increase to +3 (from +2). Perception bonus to spot hidden creatures in darkness increases to +4.\n"
           "<b><font color='#C0392B'>Shadows (Reinforced):</font></b> The Stealth bonus rises to +4 (from +3). "
           "The Nightmare can merge into shadows as a free action once per turn, "
           "gaining Invisibility (vision only) until they attack or leave the shadow.\n"
           "<b><font color='#C0392B'>Danger Detection (Reinforced):</font></b> +5 to any roll to detect "
           "ambushes and traps (from +4). Range expands to 30 m (from 20 m)."),

        # ── Death Pathway ──

           ("Spirit Medium", "Death Pathway",
           [("SPI", "+3"),
            ("Per", "+1"),
            ("Will", "+1")],
          [("Occultism/IQ [Average]", "+2 (additional)"),
           ("Ritualistic Magic/IQ [Very Hard]", "+2 (upgrade)"),
            ("Thaumatology/IQ [Very Hard]", "+1"),
            ("Spiritual Perception/SPI [Average]", "+2")],
            "<b><font color='#C0392B'>Spirit Channeling (2 SPI):</font></b> "
            "Roll Ritualistic Magic to communicate with natural spirits and dead souls. Most require materials "
            "(Full Moon Essence Oil, Corpse Incense, or the Medium's own blood). "
            "Success = willing to converse. Success by 3+ = favorable. "
            "Failure = refuse. Critical Failure = offended — they haunt you. 1 spirit at a time.\n"
            "Living souls can also be channeled (harder). Two methods: "
             "(1) Forceful — SPI contest vs Will; (2) Relaxation — Amantha Extract + Eye of Spirit medication. "
             "Crit fail on a living soul causes backlash (+1 CP). Deceased spirits need no ritual penalty.\n"
             "<b><font color='#C0392B'>Frost Shadow (1–2 SPI/turn):</font></b> "
             "Roll Ritualistic Magic to summon a combat spirit. On success, it manifests on your turn and you control it "
             "mentally as a free action. Duration: concentration, up to 1 minute (dismiss as free action). Choose one form "
             "per summon:\n"
             "• Ice Armor — +2 DR (+3 vs cold), lasts while maintained.\n"
             "• Frost Scythe — sw+2 cutting +1 cold damage, Reach 1–2.\n"
             "• Freezing Field — 10m radius; enemies inside take 1 HP cold damage per round (HT roll to resist; half damage on success).\n"
             "<b><font color='#C0392B'>Spirit Affinity (Passive):</font></b> "
             "Understand spirits without Ritualistic Magic. Spirits regard you as kin — won't attack first. "
             "If friendly, they may share information unprompted (1d6; 4+ succeeds). "
             "Intelligent undead (IQ 8+) may resist with a Will roll; on success they ignore the affinity.\n"
            "<b><font color='#C0392B'>Zombie Disguise (1 SPI):</font></b> "
            "Disguise as zombie; +1 Will vs death/cold/decay auras (including from ghosts and undead).\n"
            "<b><font color='#C0392B'>Eye of Death (1 SPI):</font></b> "
            "Upgrade from Gravedigger — costs SPI instead of FP. Reveals all weaknesses of Undead/Spirit creatures. "
              "For the rest of the scene: +2 to hit, +2 damage, ignore 2 DR against that creature.\n"
             "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
             "<b><font color='#C0392B'>Undead Deterrence (Reinforced):</font></b> Range expands to 15 m and the Will penalty "
             "for undead approaching the Spirit Medium increases to -3. Affects all undead up to Seq 7 "
             "(from Seq 8-9).\n"
             "<b><font color='#C0392B'>Controlled Zombie (Reinforced):</font></b> The Spirit Medium can maintain control "
             "over up to 3 zombies at once (from 2). Zombies gain +2 to ST and +1 HP from the increased "
             "spiritual power flowing through them.\n"
             "<b><font color='#C0392B'>Corpse Vision (Reinforced):</font></b> Range expands to 30 m. The Spirit Medium can "
             "see through the eyes of any corpse they have personally touched within the past week "
             "(instead of 24 hours). Duration of shared vision increases to 5 minutes."),

        # ── Twilight Giant Pathway ──

           ("Weapon Master", "Twilight Giant Pathway",
            [("ST", "+2"),
             ("DX", "+1"),
             ("HT", "+1"),
             ("Per", "+1"),
             ("SPI", "+1"),
             ("DR 1 (all, stacks with Pugilist)", "total DR 2 from Pugilist + Weapon Master")],
            [("Broadsword/DX [Average]", "+3"),
             ("Polearm/DX [Average]", "+2"),
             ("Shield/DX [Easy]", "+2"),
             ("Armoury (any)/IQ [Average]", "+2")],
            "<b><font color='#C0392B'>Weapon Mastery (Passive):</font></b> "
            "The Weapon Master can use any weapon at master-level standard the moment it enters "
            "their hands. This includes mundane weapons, Beyonder weapons, Mystical Items, and "
            "Sealed Artifacts in weapon form — swords, guns, axes, polearms, and any other weapon "
            "type. Unlike the Warrior, the Weapon Master requires no warm-up — every weapon is treated "
            "as known at effective DX (no default penalty) instantly, and the Weapon Master also dons and maintains "
            "any armour type without penalty. <b>Example:</b> A Weapon Master who picks up a flintlock "
            "pistol for the first time fires it at effective DX (no default penalty) immediately — no repeated uses "
            "needed. The same applies to a legendary sealed-artifact sword or a Beyonder weapon: "
            "full mastery from the first swing. "
            "Skill bonuses from this potion are cumulative with those from earlier Twilight Giant potions (Warrior, Pugilist). "
            "This is a strict upgrade to and replacement of the Warrior's Combat Mastery.\n"
           "<b><font color='#C0392B'>Negative Effect Resistance (Passive):</font></b> "
           "The Weapon Master's superhuman physique and spiritual fortitude reduce the harmful "
           "side effects of Beyonder weapons, Mystical Items, and Sealed Artifacts they wield. "
           "When wielding such an item, the Weapon Master halves any FP or HP damage taken from "
           "its negative effects (after any resistance roll, before modifiers, rounded down) and gains +3 to any resistance roll against its "
            "detrimental effects (e.g. Will rolls against madness, HT rolls against curses).\n"
            "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
            "<b><font color='#C0392B'>Powerful Blow (Reinforced):</font></b> The Weapon Master may charge an attack for "
            "2 consecutive turns of concentration — the third turn's melee attack deals double damage "
            "(minimum +1d6). At the GM's discretion, a suitably dramatic weapon (greatsword, warhammer) "
            "may also shatter non-magical shields or objects on a hit.\n"
            "<b><font color='#C0392B'>Counterattack (Reinforced):</font></b> After a successful active defense, the Weapon Master "
            "may make an immediate counterattack at no penalty (the usual -4 for a stop-hit is waived). "
            "This may be done once per turn.\n"
            "<b><font color='#C0392B'>Stone Body (Reinforced):</font></b> DR from Pugilist's Stone Body increases by +1 "
            "(total DR 3 vs. physical if combined with potion DR). The Weapon Master's natural DR now "
            "also protects against corrosion damage at half value (rounded down)."),

         # ── Demoness Pathway ──

          ("Witch", "Demoness Pathway",
             [("SPI", "+7"), ("Charisma +1", "+1 to reaction rolls and Influence skills"), ("Appearance (Beautiful)", "the potion perfects the Witch's features; +2 to reaction rolls")],
           [("Ritualistic Magic (Mirror, Dowsing)/IQ [Very Hard]", "+4"),
            ("Divination Arts/SPI [Hard]", "+2"),
            ("Occultism/IQ [Average]", "+2")],
          "<b><font color='#C0392B'>Permanent Changes:</font></b> The potion changes the Beyonder's gender to female. "
          "Slight height increase (~5 cm). Body proportions approach perfection. Details become more alluring.\n"
          "<b><font color='#C0392B'>Invisibility (X SPI):</font></b> By scattering shimmering powder and reciting an incantation, "
          "a Witch can turn Invisible to the naked eye. Lasts 10 minutes per SPI spent, up to 1 hour max. The Invisibility "
          "ends if physical contact is made.\n"
          "<b><font color='#C0392B'>Ice Projectiles (1 SPI):</font></b> Create and project several ice projectiles at a target, "
          "inflicting 2d-2 damage.\n"
          "<b><font color='#C0392B'>Mirror Substitution (3 SPI):</font></b> Set up a Substitution using a Mirror, transferring "
          "all the damage from the next successful attack to the mirror. The mirror shatters on use. Can be used on an ally "
          "under 2 conditions: they provide a medium (hair, blood, etc.) and stay within 30 meters of the Witch.\n"
          "<b><font color='#C0392B'>Staff Substitution (3 SPI):</font></b> Witches can use staves as a medium for substitutes "
          "to counteract fatal harm. Upon being harmed, switch positions with the staff, which takes the damage and shatters.\n"
          "<b><font color='#C0392B'>Black Flames:</font></b> Black flames burn spirituality rather than objects, thus allowing "
          "spirit bodies and Beyonder effects to be set aflame. Cannot be extinguished with water. Can be extinguished only "
          "by controlling one's own spirituality or the target's below 1/3 of maximum.\n"
          "<b><font color='#C0392B'>Flame Envelopment (2 SPI + 1 SPI/turn):</font></b> Envelop a weapon with black flames. "
          "After landing a successful hit that causes laceration, you may detonate the flames coursing inside the target's "
          "veins for 2d6+1 damage (costs 2 SPI). Must be done the next turn or the flames extinguish.\n"
          "<b><font color='#C0392B'>Flame Compression (2 SPI):</font></b> Compress black flames into a dense, cannonball-sized "
          "sphere and throw it. Hits with the force of a cannonball, spewing flames on impact. Deals 2d6 damage + burning "
          "(1d3 per turn, -1 SPI per turn while burning until target's SPI is under 1/3 max). Range 35 meters, blast radius "
          "10 meters.\n"
           "<b><font color='#C0392B'>Freeze — Target (2 SPI):</font></b> Freeze a target by touch, up to 1 cubic meter. "
           "Target rolls HT-1; on failure takes 2d6-1 damage, on success takes half (rounded down).\n"
            "<b><font color='#C0392B'>Freeze — Area (3 SPI):</font></b> Freeze an area up to 10 meter radius centred on self. "
           "All targets in range roll HT-1; failure takes 2d6-1 damage, success takes half (rounded down).\n"
          "<b><font color='#C0392B'>Ice Wind (2 SPI + 1 SPI/turn):</font></b> Icy wind and hail swirl around the Witch "
          "(10 meter radius), imposing -3 to all rolls relying on sight and smell. Lasts until dispelled or the Witch "
          "runs out of Spirituality.\n"
          "<b><font color='#C0392B'>Ice Seal (2 SPI):</font></b> Seals the target in a cage of layered ice for 1d4 turns. "
          "Can be broken with ST-1 roll.\n"
          "<b><font color='#C0392B'>Mirror Magic — Hide (1 SPI):</font></b> Hide in a mirror for 1d6 seconds. If the mirror "
          "is destroyed, the Witch is thrown out and takes 2d6 damage.\n"
          "<b><font color='#C0392B'>Mirror Magic — Sense (Passive):</font></b> Sense mirrors within 25 meters.\n"
          "<b><font color='#C0392B'>Cursing:</font></b> Can curse a target if possessing their blood (+2) or a doll made from "
          "their flesh and hair (+4). Uses Ritualistic Magic skill. Once the connection is established, the Witch may burn "
           "the medium for 2d6 damage, or use it as a base for other rituals (add the medium's bonus to the success rate).\n"
            "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
            "<b><font color='#C0392B'>Feather Fall (Reinforced):</font></b> The glide ratio improves to 3:1 (from 2:3). "
            "The Witch may also slow the fall of 1 additional person within 3 m at no extra SPI cost.\n"
            "<b><font color='#C0392B'>Shadow Concealment (Reinforced):</font></b> The Stealth bonus in dim or dark conditions "
            "increases to -6 (from -5). When standing still in complete darkness, the Witch is effectively "
            "invisible to mundane sight — observers roll Per-4 to notice.\n"
            "<b><font color='#C0392B'>Charm (Reinforced):</font></b> The Instigator's innate Charm improves — the Witch gains "
            "+2 to all Influence skill rolls (Diplomacy, Fast-Talk, Sex Appeal) against targets who are "
            "attracted to the Witch's gender."),

        # ── Red Priest Pathway ──

          ("Pyromaniac", "Red Priest Pathway",
            [("SPI", "+7"), ("HT", "+1"), ("ST", "+1"),
            ("DR 2 (fire)", "resistance to fire damage")],
         [("Guns (any)/DX [Easy]", "+3"),
          ("Intimidation/Will [Average]", "+3"),
          ("Traps/IQ [Average]", "+3"),
          ("Survival (any)/Per [Average]", "+2")],
         "<b><font color='#C0392B'>Spirit Vision Enhancement:</font></b> The Pyromaniac's spirit vision is easier to activate and can now perceive the Ether Body of spirits and Beyonders.\n"
         "<b><font color='#C0392B'>Danger Intuition Buff:</font></b> Pre-emptive threat detection is enhanced. Enemies tracking the Pyromaniac suffer -2 to their Tracking rolls.\n"
          "<b><font color='#C0392B'>Pyrokinesis:</font></b> The Pyromaniac can freely control existing flames within a 5-meter radius at no cost (shape, move, intensify, or extinguish). Creating flames from nothing requires Conjure (1 SPI). Each additional 15 meters of range costs 1 SPI. "
         "All abilities below are part of Pyrokinesis.\n"
          "<b><font color='#C0392B'>Compress (1 SPI):</font></b> Compresses an existing flame before releasing it. "
           "Base damage is 1d6 burning. Each turn spent charging adds +3 damage (max +9, requiring 3 turns of charging).\n"
          "<b><font color='#C0392B'>Fire Armour (1 SPI):</font></b> Wreathes the body in protective flame, granting DR 1 and resistance to cold and poison effects. Lasts until dismissed.\n"
          "<b><font color='#C0392B'>Conjure (1 SPI):</font></b> Conjures a crude flame weapon (improvised weapon stats) that deals burning damage. Lasts 1 minute.\n"
          "<b><font color='#C0392B'>Area Burst (2 SPI):</font></b> Creates a burst of flame in a 3-meter radius. Targets take 1d6+1 burning damage (Dodge to halve).\n"
          "<b><font color='#C0392B'>Delay Explosions (2 SPI):</font></b> Sets a delayed flame trap. 1d6+3 burning damage on detonation (Dodge to halve). Lasts 1 hour or until triggered.\n"
          "<b><font color='#C0392B'>Fire Enchant (1 SPI):</font></b> Enchants a held weapon with flame. The weapon deals +1d6 burning damage for 1 minute. Affects spirits and incorporeal beings normally.\n"
           "<b><font color='#C0392B'>Fire Ravens (1 SPI per raven):</font></b> Conjures 1 flaming raven construct per SPI spent. "
           "Each raven has Move 8, HP 2, and deals 1d6-1 burning damage on impact (Dodge to avoid). Ravens disperse "
           "after 3 turns.\n"
            "<b><font color='#C0392B'>Fire Infusion (1 SPI per hit, free action):</font></b> When hitting a target with an unarmed strike, infuse it with 1 stack of Fire Infusion. On a subsequent turn, the Pyromaniac may detonate all stacks on a target as a standard action, dealing 1d6 burning damage per stack.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Environment Memory (Reinforced):</font></b> Range expands to 30 m. The Pyromaniac can "
           "replay the last 10 minutes of any fire source's surroundings (from 5 minutes). A successful "
           "Survival Knowledge analysis of a burned area reveals the exact cause of ignition and any "
           "metaphysical traces left behind.\n"
           "<b><font color='#C0392B'>Survival Knowledge (Reinforced):</font></b> The healing from a successful Survival Knowledge "
           "check increases to 1d6+2 HP (from 1d6+1). The Pyromaniac may apply this to self or an ally "
           "once per scene without needing to retreat from combat."),

        # ── Hermit Pathway ──

          ("Warlock", "Hermit Pathway",
            [("SPI", "+2")],
          [("Spiritual Intuition/SPI [Hard]", "+2"),
            ("Occultism/IQ [Average]", "+3"),
           ("Thaumatology/IQ [Very Hard]", "+4"),
           ("Hidden Lore (Mysticism)/IQ [Average]", "+2"),
           ("Alchemy/IQ [Very Hard]", "+2")],
           "<b><font color='#C0392B'>Spell Casting:</font></b> The Warlock's signature ability. Requires one turn of Concentration "
           "to gather Spirituality, then one turn to cast the spell. A material medium or component is required. "
           "Artifacts may substitute if the Warlock knows their function.\n"
           "Note: Due to the Law of Beyonder Indestructibility, spell mediums that are main potion ingredients are not "
           "exhausted after use. Other ingredients (spirituality-rich items without Beyonder characteristics) are one-time use.\n\n"
          "<b><font color='#C0392B'>Spell Creation System:</font></b> The Warlock can design new spells using Thaumatology.\n"
          "• The medium must have a concrete mystical connection. Roll Occultism to remember the connection.\n"
          "• Spirituality determines spell strength: 1 SPI for the effect, 2 SPI when strength is needed, 3 SPI for duration.\n"
          "• Roll Thaumatology to design the spell. Results:\n"
          "  — Success: Spell works but not flawlessly. SPI cost +2.\n"
          "  — Success by 3: Spell works as intended but inefficiently. SPI cost +1.\n"
          "  — Success by 5+: Masterfully designed. No cost increase.\n"
          "  — Critical Success: Masterpiece. SPI cost -1 (minimum 1 SPI).\n"
          "  — Failure: Fail to create the spell.\n"
          "  — Critical Failure: The spell WILL backfire. Roll IQ to understand — success means you realize "
           "the spell is flawed; failure means you don't.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Eyes of Mystery Prying (Reinforced):</font></b> The Warlock can now read surface thoughts "
           "of sleeping targets and glean dream content without a roll. Against waking targets, the "
           "penalty to the target's save increases to -4 (from -3). The Warlock may also learn 1 "
           "random weakness or fear of the target (GM discretion) on a successful use.\n"
           "<b><font color='#C0392B'>Quick Rituals (Reinforced):</font></b> The time reduction for known rituals improves to -5 "
           "(from -4). The Warlock can perform rituals at half the listed time (minimum 1 minute), "
           "and may maintain concentration on one ritual while taking Move-equivalent actions."),

        # ── Paragon Pathway ──

           ("Appraiser", "Paragon Pathway",
            [("Per", "+2"), ("SPI", "+1")],
            [("Appraisal/IQ [Average]", "+6")],
           "<b><font color='#C0392B'>Appraisal (Passive):</font></b> "
           "The Appraiser examines a Beyonder item, Mystical Item, or Sealed Artifact and instantly "
           "identifies its general purpose, dangers, and domain alignment (no roll for common items). "
           "For rare or complex items, roll Appraisal — success reveals 1 hidden property, "
           "success by 3+ reveals all immediate dangers. This does not bypass active curses or binding, "
           "but the Appraiser instinctively knows the safest way to handle the item "
            "(which side not to touch, which words not to speak, etc.).\n"
            "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
            "<b><font color='#C0392B'>Total Memory (Reinforced):</font></b> The Appraiser can recall the exact spiritual "
            "signature of any item they have appraised, allowing them to identify a disguised or "
            "altered version of the same item without a roll. The tactile memory now extends to "
            "textures and spiritual resonance, not just shapes.\n"
            "<b><font color='#C0392B'>Rapid Analysis (Reinforced):</font></b> One-quarter time is now one-fifth time (minimum "
            "1 second). The Appraiser may appraise an item instantly (free action) if it is a "
            "common type they have seen before."),

        # ── Wheel of Fortune Pathway ──

          ("Lucky One", "Wheel of Fortune Pathway",
            [("SPI", "+2"), ("Lucky One", "5 rerolls per session")],
          [],
          "<b><font color='#C0392B'>Passive Luck:</font></b> At session start, roll 1d6:\n"
          "<b>1</b> — Find 1d6 soli. No Passive Luck this session.\n"
          "<b>2–3</b> — Luck die = <b>1d6</b>.\n"
          "<b>4–5</b> — Luck die = <b>1d6+2</b>.\n"
          "<b>6</b> — Luck die = <b>2d6</b>.\n"
          "Once per session, after any 3d6 roll you make, you may subtract your luck die from the total "
           "(minimum 3). This can negate a critical failure (17–18).\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Foresight (Reinforced):</font></b> The Lucky One may use Foresight up to 3 times per "
           "session (from 2). The GM must warn the Lucky One of any impending danger at least "
           "3 seconds before it occurs (from 2 seconds), giving them a chance to take a "
           "defensive action.\n"
           "<b><font color='#C0392B'>Premonition (Reinforced):</font></b> When a Premonition triggers, the Lucky One gains "
           "+3 to any single roll made to avoid or mitigate the foreseen event (instead of +2). "
           "This bonus may be applied after seeing the roll result."),

        # ── Mother Pathway ──

            ("Harvest Priest", "Mother Pathway",
             [("IQ", "+1"), ("Per", "+1"), ("Will", "+1"),
              ("Disease Resistance", "+3 to HT vs disease and natural toxins"),
              ("SPI", "+2")],
            [("Farming/IQ [Easy]", "+4"),
             ("Naturalist/IQ [Hard]", "+3"),
            ("Survival (any)/Per [Average]", "+2"),
            ("Ritualistic Magic/IQ [Very Hard]", "+2 (Nature, Life, and Weather domains)")],
           "<b><font color='#C0392B'>Command Plants (2 SPI):</font></b> The Harvest Priest exerts authority over plant life and "
           "plant-based creatures within 20 meters. Resolve as a Quick Contest of SPI vs the target's Will "
           "(for intelligent plant creatures) or a straightforward roll (for mundane plants). "
           "Success: the target follows a simple command — entangle, release pollen, part foliage, grow "
           "thorns, or hold position — for up to 1 hour. Intelligent plant creatures may attempt a new Will "
           "roll each minute to break free. If the command harms the target or its allies, the target "
           "gets +3 to resist.\n"
           "<b><font color='#C0392B'>Weather Rituals (Ritualistic Magic):</font></b> Upon drinking the potion, the Harvest Priest "
           "obtains several Ritualistic Spells focused on manipulating the weather within a certain area. "
           "All are cast using Ritualistic Magic and cost SPI as noted.\n"
           "<b>Clear Skies (2 SPI):</b> Clears clouds, fog, and precipitation in a 200-meter radius over "
           "1d6 minutes. Works against natural weather only; supernatural weather effects resist with a "
           "Quick Contest of the caster's Ritualistic Magic vs the effect's source.\n"
           "<b>Summon Rain (2 SPI):</b> Conjures steady rain in a 200-meter radius. Takes effect over "
           "1d6 minutes. Can end droughts, water crops, or create cover. Does not produce lightning or storms.\n"
           "<b>Calm Winds (1 SPI):</b> Reduces wind speed in a 100-meter radius. Strong gales become "
           "breezes; hurricane-force drops to strong wind. Lasts 10 minutes.\n"
           "<b><font color='#C0392B'>Nature's Bounty (1 SPI):</font></b> Accelerates plant growth in a 5-meter radius. Crops, "
           "herbs, and medicinal plants mature in 1 minute. Produces enough food for 2 people per casting. "
           "Does not affect magical or spiritually-altered flora.\n"
           "<b><font color='#C0392B'>Restorative Harvest (2 SPI):</font></b> Touches a living plant and draws on its life force to "
           "heal the Priest or an ally for 1d HP. The plant wilts visibly for 24 hours and cannot be used "
           "again during that time.\n"
           "<b><font color='#C0392B'>Spirit Vision (Nature):</font></b> The Harvest Priest's Spirit Vision reads the health and "
           "spiritual state of natural life. Costs 1 SPI per minute. While active, senses disease, "
            "corruption, and unnatural influences within 100 meters.\n"
            "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
            "<b><font color='#C0392B'>Farming Tools (Reinforced):</font></b> The Harvest Priest can use any farming or "
            "gardening tool as a weapon at no default penalty, and the bonus to tool-based attacks "
            "increases to +5 (from +4). The tool counts as a Beyonder weapon of the Priest's Sequence "
            "for harming spiritual entities.\n"
            "<b><font color='#C0392B'>Physician (Reinforced):</font></b> The +3 bonus to Physician checks now applies to "
            "diagnosing and treating supernatural ailments (spiritual contamination, Beyonder-induced "
            "illnesses, curses with biological symptoms). The healing time for natural diseases under "
            "the Harvest Priest's care is halved.\n"
            "<b><font color='#C0392B'>Potion Brewing (Reinforced):</font></b> The -1 penalty for brewing Potions without a "
            "proper lab is eliminated entirely when working with natural ingredients (herbs, plants, "
            "mineral salts). Brewing time for healing potions is reduced by half."),

        # ── Moon Pathway ──

            ("Vampire", "Moon Pathway",
              [("SPI", "+2"), ("Basic Speed", "+1"), ("ST", "+3"), ("Per", "+2"), ("DX", "+2"),
              ("Spirituality Absorption", "when feasting on spiritually rich blood, restore SPI")],
          [("Ritualistic Magic/IQ [Very Hard]", "+3 (Moon, Darkness and Shadow domains)"),
           ("Hidden Lore (Darkness, Shadow and Moon domains)/IQ [Average]", "+3")],
           "<b><font color='#C0392B'>Wings of Flight (1 SPI):</font></b> "
           "Gain +2 Basic Move for flight for 1 minute. Extended flight costs 1 SPI per additional minute.\n"
           "<b><font color='#C0392B'>Bat Swarm Form (3 SPI):</font></b> "
           "Transform into a swarm of illusory bats for 1 minute. In this form you are immune to physical damage "
           "from non-magical weapons. You may emit black gases that poison a target for 1d6 damage over 2 turns "
           "(HT roll to resist), or create black flames that deal 1d6 burn per turn for 4 turns. "
           "Cannot use other abilities while in swarm form.\n"
           "<b><font color='#C0392B'>Corrosive Claw (2 SPI):</font></b> An innate melee attack (Brawling skill). "
           "Counts as a knife for damage purposes (thr-1 cut / sw-2 imp). Ignores natural DR — skin, hide, fur, "
           "scales, chitin, and membrane — but not manufactured armour or magical DR.\n"
          "<b><font color='#C0392B'>Abyss Shackles (2 SPI):</font></b> A spell belonging to the Darkness domain "
          "that condenses nearby shadow and darkness into tangible shackles to restrict and control the enemy. "
          "Roll Ritualistic Magic vs the target's HT. On success, the target is bound for 3 turns. "
          "The target may attempt to break free with a ST-3 roll each turn. "
          "If the caster's concentration is broken, the shackles dissolve immediately.\n"
          "<b><font color='#C0392B'>The Embrace (7 SPI):</font></b> When a Vampire has fully digested their current Sequence and "
           "possesses at least 1 surplus Beyonder characteristic (representing excess essence beyond what their "
           "own advancement requires), they may bestow it upon a willing or helpless human through a 1-hour "
           "ritual. The target rises as a Sequence 7 Vampire after 1d3 hours. The Vampire "
           "permanently loses 1 max SPI per use until they consume and digest additional potion material to "
           "replenish the lost characteristic.\n"
          "<b><font color='#C0392B'>Blood Servant Conversion (3 SPI):</font></b> "
          "A spell that a Vampire can use to turn a willing or helpless living creature into a blood servant. "
          "Roll Ritualistic Magic. On success, the target becomes a blood servant: they cannot disobey a direct "
          "order from the Vampire, all mundane illnesses are cured, and they permanently gain +2 HT and +2 HP. "
          "The bond lasts until the blood servant dies or the Vampire voluntarily releases them. "
           "Failure: SPI is spent, no effect. Critical Failure: the target becomes hostile and gains +2 to all "
             "actions against the Vampire for 24 hours.\n"
             "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
             "<b><font color='#C0392B'>Spirit Vision (Animals) (Reinforced):</font></b> The Vampire's animal Spirit Vision "
             "range expands to 80 m (from 50 m). The Vampire can read an animal's emotional state, "
             "recent memories (last 24 hours), and whether it has been spiritually tampered with.\n"
             "<b><font color='#C0392B'>Beast Taming (Reinforced):</font></b> The Vampire can now control up to 3 animals "
             "simultaneously (from 2) and may issue complex multi-step commands. Animals under "
             "the Vampire's control gain +2 to ST and +1 Basic Speed.\n"
             "<b><font color='#C0392B'>Physician (Animal) (Reinforced):</font></b> The +3 Physician bonus now applies to "
             "the Vampire's own natural healing processes — recover +1 extra HP per day of rest. "
             "The Vampire may also use Physician to diagnose spiritual ailments in animals and "
             "moon-aligned creatures without penalty.",
              [("Vampire Diet", "can only drink spiritually rich blood"),
              ("Sun Allergy", "extreme discomfort under direct sunlight"),
              ("Purification Weakness", "2d6 damage if targeted by purification"),
              ("Slow-beating Heart", "piercing/stake attacks to the heart deal ×2 damage")]),

        # ── Abyss Pathway ──

            ("Serial Killer", "Abyss Pathway",
             [("IQ", "+2"), ("SPI", "+1")],
           [("Ritualistic Magic/IQ [Very Hard]", "+2")],
           "<b><font color='#C0392B'>Interference (Ritual):</font></b> "
           "The Serial Killer may sacrifice a living being in a 1-hour ritual to shroud themselves "
           "in sacrificial residue. Animal sacrifice: Divination and Spirit Channeling targeting the "
           "Serial Killer are at -2 for 1d6 days. Human sacrifice: -4 for 1d6 days.\n"
           "<b><font color='#C0392B'>Devil Worship (Ritual):</font></b> Requires a unique serial killing spree "
           "(minimum 3 murders) without being caught. Once all cases are officially closed, the "
           "Serial Killer may perform a ritual (standard ritual rules) to summon a Devil projection. "
           "Roll 3d6 + modifiers vs Ritualistic Magic — lower roll = more favorable outcome. "
           "The GM determines the Devil's ST, IQ, and Favourability (roll 3d6 for each if desired; "
           "lower = better on all three). Failure: ritual fails; the killing spree must be repeated "
            "from scratch.\n"
            "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
            "<b><font color='#C0392B'>Enhance Improvised Weapons (Reinforced):</font></b> The Serial Killer's improvised "
            "weapon skill increases to Brawling+3 (from Brawling+2). The weapon counts as a Beyonder "
            "weapon of the Serial Killer's Sequence, and on a critical hit, the improvised weapon "
            "breaks in a way that deals an additional 1d6 corrosion damage.\n"
            "<b><font color='#C0392B'>Firearms Proficiency (Reinforced):</font></b> The DX bonus increases to +2 (from +1). "
            "The Serial Killer may fire two shots as a single Attack maneuver without the usual "
            "dual-wield penalties, provided both shots target the same enemy.\n"
            "<b><font color='#C0392B'>Poison Enhancement (Reinforced):</font></b> The +2 bonus to poison-crafting rolls "
            "now applies to identifying and creating supernatural toxins (spiritual venom, "
             "corrupted elixirs). The Serial Killer's poisons also affect spirits and incorporeal "
             "beings at half potency (round down)."),

         # ── Chained Pathway ──

          ("Werewolf", "Chained Pathway",
           [("ST", "+3"), ("DX", "+1"), ("HT", "+1"), ("SPI", "+1"),
            ("DR 2 (all)", "physical toughness even outside transformation"),
            ("Regeneration (fast)", "recover 1 HP per minute while in Full Transformation only"),
            ("Basic Move", "+1"),
            ("Night Vision 9", "see clearly in near-total darkness; no penalties in moonlight or starlight")],
           [("Brawling/DX [Easy]", "+4"),
            ("Intimidation/Will [Average]", "+4"),
            ("Survival (any)/Per [Average]", "+3"),
            ("Stealth/DX [Average]", "+2"),
            ("Tracking/Per [Average]", "+3")],
          "<b><font color='#C0392B'>Partial Transformation (1 SPI per feature):</font></b> "
          "Manifest individual werewolf features — claws, venom, or enhanced speed — without full transformation. "
          "Each feature costs 1 SPI and lasts the scene.\n"
          "<b><font color='#C0392B'>Full Transformation (1 SPI):</font></b> "
          "Ready maneuver to transform completely. Lasts 1 minute (extend at 1 SPI per minute). While transformed:\n"
           "• ST +3, DX +2 (adds to base potion stats)\n"
          "• Claws: sw+2 cut; Bite: thr+2 imp. Both count as Beyonder weapons of the Werewolf's Sequence\n"
          "• Venom: on a hit that breaks skin, target rolls HT-2 each round for 1d rounds or suffers -2 to all "
          "physical rolls. Failure by 5+ causes partial muscle control loss for 1d minutes\n"
          "• Speed: +1 Basic Move (stacks with base potion bonus for +2 total). Opponents roll Per-2 to track position at full speed\n"
          "• Regeneration (Fast): 1 HP per minute. Sun-domain damage heals at normal rate\n"
          "<b><font color='#C0392B'>Weakness — Sun Vulnerability:</font></b> Sun-domain abilities deal double damage "
          "and ignore DR entirely. Regeneration suspended for 1 minute after a Sun-domain hit.\n"
          "<b><font color='#C0392B'>Werewolf Kin (1 SPI):</font></b> When a target has failed its HT roll against venom, "
          "spend 1 SPI and make a Quick Contest of SPI vs the target's Will. On success, the target becomes a "
          "puppet Werewolf for 1d hours — ST 14, DX 10, claws only, no special abilities. "
          "Collapses and reverts at duration's end or at 0 HP.\n"
          "<b><font color='#C0392B'>Dark Horror (1 SPI):</font></b> Free action. Deepens darkness within 10 meters — faint light "
          "sources extinguished, moonlight banished. Targets roll Will or suffer -2 to rational thought and movement for 1d rounds. "
          "Fail by 5+ — paralyzed with dread for one round. Strong light sources reduce radius to 5 meters. "
          "Sun-domain holy light negates entirely.\n"
          "<b><font color='#C0392B'>Repel Light (Free):</font></b> Free action. Pushes back faint illumination — candles, distant gas "
          "lamps, ambient moonlight — within 5 meters. No effect against strong or supernatural light. Primarily maintains "
          "darkness during Dark Horror.\n"
          "<b><font color='#C0392B'>Anti-Divination (Passive):</font></b> Any divination or Spirit Vision targeting the Werewolf reveals "
          "only a figure covered in black hair regardless of transformation state. True identity, Sequence, pathway, emotional "
          "state, and location cannot be read through any spiritual means. Higher-Sequence Beyonders (Seq 5+) may bypass "
          "this with a Quick Contest of SPI vs the Werewolf's SPI.\n"
          "<b><font color='#C0392B'>Werewolf's Curse — Full Moon:</font></b> Every full moon roll Will-3 or enter uncontrolled "
          "semi-transformed state — predatory, bloodlust-driven, aware but unable to fully suppress. Consistent failures "
          "accumulate as narrative disadvantage toward permanent personality change and loss of humanity. Certain Sealed "
          "Artifacts corresponding to the Scarlet Scholar allow rationality to be maintained during full moon. "
          "Acquiring one is a significant campaign goal.\n"
          "<b><font color='#C0392B'>Lunatic's Curse — Retained:</font></b> All corruption thresholds remain reduced by 2. "
           "Full moon curse stacks with existing instability.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Improvised Weapons Expertise (Reinforced):</font></b> The Werewolf's improvised weapon "
           "damage bonus increases to +2 (from +1). Any object used as a weapon also counts as a "
           "Beyonder weapon of the Werewolf's Sequence, and on a successful hit, the target must "
           "roll HT or be Shaken (see GURPS p. B360) for 1 turn.\n"
           "<b><font color='#C0392B'>Escape Artist (Reinforced):</font></b> The Werewolf may attempt to escape supernatural "
           "bonds (magical restraints, spirit chains, shadow shackles) at full Escape skill with "
           "+2. Against mundane restraints, escape is automatic unless the restraints are "
           "specifically designed to hold a supernatural creature.\n"
           "<b><font color='#C0392B'>Hidden Exits Sense (Reinforced):</font></b> Range expands to 30 m (from 20 m). "
           "The Werewolf can sense hidden exits even when they are magically concealed — the "
           "ability pierces concealment up to Seq 7 level.",
             [("Sun Vulnerability", "Sun-domain abilities deal double damage and ignore DR entirely; regeneration suspended for 1 minute after a Sun-domain hit"),
             ("Full Moon Curse", "Every full moon roll Will-3 or enter uncontrolled semi-transformed state; consistent failures accumulate toward permanent personality change")]),

        # ── Justiciar Pathway ──

           ("Interrogator", "Justiciar Pathway",
            [("ST", "+2"), ("SPI", "+5")],
          [("Brawling/DX [Easy]", "+2"),
            ("Guns (any)/DX [Easy]", "+1"),
            ("Explosives (Demolition)/IQ [Average]", "+2")],
           "<b><font color='#C0392B'>Illusory Torture Devices (1 SPI):</font></b> An Interrogator can shape their spirituality into "
           "any kind of torture device. The device must be held, or it ceases to exist. "
           "The device deals spirit body damage (see Chapter 5) as a small weapon (Knife): thr-1 cut / sw-2 imp.\n"
            "<b><font color='#C0392B'>Psychic Lashing (2 SPI):</font></b> Coats a held object with illusory lightning for 1 minute. "
            "Attacks deal +2 spirit body damage (see Chapter 5) in addition to normal damage. Melee range.\n"
            "<b><font color='#C0392B'>Psychic Piercing (1 SPI):</font></b> Range 5 meters. Target rolls HT or is mentally Stunned for 1 turn "
            "(see GURPS stun rules, p. B420: -4 to active defenses, may attempt HT each turn to recover). Deals 2d6-3 spirit body damage (see Chapter 5).\n"
           "<b><font color='#C0392B'>Whip of Pain (1 SPI):</font></b> Deals continuous 1d6-3 spirit body damage per turn and "
           "costs 1 SPI each turn to maintain. Target must roll HT or be mentally Stunned for 1 turn "
            "(GURPS stun rules, p. B420). On subsequent turns, the target may roll Will to recover from the stun.\n"
            "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
            "<b><font color='#C0392B'>Authority (Reinforced):</font></b> The Will penalty for targets within the Interrogator's "
            "Jurisdiction increases to -4 (from -2). The Interrogator may also project Authority "
            "as a free action once per scene, causing all hostile NPCs within 10 m to hesitate "
            "for 1 turn (no actions except active defenses). This does not affect PCs or major NPCs.\n"
            "<b><font color='#C0392B'>Jurisdiction (Reinforced):</font></b> The Interrogator's knowledge of local laws, "
            "procedures, and loopholes now extends to neighbouring jurisdictions. Rote legal knowledge "
            "is automatic — no roll needed. For obscure or hidden regulations, the IQ bonus increases "
            "to +4 (from +2)."),

        # ── Black Emperor Pathway ──

         ("Briber", "Black Emperor Pathway",
           [("SPI", "+4")],
           [],
           "<b><font color='#C0392B'>Bribery (1 SPI):</font></b> All Bribe effects cost 1 SPI each to activate. By offering the target a symbolic or material bribe, you impose one of four "
           "effects on them. The bribe does not need to be willingly accepted — throwing an object counts as a valid bribe "
           "as long as the target interacts with it or is simply near it. Make a DX roll (or Throwing skill, if known) to land the bribe. "
           "If the bribe is thrown and misses: a margin of "
           "failure of 1–2 still counts, but duration becomes halved.\n"
           "<b><font color='#C0392B'>Diminishing Rule (applies to all Bribe effects):</font></b> At the end of each turn, the penalty/bonus decreases by 1. "
           "Once it reaches 0, the effect ends.\n\n"
          "<b><font color='#C0392B'>Weaken:</font></b> Target suffers -4 to attack and defense rolls (drops -1/turn, lasts 4 turns).\n"
          "<b><font color='#C0392B'>Charm (1 SPI):</font></b> Target rolls Will at -3 each turn (drops -1/turn, 3 turns max). "
          "Failure: target will not attack the briber that turn. Critical Failure: target lashes out at self or allies.\n"
          "<b><font color='#C0392B'>Arrogance (1 SPI):</font></b> Target rolls IQ at -2 each turn (drops -1/turn, 2 turns max). "
          "Failure: target makes a reckless or stupid action (GM discretion). Critical Failure: target loses their turn.\n"
           "<b><font color='#C0392B'>Connection (1 SPI):</font></b> Mystical link to target. You gain +2 to Divination and Tracking rolls against them (drops -1/turn, 2 turns max).\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Eloquence (Reinforced):</font></b> When using Eloquence through Intimidation, the "
           "target's Will penalty increases to -5 (from -3). The Briber may also use Eloquence "
           "through Diplomacy or Fast-Talk (choose one per scene) with a -2 penalty to the "
           "target's save instead of -5.\n"
           "<b><font color='#C0392B'>Intimidation (Reinforced):</font></b> The Intimidation skill bonus from Barbarian "
           "increases by +2 (total +4 from all sources). If the Briber successfully Intimidates "
           "a target, the next Bribery attempt against that target in the same scene has its "
           "SPI cost reduced by 1 (minimum 1 SPI)."),
          ]

    for entry in seq7_pathways:
        title, pathway, stats, skills, ability = entry[:5]
        disadvantages = entry[5] if len(entry) > 5 else []

        story.append(sp(4))
        story += subsection(f"Sequence 7: {title}  ·  {pathway}")
        story.append(sp(2))

        # Build merged stat + disadvantages table (continuous, with divider)
        if stats or skills or disadvantages:
            stat_rows = [[Paragraph("Stat / Advantage", S['TableHeader']), Paragraph("Gain", S['TableHeader'])]]
            for k, v in stats:
                stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            divider_idx = None
            if disadvantages:
                divider_idx = len(stat_rows)
                # Divider row — matches header style (navy bg, cream text, bold)
                stat_rows.append([Paragraph("<b>Drawbacks</b>", S['TableHeader']),
                                  Paragraph("", S['TableHeader'])])
                for k, v in disadvantages:
                    stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            stat_t = Table(stat_rows, colWidths=[1.55*inch, 1.55*inch])
            stat_t.setStyle(table_style())
            if divider_idx is not None:
                stat_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, divider_idx), (-1, divider_idx), MID_NAVY),
                    ('LINEABOVE', (0, divider_idx), (-1, divider_idx), 0.5, GOLD),
                    ('TOPPADDING', (0, divider_idx), (-1, divider_idx), 3),
                    ('BOTTOMPADDING', (0, divider_idx), (-1, divider_idx), 3),
                ]))

            if skills:
                skill_rows = [[Paragraph("Skill", S['TableHeader']), Paragraph("Change", S['TableHeader'])]]
                for k, v in skills:
                    skill_rows.append([
                        Paragraph(k, S['TableCell']),
                        Paragraph(v, S['TableCell']),
                    ])
                skill_t = Table(skill_rows, colWidths=[2.4*inch, 0.85*inch])
                skill_t.setStyle(table_style())

                # Combo: merged stat table + skills table side by side
                combo = Table([[stat_t, skill_t]], colWidths=[3.2*inch, 3.35*inch])
            else:
                combo = Table([[stat_t]], colWidths=[6.4*inch])

            combo.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(combo)
        else:
            story.append(Paragraph("<i>No stat or skill changes at this Sequence.</i>", S['Body']))
        
        story.append(sp(3))

        # Ability block (with optional Reinforced box)
        main_ab, reinf_ab = split_reinforced(ability)
        render_ability_boxes(main_ab, reinf_ab, story)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════════
    # Chapter 12: Sequence 6 Potion Effects
    # ═══════════════════════════════════════════════════════════════════════════════

    story += chapter("Chapter 12: Sequence 6 Potion Effects")
    story.append(body(
        "Sequence 6 represents a significant leap in power. Beyonders at this level begin to exhibit "
        "truly supernatural capabilities that transcend mere skill enhancement."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Reading these entries:</b> See <b>Chapter 9</b> for instructions on how to read a pathway entry. "
        "The same rules for potion-granted skills and attributes from Chapter 9 apply here."
    ))
    story.append(sp(2))

    seq6_pathways = [

         # ── Fool Pathway ──

          ("Faceless", "Fool Pathway",
           [("SPI", "+2")],
           [("Acting/IQ [Average]", "+4"),
            ("Divination Arts/SPI [Hard]", "+2"),
            ("Brawling/DX [Easy]", "+2"),
            ("Observation/PER [Average]", "+4")],
          "<b><font color='#C0392B'>Shapeshifting:</font></b> The Faceless can freely mould their body and flesh, "
          "enabling them to perfectly mimic their target's face, body, voice, and even smell to some degree. "
          "It is not possible for a Faceless to change their gender. Their new height cannot be more than "
          "a head taller or shorter than their original height (15/20 cm). They can make their face completely "
          "featureless, without any eyes, nose, or mouth. They can change their body odour by adjusting the "
          "pores on their skin. To successfully impersonate someone in front of a person who knows the person "
          "being impersonated, the Faceless must succeed an Acting roll, or the person will grow suspicious. "
          "Not knowing the person being impersonated well causes a -3 penalty to the roll.\n"
          "<b><font color='#C0392B'>Identity Confusion (2 SPI):</font></b> The Faceless can mask their spiritual "
          "aura to match a different person they have studied or touched. If a divination targets the "
          "Faceless's original identity, it instead picks up the masked aura — leading the diviner to the "
          "wrong person. Duration: 1 hour, or until the Faceless changes their masked identity. The Faceless "
          "must have met or studied the target whose aura they mimic — a simple description is not enough; "
          "10+ minutes of close observation or a personal item is required. A diviner who critically succeeds "
          "on their Divination Arts or Ritualistic Magic roll realises the spiritual signature is a mask and "
          "may attempt a Quick Contest of Divination Arts or Ritualistic Magic vs the Faceless's SPI to pierce it.\n"
          "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
          "<b><font color='#C0392B'>Flaming Jump (1 SPI):</font></b> Range increased to 40 m.\n"
          "<b><font color='#C0392B'>Flame Controlling (1 SPI):</font></b> Range increased to 40 m.\n"
          "<b><font color='#C0392B'>Illusion Creation (1 SPI):</font></b> Range increased to 26 m.\n"
           "<b><font color='#C0392B'>Air Bullet (1 SPI):</font></b> Damage increased to 2d+2 pi (range 20/40)."),

         # ── Black Emperor Pathway ──

          ("Baron of Corruption", "Black Emperor Pathway",
           [("ST", "+6"), ("SPI", "+3")],
           [],
          "<b><font color='#C0392B'>Distortion (3 SPI):</font></b> The Baron of Corruption can use the loopholes found in Order. "
          "By distorting the target's words, actions, and intent, they can formulate a certain Order that provides "
          "them with an advantage, restraining and influencing their opponent. They can distort the direction and "
          "target of attacks. They can Seal ordinary rooms or Unseal confined spaces. The extent to which they can "
          "distort the direction and target of attacks is at the GM's discretion.\n"
            "<b><font color='#C0392B'>Corrosion (2 SPI):</font></b> The Baron of Corruption can turn the hearts of people within "
            "10 metres dark and greedy, making them make irrational choices.\n"
            "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
            "<b><font color='#C0392B'>Bribery — All Effects (Reinforced):</font></b> The Briber's Weaken penalty increases "
            "to -6 (from -4). Charm's Will penalty increases to -5 (from -3). "
            "Connection's bonus increases to +4 (from +2). The Diminishing Rule still applies.\n"
            "<b><font color='#C0392B'>Eloquence (Reinforced):</font></b> The Baron of Corruption may use Eloquence as a "
            "free action once per scene to impose the Arrogance effect on a target within "
            "10 m without spending SPI. The target rolls IQ-2 as usual."),

          # ── Justiciar Pathway ──

             ("Judge", "Justiciar Pathway",
              [("SPI", "+4"), ("Ancient Hermes", "Fluent — can speak, read, and write this dead mystical language")],
            [("Law (specify)/IQ [Hard]", "+4"),
             ("Brawling/DX [Easy]", "+2"),
             ("Intimidation/Will [Average]", "+2")],
             "<b><font color='#C0392B'>Prohibition (2 SPI):</font></b> Speak in Ancient Hermes to forbid certain actions or "
              "Beyonder powers within a 10-meter radius — no contest required. "
              "Format: <i>\"'X' is Prohibited here\"</i>. Examples: Flight, "
              "Teleportation, Invisibility. Violators suffer <b>-12</b> "
              "to all rolls involving the prohibited action. Targets with SPI higher than the Judge's suffer "
              "<b>-6</b> instead. Cannot kill specific individuals — suppresses or repels them instead. "
              "Suppressed if the target is 3+ Sequences above the Judge.\n"
              "<b><font color='#C0392B'>Imprison (2 SPI):</font></b> Range: LOS, up to 15 m. "
              "Freezes one target in place. "
              "Breaking free requires <b>ST-4</b> or <b>Escape-4</b> "
              "each turn. Roots Spirit Body-type creatures, but cannot prevent escape via "
              "Substitution abilities. Declare <i>\"Release\"</i> to end early.\n"
              "<b><font color='#C0392B'>Confinement (2 SPI):</font></b> Range: LOS, up to 10 m. "
              "Area variant of Imprison — immaterial cell around a designated area, impenetrable by Spirit Bodies. "
              "Circumvents Substitution — targets reappear within boundaries. "
              "Can seal a room against entry or exit.\n"
             "<b><font color='#C0392B'>Maintain Secrecy (1 SPI):</font></b> Eye contact. "
             "<b>Quick Contest:</b> Judge's SPI vs. target's Will. On failure, the target cannot voluntarily "
             "reveal the Judge's secrets or disobey a simple instruction for 1 hour, and must actively conceal them. "
             "Mind-affecting compulsion. May release early.\n"
             "<b><font color='#C0392B'>Death (3 SPI):</font></b> Declare target Dead, then charge. "
             "Roll <b>Brawling</b> or <b>DX</b> to hit. Deals "
             "<b>swing crushing damage × hit location wounding "
             "multiplier</b> (e.g., skull ×4, vitals ×3).\n"
             "<b><font color='#C0392B'>Flog (1 SPI):</font></b> Swing hand to strike with an invisible whip. "
             "Roll <b>Brawling +2</b> or "
             "<b>DX +2</b> to hit. Deals <b>2d+3 cutting</b>; ignores <b>1 DR</b>. "
             "Invisible — unaware targets cannot defend unless they suspect attack.\n"
             "<b><font color='#C0392B'>Exile (X SPI):</font></b> Speak <i>\"Exile\"</i> to blast the target away. "
             "Per SPI spent (1-5), hurl target <b>20 meters</b> in a chosen direction. "
             "Target rolls <b>HT-4</b> to halve distance. Affects Spirit Bodies. "
             "Collision deals <b>1d crushing per 10 meters</b> travelled (or fraction).\n"
             "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
              "<b><font color='#C0392B'>Authority (Reinforced):</font></b> Still costs 1 SPI to activate for the scene. "
              "Aura forces anyone meeting the Judge's eyes to roll <b>Will</b> or suffer <b>-1</b> to attack rolls "
              "against the Judge for that turn. Can subtly influence environment within 10 m "
              "(still air, dim lights, quiet sounds). Authority's <b>-1</b> penalty applies to all hostile actions "
              "within earshot that violate the Judge's stated rules.\n"
              "<b><font color='#C0392B'>Jurisdiction (Reinforced):</font></b> Maximum range approaches "
              "the size of Backlund. While inside Jurisdiction, the Judge gains "
              "<b>+2</b> to Law, Intimidation, and Administration rolls."),

          # ── White Tower Pathway ──

           ("Polymath", "White Tower Pathway",
            [("SPI", "+5"), ("Jack-of-all-trade", "Reduce study time by half")],
            [("Thaumatology/IQ [Very Hard]", "+2"),
             ("Research/IQ [Average]", "+2"),
             ("Observation/Per [Average]", "+2")],
            "<b><font color='#C0392B'>Analysis (1 SPI):</font></b> Roll <b>Thaumatology</b> to analyze a Beyonder power used by an opponent. "
            "Bonuses by target Sequence: +3 (Seq 9), +2 (Seq 8), +1 (Seq 7), +0 (Seq 6), -3 (Seq 5), -8 (Seq 4). "
            "Success reveals the exact details of the ability. Failure wastes the SPI — no information gained.\n"
            "<b><font color='#C0392B'>Imitation (2 SPI):</font></b> After a successful Analysis, imitate the analyzed power. "
            "Roll <b>Thaumatology</b>. Bonus based on Analysis margin of success:\n"
            "• +0 (by 0-2) → 20% efficiency\n"
            "• +2 (by 3-5) → 35% efficiency\n"
            "• +4 (by 6+) → 50% efficiency\n"
            "• +6 (crit) → 50% efficiency (Seq 4 powers do not receive the crit bonus)\n"
            "Damage abilities deal <b>half damage</b> at all efficiency levels. "
            "Non-damage abilities have range or effect reduced proportionally. "
            "Can imitate passive powers (Danger Premonition, Fate powers) and active powers (Recording). "
             "Cannot imitate Authorities at any Sequence."),

            # ── Tyrant Pathway ──

           ("Wind-blessed", "Tyrant Pathway",
            [("SPI", "+7")],
            [("Weather Sense/IQ [Average]", "+2"),
             ("Throwing/DX [Average]", "+2"),
             ("Aerobatics/DX [Hard]", "+2")],
            "<b><font color='#C0392B'>Wind Control (3 SPI):</font></b> Surround yourself with howling winds for 1 minute. "
            "Ranged attacks against you suffer <b>-4</b> to hit. Melee attackers within 2 m must roll <b>ST</b> or be pushed back 1d m.\n"
            "<b><font color='#C0392B'>Windblades (3 SPI):</font></b> Create invisible sharp wind blades at range. "
            "Roll <b>Throwing</b> or <b>DX</b> to hit. Deals <b>3d+3 cutting</b>. Range 20/40 m. Target may dodge.\n"
            "<b><font color='#C0392B'>Flight (1 SPI):</font></b> Fly at Basic Move ×1.5, max altitude 10 m. Duration 1 minute (extend at 1 SPI/min).\n"
            "<b><font color='#C0392B'>Floating Wind (1 SPI):</font></b> Hover in place up to 1 m off the ground for 1 minute.\n"
            "<b><font color='#C0392B'>Wind Footing (1 SPI):</font></b> Generate wind beneath feet — Move ×2 for 1 minute.\n"
            "<b><font color='#C0392B'>Glide (1 SPI):</font></b> Glide at normal Move, losing 1 m altitude per 3 m forward. "
            "Functions even if Flight is Prohibited by a Judge.\n"
            "<b><font color='#C0392B'>Wind Fist (1 SPI):</font></b> Imbue fists with spiraling wind for 1 minute. "
            "Unarmed strikes deal <b>+1d crushing</b> damage.\n"
            "<b><font color='#C0392B'>Wind Manipulation (1 SPI):</font></b> Use wind to carry small objects (up to 1 kg) to your hand within 10 m. "
            "Also eavesdrop on conversations within 20 m via wind vibrations. Duration 1 minute.\n"
            "<b><font color='#C0392B'>Wind Cushion (X SPI):</font></b> Reactive. When you would take damage, spend SPI to create an air cushion. "
            "Gain <b>DR 3 per SPI</b> spent against that single instance. Decide before damage is rolled.\n"
            "<b><font color='#C0392B'>Water Control (X SPI):</font></b> Manipulate and shape water within 10 m. "
            "1 SPI for simple shapes or moving water; 2 SPI for complex manipulation (GM discretion).\n"
            "<b><font color='#C0392B'>Deep Dive (Passive):</font></b> Dive to 100 m depth without pressure penalties.\n"
            "<b><font color='#C0392B'>Float (1 SPI):</font></b> Float on water without sinking for 10 minutes.\n"
            "<b><font color='#C0392B'>Night Vision (Passive):</font></b> See clearly in darkness up to normal vision range.",
            [("Irascible", "GM may remind the player to roleplay irritability matching a gale. "
              "Refusing to act irascible when appropriate may incur a penalty at GM discretion.")]),

         # ── Error Pathway ──

          ("Prometheus", "Error Pathway",
           [("ST", "+1"), ("DX", "+1"), ("SPI", "+3")],
           [("Sleight of Hand/DX [Hard]", "+2")],
           "<b><font color='#C0392B'>Mental Fortitude (Passive):</font></b> The Prometheus has hardened their mind against "
           "mental corruption. Reduce any CoR gained from purely mental sources (psychic attacks, "
           "madness-inducing effects, mental influence, and similar effects) by 3 (minimum 0). "
           "This does not protect against physical or spiritual corruption.\n"
           "<b><font color='#C0392B'>Superior Observation (Passive):</font></b> The Prometheus can directly sense where "
           "valuable items are within a 50-meter range, their approximate value, and possible types. "
           "Unless there are Beyonder powers of Concealment that can resist this type of perception, "
           "no treasure can escape a Prometheus' nose.\n"
           "<b><font color='#C0392B'>Steal (1+ SPI):</font></b> The Prometheus can steal many things within a 50 m radius.\n"
           "<b>Steal Beyonder Power (2 SPI):</b> Choose a target and a specific Beyonder power you have witnessed them use. "
           "Roll Thaumatology with modifiers:\n"
           "• +4 per Sequence below the Prometheus\n"
           "• -4 per Sequence above the Prometheus\n"
           "• +2 if you have studied or witnessed the target's power multiple times\n"
           "• -2 if the power is poorly understood or unfamiliar\n"
           "Success: you steal that power and may use it freely for the next 10 minutes at its full potency. "
           "The target loses access to the power for at least 12 hours. "
           "A power already activated before the theft continues functioning normally.\n"
           "<b>Steal Object (1 SPI):</b> Roll Sleight of Hand to covertly steal a visible object from a target within 50 m "
           "(a held item, worn necklace, pocketed key) or to slip a held object into a target's pocket or hand "
           "within the same range. Resisted by the target's Per if they might notice, or by an opposed "
           "Sleight of Hand roll if they are alert.\n"
           "<b>Steal Fire (1 SPI):</b> Steal flame itself — extinguish any non-magical fire within 50 m immediately. "
           "Magical fire (Beyonder flames) requires a Thaumatology roll at -2 to extinguish.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Decryption (Reinforced):</font></b> Decryption now requires only 1 minute of "
           "concentration (instead of the usual time) for mundane subjects, and 5 minutes for mystical subjects. "
           "The Prometheus automatically receives at least a Standard fact on any successful roll.\n"
           "<b><font color='#C0392B'>Beyonder Knowledge (Reinforced):</font></b> By handling a mystical item or ritual "
           "component for 1 turn, the Prometheus intuitively senses its general purpose and relative danger — no roll required.\n"
           "<b><font color='#C0392B'>Superior Observation (Reinforced):</font></b> The Cryptologist's trained observation "
           "range expands to 50 m, now matching the Prometheus's innate range. The Prometheus can sense whether a "
           "concealed target within range is a Beyonder, though not their specific Sequence or pathway. "
           "Detect Lies and Body Language rolls gain +4 (from +3).\n"
           "<b><font color='#C0392B'>Mental Disruption (Reinforced):</font></b> The Will penalty increases to -5. "
           "The Prometheus may target up to 3 individuals simultaneously by spending 3 SPI total.\n"
           "<b><font color='#C0392B'>Reminder / Theft (Reinforced):</font></b> Reminder distance increases to 15 m. "
           "The Prometheus can now steal spiritual materials that are actively in use by a target "
           "(e.g., a talisman being held ready for casting) by winning a Quick Contest of "
           "Thaumatology vs. the target's Will."),

            # ── Door Pathway ──

            ("Scribe", "Door Pathway",
           [("SPI", "+4")],
           [],
           "<b><font color='#C0392B'>Record (1 SPI):</font></b> After witnessing an active Beyonder power being used, "
          "roll 3d6 against the target below based on the power's origin Sequence. Success stores one use of that power; "
          "failure wastes the SPI. Only active (not passive) powers can be Recorded.\n"
          "<b>Record target (roll 3d6 ≤ target):</b>\n"
          "Seq 7-9: 15 | Seq 6: 11 | Seq 5: 9 | Seq 4: 5 (cannot succeed even after 10 attempts)\n"
          "<b>Storage slots:</b> 1 Demigod-level power (2 after full digestion), 8 Seq 5-6 powers, 20 Seq 7-9 powers.\n"
           "If a Seq 7 power is demonstrated by a Seq 5 Beyonder and stored in a Seq 7 slot, it manifests at Seq 6 level.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Crystal Ball Focus (Reinforced):</font></b> When using a crystal ball for divination, "
           "the bonus to Ritualistic Magic rolls increases to +4 (from +2). The Scribe may also "
           "use a crystal ball to Record a power seen within the ball's reflection, as long as "
           "the power was demonstrated within the past 24 hours.\n"
           "<b><font color='#C0392B'>Interference (Reinforced):</font></b> The SPI contest for anti-divination gains +3 "
           "in the Scribe's favour. The Scribe may extend Interference to cover a 10 m radius "
           "around themselves for 2 SPI, protecting all allies within.\n"
           "<b><font color='#C0392B'>Door Opening / Peephole (Reinforced):</font></b> Door Opening can now bring up to 5 "
           "people through a spatial obstacle. Peephole thickness limit increases to 2 m."),

         # ── Demoness Pathway ──

          ("Demoness of Pleasure", "Demoness Pathway",
             [("ST", "+1"),
              ("DX", "+1"),
              ("SPI", "+3"),
              ("Per", "+1"),
              ("Charisma +1", "+1 to reaction rolls and Influence skills"),
              ("Throat Control", "cannot be easily choked — immune to chokeholds and neck-crushing techniques"),
              ("Greater Acute Vision", "+4 to all vision-based Perception rolls; allows the Pleasure to see their own Spider's Threads"),
              ("Appearance (Very Beautiful)", "+3 to social reaction rolls")],
           [("Ritualistic Magic/IQ [Very Hard]", "+1")],

         "<b><font color='#C0392B'>Spider's Threads:</font></b> The Pleasure can spread spider-like, almost invisible silk threads from her hair "
         "that can be used for various purposes.\n"
         "<b><font color='#C0392B'>Basic Spider Threads Trap (1 SPI / free outside battle):</font></b> The Pleasure places her threads to create a "
         "detection mechanism. She can easily detect when her silk is destroyed. In battle, this reveals the enemy's size, relative strength, "
         "and speed. Noticing the threads requires a Per roll at <b>-5</b>.\n"
         "<b><font color='#C0392B'>Threads Cocoon (2 SPI + 1 SPI/turn):</font></b> The Pleasure rapidly spins a cocoon of threads around herself "
         "as a protective barrier. She recovers <b>+1 HP/turn</b> (at the start of her turn) while inside. The cocoon possesses the Pleasure's "
         "maximum SPI in HP. When the cocoon is destroyed, remaining damage is transferred to the Pleasure (e.g., if the cocoon has 4 HP "
         "remaining and an attack deals 7 damage, the cocoon is destroyed and the Pleasure takes the remaining 3 HP of damage).\n"
         "<b><font color='#C0392B'>Pleasure Shock (2 SPI):</font></b> If the enemy has made contact with the Pleasure's threads, she can cause "
         "them to experience \"true pleasure\" — spasms and loss of bodily control. The target must roll <b>Will -4</b>; on failure they lose "
         "control of their body for <b>1d turns</b>.\n"
         "<b><font color='#C0392B'>Thread Entanglement (2 SPI):</font></b> The Pleasure shoots out a mass of threads that restrain her enemy. "
         "Breaking free requires a <b>ST -4</b> or <b>Escape -3</b> roll.\n\n"

         "<b><font color='#C0392B'>Charm (Passive):</font></b> The Pleasure's beauty and charm are significantly enhanced. Any man who comes into "
         "contact with her must roll <b>Will -2</b> or be charmed. The longer someone is in her presence, the harder the Will roll becomes "
         "to break free from infatuation (GM's discretion). This also affects homosexual men and, to a lesser degree, women. The Pleasure "
         "may hide her beauty by using the <b>Disguise</b> skill at <b>-2</b> to negate this effect.\n\n"

         "<b><font color='#C0392B'>Dark Magic:</font></b> The Pleasure's dark magic is enhanced.\n"
         "<b><font color='#C0392B'>Cleansing Black Flame (1 SPI + 1 SPI/turn):</font></b> The Pleasure ignites a silent black flame within her "
         "body to cleanse curses, negative influences, or purge ghosts/wraiths. Wraiths inside her take <b>2d+1 damage per turn</b>.\n"
         "<b><font color='#C0392B'>Spirit Body Trap (4 SPI + 1 SPI/turn):</font></b> The Pleasure encases a spiritual creature in layers of "
         "frost and black fire to contain it. The spiritual creature must roll <b>SPI -5</b> to break out.\n"
         "<b><font color='#C0392B'>Black Flame Bullets (1 SPI per 2 bullets):</font></b> The Pleasure creates up to 7 black flames around her "
         "and launches them at opponents. Roll <b>Thaumatology</b> to hit. Each bullet deals <b>2d damage</b> and then ignites the target "
         "for <b>1d damage/turn</b> while burning. Burning persists until the target's SPI drops below 1/3 max (rounded down) or the "
         "flames are extinguished.\n"
         "<b><font color='#C0392B'>Ice Barrier (2 SPI + 1 SPI/turn):</font></b> The Pleasure encases herself or an ally within reach in an "
         "ice barrier. The barrier has <b>SPI + 4 HP</b>. After destruction, remaining damage is negated.\n"
         "<b><font color='#C0392B'>Ice Spear (3 SPI):</font></b> The Pleasure conjures a spear of pure ice that pierces mystical defences. "
         "Roll <b>Thaumatology</b> to hit. On impact, deals <b>5d+2 damage</b>.\n\n"

         "<b><font color='#C0392B'>Mirror Magic:</font></b> The Pleasure can cast her curses on an enemy if she manages to reflect the "
         "enemy's entire figure in a mirror.\n"
         "<b><font color='#C0392B'>Mirror and Stave Substitution (3 SPI):</font></b> The Pleasure's mirror substitution can now be performed "
          "up to <b>twice per turn</b> and heals her for <b>+1 HP</b> and <b>+1 FP</b>.\n"
          "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
          "<b><font color='#C0392B'>Black Flames (Reinforced):</font></b> The Pleasure's black flames deal +2 damage per "
          "die (minimum +1) against spirit bodies. Flames can now be extinguished only by "
          "reducing the target's SPI below 1/4 of maximum (from 1/3).\n"
          "<b><font color='#C0392B'>Flame Compression (Reinforced):</font></b> Damage increases to 3d6 (from 2d6). "
          "Blast radius expands to 15 m (from 10 m). The compressed sphere may also be "
          "split into 2 smaller spheres (1d6+2 each) targeting separate enemies.\n"
          "<b><font color='#C0392B'>Freeze — Target (Reinforced):</font></b> HT penalty increases to -3 (from -1). "
          "Damage increases to 3d6-1 (from 2d6-1). May freeze up to 2 cubic meters.\n"
           "<b><font color='#C0392B'>Mirror Magic — Hide (Reinforced):</font></b> Duration increases to 1 minute (from "
           "1d6 seconds). If the mirror is destroyed, the Pleasure takes only 1d6 damage (from 2d6)."),

         # ── Hermit Pathway ──

          ("Scrolls Professor", "Hermit Pathway",
           [("SPI", "+2")],
           [("Ritualistic Magic/IQ [Very Hard]", "+2"),
            ("Occultism/IQ [Average]", "+2"),
            ("Alchemy/IQ [Very Hard]", "+2"),
            ("Thaumatology/IQ [Very Hard]", "+2")],
           "<b><font color='#C0392B'>Scroll Making (1+ SPI):</font></b> The Scrolls Professor can create magical scrolls from "
           "various materials. The Warlock's Spell Creation system is upgraded — any spell the Professor has "
           "designed or learned can be inscribed into a scroll for instant later use.\n"
           "<b>Creating a Scroll:</b> Roll Alchemy to prepare the material (parchment, ink, or leather infused with "
           "spiritual components), then roll Thaumatology to inscribe the spell's mystical pattern. Failure on either "
           "roll simply wastes the materials — the scroll is not created but no SPI is lost. "
           "Additional scroll types may be created with GM approval.\n"
           "<b>Using a Scroll:</b> On a later turn, recite the corresponding incantation as a Ready maneuver. The scroll "
           "burns and releases its stored ability immediately — no concentration or casting time required. The SPI cost "
           "was paid at creation time; the user only needs a free hand to hold and activate the scroll.\n"
           "Some of the Scroll Spells the Scrolls Professor can create include:\n"
           "<b>Secret Voice:</b> Forms a channel linking 3 to 5 people within 50 meters, allowing communication without "
           "obstruction. Lasts 10 minutes.\n"
           "<b>Freezing:</b> Creates a stream of crystal clear light that freezes the target. The target suffers -3 to all "
           "rolls, and halves Basic Move and Dodge for 1d6 turns. If a second Freezing scroll is used on the same target "
           "within 1 minute, the target is sealed in ice — break free with ST-3.\n"
           "<b>Storm:</b> Creates a wide thunderstorm centred on the user. Deals 3d6 damage to all in a 10 m radius. "
           "Half damage on HT-2 save.\n"
           "<b>Numb:</b> Releases a light green luster that paralyzes a single target within 20 m. The target is Stunned "
           "and may resist with Will-3 at the start of each turn.\n"
           "<b>Burning:</b> Releases flames that engulf a 5 m radius. Deals 1d6 burning damage, plus "
           "1d6 per turn for 1d3 turns unless the target uses an action to extinguish the flames.\n"
           "<b>Wind:</b> A swift wind envelops a selected target within 20 m, doubling their Basic Move and granting "
           "+3 to Dodge for 1 minute.\n"
           "<b>Healing:</b> Releases a green light that heals all allies within a 10 m radius for 1d6 HP.\n"
           "<b>Sun:</b> Releases a holy light aura in a 10 m radius. Deals 3d6 damage to undead and evil creatures. "
           "No effect on living creatures.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Eyes of Mystery Prying (Reinforced):</font></b> The Scrolls Professor can read the "
           "contents of any written mystical text (scrolls, grimoires, encrypted notes) by touch alone — "
           "no roll required. The passive penalty to Dream/Illusion rolls against the Professor increases to -5.\n"
           "<b><font color='#C0392B'>Quick Rituals (Reinforced):</font></b> The time reduction for known rituals improves to -6 "
           "(from -5). The Professor can perform rituals at 1/3 the listed time (minimum 1 minute), "
           "and may maintain concentration on one ritual while taking Attack or All-Out Defense actions.\n"
           "<b><font color='#C0392B'>Spirit Contract (Reinforced):</font></b> Maximum simultaneous contracts increases to 8 (from 4). "
            "The Professor may now inscribe a Spirit Contract onto a scroll — anyone who reads and activates "
            "the scroll is bound by the contract's terms as if they had negotiated it themselves."),

          # ── Paragon Pathway ──

           ("Artisan", "Paragon Pathway",
           [],
           [("Ritualistic Magic/IQ [Very Hard]", "+5"),
            ("Mechanic/IQ [Average]", "+3"),
            ("Smith (Iron)/IQ [Average]", "+4"),
            ("Jeweler/IQ [Average]", "+4"),
            ("Machinist/IQ [Average]", "+4"),
            ("Leatherworking/DX [Average]", "+4")],
           "<b><font color='#C0392B'>Manufacturing (1 SPI):</font></b> The Artisan is an undisputed master of creation. "
           "To craft a Sealed Artifact, the Artisan first makes a crafting skill roll (Smith, Jeweler, "
           "Machinist, etc.) to manufacture the item from the Beyonder Characteristic, then rolls "
           "Thaumatology with a bonus equal to the margin of success from the crafting roll. "
           "The Sealed Artifact gains better effects and fewer negative side effects depending on "
           "how well the Thaumatology roll succeeds. If the Characteristic is from a higher or lower "
           "Sequence, apply ±2 to the Thaumatology roll per Sequence difference. "
           "Failing the Thaumatology roll means reduced power and increased drawbacks — the item is "
           "still created but flawed.\n"
           "To create a Mystical Item (without a Beyonder Characteristic), the Artisan follows the "
           "same process. The item's longevity depends on success margin: 0–2 = 6 months, "
           "3–5 = 1 year, 6–8 = 2 years, Critical Success = 3 years.\n"
           "The Artisan can also fix Spirit World summoning rituals (such as Messenger contracts) "
           "directly into an item — anyone who possesses the item may activate the summoning "
           "without knowing the ritual.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Appraisal (Reinforced):</font></b> The Artisan's Appraisal sense is now reflexive. "
           "They may identify a Beyonder item's purpose, dangers, and domain alignment as a free "
           "action. For rare or complex items, roll Appraisal — on success, all immediate dangers "
           "are revealed (not just one). Items lower than the Artisan's own Sequence are "
           "identified automatically.\n"
           "<b><font color='#C0392B'>Rapid Manufacturing (Reinforced):</font></b> The Artisan may reduce the "
           "manufacturing time for crafting by half. For items of the Artisan's own Sequence or "
           "lower, they may attempt to craft a rushed version in 1/4 the normal time (minimum "
           "1 hour), taking -3 to the crafting roll."),

          # ── Visionary Pathway ──

          ("Hypnotist", "Visionary Pathway",
           [("SPI", "+3"), ("ST", "+3"), ("DX", "+3"),
            ("DR +3", "Dragon Scales — draconic scales beneath the skin provide DR 3 against all physical damage")],
           [("Psychology/IQ [Hard]", "+4"),
            ("Detect Lies/Per [Hard]", "+3"),
            ("Body Language/Per [Average]", "+3"),
            ("Observation/Per [Average]", "+3")],
          "<b><font color='#C0392B'>Psychological Invisibility (Free, No SPI Cost):</font></b> The Hypnotist can remain in the "
          "blind spot of one's consciousness. This works even against Spirit Vision and a Hunter's Danger Intuition "
          "(until the user prepares to strike). The target will not perceive the user even when standing right before them. "
          "Strong interactions with the surroundings can break the invisibility. At this Sequence, can only work on one "
          "target at a time.\n"
          "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
          "<b><font color='#C0392B'>Hypnosis (Reinforced):</font></b> Psychological Cue undergoes a qualitative change, becoming Hypnosis.\n"
          "<b><font color='#C0392B'>Non-Combat Hypnosis (2 SPI):</font></b> Open the door and enter the target's Body of Heart and Mind. "
          "The target rolls Will-6 to resist. The target will not notice they are following the Hypnotist's arrangements. "
          "Cannot directly harm the target's life.\n"
          "<b><font color='#C0392B'>Battle Hypnotism (2 SPI):</font></b> Forcefully hypnotize an enemy mid-combat. The target rolls "
          "Will-6 to resist. Lasts 1 turn. The Hypnotist can make the target perform an action that does not threaten their "
          "own life."),

         # ── Sun Pathway ──

          ("Notary", "Sun Pathway",
           [("SPI", "+4"), ("ST", "+2"), ("DX", "+2"), ("HT", "+2"),
            ("DR 1", "Fire/Light — resistance to fire and light-based attacks")],
           [],
          "<b><font color='#C0392B'>Notarization:</font></b> By utilizing a language that stirs the powers of nature along with "
          "the relevant words, a Notary can achieve Authentication, Amplification, or Nullification.\n"
          "<b><font color='#C0392B'>Authentication (1 SPI):</font></b> Determine the authenticity of various things such as potion "
          "formulas, and enforce Contracts. Once a signature is provided as confirmation, even a Sequence 5 Beyonder cannot "
          "violate it, and a Sequence 4 Demigod would have great difficulty. Those who lie or break the Contract are engulfed "
          "in burning golden flames, suffering 15d damage.\n"
          "<b><font color='#C0392B'>Amplification (2 SPI):</font></b> A valid Notarization temporarily enhances a targeted Beyonder "
          "power. Proclaim \"God says it's effective!\" The effect depends on the GM.\n"
          "<b><font color='#C0392B'>Nullification (2 SPI):</font></b> An invalid Notarization weakens or forcefully disperses a "
          "targeted Beyonder power. Proclaim \"God says it's ineffective!\" Powers of all kinds, including verbal command "
          "abilities, authorities, and traits can be affected."),

         # ── Hanged Man Pathway ──

          ("Rose Bishop", "Hanged Man Pathway",
           [("SPI", "+3")],
           [("Ritualistic Magic/IQ [Very Hard]", "+2")],
          "<b><font color='#C0392B'>Flesh & Blood Magic (Passive):</font></b> A Rose Bishop can stack up to 50 Stacks of Flesh and "
          "Blood; 1 Stack equals 1 HP. They can use Stacks as a free action to regenerate. A Rose Bishop must regularly "
          "replenish their Flesh and Blood. If they have less than 10 Stacks, they double any corruption they would take. "
          "They can use the Flesh and Blood of corpses in their immediate surroundings. A corpse equals 25 Flesh and Blood Stacks.\n"
          "<b><font color='#C0392B'>Flesh Cloak (X Flesh and Blood):</font></b> Create cloaks of sticky Flesh that resist magic "
          "and reduce damage. The cloak has 1 HP per Flesh used and DR 3 against Beyonder Powers.\n"
          "<b><font color='#C0392B'>Flesh Blood Fusion (0 Flesh and Blood):</font></b> Melt into pure sticky Flesh and Blood that "
          "can penetrate the ground and move. Halves all damage except large-area damage (which deals double). Can hide inside "
          "a host's stomach — the host dies upon the Rose Bishop's departure. Takes 3 turns to blend in.\n"
          "<b><font color='#C0392B'>Flesh Bomb (5 Flesh and Blood):</font></b> Tear off flesh to make explosive Flesh Bombs that "
          "explode into corrosive blood rain, dealing 3d Corrosive damage. Can be buried inside others' bodies and detonated.\n"
          "<b><font color='#C0392B'>Flesh Blood Servants (15 Flesh and Blood):</font></b> Create puppets with immense strength "
          "(ST 17), immune to spirit attacks. 15 HP. Self-destruct deals 5d damage in a 3 m radius.\n"
          "<b><font color='#C0392B'>Flesh Blood Curse (0 Flesh and Blood):</font></b> Curse a target if possessing their flesh "
          "(+2) and/or blood (+4). Use Ritualistic Magic to inflict 3d damage or for other rituals.\n"
          "<b><font color='#C0392B'>Devouring (0 Flesh and Blood):</font></b> Envelop a target, corrode their body from the "
          "inside, dealing 2d damage per turn.\n"
          "<b><font color='#C0392B'>Flesh Softening (0 Flesh and Blood):</font></b> Negate the next instance of physical damage "
          "except from knives and swords (which slash through).\n"
          "<b><font color='#C0392B'>Disguise (0 Flesh and Blood):</font></b> Modify appearance (muscularity, facial features) "
          "with practice. -3 to all reaction rolls while in disguise."),

          # ── Darkness Pathway ──

           ("Soul Assurer", "Darkness Pathway",
           [("SPI", "+2")],
           [("Ritualistic Magic/IQ [Very Hard]", "+2"),
            ("Divination Arts/SPI [Hard]", "+2")],
           "<b><font color='#C0392B'>Spiritual Vision (Passive – Reinforced):</font></b> The Soul Assurer sees spiritual "
            "lifeforms at all times without activating Spirit Vision. Constant exposure grants +3 to "
            "Spiritual Perception rolls and makes it impossible for spirits to hide within line of sight.\n"
            "<b><font color='#C0392B'>Requiem (2 SPI):</font></b> Cause the target's Spirit Body to fall asleep. The target "
            "skips 2 turns (stimuli — being damaged, shaken, or a loud noise on their turn — wakes them "
            "immediately). Will-5 to resist; on success only halves Basic Move and Basic Speed for 1 turn "
            "and the target suffers -5 to Spiritual Intuition rolls for the same duration. "
            "On unwilling spirits, ghosts, and undead: Will-4 or forced into silent slumber. "
            "On willing allies: heal the Spirit Body, reducing Corruption by 1d3 points.\n"
            "<b><font color='#C0392B'>Agitate (1 SPI):</font></b> Agitate the target's Spirit Body, heightening their "
            "frustrations and destructive urges. The target must perform an offensive action this turn "
            "instead of fleeing or hesitating (Will-2 to resist). On a successful Divination Arts roll, "
            "one hidden psychological flaw or spiritual corruption in the target is revealed.\n"
            "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
            "<b><font color='#C0392B'>Dream Invasion (Reinforced):</font></b> Range increased to 150 m (from 20 m quick / 100 m "
            "prepared).\n"
            "<b><font color='#C0392B'>Midnight Poem (Reinforced):</font></b> The Soul Assurer may manifest Midnight Poem effects "
            "through song instead of recitation.\n"
            "<b><font color='#C0392B'>Nocturnality (Reinforced):</font></b> The Soul Assurer requires only 2 hours of rest per "
            "day (down from 3–4). Night bonuses increase to +3 to all rolls (from +2)."),

          # ── Death Pathway ──

           ("Spirit Guide", "Death Pathway",
           [("SPI", "+3")],
           [("Hidden Lore (Spirit World)/IQ [Average]", "+3")],
          "<b><font color='#C0392B'>Language of the Dead:</font></b> Speak a mystical language that urges a target's Spirit to "
          "leave its body, bypassing physical protection to directly target the Spirit Body.\n"
          "<b><font color='#C0392B'>Spirit Calling (1 SPI):</font></b> Urge the spirit to leave its body. The target rolls at -2 "
          "if dead, or +6 if alive.\n"
          "<b><font color='#C0392B'>Commandeer Spirit (2 SPI):</font></b> Command a spirit to obey your orders. The target rolls "
          "Will at -2 if dead, or +4 if alive.\n"
          "<b><font color='#C0392B'>Spirit Enslavement (4 SPI):</font></b> Enslave a spirit. The target rolls Will at +2 if dead, "
          "or +8 if alive. Language of the Dead does not work on higher Sequences. Marionettes are considered undead — roll "
          "Ritualistic Magic vs the Marionettist's Ritualistic Magic; +4 to the Marionettist if the marionette has a Spirit Worm "
          "core.\n"
          "<b><font color='#C0392B'>Resurrection (1-4 SPI):</font></b> Roll Ritualistic Magic. Turn corpses into Zombies or "
          "living skeletons. They have no will or consciousness.\n"
          "<b><font color='#C0392B'>Spirit Swapping (2 SPI):</font></b> Defend against Soul Body attacks by swapping your "
          "spirit with an undead under your command.\n"
          "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
          "<b><font color='#C0392B'>Spirit Channeling (Reinforced):</font></b> Directly summon spirits from the Spirit World. "
          "Can command the deceased and natural spirits to fight. The undead commanded can have similar status to the Spirit "
          "Guide. Number of undead: up to thousands."),

         # ── Twilight Giant Pathway ──

          ("Dawn Paladin", "Twilight Giant Pathway",
           [("SPI", "+3"), ("ST", "+3"), ("HT", "+2")],
           [("Broadsword/DX [Average]", "+2"),
            ("Shield/DX [Easy]", "+2"),
            ("Polearm/DX [Average]", "+2"),
            ("Armoury (Melee)/IQ [Average]", "+2")],
          "<b><font color='#C0392B'>Giant (Free Action):</font></b> The Dawn Paladin gains +20 cm in height permanently, and can "
          "temporarily gain an additional +20 cm at will.\n"
          "<b><font color='#C0392B'>Light of Dawn (1 SPI):</font></b> Fill an area of roughly 40-50 m with sacred Dawn Light. "
          "Inflicts 2d6 burning damage (HT/2 to halve) to Wraiths, Shadows, and Evil Spirits. Reduces corruption by 1d/2 for "
          "those in the area. Nullifies concealment effects and dispels illusions.\n"
          "<b><font color='#C0392B'>Dawn Armor (2 SPI):</font></b> Conjure a silver Armor of Dawn with 20 HP. Recovers 4 HP "
          "per turn by draining 1 FP (Free Action). Includes gauntlets, breastplate, and helmet.\n"
          "<b><font color='#C0392B'>Sword of Dawn (1 SPI):</font></b> Condense Dawn into a weapon. Each strike is imbued with "
          "Purification, dealing +2d burning damage to undead, wraiths, and ghosts.\n"
          "<b><font color='#C0392B'>Hurricane of Light (3 SPI):</font></b> The Dawn Paladin's most powerful attack. Insert the "
          "Sword of Dawn into the ground and shatter it, creating a hurricane of light dealing 5d+2 damage (+3d against Shadows "
          "and Corrupted entities, +3d against Evil and spirits — up to 8d total). Needs 2 minutes of rest before reuse. "
          "The Sword of Dawn cannot be condensed for 10 seconds after activation. The Dawn Paladin can control the hurricane's "
          "direction to a certain extent."),

         # ── Red Priest Pathway ──

          ("Conspirer", "Red Priest Pathway",
           [("SPI", "+5"), ("ST", "+1"), ("DX", "+1"), ("IQ", "+1"), ("HT", "+1"),
            ("Acute Vision", "+2 to vision-based Perception rolls"),
            ("Acute Hearing", "+2 to hearing-based Perception rolls"),
            ("Acute Taste & Smell", "+2 to taste/smell-based Perception rolls"),
            ("Acute Touch", "+2 to touch-based Perception rolls")],
           [("Body Language/Per [Average]", "+4"),
            ("Intelligence Analysis/IQ [Hard]", "+4")],
          "<b><font color='#C0392B'>Conspiracy (2 SPI):</font></b> The core of a Conspirer's arsenal — weave deceptions, misdirect "
          "attention, and create confusion among enemies. All enemies within 10 m must roll Will-2 or suffer -2 to all Perception, "
          "Observation, and skill rolls for 1d turns due to confusion and misdirection.\n"
          "<b><font color='#C0392B'>Incitement (1 SPI):</font></b> Incite certain thoughts or desires in someone's mind through "
          "conversation, such as consciously igniting the flames in their heart.\n"
          "<b><font color='#C0392B'>Flame Transformation (2 SPI):</font></b> Merge with fire weapons conjured from Pyrokinesis "
          "and travel to the destination where the fire weapon lands. Can take other people, but they take 1d damage from the "
          "flames. Initial range: 10 m (30 m when potion is digested).\n"
          "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
          "<b><font color='#C0392B'>Pyrokinesis (Reinforced):</font></b> Freely control flames within 15 m.\n"
          "<b><font color='#C0392B'>Compress (1 SPI):</font></b> Damage increases to 1d+3. Can multi-turn charge (5/10 bonus "
          "damage per turn spent charging, max 10).\n"
          "<b><font color='#C0392B'>Conjure (1 SPI):</font></b> Can now gain weapon skills with conjured weapons and parry with "
          "weapons of fire. Use the skill of the weapon the flame transforms into."),

         # ── Mother Pathway ──

          ("Biologist", "Mother Pathway",
           [("SPI", "+2")],
           [("Naturalist/IQ [Hard]", "+3"),
            ("Herbal Medicine/IQ [Hard]", "+3")],
          "<b><font color='#C0392B'>Cross-breeding (1 SPI):</font></b> Create chimeras or cross-breeds between various animals, "
          "plants, and even objects — directly creating new species. Ordinary materials create unique species with directed "
          "abilities. Beyonder ingredients create more magical cross-breeds with unique properties. Before Sequence 4, "
          "cross-breeds lack a Soul. The result depends on player intent and GM discretion.\n"
          "<b><font color='#C0392B'>Poison Creation (1 SPI):</font></b> The Biologist's own body can produce highly potent "
          "toxin, accumulated and released through hair or other means. Releases poison dealing 1d+1 damage per turn for 1d "
          "turns in an area. Leaves the target poisoned for 1d/2 turns after leaving the area.\n"
          "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
          "<b><font color='#C0392B'>Knowledge — Life (Reinforced):</font></b> Deep understanding of living organisms. +6 to "
          "Hidden Lore (Living Organism)."),

         # ── Moon Pathway ──

          ("Potions Professor", "Moon Pathway",
           [("SPI", "+2"), ("ST", "+1"), ("DX", "+1"), ("HT", "+1")],
           [("Detect Lies/Per [Hard]", "+6"),
            ("Pharmacy/IQ [Hard]", "+4"),
            ("Physician/IQ [Hard]", "+4"),
            ("Herb Lore/IQ [Average]", "+4"),
            ("Poison/IQ [Hard]", "+3"),
            ("Alchemy/IQ [Very Hard]", "+5")],
          "<b><font color='#C0392B'>Natural Sense of Smell (Passive):</font></b> Differentiate people by their scent. Detect "
          "entities unable to hide their smell (e.g., wraiths). Strong odours impose -1 to all rolls.\n"
          "<b><font color='#C0392B'>Discerning Spiritual Materials (Passive):</font></b> Gain vast knowledge to discern spiritual "
          "materials for various concoctions. Can now treat terminal illnesses.\n"
          "<b><font color='#C0392B'>Potion & Perfume Crafting:</font></b> Create Potions and Perfumes with extraordinary effects. "
          "Roll Alchemy. Success margin determines longevity: 0-2 = 1 day, 3-5 = 3 days, 6-8 = 5 days, 9+ = 1 week, critical "
          "success = 2 weeks. Can drink up to 4 potions in battle before facing negative effects.\n"
          "<b>Known Potions include:</b>\n"
          "<b>Solar Water Potion (Alchemy -1):</b> Powerful against undead and vampires — 3d purification damage on contact.\n"
          "<b>Dragon's Breath (Alchemy -1):</b> Spit a fire breath dealing 3d burning (one-time use).\n"
          "<b>Invisibility Potion (Alchemy -3):</b> Become completely invisible. Lasts 1d×10 minutes.\n"
          "<b>Anti-Smell Potion (Alchemy +0):</b> Eliminates the user's smell and body odor.\n"
          "<b>Anti-Dream Potion (Alchemy -2):</b> Prevents Dream Pulling effects.\n"
          "<b>Shadow Potion (Alchemy -4):</b> Allows Shadow Movement at ×2 Base Move.\n"
          "<b>Known Perfumes include:</b>\n"
          "<b>Animal-Friendly Perfume (Alchemy -1):</b> Makes animals closer to the user — +5 to reaction rolls with animals.\n"
          "A true Potions Professor can research and invent new Potions and Perfumes (roll Inventor then Alchemy -4, with GM approval)."),

          # ── Abyss Pathway ──

          ("Devil", "Abyss Pathway",
             [("SPI", "+5"), ("ST", "+2"), ("Will", "-2"),
              ("DR 2", "Physical — skin mutated"),
              ("DR 2", "Curses, Flames, Poison — highly resistant")],
            [("Guns (Revolver)/DX [Easy]", "+2"),
             ("Knife/DX [Average]", "+2"),
             ("Brawling/DX [Easy]", "+2"),
             ("Streetwise/IQ [Average]", "+2")],
           "<b><font color='#C0392B'>Danger Premonition (Malice Perception):</font></b> The Devil can sense the place of origin "
           "of danger and who it comes from. Requires 3 conditions: (1) the threat is fatal or life-threatening, "
           "(2) the source intends harm within a certain period and range, (3) the source acts on that intent. "
           "The premonition window ranges from a few minutes to 24 hours. The range spans from a few miles to "
           "an entire metropolitan area, depending on the individual Devil.\n"
           "<b><font color='#C0392B'>Fearless:</font></b> The Devil does not feel or experience fear. Automatically succeed "
           "on all Fright Checks.\n"
           "<b><font color='#C0392B'>Devil Bloodline:</font></b> Each Devil develops unique racial abilities upon advancement. "
           "Choose one of the following (or create a new one with GM approval):\n"
           "<b>Shadow-Shifter:</b> When forced into a life-threatening situation, the Devil can escape by leaving only a "
           "shadow behind. The Devil reappears at any shadow within 30 meters.\n"
           "<b>Spirit Body (Rare):</b> The Devil can freely switch between body and spirit form like a Wraith.\n"
           "<b>Item Creation:</b> The Devil can skin humans and perform complicated processes to form Beyonder items with "
           "usage or time limitations (GM's discretion).\n"
           "<b>Skin Clothes:</b> Anyone wearing a human skin crafted by the Devil can transform into the original person, "
           "disguising themselves completely.\n"
           "<b><font color='#C0392B'>Devil Transformation (3 SPI):</font></b> Transform into true Devil form — gigantify the "
           "body, sprout bat wings and goat horns. Gain +4 ST, +4 DX, +4 HT, and +2 DR. "
           "Spell restrictions are lessened in this form (e.g., launch 10–20 Sulfur Fireballs simultaneously "
           "instead of the usual 3).\n"
           "<b><font color='#C0392B'>Language of Foulness:</font></b> Devils speak demonic words originating from the Abyss, "
           "filled with Filth and Corruption. They can use the following:\n"
           "<b>Slow (2 SPI):</b> All targets within a 7–8 meter radius turn numb and slow or come to a halt. "
           "Reduces Base Speed and Basic Move by 5 for 2 turns. Can only be maintained for 2 seconds.\n"
           "<b>Death (2 SPI):</b> Dodged normally. Target may halve the effect with a HT roll. "
           "Inflicts 2d damage per turn for 2 turns.\n"
           "<b>Corruption (3 SPI):</b> An area-of-effect attack causing Abyss Corruption symptoms. "
           "Within a 5 meter radius, each target takes 1d damage and +1 CoR, creating black fog. "
           "The area persists for 1d turns.\n"
           "<b>Sulfur Fireball (1 SPI per fireball):</b> Launch pale blue Fireballs that explode and "
           "poison on contact. No more than 3 at a time. Each inflicts 1d+1 damage, plus poison for "
           "1d-2 damage for 1d-2 turns.\n"
           "<b>Sword of Lava (4 SPI):</b> The Devil cannot move on the same turn. Deals 5d+3 damage. "
           "Can be dodged.\n"
           "<b>Flame Cage (3 SPI):</b> Within 10 meters, conjure a large Cage of Flames to block "
           "escape. Also blocks projectiles.\n"
           "<b>Poisonous Flame Manipulation (1 SPI, Free Action):</b> Manipulate Poisonous Flames "
           "within 30 meters — ignite materials, shape existing flames, or hurl a Poisonous Flame Jet "
            "at a target within 30 m (DX or Sleight of Hand to hit)."),

          # ── Wheel of Fortune Pathway ──

          ("Calamity Priest", "Wheel of Fortune Pathway",
             [("SPI", "+5")],
            [],
           "<b><font color='#C0392B'>Calamity Attraction (Passive):</font></b> The Calamity Priest's body passively draws "
           "misfortune. At the start of each session (or once per in-game day), the GM rolls 3d6 to determine a calamity "
           "that will befall the Priest. The Priest may use their Foresight (Seq 9) to foresee the calamity 1 round in "
           "advance, allowing mitigation or avoidance.\n"
           "<b><font color='#C0392B'>Active Attraction (2 SPI):</font></b> Direct calamity at a target within 30 meters. "
           "Roll 3d6:\n"
           "<b>3–6 — Major:</b> A genuine hazard — e.g., a carriage wheel flies off toward the target, a gas lamp explodes "
           "showering glass, a heavy crate falls from a pulley. GM determines damage (2d6–3d6 depending on environment).\n"
           "<b>7–14 — Moderate:</b> Noticeable misfortune — e.g., a floorboard rots through underfoot (-2 to Move), "
           "a chandelier cord snaps (1d6, Dodge to halve), a chimney pot crashes beside them.\n"
           "<b>15–18 — Minor:</b> Annoyance or fizzle — e.g., a pigeon swarm spooks their horse, a gust slams a window shut "
           "in their face (-1 to next roll). On 17–18 the calamity backfires on the Priest instead.\n"
           "The Priest cannot foresee or mitigate actively attracted calamities. +3 to the roll in hazard-rich areas "
           "(docks, factory, cliffside), -3 in sparse areas (empty field, open room).\n"
           "<b><font color='#C0392B'>Psyche Storm (2 SPI):</font></b> Assault the target's Spirit Body directly. "
           "Inflicts 1d-2 SPI damage (reducing the target's Spirituality pool) and applies -3 to all the target's rolls "
           "for the next 2 turns. At the end of each turn, the target may roll Will-3 — on success, the penalty ends early."),

          # ── Chained Pathway ──

          ("Zombie", "Chained Pathway",
           [("SPI", "+3"), ("ST", "+2"),
            ("DR 3", "Physical — natural hardened body armor"),
            ("Regeneration (Very Fast)", "Recover 1 HP per second"),
            ("Basic Move", "+1")],
           [],
          "<b><font color='#C0392B'>Ice Control:</font></b> The Zombie can control ice they are in physical contact with, "
          "gaining the following abilities:\n"
          "<b>Contact-Freeze (Free Action, 1 SPI):</b> Any physical attack that contacts a target's skin can freeze their "
          "body. On a successful Brawling/Boxing/Wrestling roll the Zombie freezes a body part — target's physical rolls at "
          "-1. Stacks with repeated hits.\n"
          "<b>Ice Stun (3 SPI):</b> Seal opponents in ice on physical contact. Target breaks free with ST-4.\n"
          "<b>Ice Wall (X SPI):</b> Freeze water into ice walls with 5 HP per SPI spent.\n"
          "<b>Ice Floor (2 SPI):</b> Create slippery ice layers. Targets must succeed Acrobatics or fall. The Zombie "
          "can spend 1 SPI to control the ice beneath their feet (Free Action).\n"
          "<b>Ice Temperature (2 SPI):</b> Lower air temperature, causing strong winds and snowflakes. Cold-sensitive "
          "targets roll Will or suffer -1 to all rolls in the zone.\n"
          "<b><font color='#C0392B'>Decay, Rot & Withering:</font></b>\n"
          "<b>Wither Explosion (2 SPI):</b> Make mid-range air explode into black wisps inducing Withering. "
          "Inflicts 1d6-1 damage for 1d/2 turns.\n"
          "<b>Rotting Body Aura (Free Action, 1 SPI):</b> Effuse a rotting aura — add 1d Decay damage to the next attack.\n"
          "<b>Aura of Decay (1 SPI):</b> Emit an aura that visibly withers surrounding vegetation.\n"
          "<b>Sludge Creation (1 SPI):</b> Create rotting sludge. Targets must roll ST, DX, or Acrobatics or have "
          "Base Move halved in the sludge area.\n"
          "<b><font color='#C0392B'>Zombie Manipulation:</font></b> Awaken the dead (1 SPI), cultivate puppets, "
          "control ghosts, and command them (0 SPI).",
          [("Sun Vulnerability", "Sun-domain abilities deal double damage and ignore DR; regeneration is suspended for 1 minute after a Sun-domain hit"),
           ("Zombie's Curse", "Every Full Moon, the Zombie endures great pain. If resisting, they lose the ability to fight — roll Will-2 for any action. Replaces the Lunatic's and Werewolf curses")]),
     ]

    for entry in seq6_pathways:
        title, pathway, stats, skills, ability = entry[:5]
        disadvantages = entry[5] if len(entry) > 5 else []

        story.append(sp(4))
        story += subsection(f"Sequence 6: {title}  ·  {pathway}")
        story.append(sp(2))

        # Build merged stat + disadvantages table
        if stats or skills or disadvantages:
            stat_rows = [[Paragraph("Stat / Advantage", S['TableHeader']), Paragraph("Gain", S['TableHeader'])]]
            for k, v in stats:
                stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            divider_idx = None
            if disadvantages:
                divider_idx = len(stat_rows)
                stat_rows.append([Paragraph("<b>Drawbacks</b>", S['TableHeader']),
                                  Paragraph("", S['TableHeader'])])
                for k, v in disadvantages:
                    stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            stat_t = Table(stat_rows, colWidths=[1.55*inch, 1.55*inch])
            stat_t.setStyle(table_style())
            if divider_idx is not None:
                stat_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, divider_idx), (-1, divider_idx), MID_NAVY),
                    ('LINEABOVE', (0, divider_idx), (-1, divider_idx), 0.5, GOLD),
                    ('TOPPADDING', (0, divider_idx), (-1, divider_idx), 3),
                    ('BOTTOMPADDING', (0, divider_idx), (-1, divider_idx), 3),
                ]))

            if skills:
                skill_rows = [[Paragraph("Skill", S['TableHeader']), Paragraph("Change", S['TableHeader'])]]
                for k, v in skills:
                    skill_rows.append([
                        Paragraph(k, S['TableCell']),
                        Paragraph(v, S['TableCell']),
                    ])
                skill_t = Table(skill_rows, colWidths=[2.4*inch, 0.85*inch])
                skill_t.setStyle(table_style())

                combo = Table([[stat_t, skill_t]], colWidths=[3.2*inch, 3.35*inch])
            else:
                combo = Table([[stat_t]], colWidths=[6.4*inch])

            combo.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(combo)
        else:
            story.append(Paragraph("<i>No stat or skill changes at this Sequence.</i>", S['Body']))

        story.append(sp(3))

        # Ability block (with optional Reinforced box)
        main_ab, reinf_ab = split_reinforced(ability)
        render_ability_boxes(main_ab, reinf_ab, story)

    story.append(PageBreak())

    story += chapter("Chapter 13: Boon Granting — The Price of Borrowed Power")

    story.append(flavor(
        "All that you touch, you change. All that you change, changes you. — Octavia Butler"
    ))
    story.append(sp(4))

    story += section("I. What Is a Boon?")
    story.append(body(
        "For all of the Fifth Epoch, the Great Ones — hidden existences beyond the Wall of "
        "Spirituality — have sought to infiltrate Earth through the Great Barrier. Unable to cross "
        "directly, they extend their influence through the willing. By praying to one of these "
        "Hidden Existences with the correct honorific name, a mortal may acquire a <b>boon</b> — "
        "a fragment of the Great One's power that functions similarly to a Beyonder potion."
    ))
    story.append(body(
        "A boon grants supernatural abilities following the same Sequence ladder as the standard "
        "22 Pathways. However, boons differ from potions in a critical way: where a potion carries "
        "only the passive will of the sealed Beyonder characteristic, a boon carries the <i>active will</i> "
        "of the Great One who grants it. The supplicant does not simply ingest power — they open "
        "themselves to influence."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Personality Erosion:</b> Over time, the boon reshapes the supplicant's personality to "
        "more closely match their patron. A boon-granted Beyonder may find their values shifting, "
        "their desires aligning with their Great One's domain, and their sense of self slowly "
        "subsumed. This is not corruption in the usual sense — it is <i>alignment</i>. The more "
        "power one accepts, the more one becomes a vessel."
    ))
    story.append(sp(3))

    story += section("II. Requirements for a Boon")
    story.append(body(
        "To petition for a boon, a supplicant must possess all of the following:"
    ))
    story.append(bullet(
        "<b>The full honorific name</b> of the Hidden Existence. Incomplete or incorrect names "
        "are likely to attract the wrong attention — or no attention at all."
    ))
    story.append(bullet(
        "<b>Corresponding mystical ingredients</b> for appeasement. These vary by Great One and "
        "are tied to their domain and symbolism. Incense, rare oils, consecrated items, or "
        "the blood of specific creatures are common requirements."
    ))
    story.append(bullet(
        "<b>A sacrifice.</b> Sacrifices are almost mandatory for even a Sequence 9 equivalent "
        "boon. The quality, significance, and appropriateness of the sacrifice directly affect "
        "the ritual's outcome."
    ))
    story.append(sp(3))

    story += section("III. The Boon Granting Ritual")
    story.append(body(
        "The boon granting ritual uses the standard <b>Ritualistic Magic</b> system "
        "(see Chapter 7). The supplicant rolls <b>Ritualistic Magic/IQ (Very Hard)</b> to "
        "determine the Great Existence's response."
    ))
    story.append(body(
        "The ritual's baseline parameters are fixed:"
    ))
    story.append(bullet("<b>Ritual Complexity:</b> Heavy (1 hour base time)"))
    story.append(bullet("<b>Effect Weight:</b> Moderate (-2 difficulty, 4–6 SPI required)"))
    story.append(body(
        "<i>The ritual takes Heavy time (1 hour) because of the involved preparation — prayers, "
        "invocations, and sacrifice arrangement — but its effect weight is Moderate (−2) because "
        "the actual power comes from the patron, not the ritual itself.</i>"
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Modifiers to the roll:</b> The quality of the sacrifice, the quality and precision "
        "of the ritual, and the level of the boon being supplicated all contribute to the final "
        "modifier. The GM should apply circumstantial bonuses or penalties as follows:"
    ))
    story.append(bullet(
        "<b>Sacrifice quality:</b> A perfunctory sacrifice (-2 to -4), an appropriate sacrifice (+0), "
        "a meaningful sacrifice (+1 to +3), or a great sacrifice that aligns perfectly with the "
        "Great One's domain (+4 to +6)."
    ))
    story.append(bullet(
        "<b>Ritual quality:</b> Sloppy or rushed (-3), standard preparation (+0), meticulous "
        "with rare materials (+1 to +3), or performed at a place of power aligned with the patron (+4)."
    ))
    story.append(bullet(
        "<b>Boon level:</b> Sequence 9 equivalent (+0), Sequence 8 (-2), Sequence 7 (-4), "
        "and so on, doubling the penalty with each sequence. Generous sacrifices that align "
        "with the patron's domain can offset or even negate this penalty — see Sacrifice "
        "quality modifiers above."
    ))
    story.append(sp(3))

    story += section("IV. Consequences & Risks")
    story.append(body(
        "Accepting a boon is not a transaction between equals. The Great One is always aware of "
        "the supplicant after the first successful ritual. Consequences may include:"
    ))
    story.append(bullet(
        "<b>Personality drift:</b> The GM should periodically introduce subtle changes to the "
        "character's personality, reflecting the patron's influence. A boon-granted Beyonder of "
        "a Fool-adjacent Great One may become more deceptive; one aligned with a Calamity "
        "Existence may grow more destructive."
    ))
    story.append(bullet(
        "<b>Dreams and visions:</b> The patron may communicate — or simply observe — through "
        "the boon connection. Sleep is no longer private."
    ))
    story.append(bullet(
        "<b>Increased vulnerability:</b> The connection works both ways. Those with knowledge of "
        "the patron may detect the supplicant's taint. Church Inquisitors and Mandated Punishers "
        "are trained to recognise boon-granted Beyonders."
    ))
    story.append(bullet(
        "<b>Refusal penalty:</b> Once a boon has been accepted, refusing a direct request from "
        "the patron may incur spiritual backlash (see Critical Failure Table, Chapter 7, Section VI)."
    ))
    story.append(sp(3))

    story.append(PageBreak())

    story += chapter("Chapter 14: Non-Standard Pathways — Boon-Granted Paths")

    story.append(body(
        "Beyond the 22 standard Pathways lie others — sequences that do not correspond to the "
        "Beyonder Characteristics sealed on Earth. These <b>non-standard pathways</b> are the domains "
        "of <b>Outer Deities</b>: Great Old Ones who exist beyond the cosmos, each ruling a unique "
        "Pathway with its own Sequence ladder from 9 to 0."
    ))
    story.append(body(
        "Unlike standard Beyonders who consume potions brewed from Beyonder Characteristics, "
        "followers of non-standard pathways advance through <b>boons</b> — power granted by an "
        "Outer Deity in response to prayer, sacrifice, and ritual. The boon system described in "
        "<b>Chapter 13</b> governs this process. Each non-standard pathway has a corresponding "
        "Outer Deity at Sequence 0 (Above the Sequence) who is the sole source of all boons "
        "on that path."
    ))
    story.append(body(
        "The following entries document the known Sequence 9 of each non-standard pathway. Due to "
        "the fragmentary nature of knowledge about Outer Deities, most pathways are only known at "
        "this sequence, though a few higher sequences have been recorded in the next chapter."
    ))
    story.append(sp(3))

    # ── Non-Standard Seq 9 entries ──
    nonstandard_seq9 = [
        ("Dancer", "Eternal Aeon (Inevitability) Pathway",
            [("DX", "+2"), ("SPI", "+6"), ("HT", "+1"),
             ("Double-Jointed", "Super flexible joints; +2 to Escape and any roll involving contortion or squeezing through tight spaces")],
            [("Dancing/DX [Average]", "+4"),
             ("Acrobatics/DX [Hard]", "+3")],
          "<b><font color='#C0392B'>Spiritual Dance (1 SPI):</font></b> Roll Dancing skill to begin a strange, "
          "over-the-top dance that places the Dancer in a transcendent, mystical state. After dancing for at "
          "least one turn, passively activate Spirit Vision and gain +2 to all Will rolls for 1d turns.\n"
          "<b><font color='#C0392B'>Appeasing Dance (2 SPI):</font></b> Roll Dancing skill at -1. On success, "
          "all witnesses must roll Will at -2 or be pacified — rendered calm, non-hostile, and disinclined "
          "toward violence for the duration of the dance and 1d turns after.\n"
          "<b><font color='#C0392B'>Summoning Dance (4 SPI):</font></b> Roll Dancing skill at -3, then summon "
          "up to 3 spiritual creatures whose powers, temperament, and hostility depend on the quality of the "
          "roll. By offering blood to one of them, the Dancer may temporarily have the spiritual creature "
          "inhabit their body, gaining the creature's abilities — but suffering severe drawbacks determined "
          "by which creature answers (GM's discretion). The creature inhabits the Dancer for 3d turns in "
          "combat (roughly 10–30 seconds outside combat). On a critical failure, summon an <i>incredibly "
          "hostile</i> spiritual creature that attacks the Dancer immediately, even before the dance ends."),

        ("Patient", "Monarch of Decay Pathway",
            [("SPI", "+2"), ("HT", "+4"),
             ("Hard Stomach", "Can consume spoiled, rotten, or contaminated food and drink without ill effect; +4 to HT rolls to avoid food-borne illness"),
             ("Resistance (Pathogens)", "+3 to all HT rolls that involve resisting disease already inside you")],
            [("Diagnosis/IQ [Hard]", "+3")],
          "<b><font color='#C0392B'>Pathogen Mutator (once per day):</font></b> Roll HT to mutate and empower one "
          "of the pathogens inside the Patient's body. On a successful roll, the disease gains +1 level (maximum +3), "
          "imposing an additional -1 penalty to HT to resist infection and empowering all of its negative effects. "
          "This is displayed as +1 within the disease's stat block — e.g., <i>Flu +1</i> (Roll HT -1 to not get "
          "infected when within 2m of someone infected; -2 to all ST, DX, and HT rolls). Each subsequent use on the "
          "same disease increases the level by another +1, up to a maximum of +3.\n"
          "<b><font color='#C0392B'>Hyper Contaminator (passive):</font></b> Any and all of the Patient's bodily "
          "fluids are guaranteed to transmit disease. The Patient's pathogens ignore normal methods of transmission — "
          "contact, airborne droplets, and environmental vectors all become viable. Even dried or diluted fluids "
           "retain full infectious potency.",
          [("Pathogen Magnet", "Perfect host for disease. Upon coming into contact with contaminated material, roll HT -2 or become infected.")]),

        ("Shaman", "High-Dimensional Overseer Pathway",
            [("SPI", "+8")],
            [("Ritualistic Magic/IQ [Very Hard]", "+4")],
          "<b><font color='#C0392B'>Territory Creation (6 SPI):</font></b> The Shaman may designate an object as a totem "
          "and create a mystical territory around it using Ritualistic Magic. Roll Ritualistic Magic/IQ (Very Hard). "
          "Success creates a normal territory (~75m radius); critical success creates an enhanced territory (~150m radius). "
          "Failure yields no result. On a critical failure, the Shaman suffers spiritual whiplash and a higher-dimensional "
          "monster takes notice of them. Within their territory, the Shaman receives +1 to ST, DX, and HT.\n"
          "<b><font color='#C0392B'>Ritualistic Spell Creation (varies):</font></b> Functionally similar to the Seq 7 "
          "Warlock's Spell Creation, the Shaman is able to borrow the powers of spirituality within their domain to create "
          "various spells. The specifics must be discussed with the GM, and the spells are always tied to the spirituality "
          "found within the territory — e.g., a river's innate spirituality may be used to create a rain spell; a graveyard's "
          "spirituality may be used to create a withering spell. All such spells use the Ritualistic Magic/IQ (Very Hard) "
          "skill for casting, and they may require inanimate or living sacrifices to activate.",
          [("Open Soul", "Due to passively entering an ascended spiritual state, become a target of monsters. Roll 3d at the "
            "start of every session; on a critical failure (17-18), attract the attention of a higher-dimensional monster.")]),

        ("Dreamless", "Goddess of Fate Pathway",
            [("SPI", "+10")],
            [("Spiritual Intuition/SPI [Hard]", "+2"),
             ("Spiritual Perception/SPI [Average]", "+2"),
             ("Divination Arts/SPI [Hard]", "+2")],
          "<b><font color='#C0392B'>Fate Sensation (passive):</font></b> The Dreamless is capable of sensing the flow and "
          "changes within fate around them. The GM may call for a Spiritual Intuition/SPI (Hard) roll to sense specific "
          "changes in fate.\n"
          "<b><font color='#C0392B'>Fate Sensation (active):</font></b> At any moment, the Dreamless may concentrate and "
          "roll Spiritual Perception/SPI (Hard) -2 to sense any nearby changes in fate. This can indicate many things, "
          "but all results are restricted to possible fates — absolute certainties or impossibilities lie beyond its reach.",
          [("Dreamless State", "Cannot have dreams or receive revelations through them.")]),

        ("Tramp", "Primordial Hunger Pathway",
            [("SPI", "+1"), ("DX", "+1"),
             ("Enhanced Stomach", "Penalties related to unfamiliar, rancid, bad-tasting food or other strange substances "
              "do not apply. Penalty to emotional damage for eating bad food is not included.")],
            [("Urban Survival/Per [Average]", "+3"),
             ("Survival (Rural)/Per [Average]", "+2"),
             ("Brawling/DX [Easy]", "+2"),
             ("Wrestling/DX [Average]", "+2")],
          "<b><font color='#C0392B'>Overwhelming Hunger:</font></b> When doing anything other than searching for food or "
          "eating, the Tramp suffers -5 to Will rolls to resist any activity related to duty, compulsion, desire, or goal. "
          "Their craving for food takes precedence over nearly everything else.",
          [("Voracious Appetite", "The Tramp's overwhelming craving for food becomes their primary Desire. The impact of "
            "other Desires on them is significantly reduced.")]),

        ("Villain", "Mother Goddess of Depravity Pathway",
            [("SPI", "+1"), ("ST", "+1"), ("HT", "+1"), ("DX", "+1")],
            [("Brawling/DX [Easy]", "+3"),
             ("Wrestling/DX [Average]", "+3"),
             ("Intimidation/Will [Average]", "+3")],
          "",
          [("Societal Menace", "A menace to society and a threat to those around you. When other people place trust in you "
            "or you sense someone's weakness, you feel a powerful urge to exploit that trust or weakness. Roll Will -4 to "
            "resist.")]),

        ("Scrooge", "Patriarch Pathway",
            [("SPI", "+4"), ("ST", "+1"), ("DX", "+1")],
            [],
          "<b><font color='#C0392B'>Greed Inducement (2 SPI):</font></b> Induces greed into a target, compelling a person "
          "to comply with the desire. -2 to the opponent's Will roll, or -4 if an object is used as a medium "
          "that the person is greedy for.\n"
          "<b><font color='#C0392B'>Ownership:</font></b> Within 24 hours, the Scrooge can track down the location of an "
          "object that belongs to them and find its current location.\n"
          "<b><font color='#C0392B'>Gluttony Inducement (2 SPI):</font></b> Induces a desire to eat something into a target, "
          "compelling a person to comply. -2 to the opponent's Will roll, or -4 if the medium is a food the "
          "person is hungry for. -1 to the opponent's Will roll if the object designated is inedible.",
           [("Sin of Greed", "In any scenario involving spending money, -5 to Will roll to resist (or -1 if it is "
            "absolutely necessary). In any scenario involving gaining money, -4 to Will roll — even if the "
            "mission is dangerous, the Scrooge accepts it because of their greed.")]),

        ("Broker", "Chaos Mist Pathway",
            [("IQ", "+1"), ("SPI", "+5"),
             ("Charisma +2", "+2 to reaction rolls and Influence skills")],
            [("Fast-Talk/IQ [Average]", "+3"),
             ("Diplomacy/IQ [Hard]", "+4"),
             ("Psychology/IQ [Hard]", "+2"),
             ("Merchant/IQ [Average]", "+3")],
          "<b><font color='#C0392B'>Order Sense (Passive):</font></b> The Broker may request the GM to describe the "
          "order inclinations of a person, room, conversation, or even something as abstract as an organisation, "
          "though appropriate knowledge is required. The GM must answer by describing the shade of 'grey' that "
          "is applicable — e.g. \"the room appears to be a darker grey\" showing the disorderly inclinations of "
          "all parties within, \"the man appears a radiant, almost pure white\" showing incorruptible justice.",
          [("Uncertain Order", "You gain a need to bring all forms of order to 'greyness'. When in a position to "
            "transform order or disorder into 'grey', roll against 12 to resist the desire. 'Grey' is the state "
            "between order and disorder where uncertainty can be exploited.")]),

        ("Initiator", "Everlasting Pathway",
            [("SPI", "+8")],
            [("Ritualistic Magic/IQ [Very Hard]", "+4"),
             ("Occultism/IQ [Average]", "+5")],
          "<b><font color='#C0392B'>Spell Mastery (Passive):</font></b> Learn and cast spells through worship of the "
          "Inextinguishable Ravings.\n"
          "<b><font color='#C0392B'>Midoro's Worship (8 SPI):</font></b> Roll Ritualistic Magic. Success: learn one "
          "spell. Critical success: learn two. Failure: +1 CoR. Critical failure: +3 CoR. Max 3 spells at a time.\n"
          "<b>Learnable spells:</b>\n"
          "<b>Star Scrying (3 SPI):</b> Gaze into the cosmos for a relevant revelation. "
          "Passive: once/session roll 3d ≤ 14; better result = better revelation. Failure: +1 CoR. Crit fail: +2 CoR.\n"
          "<b>Eyes of Depravity (2 SPI):</b> All in LOS roll Will-2 or act on base instinct desire for 1d turns. "
          "Passive: once/session, Initiator rolls Will-2 or becomes depraved for 1d minutes.\n"
          "<b>Weakening (2 SPI):</b> Target rolls HT-4 or suffers -2 to all rolls for 2d turns. "
          "Passive: once/session, Initiator rolls HT-2 or gains -2 to all rolls for 1d minutes.\n"
          "<b>Energize (1 SPI):</b> Target ally or self gains +1 to all rolls for 1d turns. "
          "Passive: once/session, Initiator rolls HT-1 or gains -1 to all rolls for 1d minutes.\n"
          "<b>Regeneration (2 SPI per 3 HP):</b> Heal any living thing within 5 m. Up to 6 HP/turn. "
          "Passive: once/session, Initiator rolls ST-1 or suffers 5 HP damage.\n"
          "<b>Adrenaline (3 SPI):</b> Target in LOS gains +1 to ST, DX, HT for 2d turns; halve FP costs. "
          "Passive: once/session, Initiator rolls HT-2 or loses 5 FP.\n"
          "<b>Earth Wall (4 SPI):</b> Create a 2 m tall, 4 m wide, 20 cm thick wall. "
          "Passive: when encountering a pretty plant, roll 12 or stop to admire for 1d minutes.\n"
          "<b>Pulse (3 SPI):</b> Create an impulse from the hands. Anything within 4 m rolls HT/DX/Acrobatics "
          "or is knocked down. "
          "Passive: once/session, roll HT or suffer headache (-1 IQ rolls) until cured.\n"
          "<b>Sensory Illusion (1 SPI):</b> Create a small sensory illusion to confuse opponents. "
          "Passive: once/session, hear a sudden loud sound that distracts.\n"
          "<b>History Replay (4 SPI):</b> Replay the past 12 hours of events in a room. "
           "Can fast-forward or start at a specific time.",
           [("Philosophy", "Strong desire to contemplate the philosophy of existence. "
             "Roll against 12 at any downtime or get lost in deep philosophical introspection.")]),

        ("Astronomy Aficionado", "Condenser Pathway",
            [("ST", "+1"), ("SPI", "+8"), ("HT", "+2")],
            [("Hidden Lore (Stars)/IQ [Average]", "+4"),
             ("Ritualistic Magic/IQ [Very Hard]", "+2"),
             ("Astrology/IQ [Hard]", "+3"),
             ("Astronomy/IQ [Hard]", "+4")],
          "",
          [("Star Worship", "At least once per day, roll 3d against 16 to study the cosmos. "
            "On a critical failure, gain 1 CoR. On a critical success, gain some insight about the world "
            "(up to the GM). If the desire is ignored, after a day gain -1 to all Will rolls "
            "(cumulative, per day of non-observing).")]),
     ]

    for entry in nonstandard_seq9:
        title, pathway, stats, skills, ability = entry[:5]
        disadvantages = entry[5] if len(entry) > 5 else []

        story.append(sp(4))

        # Pathway header
        story += subsection(f"Sequence 9: {title}  ·  {pathway}")
        story.append(sp(2))

        # Build merged stat + disadvantages table (continuous, with divider)
        if stats or skills or disadvantages:
            stat_rows = [[Paragraph("Stat / Advantage", S['TableHeader']), Paragraph("Gain", S['TableHeader'])]]
            for k, v in stats:
                stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            divider_idx = None
            if disadvantages:
                divider_idx = len(stat_rows)
                stat_rows.append([Paragraph("<b>Drawbacks</b>", S['TableHeader']),
                                  Paragraph("", S['TableHeader'])])
                for k, v in disadvantages:
                    stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            stat_t = Table(stat_rows, colWidths=[1.55*inch, 1.55*inch])
            stat_t.setStyle(table_style())
            if divider_idx is not None:
                stat_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, divider_idx), (-1, divider_idx), MID_NAVY),
                    ('LINEABOVE', (0, divider_idx), (-1, divider_idx), 0.5, GOLD),
                    ('TOPPADDING', (0, divider_idx), (-1, divider_idx), 3),
                    ('BOTTOMPADDING', (0, divider_idx), (-1, divider_idx), 3),
                ]))

            skill_rows = [[Paragraph("Skill", S['TableHeader']), Paragraph("Change", S['TableHeader'])]]
            for k, v in skills:
                skill_rows.append([
                    Paragraph(k, S['TableCell']),
                    Paragraph(v, S['TableCell']),
                ])
            skill_t = Table(skill_rows, colWidths=[2.4*inch, 0.85*inch])
            skill_t.setStyle(table_style())

            # Combo: merged stat table + skills table side by side
            combo = Table([[stat_t, skill_t]], colWidths=[3.2*inch, 3.35*inch])
        else:
            combo = stat_t

        combo.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(combo)
        story.append(sp(2))

        # Ability block (with optional Reinforced box)
        main_ab, reinf_ab = split_reinforced(ability)
        render_ability_boxes(main_ab, reinf_ab, story)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════════
    # Chapter 15: Non-Standard Sequence 8 Potion Effects
    # ═══════════════════════════════════════════════════════════════════════════════

    story += chapter("Chapter 15: Non-Standard Sequence 8 Potion Effects")

    story.append(body(
        "The following entries document higher sequences of certain non-standard pathways "
        "where the potion formula or boon structure has been recorded."
    ))
    story.append(sp(2))
    story.append(body(
        "<b>Reading these entries:</b> See <b>Chapter 9</b> for instructions on how to read a pathway entry. "
        "The same rules for potion-granted skills and attributes from Chapter 9 apply here."
    ))
    story.append(sp(3))

    nonstandard_seq8 = [

        ("Secretary", "Second Law Pathway",
            [("SPI", "+1"),
             ("Acute Hearing", "+2 to Hearing rolls; detect faint sounds, eavesdrop through walls, identify speech in noise"),
             ("Wolf of Wall Street", "+2 to all rolls when representing an organization")],
            [("Fast-Talk/IQ [Average]", "+2"),
             ("Acting/IQ [Average]", "+1"),
             ("Diplomacy/IQ [Hard]", "+2"),
             ("Psychology/IQ [Hard]", "+3"),
             ("Savoir-Faire (Corporate)/IQ [Easy]", "+3"),
             ("Forgery/IQ [Hard]", "+2"),
             ("Law (Corporate)/IQ [Hard]", "+4")],
          "",
          [("Compulsion: Corporate Inconvenience", "When dealing with people while in a position of power, gain a compulsion "
            "to make their life harder by overcomplicating the bureaucratic process.")]),

        ("Reporter", "Sublunary Eye Pathway",
            [("ST", "+1"), ("DX", "+3"), ("IQ", "+1"), ("SPI", "+2"),
             ("Basic Speed", "+2.00"),
             ("Acute Vision", "+2 to vision-based Perception rolls; spot distant details"),
             ("Experienced Investigator", "+1 to all Investigation, Observation, and Search rolls")],
            [("Observation/Per [Average]", "+3"),
             ("Shadowing/IQ [Average]", "+3"),
             ("Forensics/IQ [Hard]", "+3"),
             ("Search/Per [Average]", "+3"),
             ("Sleight of Hand/DX [Hard]", "+3")],
          "<b><font color='#C0392B'>Investigation (once per scene):</font></b> Roll 3d against 14. Depending on the "
          "degree of success, the GM must disclose some of the yet undiscovered information about the "
          "current scene. Does not necessarily apply only to investigation scenes. On failure, nothing happens. "
          "This ability stacks with the Experienced Investigator advantage.\n"
          "<b><font color='#C0392B'>True Sight (1 SPI per minute):</font></b> While active, see through any illusion, "
          "substitution, concealment, or other spiritual phenomena at the level of a Sequence higher or below. "
          "While active, it is possible for the Reporter to witness the scene from a different angle. For example, "
          "if there is a person hiding under a window on the second floor, the Reporter may use True Sight to "
          "shift their perspective higher up to see them crouching beneath the window. They may use their Spiritual "
          "Intuition to know how to shift their perspective for the best viewing angle.",
          [("Imaginary Mismatch", "Begin to dislike or outright hate anything about the world that does not match your "
            "'fantasy' of how the world should be. Roll against 12 when interacting with a mismatched phenomenon "
            "to not show disdain.")]),

        ("Sex Addict", "Patriarch Pathway",
            [("SPI", "+2"), ("DX", "+1"), ("Will", "+1"),
             ("Basic Speed", "+1.00"), ("ST", "+1"), ("HT", "+1"),
             ("Fit", "+1 to all HT rolls; recover FP at twice the normal rate"),
             ("Simp", "Mental suggestion and charm rolls against you are at -2. "
              "From a desired target, these gain +2 (mental suggestion) or +4 (charm).")],
            [("Pharmacy/IQ [Hard]", "+4"),
             ("Alchemy/IQ [Very Hard]", "+3")],
          "<b><font color='#C0392B'>Lust Inducement (2 SPI):</font></b> Induce lust into a target. "
          "-2 to the opponent's Will roll, or -4 if a crush or desired type is used as the designated target.\n"
          "<b><font color='#C0392B'>Drug Knowledge:</font></b>\n"
          "<b>Truth Serum:</b> Compels truth-telling. -2 Will (first question), -3 Will (third question), "
          "-4 Will (subsequent questions).\n"
          "<b>Cough Antidote Gas:</b> Antidote to Truth Serum.\n"
          "<b>Sedative Gas:</b> ST and DX temporarily reduced to 25% of normal.\n"
           "<b><font color='#C0392B'>Hormonal Analysis:</font></b> Acquire differentiating hormonal "
           "information of various individuals.\n"
           "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
           "<b><font color='#C0392B'>Greed Inducement (Reinforced):</font></b> The Sex Addict's Sin-based compulsion "
           "may be substituted for Greed Inducement — treat as Greed Inducement with -3 "
           "to the target's Will (instead of -2). If a desired object or person is used "
           "as the medium, the penalty increases to -5 (from -4).\n"
           "<b><font color='#C0392B'>Ownership (Reinforced):</font></b> The Sex Addict can track any person they have "
           "had intimate contact with within the past 48 hours (from 24 hours). The "
           "tracking is instinctive — no roll required unless the target is shielded "
           "by anti-divination wards (roll Spiritual Intuition to bypass).\n"
           "<b><font color='#C0392B'>Gluttony Inducement (Reinforced):</font></b> Can now induce cravings beyond food — "
           "alcohol, drugs, or any consumable substance. The Will penalty increases "
           "by +1 in all cases (-3 base, -5 if the consumable is already desired).",
           [("Sin of Lust", "Replaces Sin of Greed. Crave intimate acts with another person. "
              "-5 to Will when pursuing, performing, or preparing for the deeds.")]),

        ("Alms Monk", "Eternal Aeon Pathway",
            [("SPI", "+3"), ("Will", "+2"),
             ("Resistant (Weather)", "+8 to HT vs. weather hazards")],
            [("Hiking/HT [Average]", "+2"),
             ("Ritualistic Magic/IQ [Very Hard]", "+3")],
           "<b><font color='#C0392B'>Luck Intuition (Passive):</font></b> Without a roll, the Alms Monk understands the luck of any "
            "person within line of sight. They perceive a vague trend through different colours (e.g. future "
            "romantic encounter, possible wealth gain, impending life-threatening calamity). The exact nature "
            "is up to the GM.\n"
            "<b><font color='#C0392B'>Prophecy Spell (3 SPI):</font></b> After gathering several ingredients (not too rare), combine "
            "them into a concoction and feed it to a non-purified corpse that has been dead for less than a "
            "week. After completing the ritual, ask <b>3 questions</b> about the future of anyone or anything. "
            "The GM must provide true answers within reason. Questions regarding demigods always fail. The "
            "prophecy answers only one element per question (if a question has multiple elements — e.g. "
            "\"when and where\" — only one is answered).\n"
            "<b><font color='#C0392B'>Luck Enhancement Spell (3 SPI):</font></b> The Alms Monk can 'extract' someone else's bad luck "
            "using a mystical medium (such as blood, or their own) and attach it to an object. If that object "
            "is opened, taken, worn, or stepped on without the Alms Monk's explicit or implied consent, the "
            "bad luck transfers to that individual. If the luck is not transferred within 3 days of attachment, "
            "the bad luck returns and becomes untransferable for a month.\n"
            "<b><font color='#C0392B'>Animal Creation Spell (3 SPI):</font></b> The Alms Monk can enchant a full animal skin. After "
            "covering a person with it, it allows them to turn into that animal with an incantation, and a "
            "separate incantation to return. The animal skin must be large enough to fully cover the person. "
            "After use, it loses its mystical properties but may be used for the creation of a new pelt.\n"
            "<b><font color='#C0392B'>Exorcism Spell (4 SPI):</font></b> By knowing a wraith's or spectre's true name, the Alms Monk "
             "rolls Ritualistic Magic vs. the spirit's SPI or Will (whichever is higher). On success, the "
             "creature is exorcised. The ritual requires at least 5 turns to take effect.\n"
             "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
             "<b><font color='#C0392B'>Spiritual Dance (Reinforced):</font></b> The Alms Monk may substitute a slow, "
             "meditative walk for the dance. The +2 to Will rolls extends to all SPI-based "
             "rolls and lasts for 2d turns (from 1d). Spirit Vision activates automatically "
             "without an SPI cost while the walk continues.\n"
             "<b><font color='#C0392B'>Appeasing Dance (Reinforced):</font></b> The Will penalty for witnesses increases "
             "to -4 (from -2). The Alms Monk may target a single hostile creature with the "
             "appeasing effect without needing to perform the full dance — a gesture and "
             "a murmured verse suffice (costs 1 SPI, range 10 m).\n"
             "<b><font color='#C0392B'>Summoning Dance (Reinforced):</font></b> On a successful summon, the Alms Monk "
             "may negotiate with the summoned creature for an additional service (beyond "
             "inhabitation) — the creature will perform one task of equivalent difficulty "
             "to the summoning, provided the task aligns with its nature. The creature "
              "remains for up to 1 hour outside combat (instead of 10-30 seconds)."),

        ("Musician", "Eternal Edict Pathway",
            [("SPI", "+2")],
            [("Singing/HT [Easy]", "+4"),
             ("Spiritual Intuition/SPI [Average]", "+1"),
             ("Spiritual Perception/SPI [Hard]", "+1")],
          "<b><font color='#C0392B'>Fate Symphony (passive):</font></b> Fate Sensation is enhanced. The Musician constantly "
          "hears the symphony of fate around them.\n"
          "<b><font color='#C0392B'>Symphony Decryption (active):</font></b> Concentrate on a source and roll IQ to decrypt "
          "its symphony. Success reveals several possible futures. Critical success yields a clear sign. "
          "On failure, spend 1 FP. On critical failure, spend 3 FP and gain 1 CoR. What the Musician "
          "discerns depends on the degree of success and GM discretion.\n"
          "<b><font color='#C0392B'>Song of Fate (varies):</font></b> After decrypting a target's fate, the Musician may amplify "
          "it by singing. Roll Singing (HT/Easy) with a bonus or penalty depending on the significance "
          "of the fate amplified (GM discretion). Spend SPI appropriate to the effect (GM discretion). "
          "The Musician may spend additional SPI to forcibly succeed on the Singing roll. Fate cannot be "
          "changed — only amplified. Examples: amplifying the fate of an impending illness forces the "
          "target to roll HT or fall ill immediately; amplifying the fate of an emotional breakdown "
          "forces a Will roll or the target becomes uncontrollable temporarily.",
           [("Distracted by Sight", "When not blinded or wearing a blindfold, −2 to Symphony Decryption and Song of Fate.")]),

        ("Shadow Merchant", "Chaos Mist Pathway",
            [("SPI", "+6"),
             ("Pacifying Aura", "Unless provoked, anyone with malice towards you rolls Will -4 or becomes pacified. "
              "Disadvantage decreased or turned into advantage depending on the being's level, up to the GM")],
            [("Fast-Talk/IQ [Average]", "+2"),
             ("Diplomacy/IQ [Hard]", "+3"),
             ("Merchant/IQ [Average]", "+1"),
             ("Spiritual Perception/SPI [Average]", "+3")],
          "<b><font color='#C0392B'>Shadow Creature Detection (1 SPI):</font></b> Detect any shadow creature within vicinity. "
          "If possible for one to be nearby, the GM must determine the power and hostility of the shadow creature. "
          "If the creature is of a sufficiently high level, roll Will or gain 1 CoR upon witnessing it. Due to "
          "Pacifying Aura it is possible for the Shadow Merchant to broker deals with these creatures. When dealing "
          "with shadow creatures, it is prudent not to show malice, attack them, or secretly plot against them.\n"
          "<b><font color='#C0392B'>Shadow Contract (4 SPI):</font></b> Form contracts with any consenting party, with each "
          "other's shadows acting as witnesses. The other party must possess a shadow or be a shadow creature for the "
          "contract to be binding. At signing the Shadow Merchant can roll Will to bend the contract's terms, with "
          "the degree of success indicating how much can be distorted (up to the GM). If broken by either party, "
          "the responsible party receives 2d+1 spiritual damage.\n"
          "<b><font color='#C0392B'>Fake Shadow Creation (Varies):</font></b> Create fake shadows within a 10 m area.\n"
          "<b><font color='#C0392B'>Shadow Transformation (3 SPI per 10 min):</font></b> Transform into shadows and move through "
          "them at Base Speed × 4. By transforming into a shadow the Shadow Merchant can avoid most forms of physical "
          "damage by rolling against DX +3.\n"
          "<b><font color='#C0392B'>Shadow Concealment (1 SPI per 10 min):</font></b> Conceal themselves in shadows. Roll Per "
           "-3 to detect them while still, Per -1 while moving. Attacking or sudden actions break concealment."),

        ("Commentator", "Everlasting Pathway",
            [("IQ", "+1"), ("SPI", "+3")],
            [("Fast-Talk/IQ [Average]", "+4"),
             ("Diplomacy/IQ [Hard]", "+4"),
             ("Public Speaking/IQ [Average]", "+4"),
             ("Psychology/IQ [Hard]", "+5")],
          "<b><font color='#C0392B'>Consciousness Understanding (Passive):</font></b> By rolling Psychology -2, the "
          "Commentator can glean significantly more information about a person, similar to a Spectator's analysis.\n"
          "<b><font color='#C0392B'>Commentary (2 SPI):</font></b> Roll an appropriate speech skill at -2. All who hear "
          "the Commentator must roll Will against the Commentator's degree of success on their speech roll, or become "
          "influenced by their ideas.\n"
          "<b><font color='#C0392B'>Reinforced Abilities:</font></b>\n"
          "<b><font color='#C0392B'>Midoro's Worship (Reinforced):</font></b> The Commentator can now hold up to four "
          "spells at a time (up from three)."),
     ]

    for entry in nonstandard_seq8:
        title, pathway, stats, skills, ability = entry[:5]
        disadvantages = entry[5] if len(entry) > 5 else []

        story.append(sp(4))
        story += subsection(f"Sequence 8: {title}  ·  {pathway}")
        story.append(sp(2))

        # Build merged stat + disadvantages table
        if stats or skills or disadvantages:
            stat_rows = [[Paragraph("Stat / Advantage", S['TableHeader']), Paragraph("Gain", S['TableHeader'])]
                        for _ in range(1)]  # placeholder, rebuild below
            stat_rows = [[Paragraph("Stat / Advantage", S['TableHeader']), Paragraph("Gain", S['TableHeader'])]]
            for k, v in stats:
                stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            divider_idx = None
            if disadvantages:
                divider_idx = len(stat_rows)
                stat_rows.append([Paragraph("<b>Drawbacks</b>", S['TableHeader']),
                                  Paragraph("", S['TableHeader'])])
                for k, v in disadvantages:
                    stat_rows.append([Paragraph(k, S['BodyBold']), Paragraph(v, S['TableCell'])])

            stat_t = Table(stat_rows, colWidths=[1.55*inch, 1.55*inch])
            stat_t.setStyle(table_style())
            if divider_idx is not None:
                stat_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, divider_idx), (-1, divider_idx), MID_NAVY),
                    ('LINEABOVE', (0, divider_idx), (-1, divider_idx), 0.5, GOLD),
                    ('TOPPADDING', (0, divider_idx), (-1, divider_idx), 3),
                    ('BOTTOMPADDING', (0, divider_idx), (-1, divider_idx), 3),
                ]))

            skill_rows = [[Paragraph("Skill", S['TableHeader']), Paragraph("Change", S['TableHeader'])]]
            for k, v in skills:
                skill_rows.append([
                    Paragraph(k, S['TableCell']),
                    Paragraph(v, S['TableCell']),
                ])
            skill_t = Table(skill_rows, colWidths=[2.4*inch, 0.85*inch])
            skill_t.setStyle(table_style())

            combo = Table([[stat_t, skill_t]], colWidths=[3.2*inch, 3.35*inch])
        else:
            combo = stat_t

        combo.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(combo)
        story.append(sp(2))

        # Ability block (with optional Reinforced box)
        main_ab, reinf_ab = split_reinforced(ability)
        render_ability_boxes(main_ab, reinf_ab, story)

    story.append(PageBreak())

    story += chapter("Appendix A: Quick Reference Tables")

    story += section("Core Mechanic: Roll 3d6 Equal to or Under Target Number")
    story.append(body("Critical Success: 3–4 always | Critical Failure: 17–18, or fail by 10+"))
    story.append(sp(3))

    quick_skill = [
        ["Difficulty", "1 pt", "2 pts", "4 pts", "8 pts", "16 pts"],
        ["Easy (E)", "Attr+0", "Attr+1", "Attr+2", "Attr+3", "Attr+4"],
        ["Average (A)", "Attr-1", "Attr+0", "Attr+1", "Attr+2", "Attr+3"],
        ["Hard (H)", "Attr-2", "Attr-1", "Attr+0", "Attr+1", "Attr+2"],
        ["Very Hard (VH)", "Attr-3", "Attr-2", "Attr-1", "Attr+0", "Attr+1"],
    ]
    quick_skill[0] = [Paragraph(c, S['TableHeader']) for c in quick_skill[0]]
    for i in range(1, len(quick_skill)):
        quick_skill[i] = [Paragraph(c, S['TableCellCenter']) for c in quick_skill[i]]
    story.append(Table(quick_skill, colWidths=[0.95*inch, 0.95*inch, 0.95*inch, 0.95*inch, 0.95*inch, 0.95*inch],
                        style=table_style()))
    story.append(sp(3))

    story += section("Combat Quick Reference")
    story.append(body("<b>Active Defenses:</b> Dodge = Speed+3 | Parry = Skill/2+3 (-4 cumulative) | Block = Shield/2+3"))
    story.append(body("<b>Direction Penalties:</b> Side -2 | Rear -4"))
    story.append(body("<b>Bonuses:</b> Retreat: +3 Dodge/+1 Block/+1 Parry | Aim: weapon ACC bonus (+1/extra Aim round)"))
    story.append(body("<b>Hit Locations:</b> Torso +0 ×1 | Arm/Leg -2 ×1 | Vitals -3 ×3 | Hand/Foot -4 ×1 | Face -5 ×1 | Neck -5 Cr×1.5/Cut×2/Imp×2 | Skull -7 ×4 DR2 | Eye -9 ×4"))
    story.append(body("<b>Wounding:</b> Crush ×1 | Cut ×1.5 | Impale ×2 | Pi (small) ×0.5 / Pi ×1 / Pi+ ×1.5 | Burn ×1 | Toxic ×1"))
    story.append(body("<b>Major Wound:</b> Hit > ½ HP -> HT or stunned 1d6 sec | Fail by 5+ -> down 15 min"))
    story.append(sp(3))

    crit_table = [
        ["Roll", "Result"],
        ["3–4", "Critical Success (always)"],
        ["Roll <= Target", "Success"],
        ["Roll <= Target -3", "Good Success"],
        ["Roll <= Target -5", "Excellent Success"],
        ["Roll > Target", "Failure"],
        ["Roll >= Target +10", "Critical Failure"],
        ["17–18", "Critical Failure (always)"],
    ]
    crit_table[0] = [Paragraph(c, S['TableHeader']) for c in crit_table[0]]
    for i in range(1, len(crit_table)):
        crit_table[i] = [Paragraph(c, S['TableCellCenter']) for c in crit_table[i]]
    story.append(Table(crit_table, colWidths=[1.3*inch, 3.0*inch], style=table_style()))
    story.append(sp(3))

    story += section("Spiritual Skills Quick Reference")
    spi_quick = [
        ["Skill", "Difficulty", "What It Does", "When to Use"],
        ["Spiritual Intuition", "SPI/Hard", "Sense danger through fate before it happens", "Before danger strikes; suspicious situations"],
        ["Spiritual Perception", "SPI/Average", "Detect spiritual presences passively or actively", "Entering locations; sensing Beyonders"],
        ["Divination Arts", "SPI/Hard", "Focused divination: pendulum, coin, dowsing, dream, scrying, tarot", "Gathering hidden information; quick questions"],
    ]
    spi_quick[0] = [Paragraph(c, S['TableHeader']) for c in spi_quick[0]]
    for i in range(1, len(spi_quick)):
        spi_quick[i] = [Paragraph(c, S['TableCell']) for c in spi_quick[i]]
    story.append(Table(spi_quick, colWidths=[1.1*inch, 0.85*inch, 1.8*inch, 2.6*inch], style=table_style()))
    story.append(sp(3))

    story += section("CoR & Digestion Reference")
    story.append(bullet("Max CoR = Will score | At max: character becomes NPC monster"))
    story.append(bullet("Digestion: 0% -> 100% required before advancing sequence"))
    story.append(bullet("Using powers while drained of Spirituality: +1 CoR per use"))
    story.append(bullet("Advancing without full digestion: +10 CoR (catastrophic)"))
    story.append(sp(3))

    story += section("SPI Recovery Reference")
    spi_rec = [
        ["Method", "Recovery", "Requirements"],
        ["Rest", "1 SPI per hour", "No strenuous physical or spiritual activity"],
    ]
    spi_rec[0] = [Paragraph(c, S['TableHeader']) for c in spi_rec[0]]
    for i in range(1, len(spi_rec)):
        spi_rec[i] = [Paragraph(c, S['TableCell']) for c in spi_rec[i]]
    story.append(Table(spi_rec, colWidths=[1.5*inch, 1.8*inch, 3.0*inch], style=table_style()))
    story.append(sp(3))

    story += section("Common Modifiers")
    mod_data = [
        ["Situation", "Modifier"],
        ["Easy task (well-lit, calm, plenty of time)", "+4 or more"],
        ["Routine conditions", "+0"],
        ["Distracted or hurried", "-2"],
        ["Adverse conditions (dark, noisy, dangerous)", "-4"],
        ["Very adverse conditions (combat, extreme weather)", "-6 or worse"],
        ["Using untrained skill (default)", "Attribute -4 to -6"],
        ["Good tools / equipment", "+1 to +2"],
        ["Improvised / poor tools", "-2 to -4"],
        ["Aided by someone with the same skill", "+2 (if they succeed first)"],
    ]
    mod_data[0] = [Paragraph(c, S['TableHeader']) for c in mod_data[0]]
    for i in range(1, len(mod_data)):
        mod_data[i] = [Paragraph(c, S['TableCell']) for c in mod_data[i]]
    story.append(Table(mod_data, colWidths=[3.0*inch, 3.3*inch], style=table_style()))
    story.append(sp(3))

    story.append(body(
        "<i>This rulebook was created by fans for fans. It is intended for personal, non-commercial use. "
        "Lord of the Mysteries is the creative work of Cuttlefish That Loves Diving. "
        "GURPS is a trademark of Steve Jackson Games.</i>"
    ))

    story += chapter("Appendix B: The Political World of the Fifth Epoch")
    story.append(flavor(
        "Seven Orthodox Churches. Four Great Nations. Countless secret organizations. "
        "And beneath it all, a hidden world of Beyonders that ordinary people will never know exists."
    ))
    story.append(body(
        "The Fifth Epoch began with the collapse of the Trunsoest Empire and the rise of the Four Great "
        "Nations on the Northern Continent. By Year 1349 — the era in which most LOTM campaigns are set — "
        "the world resembles a Victorian-industrial age: steam power, railways, gas lamps, and newspapers "
        "sit alongside divine miracles, cursed artifacts, and secret Beyonder factions. The Seven Orthodox "
        "Churches and the Four Great Nations govern the visible world jointly. Everything else operates in shadow."
    ))
    story.append(sp(3))

    story += section("The Four Great Nations")

    story += subsection("Loen Kingdom — The Dominant Power")
    story.append(body(
        "The strongest nation on the Northern Continent, located in the east. Founded by the Augustus "
        "Family after the collapse of the Trunsoest Empire, Loen's industrial and economic strength "
        "is unrivalled. Its capital, Backlund, is the most populous city in the known world — a sprawling "
        "mass of factories, fog, poverty, and aristocratic excess. Politically, Loen resembles a "
        "constitutional monarchy under tension: the old noble landowning class clings to its privileges "
        "while a rising New Party of industrialists and capitalists — empowered by the Industrial "
        "Revolution — pushes for reform. The Church of the Evernight Goddess holds enormous influence "
        "over Loen's spiritual life, and its Nighthawk Beyonder faction polices supernatural threats "
        "within the kingdom's borders."
    ))
    story.append(sp(3))

    story += subsection("Intis Republic — Revolution's Legacy")
    story.append(body(
        "The second-strongest nation, located in the west. Originally the Intis Kingdom, it was "
        "overthrown by the legendary Emperor Roselle Gustav, whose reign transformed the continent "
        "and left behind a scattered legacy of golden diaries. After Roselle's death, Intis became "
        "a parliamentary republic, governed by a National Convention of over 300 members with the "
        "authority to appoint the president, prime minister, and ministers. Its national slogan is "
        "<i>Freedom, Equality, Fraternity.</i> Internally, Intis is fractious: the National Party, "
        "Enlightenment Party, and Revolutionary Party compete in elections, while the Emperor Party "
        "and the underground Carbonari seek change by other means. The Church of the God of Steam "
        "and Machinery holds particular sway here."
    ))
    story.append(sp(3))

    story += subsection("Feynapotter Kingdom — The Pious Realm")
    story.append(body(
        "The third power on the Northern Continent, Feynapotter is the most religiously conservative "
        "of the four great nations. Its monarchy rules in close partnership with the Church of the "
        "God of Knowledge and Wisdom. Scholarship, arcane research, and magical tradition are "
        "central to its culture. Feynapotter sits between Loen and Feysac geographically, making "
        "it a frequent site of diplomatic tension and proxy conflict."
    ))
    story.append(sp(3))

    story += subsection("Feysac Empire — The Northern Giant")
    story.append(body(
        "The northernmost empire and the most militaristic of the four powers. Feysac's brutal "
        "winters and vast interior have produced a culture that prizes strength, endurance, and "
        "martial honour. After Roselle opened the sea routes to the Southern Continent (Balam), "
        "Feysac sent its own armies south to claim colonial territory — competing bitterly with "
        "Loen and Intis for resources and influence. The Church of the God of Combat and Hunting "
        "holds significant power within the empire."
    ))
    story.append(sp(3))

    story += section("The Southern Continent — Balam")
    story.append(body(
        "At the close of the Fourth Epoch, the ancient Balam "
        "Empire collapsed. The Star Highlands and Paz Valley briefly broke away as independent "
        "kingdoms, but both were eventually crushed by Northern Continent invasion and colonisation. "
        "By the Fifth Epoch, the Southern Continent is divided primarily between Loen and Intis as "
        "colonial territories. West Balam is especially volatile — a contested frontier where Loen "
        "and Intis forces, mercenaries, and local resistance movements fight continuously. Ruined "
        "temples, lost artefacts of the old gods, and buried Sequence ingredients make Balam a "
        "destination for treasure hunters, Beyonder factions, and desperate adventurers."
    ))
    story.append(sp(3))

    story += section("The Seas and the Pirate Kings")
    story.append(body(
        "The seas between the continents are not governed by any nation. They are ruled by "
        "violence, tradition, and the authority of the four Pirate Kings and seven Admirals — "
        "powerful Beyonders who have carved out dominion over the ocean lanes. The Church of the "
        "Lord of Storms has its own complicated relationship with the sea, as its followers "
        "include both lawful sailors and sea-going Beyonders who have little interest in "
        "terrestrial politics. For campaigns set aboard ships or in island ports, the seas "
        "represent a third space: outside the law of any nation, governed only by power."
    ))
    story.append(sp(3))

    story += section("The Seven Orthodox Churches")
    story.append(body(
        "Running parallel to national governments — and often deeper in power — are the Seven "
        "Orthodox Churches. Each god grants its followers a distinct pathway and maintains "
        "institutional Beyonder forces that police supernatural threats, hunt heretics, and "
        "pursue their deity's agenda. The major churches relevant to a Fifth Epoch campaign are:"
    ))

    churches = [
        ["Deity", "Stronghold", "Beyonder Faction"],
        ["Goddess of Evernight", "Cathedral of Serenity — Amantha mountain range, Winter County, Loen Kingdom", "Nighthawks"],
        ["God of Steam & Machinery", "Patriarchal Cathedral — Cathedral District, Trier", "Machinery Hivemind"],
        ["God of Knowledge and Wisdom", "Azshara, capital of Lenburg", "The Knowing Eye"],
        ["God of Combat", "St. Millom, capital of the Feysac Empire", "Sentinels"],
        ["Lord of Storms", "Pasu Island, Sonia Sea", "Mandated Punishers"],
        ["Eternal Blazing Sun", "Saint Viève Cathedral — Island District, Trier", "Inquisition"],
        ["Earth Mother", "Feynapotter Kingdom", "Fertility Order"],
    ]
    churches[0] = [Paragraph(c, S['TableHeader']) for c in churches[0]]
    for i in range(1, len(churches)):
        churches[i] = [Paragraph(c, S['TableCell']) for c in churches[i]]
    story.append(Table(churches, colWidths=[1.7*inch, 2.6*inch, 1.95*inch],
                       style=table_style()))
    story.append(sp(3))

    story += section("The Undercurrent: What Year 1349 Feels Like")
    story.append(body(
        "By the time most campaigns begin, the Fifth Epoch is approaching a breaking point. "
        "The Outer Gods — vast, unknowable entities beyond the barrier between worlds — are "
        "pressing inward with increasing intensity. Forbidden power is spreading. Ancient sealed "
        "evils are stirring. The major churches are mobilising resources and tightening control "
        "over their Beyonder factions. Nations are arming. And in the fog-choked streets of "
        "Backlund, ordinary people go about their lives entirely unaware that the world is "
        "balanced on a knife's edge."
    ))
    story.append(body(
        "For player characters, this tension is the campaign's engine. Every secret uncovered, "
        "every Sequence advanced, every faction approached is one more thread pulled on a tapestry "
        "that — if the wrong threads are pulled in the wrong order — could unravel entirely."
    ))
    story.append(sp(3))

    story += chapter("Appendix C: Orthodox Churches & Secret Organizations")

    story.append(body(
        "The Northern Continent is governed not only by four great nations but by seven Orthodox "
        "Churches whose influence touches every aspect of daily life, politics, and the Beyonder world. "
        "Alongside them, countless secret organizations operate in the shadows — some ancient, some "
        "newly formed, all dangerous. What follows is what is known, or can be inferred, as of Year 1349."
    ))
    story.append(sp(3))

    story += section("The Seven Orthodox Churches")
    story.append(body(
        "The seven Orthodox Churches were formally established after the Cataclysm at the end of the "
        "Third Epoch. Each church controls specific Beyonder pathways, runs its own enforcement division "
        "(functionally a supernatural police force), and maintains a presence in all major cities. "
        "The churches cooperate on existential threats but compete fiercely for influence, territory, "
        "converts, and the control of Sealed Artifacts. Church inter-rivalry is not just political — "
        "it is built into the cosmology. The fall of adjacent pathway gods is necessary for any god "
        "to ascend further, meaning the orthodox gods are, by definition, each other's ultimate enemies."
    ))
    story.append(sp(3))

    # Build the master church table
    church_rows = [
        ["Church", "Pathway", "Domain & Main Territory", "Enforcement Division", "Key Notes"],
        ["Evernight Goddess",
         "Darkness",
         "Night, darkness, death, fate. Dominant in Loen Kingdom; domains in East Balam.",
         "Nighthawks (local) + Red Gloves (elite, Seq 7+)",
         "HQ: Cathedral of Serenity, Amantha Mts. Promotes gender equality. Clergymen in black-red robes. Rivals: Church of the God of Combat."],
        ["Lord of Storms",
         "Tyrant",
         "Sea, storms, sailors. Strong in Loen, Rorsted Archipelago, Sonia Sea.",
         "Mandated Punishers",
         "HQ: Chasm of Storms Cathedral, Pasu Island. Most male-centric church. Doctrine: vent all anger like a storm. Even pirates worship informally. Rivals: Eternal Blazing Sun, God of Knowledge."],
        ["Eternal Blazing Sun",
         "Sun",
         "Light, fire, holy war. Dominant in Intis Republic; strong in Southern Continent colonies.",
         "Inquisitors",
         "Gold-adorned cathedrals. Sun Sacrifice is their major festival (longest day of year). At least one female Angel. Rivals: Lord of Storms, God of Knowledge."],
        ["God of Knowledge & Wisdom",
         "White Tower",
         "Learning, secrets, the mind. Lenburg, Segar, Masin (expelled from Feynapotter in 738).",
         "The Knowing Eye",
         "Discriminates by intelligence, not gender. Prizes scholars and investigators. Symbol: omniscient eye on an open book. Rivals: Lord of Storms, Eternal Blazing Sun."],
        ["Earth Mother",
         "Mother",
         "Nature, fertility, reproduction. Feynapotter Kingdom; limited in Loen.",
         "Fertility Order (limited)",
         "Promotes gender equality with emphasis on birth as sacred. Quiet and pastoral. Split into 'Favored' and 'Blessed' divisions to guard against false revelations."],
        ["God of Combat",
         "Twilight Giant",
         "War, strength, martial glory. Feysac Empire (sole state religion).",
         "The Bloodgrave Order",
         "Most male-centric church. Militaristic and aggressive. Historically hostile to Evernight Goddess. Beyonders are among the most physically powerful Demigods in the world."],
        ["God of Steam & Machinery",
         "Paragon",
         "Industry, invention, progress. Intis Republic; formerly major in Loen (expelled post-1350).",
         "Machinery Hivemind",
         "Formerly God of Craftsmanship; renamed in Roselle's era. Fewest Sealed Artifacts. Neutral on gender. Hivemind members often mechanize parts of their own bodies."],
    ]
    church_rows[0] = [Paragraph(c, S['TableHeader']) for c in church_rows[0]]
    for i in range(1, len(church_rows)):
        church_rows[i] = [Paragraph(c, S['TableCell']) for c in church_rows[i]]
    story.append(Table(church_rows, colWidths=[1.0*inch, 0.7*inch, 1.55*inch, 1.25*inch, 1.8*inch],
                       style=table_style()))
    story.append(sp(3))

    story += section("Enforcement Divisions — What Players Will Encounter")
    story.append(body(
        "In practice, the church division a player character deals with most depends entirely on where "
        "they operate and whose believers are involved in a given incident. In Loen (the default campaign "
        "setting), the Nighthawks and Machinery Hivemind are the most visible. On the seas, it is the "
        "Mandated Punishers. In Intis and colonial territory, it is the Inquisitors."
    ))
    story.append(sp(3))
    div_data = [
        ["Division", "Church", "Jurisdiction", "How They Operate"],
        ["Nighthawks",
         "Evernight Goddess",
         "Loen Kingdom, East Balam",
         "Work undercover. Jurisdiction divided by borough. Names kept confidential even after death. Red Gloves (Seq 7+) handle cross-borough manhunts without restriction."],
        ["Mandated Punishers",
         "Lord of Storms",
         "Seas, port cities, Rorsted Archipelago",
         "Maritime law enforcement. Patrol shipping lanes and port cities. Dealt directly with Beyonder-related piracy and sea-entity incidents."],
        ["Inquisitors",
         "Eternal Blazing Sun",
         "Intis Republic, Southern Continent",
         "Zealous and feared. Operate with broad authority in Intis territory. Pursue heresy, corruption, and dark supernatural activity with considerable force."],
        ["The Knowing Eye",
         "God of Knowledge",
         "Lenburg, Segar, Masin",
         "Emphasis on observation and psychology. Embedded in academic and investigative roles. Gather intelligence on supernatural phenomena more than direct enforcement."],
        ["Machinery Hivemind",
         "God of Steam",
         "Intis Republic, Loen (pre-1352)",
         "Act undercover as security companies. Possess significant Beyonder Weapons. Members fanatically devoted; partial body mechanization is common."],
        ["The Bloodgrave Order",
         "God of Combat",
         "Feysac Empire",
         "Martial and aggressive. Among the most physically capable church divisions. Drawn from noble houses Sauron and Einhorn; membership tied to bloodline. Almost entirely male. Rarely operate outside Feysac territory in normal circumstances."],
        ["Fertility Order",
         "Earth Mother",
         "Feynapotter, limited",
         "Small-scale, low-profile. In Loen they operate only informally and are not recognized by the government. Primarily composed of Beyonders aligned with the Mother pathway."],
    ]
    div_data[0] = [Paragraph(c, S['TableHeader']) for c in div_data[0]]
    for i in range(1, len(div_data)):
        div_data[i] = [Paragraph(c, S['TableCell']) for c in div_data[i]]
    story.append(Table(div_data, colWidths=[1.0*inch, 1.0*inch, 1.3*inch, 3.0*inch],
                       style=table_style()))
    story.append(sp(3))

    story += section("Church Inter-Relations at a Glance")
    story.append(body(
        "The following summarises active rivalries and alignments relevant to a Year 1349 campaign. "
        "These are not mere political tensions — in the Beyonder world, inter-church conflict can "
        "and does turn violent at the higher Sequences."
    ))
    story.append(sp(3))
    rel_data = [
        ["Church A", "Church B", "Relationship"],
        ["Evernight Goddess",    "God of Combat",         "Archrivals — deeply hostile, doctrinal and cosmological enmity"],
        ["Lord of Storms",       "Eternal Blazing Sun",   "Enemies — see each other as direct rivals"],
        ["Lord of Storms",       "God of Knowledge",      "Enemies — perpetual mutual hostility"],
        ["Eternal Blazing Sun",  "God of Knowledge",      "Enemies — three-way mutual enmity with Lord of Storms"],
        ["Evernight Goddess",    "Lord of Storms",        "Cooperative — share jurisdiction and influence in Loen Kingdom"],
        ["Evernight Goddess",    "God of Steam",          "Cooperative — worked together; Steam Church encouraged women in workforce"],
        ["Eternal Blazing Sun",  "God of Steam",          "Aligned — both dominant in Intis Republic"],
        ["Earth Mother",         "Evernight Goddess",     "Friendly — both support gender equality; Earth Mother later allied with Evernight"],
    ]
    rel_data[0] = [Paragraph(c, S['TableHeader']) for c in rel_data[0]]
    for i in range(1, len(rel_data)):
        rel_data[i] = [Paragraph(rel_data[i][j],
            S['TableCellCenter'] if j==2 else S['TableCell']) for j in range(3)]
    story.append(Table(rel_data, colWidths=[1.4*inch, 1.4*inch, 3.5*inch],
                       style=table_style()))
    story.append(sp(3))

    story += section("Major Secret Organizations")
    story.append(body(
        "Alongside the orthodox churches, countless secret organizations operate in the shadows. "
        "Most are composed entirely of Beyonders. Their goals range from ancient conspiracies "
        "to mercenary trade to scholarly obsession. Encountering one — or being recruited by one — "
        "is one of the most dangerous things that can happen to a low-Sequence Beyonder."
    ))
    story.append(sp(3))

    org_data = [
        ["Organization", "Type", "Alignment", "Known Focus"],
        ["Nighthawks",
         "Church Division (Evernight)",
         "Orthodox",
         "See Orthodox Divisions table above. The primary supernatural police of Loen Kingdom."],
        ["Machinery Hivemind",
         "Church Division (Steam)",
         "Orthodox",
         "See Orthodox Divisions table above. Operate in Intis and industrialised Loen territory."],
        ["Twilight Hermit Order",
         "Ancient (Second Epoch)",
         "Secretive / Neutral",
         "The oldest known secret organization, founded by Adam, eldest son of the Ancient Sun God. "
         "Aims to guide history from the shadows so the Original Creator may one day resurrect. "
         "Has members embedded at the highest levels of every church and government. "
         "Members may not speak the Order's name outside. Possesses the Second Blasphemy Slate."],
        ["Rose School of Thought",
         "Early Fifth Epoch",
         "Hostile",
         "Originally worshipped the Chained God; believes magic is a science of the will. "
         "Retains bloody ancient rituals including sacrifice. Main influence covers the Southern Continent. "
         "Their ideology holds that desire, combined with Beyonder power, can accomplish anything. "
         "Considered dangerous and heretical by the Orthodox Churches."],
        ["Psychology Alchemists",
         "Newly Founded",
         "Neutral / Academic",
         "Formed from a scholarly seminar that discovered ruins left by the ancient being Hermes. "
         "Holds formulas of the Visionary Pathway. Believes human consciousness is an island "
         "above a vast subconscious sea. Operates loosely — more seminar than army. "
         "Secretly under the influence of the Twilight Hermit Order."],
        ["Secret Order",
         "Fourth Epoch",
         "Unknown",
         "Founded by the Zaratul Family after the War of the Four Emperors. "
         "Extremely secretive — goals and philosophy are largely unknown. "
         "Their founder Zaratul failed an advancement beyond Sequence 1 and became a monster. "
         "Believed to be searching for relics of the Antigonus Family (Fool Pathway). "
         "Deep connections to the Intis Republic."],
        ["Aurora Order",
         "Early Fifth Epoch",
         "Hostile",
          "Worshippers of the True Creator — a dangerous ancient fallen god. "
         "Considered extremely dangerous and hunted actively by the Orthodox Churches. "
         "Members pursue radical ends using the power of the True Creator's pathway group."],
        ["Abraham Family",
         "Fourth Epoch",
         "Neutral / Allied",
         "One of the five great angel families of the Fourth Epoch Tudor Empire. "
         "Survived into the Fifth Epoch and maintains connections across multiple power structures. "
         "Has provided aid and information to various independent Beyonder parties."],
    ]
    org_data[0] = [Paragraph(c, S['TableHeader']) for c in org_data[0]]
    for i in range(1, len(org_data)):
        org_data[i] = [Paragraph(c, S['TableCell']) for c in org_data[i]]
    story.append(Table(org_data, colWidths=[1.3*inch, 1.1*inch, 0.9*inch, 3.0*inch],
                       style=table_style()))
    story.append(sp(3))

    story += section("A Note on Faction Play")
    story.append(body(
        "Most player characters at the start of a campaign have no affiliation. The choice of which "
        "organization to approach — or avoid — is one of the most consequential decisions they will make. "
        "The Orthodox Churches offer safety, resources, and salary, but also obligation, surveillance, "
        "and institutional control. Secret organizations offer freedom, rare knowledge, and powerful "
        "allies, but also danger, secrecy, and the weight of agendas they may not fully understand. "
        "Wild Beyonders have neither support — but owe nothing to anyone."
    ))
    story.append(sp(3))

    story.append(PageBreak())
    story += chapter("Glossary of Terms")
    story.append(body(
        "A quick-reference glossary of setting-specific and mechanical terms used in this book. "
        "Terms in <i>italics</i> are game mechanics; bold terms are setting concepts."
    ))
    story.append(sp(3))
    glossary_entries = [
        ("<b>Acting Method</b>", "The practice of embodying your Beyonder potion's 'role' to digest it safely. The more faithfully you act, the faster you digest (see Digestion)."),
        ("<b>Astral Projection / Astral Body</b>", "The layer of a soul that reveals emotional state. Visible through Spirit Vision."),
        ("<b>Backlund</b>", "The capital of the Loen Kingdom. A sprawling industrial city of fog, factories, slums, and aristocratic mansions. Most campaigns begin here."),
        ("<b>Beyonder</b>", "A person who has consumed a potion and gained supernatural abilities along a divine Pathway. Beyonders progress from Sequence 9 (weakest) to Sequence 0 (godlike)."),
        ("<i>Beyonder Weapon</i>", "A weapon imbued with spiritual power (either innately or through a Beyonder's ability) that can damage spirit bodies, incorporeal beings, and spiritually reinforced targets as though it were a Beyonder-level effect. Mundane weapons without this property deal half or no damage to such targets at the GM's discretion."),
        ("<b>Body of Heart and Mind</b>", "The layer of a soul governing emotion, reason, and self-awareness. Lies between the Astral Body and the Spirit Body. Targeted by Visionary pathway mental manipulation abilities such as Frenzy and Telepathy."),
        ("<i>Character Points</i>", "The currency used to build characters. You spend points on attributes, advantages, and skills. Disadvantages give points back. Starting budget: 70 points."),
         ("<i>CoR</i>", "A measure of how close a Beyonder is to losing control. Max CoR = Will score. At max, the character becomes an NPC monster."),
        ("<i>Critical Success / Failure</i>", "Rolling 3–4 is always a critical success (brilliant result). Rolling 17–18 is always a critical failure (disaster)."),
        ("<i>Digestion</i>", "The process of safely incorporating a potion's power. Tracked as 0% -> 100%. Must be at or near 100% before advancing to the next Sequence."),
        ("<i>Ether Body</i>", "The outermost layer of a soul, visible through Spirit Vision. Shows physical health — white = healthy, dark = ill."),
        ("<i>FP (Fatigue Points)</i>", "Energy for physical exertion, extra effort, and some supernatural abilities. Recovered by rest. Equal to HT at character creation."),
        ("<b>Game Master (GM)</b>", "The player who runs the game — describes the world, plays NPCs, calls for rolls, and keeps the story moving."),
        ("<i>HP (Hit Points)</i>", "Physical damage capacity. Equal to ST at character creation. At 0 HP you are near death; negative HP forces consciousness checks."),
        ("<b>Loen Kingdom</b>", "See Backlund. The dominant nation of the Fifth Epoch, equivalent to Victorian Britain."),
         ("<b>Losing Control</b>", "When a Beyonder's CoR reaches their maximum. They transform into a monster or mad creature — permanently removed from play."),
        ("<i>Margin of Success / Failure</i>", "The difference between your roll and your target number. A bigger margin means a better (or worse) outcome."),
        ("<b>Pathway</b>", "One of 22 divine progressions. Each pathway runs from Sequence 9 to Sequence 0 and grants specific abilities. Examples: Fool Pathway, Error Pathway, Darkness Pathway."),
        ("<b>Potion</b>", "An alchemical brew that grants Beyonder powers. Must be brewed from specific ingredients, then consumed. Brings side effects and corruption risk."),
        ("<b>Sequence</b>", "The numerical rank of a Beyonder's power level. Sequence 9 = newly awakened. Sequence 0 = god-equivalent. Lower numbers are stronger."),
        ("<i>SPI — Spirituality</i>", "A spiritual stat (not a buyable attribute). Measures connection to the spirit world. Fixed at 0 for mortals; increased only by Beyonder potions or supernatural means. Used for Spirit Vision, Ritualistic Magic (as a resource), and Beyonder abilities."),
        ("<i>Spirit Vision</i>", "A Beyonder ability that reveals auras, Ether Bodies, Astral Bodies, and supernatural entities. Costs 1 SPI per minute to maintain."),
        ("<b>Sea of Collective Subconscious</b>", "A shared psychic realm containing the unconscious minds of all sentient beings. Accessible via certain Visionary-pathway abilities (e.g., Psychological Cue). The GM determines effects when a character enters this realm."),
        ("<i>3d6</i>", "Three six-sided dice rolled together. The standard die roll for all success checks. Add the three numbers for your result (range 3–18)."),
         ("<i>Will</i>", "Mental fortitude and resistance to influence. = IQ at character creation. Used to resist intimidation, mind control, and CoR."),
    ]
    for term, defn in glossary_entries:
        story.append(Paragraph(f"{term}: {defn}", S['Bullet']))
    story.append(sp(3))
    story.append(body(
        "<i>This glossary covers only the terms unique to this book. For full GURPS terminology, "
        "refer to the GURPS Basic Set Characters (4th Edition).</i>"
    ))
    story.append(sp(3))

    doc.build(story, onFirstPage=cover_page, onLaterPages=normal_page)

    # ── Save captured page numbers for next build's TOC ─────────────────────
    _save_page_cache(_PageNum._marks)
    # Warn if this build had no cached numbers (fresh checkout / first run)
    if not _PAGE_CACHE:
        print("[TOC] Page numbers captured. Run the script ONCE MORE for a correct Table of Contents.")
    _PageNum._marks = {}

    # ── Generate back cover as a separate single-page PDF, then merge ─────────
    from reportlab.platypus import SimpleDocTemplate as SDT
    back_path = os.path.join(OUTPUT_DIR, "back_cover.pdf")
    back_doc = SDT(back_path, pagesize=letter,
                   rightMargin=0, leftMargin=0, topMargin=0, bottomMargin=0)

    def draw_back(canvas, doc):
        back_cover(canvas, doc)

    back_doc.build([Spacer(1, 1)], onFirstPage=draw_back, onLaterPages=draw_back)

    # Merge main PDF + back cover
    from pypdf import PdfReader, PdfWriter
    main_out = os.path.join(OUTPUT_DIR, "Mr.Worms LOM TTRPG Rulebook v6.9d.pdf")
    tmp_main = os.path.join(OUTPUT_DIR, "main_body.pdf")
    import shutil
    shutil.copy(main_out, tmp_main)

    writer = PdfWriter()
    for page in PdfReader(tmp_main).pages:
        writer.add_page(page)

    # Ensure total page count (including back cover) is even
    # back cover adds 1 page, so insert blank when main body is even
    total_so_far = len(writer.pages)
    if total_so_far % 2 == 0:
        from reportlab.pdfgen import canvas as rl_canvas
        blank_path = os.path.join(OUTPUT_DIR, "blank_page.pdf")
        c = rl_canvas.Canvas(blank_path, pagesize=letter)
        w_pt, h_pt = letter
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, w_pt, h_pt, fill=1, stroke=0)
        c.save()
        for page in PdfReader(blank_path).pages:
            writer.add_page(page)

    for page in PdfReader(back_path).pages:
        writer.add_page(page)
    with open(main_out, "wb") as f:
        writer.write(f)

    print("PDF built successfully.")


def back_cover(canvas, doc):
    w, h = letter
    canvas.saveState()

    # ── White background ──────────────────────────────────────────────────────
    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # ── Outer gold border ─────────────────────────────────────────────────────
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(3.5)
    canvas.rect(0.38*inch, 0.38*inch, w - 0.76*inch, h - 0.76*inch, fill=0, stroke=1)

    # ── Inner dark-gold border ────────────────────────────────────────────────
    canvas.setStrokeColor(DARK_GOLD)
    canvas.setLineWidth(0.8)
    canvas.rect(0.52*inch, 0.52*inch, w - 1.04*inch, h - 1.04*inch, fill=0, stroke=1)

    # ── Corner ticks ──────────────────────────────────────────────────────────
    tk = 0.22 * inch
    b = 0.52 * inch
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(2)
    for (px, py) in [(b, b), (w-b, b), (b, h-b), (w-b, h-b)]:
        sx = tk if px < w/2 else -tk
        sy = tk if py < h/2 else -tk
        canvas.line(px, py, px+sx, py)
        canvas.line(px, py, px, py+sy)

    cx = w / 2

    # ── Top ornament rules ────────────────────────────────────────────────────
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.5)
    canvas.line(cx - 2.2*inch, h - 1.2*inch, cx + 2.2*inch, h - 1.2*inch)
    canvas.setLineWidth(0.5)
    canvas.line(cx - 2.0*inch, h - 1.32*inch, cx + 2.0*inch, h - 1.32*inch)

    # ── Title echo ────────────────────────────────────────────────────────────
    draw_outlined_text(canvas, "GURPS: VEILED EPOCH", cx, h - 1.85*inch,
                       'Times-Bold', 26, fill_color=GOLD,
                       stroke_color=colors.black, stroke_width=0.6,
                       align='center', page_width=w)

    draw_outlined_text(canvas, "LORD OF THE MYSTERIES", cx, h - 2.38*inch,
                       'Times-Italic', 17, fill_color=DARK_GOLD,
                       stroke_color=colors.black, stroke_width=0.35,
                       align='center', page_width=w)

    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.2)
    canvas.line(cx - 2.2*inch, h - 2.72*inch, cx + 2.2*inch, h - 2.72*inch)
    canvas.setLineWidth(0.5)
    canvas.line(cx - 2.0*inch, h - 2.84*inch, cx + 2.0*inch, h - 2.84*inch)

    # ── Supplement description (fills gap) ────────────────────────────────────
    desc_lines = [
        "A complete Powered by GURPS 4th Edition rulebook for the",
        "Lord of the Mysteries universe. Includes full character creation",
        "rules, the Beyonder Sequence system, Sequence 9 pathway templates,",
        "        Victorian-era equipment, spirituality mechanics,",
        "and a Game Master's guide for running campaigns in the world of Loen.",
    ]
    canvas.setFont('Times-Italic', 10.5)
    canvas.setFillColor(colors.HexColor("#111111"))
    canvas._textRenderMode = 0
    desc_y = h - 3.18*inch
    for line in desc_lines:
        canvas.drawCentredString(cx, desc_y, line)
        desc_y -= 16

    # ── Contents summary (small, two columns) ─────────────────────────────────
    contents_y = desc_y - 0.18*inch
    col1 = ["Chapter 1: Introduction", "Chapter 2: Core Rules", "Chapter 3: Character Creation",
            "Chapter 4: Spirituality", "Chapter 5: Combat",
            "Chapter 6: The Beyonder System", "Chapter 6.5: Divination Arts",
            "Chapter 7: Ritualistic Magic", "Chapter 7.5: Summoning Spiritual Creatures",
            "Chapter 7.6: Spirit Vision Guide"]
    col2 = ["Chapter 8: Equipment & Starting Wealth", "Chapter 9: Sequence 9 Potion Effects",
            "Chapter 10: Sequence 8 Potion Effects", "Chapter 11: Sequence 7 Potion Effects",
            "Chapter 12: Sequence 6 Potion Effects", "Chapter 13: Boon Granting",
            "Chapter 14: Non-Standard Pathways", "Chapter 15: Non-Standard Seq 8",
            "Appendix A: Quick Reference Tables",
            "Appendix B: Political World", "Appendix C: Orthodox Churches & Secret Organizations", "Glossary of Terms"]
    canvas.setFont('Times-Roman', 8.5)
    canvas.setFillColor(colors.HexColor("#1A1A1A"))
    col1_x = cx - 0.15*inch
    col2_x = cx + 0.15*inch
    cy_iter = contents_y
    for a, b_text in zip(col1, col2):
        canvas.drawRightString(col1_x, cy_iter, a)
        canvas.drawString(col2_x, cy_iter, b_text)
        cy_iter -= 13

    # ── Thin separator before credits ─────────────────────────────────────────
    sep_y = cy_iter - 0.18*inch
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.2)
    canvas.line(cx - 2.2*inch, sep_y, cx + 2.2*inch, sep_y)
    canvas.setLineWidth(0.5)
    canvas.line(cx - 2.0*inch, sep_y - 0.12*inch, cx + 2.0*inch, sep_y - 0.12*inch)

    # ── Diamond ornament (now just above credits) ─────────────────────────────
    dia_size = 0.15 * inch
    dia_cy = sep_y - 0.42*inch
    canvas.setFillColor(GOLD)
    p = canvas.beginPath()
    p.moveTo(cx,            dia_cy + dia_size)
    p.lineTo(cx + dia_size, dia_cy)
    p.lineTo(cx,            dia_cy - dia_size)
    p.lineTo(cx - dia_size, dia_cy)
    p.close()
    canvas.drawPath(p, fill=1, stroke=0)
    canvas.setStrokeColor(DARK_GOLD)
    canvas.setLineWidth(0.6)
    canvas.line(cx - 1.8*inch, dia_cy, cx - 0.28*inch, dia_cy)
    canvas.line(cx + 0.28*inch, dia_cy, cx + 1.8*inch, dia_cy)

    # ── Credits block ─────────────────────────────────────────────────────────
    canvas.setFont('Times-Bold', 12)
    canvas.setFillColor(colors.HexColor("#111111"))
    canvas._textRenderMode = 0
    cred_head_y = dia_cy - 0.42*inch
    canvas.drawCentredString(cx, cred_head_y, "SUPPLEMENT CREDITS")

    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.8)
    canvas.line(cx - 1.2*inch, cred_head_y - 0.17*inch, cx + 1.2*inch, cred_head_y - 0.17*inch)

    credit_entries = [
        ("Supplement Designer & Author", "Earvin Salonoy"),
        ("Rulebook Scribes", "Mr.Worm's LOM TTRPG Discord Server"),
        ("Source Material", "Lord of the Mysteries — Cuttlefish That Loves Diving"),
        ("Edition", "Powered by GURPS — Version 6.9c"),
        ("Usage", "Personal, non-commercial use only"),
    ]

    label_x = cx - 0.12*inch
    value_x = cx + 0.12*inch
    entry_y = cred_head_y - 0.55*inch

    for label, value in credit_entries:
        canvas.setFont('Times-Italic', 9.5)
        canvas.setFillColor(colors.HexColor("#222222"))
        canvas.drawRightString(label_x, entry_y, label + ":")
        canvas.setFont('Times-Bold', 9.5)
        canvas.setFillColor(colors.HexColor("#111111"))
        canvas.drawString(value_x, entry_y, value)
        entry_y -= 19

    # Closing line
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1)
    canvas.line(cx - 2.2*inch, entry_y - 0.15*inch, cx + 2.2*inch, entry_y - 0.15*inch)

    canvas.setFont('Times-Italic', 10)
    canvas.setFillColor(colors.HexColor("#111111"))
    canvas._textRenderMode = 0
    canvas.drawCentredString(cx, entry_y - 0.45*inch,
                             "Created with passion for the world of Lord of the Mysteries.")

    # ── Bottom ornament ───────────────────────────────────────────────────────
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.5)
    canvas.line(cx - 2.2*inch, 1.2*inch, cx + 2.2*inch, 1.2*inch)
    canvas.setLineWidth(0.5)
    canvas.line(cx - 2.0*inch, 1.08*inch, cx + 2.0*inch, 1.08*inch)

    canvas.setFillColor(GOLD)
    p2 = canvas.beginPath()
    p2.moveTo(cx,              0.82*inch + dia_size)
    p2.lineTo(cx + dia_size,   0.82*inch)
    p2.lineTo(cx,              0.82*inch - dia_size)
    p2.lineTo(cx - dia_size,   0.82*inch)
    p2.close()
    canvas.drawPath(p2, fill=1, stroke=0)

    canvas.restoreState()

build()
