#!/usr/bin/env python3
"""Paperback volume typesetter — 5.5 × 8.5" pocket-prayer-book aesthetic.

Mass-market trim, restrained Gothic Orthodox vocabulary:
  - 5.5 × 8.5" trade paperback trim
  - Cardo 10pt body, single column
  - 3-line drop cap (restrained, pocket-book scale)
  - Small Fraktur chapter numeral + small-caps title
  - ☩ Cross-of-Jerusalem section breaks
  - Italic running heads
  - No illuminated borders or marginalia

Usage: typeset-paperback.py <volume-title> <chapter-md> <out.pdf>
"""

import os
import re
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.pdfbase.pdfmetrics import stringWidth

# Trim
PAGE_W = 5.5 * inch
PAGE_H = 8.5 * inch
INNER_M = 18 * mm
OUTER_M = 14 * mm
TOP_M = 16 * mm
BOTTOM_M = 14 * mm

INK = HexColor("#1a1a1a")
RUBRIC = HexColor("#0a0a0a")  # gothic black per user direction
SUBTLE = HexColor("#666666")

GFONTS = Path(os.environ.get("GOTHIC_FONTS_DIR", str(Path(__file__).parent.parent / "fonts")))
FONT_BODY = "Times-Roman"; FONT_BODY_ITALIC = "Times-Italic"; FONT_BODY_BOLD = "Times-Bold"
FONT_FRAKTUR = "Times-Bold"
try:
    pdfmetrics.registerFont(TTFont("Cardo", str(GFONTS / "Cardo-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Cardo-Italic", str(GFONTS / "Cardo-Italic.ttf")))
    pdfmetrics.registerFont(TTFont("Cardo-Bold", str(GFONTS / "Cardo-Bold.ttf")))
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily("Cardo", normal="Cardo", bold="Cardo-Bold",
                        italic="Cardo-Italic", boldItalic="Cardo-Bold")
    FONT_BODY = "Cardo"; FONT_BODY_ITALIC = "Cardo-Italic"; FONT_BODY_BOLD = "Cardo-Bold"
except Exception:
    pass
try:
    pdfmetrics.registerFont(TTFont("UnifrakturMaguntia",
                                    str(GFONTS / "UnifrakturMaguntia-Regular.ttf")))
    FONT_FRAKTUR = "UnifrakturMaguntia"
except Exception:
    pass

# Styles
BODY = ParagraphStyle("Body", fontName=FONT_BODY, fontSize=10, leading=13.5,
    textColor=INK, alignment=TA_JUSTIFY, firstLineIndent=12)
BODY_FIRST = ParagraphStyle("BodyFirst", parent=BODY, firstLineIndent=0)
SCRIPTURE = ParagraphStyle("Scripture", fontName=FONT_BODY_ITALIC, fontSize=10, leading=14,
    textColor=INK, alignment=TA_LEFT, leftIndent=14, rightIndent=14,
    spaceBefore=6, spaceAfter=6, firstLineIndent=0)
EPIGRAPH = ParagraphStyle("Epigraph", parent=SCRIPTURE, spaceBefore=8, spaceAfter=2)
EPIGRAPH_CITE = ParagraphStyle("EpigraphCite", fontName=FONT_BODY, fontSize=9, leading=12,
    textColor=SUBTLE, alignment=TA_LEFT, leftIndent=14, rightIndent=14,
    spaceBefore=2, spaceAfter=10, firstLineIndent=0)
CH_NUM = ParagraphStyle("ChNum", fontName=FONT_FRAKTUR, fontSize=18, leading=22,
    textColor=RUBRIC, alignment=TA_CENTER, spaceAfter=2)
CH_TITLE = ParagraphStyle("ChTitle", fontName=FONT_BODY, fontSize=11, leading=14,
    textColor=RUBRIC, alignment=TA_CENTER, spaceAfter=18)


class ChapterTitleParagraph(Paragraph):
    """Marker subclass — afterFlowable updates running header when this lands."""
    pass
SECTION = ParagraphStyle("Section", fontName=FONT_BODY, fontSize=11, leading=13,
    textColor=RUBRIC, alignment=TA_CENTER, spaceBefore=10, spaceAfter=10)
SUB_HEADER = ParagraphStyle("SubHeader", fontName=FONT_FRAKTUR, fontSize=15, leading=20,
    textColor=RUBRIC, alignment=TA_CENTER, spaceBefore=14, spaceAfter=8)


class ChapterRule(Flowable):
    """Horizontal rule with centered cross — chapter-opener divider matching lectern banner."""
    def __init__(self, width):
        super().__init__()
        self.width = width
        self._height = 16  # space above + below cross

    def wrap(self, avail_w, avail_h):
        return (self.width, self._height)

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        # Rule across most of width, with gap in center for cross
        rule_y = self._height * 0.5
        gap = 8
        rule_inset = self.width * 0.20
        canvas.setStrokeColor(HexColor("#9a9a9a"))
        canvas.setLineWidth(0.4)
        canvas.line(rule_inset, rule_y, self.width / 2 - gap, rule_y)
        canvas.line(self.width / 2 + gap, rule_y, self.width - rule_inset, rule_y)
        # Cross in middle (slightly above rule for visual balance)
        canvas.setFont(FONT_BODY, 11)
        canvas.setFillColor(RUBRIC)
        canvas.drawCentredString(self.width / 2, rule_y - 3, "☩")
        canvas.restoreState()


def smart_quotes(t):
    if any(c in t for c in "“”‘’"): return t
    # Apostrophes first so closing single quotes (U+2019) are in place when
    # the closing-double rule runs (handles nested dialogue: ...said.'")
    t = re.sub(r"(?<=[a-zA-Z])'(?=[a-zA-Z])", "’", t)  # contractions
    t = re.sub(r"(?<=[a-zA-Z0-9.,!?;:\)\]\*>])'", "’", t)  # closing single
    t = t.replace("'", "‘")  # remaining = opening single
    # Closing double: preceded by word-end characters. Includes * (italic
    # delimiter at end of italic span) and > (HTML tag close, when smart_quotes
    # runs after md_inline) so the rule fires whatever the surrounding markup
    t = re.sub(r'(?<=[a-zA-Z0-9.,!?;:\)\]’\*>])"', "”", t)
    t = t.replace('"', "“")
    return t


def md_inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^\*\n]+?)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"_(.+?)_", r"<i>\1</i>", t); return t


class DropCapWrapped(Flowable):
    """Drop cap with multi-paragraph wrap.

    First paragraph (and as much of subsequent paragraphs as fit) wraps
    next to the cap glyph. Once the cap height is filled, remaining text
    re-wraps at full column width below the cap.

    Eliminates the whitespace gap that occurs when paragraph 1 is shorter
    than the cap's vertical extent.
    """
    def __init__(self, letter, opening_html, follow_paragraphs, body_style,
                 cap_font, cap_size, cap_color, column_w, gap=6):
        super().__init__()
        self.letter = letter
        self.opening_html = opening_html
        self.follow_paragraphs = follow_paragraphs
        self.body_style = body_style
        self.cap_font = cap_font
        self.cap_size = cap_size
        self.cap_color = cap_color
        self.column_w = column_w
        self.gap = gap
        from reportlab.pdfbase import pdfmetrics
        self._cap_w = stringWidth(letter, cap_font, cap_size)
        face = pdfmetrics.getFont(cap_font).face
        self._cap_ascent = face.ascent * cap_size / 1000
        self._cap_descent = abs(face.descent) * cap_size / 1000

    def wrap(self, avail_w, avail_h):
        narrow_w = self.column_w - self._cap_w - self.gap
        # Paragraph break = line break + first-line indent on next paragraph
        # (no blank line — that creates a gap inside the cap-wrap area)
        para_break = '<br/>&nbsp;&nbsp;&nbsp;&nbsp;'
        combined_html = self.opening_html
        for p in self.follow_paragraphs:
            combined_html += para_break + p
        # Wrap the combined paragraph at narrow width
        narrow_para = Paragraph(combined_html, self.body_style)
        nw, nh = narrow_para.wrap(narrow_w, 100000)
        # Cap visible height — use ascent (cap-height region)
        cap_visible_h = self._cap_ascent
        if nh <= cap_visible_h:
            self._narrow = narrow_para
            self._narrow_h = nh
            self._full = None
            self._full_h = 0
        else:
            # Split combined paragraph at cap height
            parts = narrow_para.split(narrow_w, cap_visible_h)
            if len(parts) >= 2:
                self._narrow = parts[0]
                _, self._narrow_h = self._narrow.wrap(narrow_w, 100000)
                # parts[1] is a Paragraph holding the remaining content. Re-wrap at full width.
                self._full = parts[1]
                _, self._full_h = self._full.wrap(self.column_w, 100000)
            else:
                self._narrow = narrow_para
                self._narrow_h = nh
                self._full = None
                self._full_h = 0
        cap_block_h = max(self._narrow_h, self._cap_ascent + self._cap_descent)
        total_h = cap_block_h + self._full_h
        return (self.column_w, total_h)

    def draw(self):
        canvas = self.canv
        # Total flowable height
        cap_block_h = max(self._narrow_h, self._cap_ascent + self._cap_descent)
        total_h = cap_block_h + self._full_h
        # Cap glyph: top at flowable top
        body_offset = 3
        cap_baseline_y = total_h - self._cap_ascent - body_offset
        canvas.saveState()
        canvas.setFont(self.cap_font, self.cap_size)
        canvas.setFillColor(self.cap_color)
        canvas.drawString(0, cap_baseline_y, self.letter)
        canvas.restoreState()
        # Narrow paragraph: aligned to top of flowable (right of cap)
        narrow_x = self._cap_w + self.gap
        narrow_y = total_h - self._narrow_h
        self._narrow.drawOn(canvas, narrow_x, narrow_y)
        # Full-width remainder: below the cap block
        if self._full is not None:
            full_y = narrow_y - self._full_h
            # If the narrow_h is less than cap height, the full content starts below cap height
            if self._narrow_h < cap_block_h:
                full_y = (total_h - cap_block_h) - self._full_h
            self._full.drawOn(canvas, 0, full_y)


def opening_with_capword(rest_text, body_bold_size=9.5):
    """Convert 'here was nothing...' to '<font bold>HERE</font> was nothing...' opening."""
    if not rest_text:
        return ""
    m = re.match(r"^(\S+)(\s+.*)$", rest_text, re.DOTALL)
    if m:
        return (f'<font name="{FONT_BODY_BOLD}" size="{body_bold_size}">'
                f'{m.group(1).upper()}</font>{m.group(2)}')
    return rest_text


def make_drop_cap_block(letter, first_para_rest, follow_paras, column_w):
    """Returns a DropCapWrapped flowable.

    cap_size 52pt so the visible cap-height (~ascent ≈ 0.78 × 52 = 41pt)
    spans ~3 body lines (3 × 13.5 = 40.5pt) for proper drop-cap presence.
    """
    cap_size = 52
    opening = opening_with_capword(first_para_rest)
    return DropCapWrapped(
        letter=letter,
        opening_html=opening,
        follow_paragraphs=follow_paras,
        body_style=BODY_FIRST,
        cap_font=FONT_FRAKTUR,
        cap_size=cap_size,
        cap_color=RUBRIC,
        column_w=column_w,
    )


def _is_block_marker(ln):
    """True if a line is a markdown block boundary (not just inline ** prefix)."""
    if not ln:
        return True
    if ln.startswith("#") or ln == "---" or ln.startswith(">"):
        return True
    # Single * begins an italic scripture block; ** is bold prefix on a paragraph
    if ln.startswith("*") and not ln.startswith("**"):
        return True
    return False


def parse_paragraphs_after_title(lines, start_idx, max_count=2):
    """Collect up to max_count prose paragraphs from lines[start_idx]."""
    paragraphs = []
    i = start_idx
    while i < len(lines) and len(paragraphs) < max_count:
        ln = lines[i].rstrip()
        if not ln:
            i += 1
            continue
        if _is_block_marker(ln):
            break
        buf = [ln]
        i += 1
        while i < len(lines):
            nx = lines[i].rstrip()
            if _is_block_marker(nx):
                break
            buf.append(nx)
            i += 1
        paragraphs.append(" ".join(buf))
    return paragraphs, i


def chapter_to_flowables(p):
    text = Path(p).read_text(encoding="utf-8")
    lines = text.split("\n")
    fl = []
    in_open = False
    drop_used = False
    body_w = PAGE_W - INNER_M - OUTER_M
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("# "):
            t = ln[2:].strip()
            m = re.match(r"^Chapter\s+(\w+)\s*[:\-—]\s*(.+)$", t)
            if m:
                num, name = m.group(1), m.group(2)
                try:
                    n = int(num); rmap = ["", "I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX"]
                    if 1 <= n < len(rmap): num = rmap[n]
                except ValueError: pass
                fl.append(Paragraph(num, CH_NUM))
                fl.append(ChapterTitleParagraph(smart_quotes(name).upper(), CH_TITLE))
            else:
                fl.append(ChapterTitleParagraph(smart_quotes(t).upper(), CH_TITLE))
            fl.append(ChapterRule(PAGE_W - INNER_M - OUTER_M))
            fl.append(Spacer(1, 8))
            i += 1; in_open = True; continue
        if not ln:
            i += 1; continue
        if ln == "---":
            if not in_open:
                fl.append(Paragraph("☩", SECTION))
            i += 1; continue
        # H2 sub-section header (e.g. ## Zephaniah)
        if ln.startswith("## "):
            sub_title = ln[3:].strip()
            fl.append(Paragraph(smart_quotes(sub_title), SUB_HEADER))
            i += 1; in_open = False; continue
        if ln.startswith(">"):
            buf = []; cite = None
            while i < len(lines) and lines[i].rstrip().startswith(">"):
                c = lines[i].rstrip()[1:].lstrip()
                if not c:
                    if buf: buf.append("")
                    i += 1; continue
                if c.startswith("—") or c.startswith("--"): cite = c
                else: buf.append(c)
                i += 1
            block = " ".join(b for b in buf if b).strip()
            if block:
                if block.startswith("*") and block.endswith("*"): block = block[1:-1]
                fl.append(Paragraph(smart_quotes(md_inline(block)), EPIGRAPH))
            if cite: fl.append(Paragraph(smart_quotes(md_inline(cite)), EPIGRAPH_CITE))
            in_open = False; continue
        # Italic scripture block: line starts with * (not **), and is exactly
        # one italic span (opens with *, closes with *, no other * inside).
        # If the line has multiple italic spans, treat it as prose with inline
        # italics (handled by md_inline in the regular-paragraph branch).
        if ln.startswith("*") and not ln.startswith("**"):
            # Single-line italic with optional trailing citation, exactly 2 *
            m_single = re.match(r"^\*([^*]+)\*(\s*\([^\)]+\))?\s*$", ln)
            if m_single:
                scripture_text = m_single.group(1)
                citation = m_single.group(2) or ""
                full_text = scripture_text + citation
                fl.append(Paragraph(smart_quotes(full_text), SCRIPTURE))
                i += 1; in_open = False; continue
            # Multi-line italic block: only matches if line has odd asterisk
            # count (an unclosed italic at end). Otherwise fall through.
            if ln.count("*") % 2 == 1:
                buf = [ln[1:]]; i += 1
                while i < len(lines):
                    nx = lines[i].rstrip()
                    if not nx:
                        break
                    if nx.endswith("*"):
                        buf.append(nx[:-1]); i += 1; break
                    buf.append(nx); i += 1
                block = " ".join(buf).strip()
                fl.append(Paragraph(smart_quotes(block), SCRIPTURE))
                in_open = False; continue
            # Otherwise: fall through to regular paragraph (line has multiple
            # * spans, like *X* prose *Y* — md_inline will italicize each)

        if in_open and not drop_used:
            # Collect first prose paragraph + as many follow-on prose paragraphs as
            # exist before the next non-prose boundary. Pass them all to the
            # DropCapWrapped flowable so it can wrap continuously next to the cap.
            paragraphs, next_i = parse_paragraphs_after_title(lines, i)
            if paragraphs:
                first = paragraphs[0]
                # Skip drop cap when the chapter opens with a **bold prefix**;
                # the cap glyph would tangle with the bold markup. Render
                # paragraphs normally instead.
                if first.startswith("**"):
                    for p in paragraphs:
                        fl.append(Paragraph(smart_quotes(md_inline(p)), BODY_FIRST))
                    drop_used = True
                    in_open = False
                    i = next_i
                    continue
                first_html = smart_quotes(md_inline(first))
                plain = re.sub(r"<[^>]+>", "", first_html)
                cap_letter = plain[:1] if plain else "T"
                first_rest = first_html[len(cap_letter):].lstrip()
                follow = [smart_quotes(md_inline(p)) for p in paragraphs[1:]]
                fl.append(make_drop_cap_block(cap_letter, first_rest, follow, body_w))
                drop_used = True
                in_open = False
                i = next_i
                continue
            else:
                # No prose found; just step
                i += 1
                continue

        # Regular paragraph collection
        buf = [ln]; i += 1
        while i < len(lines):
            nx = lines[i].rstrip()
            if _is_block_marker(nx): break
            buf.append(nx); i += 1
        para = smart_quotes(md_inline(" ".join(buf)))
        fl.append(Paragraph(para, BODY_FIRST if in_open else BODY))
        in_open = False
    return fl


class PaperbackDoc(BaseDocTemplate):
    def __init__(self, filename, volume_title, **kw):
        super().__init__(filename, pagesize=(PAGE_W, PAGE_H),
            leftMargin=INNER_M, rightMargin=OUTER_M,
            topMargin=TOP_M, bottomMargin=BOTTOM_M, **kw)
        self.volume_title = volume_title
        self._chap = ""; self._show = False
        recto = Frame(INNER_M, BOTTOM_M, PAGE_W-INNER_M-OUTER_M, PAGE_H-TOP_M-BOTTOM_M,
            id="r", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        verso = Frame(OUTER_M, BOTTOM_M, PAGE_W-OUTER_M-INNER_M, PAGE_H-TOP_M-BOTTOM_M,
            id="v", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        front_recto = Frame(INNER_M, BOTTOM_M, PAGE_W-INNER_M-OUTER_M, PAGE_H-TOP_M-BOTTOM_M,
            id="fr", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        front_verso = Frame(OUTER_M, BOTTOM_M, PAGE_W-OUTER_M-INNER_M, PAGE_H-TOP_M-BOTTOM_M,
            id="fv", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="FrontRecto", frames=[front_recto]),
            PageTemplate(id="FrontVerso", frames=[front_verso]),
            PageTemplate(id="BodyRecto", frames=[recto], onPage=lambda c,d: self._draw(c,d,True)),
            PageTemplate(id="BodyVerso", frames=[verso], onPage=lambda c,d: self._draw(c,d,False)),
        ])

    def afterFlowable(self, fl):
        if isinstance(fl, ChapterTitleParagraph):
            t = fl.getPlainText()
            if "VOLUME" in t:
                # "Before Volume X" preface — keep volume title in header
                return
            self._chap = t
            self._show = True

    def _draw(self, canvas, doc, recto):
        canvas.saveState()
        # Header text — only after first chapter title encountered
        if self._show:
            canvas.setFont(FONT_BODY_ITALIC, 7.5); canvas.setFillColor(SUBTLE)
            if recto:
                canvas.drawRightString(PAGE_W - OUTER_M, PAGE_H - TOP_M + 7*mm, self._chap)
            else:
                canvas.drawString(OUTER_M, PAGE_H - TOP_M + 7*mm, self.volume_title)
        # Page number — cross-flanked, matching lectern brand
        canvas.setFont(FONT_BODY_ITALIC, 9); canvas.setFillColor(SUBTLE)
        page_no = doc.page - 4  # 4 front-matter pages
        if page_no > 0:
            canvas.drawCentredString(PAGE_W/2, BOTTOM_M/2, f"☩  {page_no}  ☩")
        canvas.restoreState()


def main():
    if len(sys.argv) != 4:
        print("Usage: typeset-paperback.py <volume-title> <chapter-md> <out.pdf>"); sys.exit(1)
    vt, cp, out = sys.argv[1:]
    doc = PaperbackDoc(out, volume_title=vt)
    story = [NextPageTemplate(["BodyRecto", "BodyVerso"])]
    story.extend(chapter_to_flowables(cp))
    doc.build(story)
    print(f"Built {out}")


if __name__ == "__main__":
    main()
