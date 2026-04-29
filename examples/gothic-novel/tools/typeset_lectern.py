#!/usr/bin/env python3
"""Lectern Bible typesetter — 9 × 12" two-column hardcover.

Family-Bible / pulpit-Bible aesthetic, full Gothic Orthodox treatment:
  - 9 × 12" trim
  - Two-column body throughout (8mm column gap)
  - Cardo 10.5pt body / 14 leading (~52 chars/line per column)
  - 6-line illuminated drop cap (Fraktur)
  - Large Fraktur chapter numeral with Cardo small-caps title
  - Cross-of-Jerusalem section breaks
  - Decorative-rule running heads with cross flanks on page numbers
  - Asymmetric margins (inner 30mm, outer 22mm)

Usage: typeset-lectern.py <volume-title> <chapter-md> <out.pdf>
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
    Paragraph, Spacer, Table, TableStyle, KeepTogether,
)
from reportlab.pdfbase.pdfmetrics import stringWidth

# Trim
PAGE_W = 9 * inch
PAGE_H = 12 * inch
INNER_M = 30 * mm
OUTER_M = 22 * mm
TOP_M = 28 * mm
BOTTOM_M = 24 * mm
COL_GAP = 8 * mm
COL_W = (PAGE_W - INNER_M - OUTER_M - COL_GAP) / 2

INK = HexColor("#1a1a1a")
RUBRIC = HexColor("#0a0a0a")  # gothic black per user direction
SUBTLE = HexColor("#666666")
RULE = HexColor("#9a9a9a")

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

# Body styles for two-column flow
BODY = ParagraphStyle("Body", fontName=FONT_BODY, fontSize=10.5, leading=14,
    textColor=INK, alignment=TA_JUSTIFY, firstLineIndent=12)
BODY_FIRST = ParagraphStyle("BodyFirst", parent=BODY, firstLineIndent=0)
SCRIPTURE = ParagraphStyle("Scripture", fontName=FONT_BODY_ITALIC, fontSize=10, leading=14,
    textColor=INK, alignment=TA_LEFT, leftIndent=8, rightIndent=8,
    spaceBefore=6, spaceAfter=6, firstLineIndent=0)
EPIGRAPH = ParagraphStyle("Epigraph", parent=SCRIPTURE, spaceBefore=8, spaceAfter=2)
EPIGRAPH_CITE = ParagraphStyle("EpigraphCite", fontName=FONT_BODY, fontSize=9, leading=12,
    textColor=SUBTLE, alignment=TA_LEFT, leftIndent=8, rightIndent=8,
    spaceBefore=2, spaceAfter=10, firstLineIndent=0)

# Chapter-opener: lives at top of column 1, sized to fit column width
CH_NUM = ParagraphStyle("ChNum", fontName=FONT_FRAKTUR, fontSize=42, leading=48,
    textColor=RUBRIC, alignment=TA_CENTER, spaceBefore=0, spaceAfter=4)
CH_TITLE = ParagraphStyle("ChTitle", fontName=FONT_BODY, fontSize=14, leading=18,
    textColor=RUBRIC, alignment=TA_CENTER, spaceAfter=14)
SECTION = ParagraphStyle("Section", fontName=FONT_BODY, fontSize=14, leading=16,
    textColor=RUBRIC, alignment=TA_CENTER, spaceBefore=12, spaceAfter=12)
SUB_HEADER = ParagraphStyle("SubHeader", fontName=FONT_FRAKTUR, fontSize=20, leading=26,
    textColor=RUBRIC, alignment=TA_CENTER, spaceBefore=18, spaceAfter=10)


class ChapterTitleParagraph(Paragraph):
    """Marker subclass for chapter titles."""
    pass


def _is_block_marker(ln):
    if not ln:
        return True
    if ln.startswith("#") or ln == "---" or ln.startswith(">"):
        return True
    if ln.startswith("*") and not ln.startswith("**"):
        return True
    return False


def smart_quotes(t):
    if any(c in t for c in "“”‘’"): return t
    # Apostrophes first; trigger class includes * (italic delimiter) and >
    # (HTML close) so closures around emphasis spans are handled correctly.
    t = re.sub(r"(?<=[a-zA-Z])'(?=[a-zA-Z])", "’", t)
    t = re.sub(r"(?<=[a-zA-Z0-9.,!?;:\)\]\*>])'", "’", t)
    t = t.replace("'", "‘")
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
    """Drop cap + narrow-wrapped paragraphs that fit next to it.

    The remaining text (paragraph 2 continuation) is exposed via the
    `overflow` attribute so the chapter parser can append it as a
    separate Paragraph flowable that ReportLab will lay out below.
    """
    def __init__(self, letter, opening_html, follow_paragraphs, body_style,
                 cap_font, cap_size, cap_color, column_w, gap=8):
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
        self.overflow = None  # populated in wrap() — caller renders it below

    def wrap(self, avail_w, avail_h):
        narrow_w = self.column_w - self._cap_w - self.gap
        para_break = '<br/>&nbsp;&nbsp;&nbsp;&nbsp;'
        combined_html = self.opening_html
        for p in self.follow_paragraphs:
            combined_html += para_break + p
        narrow_para = Paragraph(combined_html, self.body_style)
        nw, nh = narrow_para.wrap(narrow_w, 100000)
        cap_visible_h = self._cap_ascent
        if nh <= cap_visible_h:
            self._narrow = narrow_para
            self._narrow_h = nh
            self.overflow = None
        else:
            parts = narrow_para.split(narrow_w, cap_visible_h)
            if len(parts) >= 2:
                self._narrow = parts[0]
                _, self._narrow_h = self._narrow.wrap(narrow_w, 100000)
                # Expose the overflow paragraph for the caller to append.
                self.overflow = parts[1]
            else:
                self._narrow = narrow_para
                self._narrow_h = nh
                self.overflow = None
        # Reserve full cap glyph extent + small buffer so Fraktur descenders
        # don't sit on top of the next flowable below.
        self._height = max(self._narrow_h, self._cap_ascent + self._cap_descent + 4)
        return (self.column_w, self._height)

    def draw(self):
        canvas = self.canv
        body_offset = 3
        cap_baseline_y = self._height - self._cap_ascent - body_offset
        canvas.saveState()
        canvas.setFont(self.cap_font, self.cap_size)
        canvas.setFillColor(self.cap_color)
        canvas.drawString(0, cap_baseline_y, self.letter)
        canvas.restoreState()
        narrow_x = self._cap_w + self.gap
        narrow_y = self._height - self._narrow_h
        self._narrow.drawOn(canvas, narrow_x, narrow_y)


def opening_with_capword(rest_text, body_bold_size=10):
    if not rest_text:
        return ""
    m = re.match(r"^(\S+)(\s+.*)$", rest_text, re.DOTALL)
    if m:
        return (f'<font name="{FONT_BODY_BOLD}" size="{body_bold_size}">'
                f'{m.group(1).upper()}</font>{m.group(2)}')
    return rest_text


def make_drop_cap_block(letter, first_para_rest, follow_paras, column_w):
    cap_size = 60
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


def parse_paragraphs_after_title(lines, start_idx, max_count=2):
    """Take up to max_count prose paragraphs from lines[start_idx]."""
    paragraphs = []
    i = start_idx
    while i < len(lines) and len(paragraphs) < max_count:
        ln = lines[i].rstrip()
        if not ln:
            i += 1; continue
        if _is_block_marker(ln):
            break
        buf = [ln]; i += 1
        while i < len(lines):
            nx = lines[i].rstrip()
            if _is_block_marker(nx): break
            buf.append(nx); i += 1
        paragraphs.append(" ".join(buf))
    return paragraphs, i


def chapter_to_flowables(p):
    """Return (banner_flowables, body_flowables) so the lectern can render
    the banner full-width across both columns at top, then two-column body."""
    text = Path(p).read_text(encoding="utf-8")
    lines = text.split("\n")
    banner = []
    body = []
    in_open = False
    drop_used = False
    chapter_started = False
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
                banner.append(Paragraph(num, CH_NUM))
                banner.append(ChapterTitleParagraph(smart_quotes(name).upper(), CH_TITLE))
            else:
                banner.append(ChapterTitleParagraph(smart_quotes(t).upper(), CH_TITLE))
            chapter_started = True
            i += 1; in_open = True; continue
        if not ln:
            i += 1; continue
        if ln == "---":
            if chapter_started and not in_open:
                body.append(Paragraph("☩", SECTION))
            i += 1; continue
        # H2 sub-section header (e.g. ## Zephaniah)
        if ln.startswith("## "):
            sub_title = ln[3:].strip()
            body.append(Paragraph(smart_quotes(sub_title), SUB_HEADER))
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
                body.append(Paragraph(smart_quotes(md_inline(block)), EPIGRAPH))
            if cite: body.append(Paragraph(smart_quotes(md_inline(cite)), EPIGRAPH_CITE))
            in_open = False; continue
        # Italic scripture block: only when line is exactly one italic span.
        # Multiple inline italics fall through to regular paragraph handling.
        if ln.startswith("*") and not ln.startswith("**"):
            m_single = re.match(r"^\*([^*]+)\*(\s*\([^\)]+\))?\s*$", ln)
            if m_single:
                scripture_text = m_single.group(1)
                citation = m_single.group(2) or ""
                full_text = scripture_text + citation
                body.append(Paragraph(smart_quotes(full_text), SCRIPTURE))
                i += 1; in_open = False; continue
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
                body.append(Paragraph(smart_quotes(block), SCRIPTURE))
                in_open = False; continue
            # else: fall through to regular paragraph (md_inline handles inlines)
        if in_open and not drop_used:
            paragraphs, next_i = parse_paragraphs_after_title(lines, i)
            if paragraphs:
                first = paragraphs[0]
                # Skip drop cap when chapter opens with **bold prefix** —
                # the cap would tangle with bold markup. Render normally.
                if first.startswith("**"):
                    for p in paragraphs:
                        body.append(Paragraph(smart_quotes(md_inline(p)), BODY_FIRST))
                    drop_used = True
                    in_open = False
                    i = next_i
                    continue
                first_html = smart_quotes(md_inline(first))
                plain = re.sub(r"<[^>]+>", "", first_html)
                cap_letter = plain[:1] if plain else "T"
                first_rest = first_html[len(cap_letter):].lstrip()
                follow = [smart_quotes(md_inline(p)) for p in paragraphs[1:]]
                cap_flow = make_drop_cap_block(cap_letter, first_rest, follow, COL_W)
                cap_flow.wrap(COL_W, 100000)
                body.append(cap_flow)
                if cap_flow.overflow is not None:
                    body.append(cap_flow.overflow)
                drop_used = True
                in_open = False
                i = next_i
                continue
            else:
                i += 1; continue
        buf = [ln]; i += 1
        while i < len(lines):
            nx = lines[i].rstrip()
            if _is_block_marker(nx): break
            buf.append(nx); i += 1
        para = smart_quotes(md_inline(" ".join(buf)))
        body.append(Paragraph(para, BODY_FIRST if in_open else BODY))
        in_open = False
    return banner, body


class LecternDoc(BaseDocTemplate):
    """Lectern document with chapter-banner template + two-column body templates."""

    BANNER_H = 55 * mm  # banner depth on chapter-opening pages

    def __init__(self, filename, volume_title, **kw):
        super().__init__(filename, pagesize=(PAGE_W, PAGE_H),
            leftMargin=INNER_M, rightMargin=OUTER_M,
            topMargin=TOP_M, bottomMargin=BOTTOM_M, **kw)
        self.volume_title = volume_title
        self._chap = ""; self._show = False

        col_h_full = PAGE_H - TOP_M - BOTTOM_M
        col_h_open = col_h_full - self.BANNER_H

        # Body-only two-column frames (regular pages)
        col1_recto = Frame(INNER_M, BOTTOM_M, COL_W, col_h_full,
            id="r1", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        col2_recto = Frame(INNER_M+COL_W+COL_GAP, BOTTOM_M, COL_W, col_h_full,
            id="r2", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        col1_verso = Frame(OUTER_M, BOTTOM_M, COL_W, col_h_full,
            id="v1", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        col2_verso = Frame(OUTER_M+COL_W+COL_GAP, BOTTOM_M, COL_W, col_h_full,
            id="v2", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

        # Chapter-opener: full-width banner frame at top + two columns below
        banner_y = PAGE_H - TOP_M - self.BANNER_H
        banner_w = PAGE_W - INNER_M - OUTER_M
        banner_recto = Frame(INNER_M, banner_y, banner_w, self.BANNER_H,
            id="br", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        col1_open_recto = Frame(INNER_M, BOTTOM_M, COL_W, col_h_open,
            id="oR1", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        col2_open_recto = Frame(INNER_M+COL_W+COL_GAP, BOTTOM_M, COL_W, col_h_open,
            id="oR2", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

        banner_verso = Frame(OUTER_M, banner_y, banner_w, self.BANNER_H,
            id="bv", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        col1_open_verso = Frame(OUTER_M, BOTTOM_M, COL_W, col_h_open,
            id="oV1", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        col2_open_verso = Frame(OUTER_M+COL_W+COL_GAP, BOTTOM_M, COL_W, col_h_open,
            id="oV2", showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

        # Full-width front-matter frames (no decoration)
        front_recto_frame = Frame(INNER_M, BOTTOM_M,
            PAGE_W - INNER_M - OUTER_M, col_h_full,
            id="frR", showBoundary=0,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        front_verso_frame = Frame(OUTER_M, BOTTOM_M,
            PAGE_W - OUTER_M - INNER_M, col_h_full,
            id="frV", showBoundary=0,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

        self.addPageTemplates([
            PageTemplate(id="FrontRecto", frames=[front_recto_frame]),
            PageTemplate(id="FrontVerso", frames=[front_verso_frame]),
            PageTemplate(id="ChapterOpenRecto",
                          frames=[banner_recto, col1_open_recto, col2_open_recto],
                          onPage=lambda c, d: self._draw_opener(c, d, recto=True)),
            PageTemplate(id="ChapterOpenVerso",
                          frames=[banner_verso, col1_open_verso, col2_open_verso],
                          onPage=lambda c, d: self._draw_opener(c, d, recto=False)),
            PageTemplate(id="BodyRecto", frames=[col1_recto, col2_recto],
                          onPage=lambda c, d: self._draw(c, d, recto=True)),
            PageTemplate(id="BodyVerso", frames=[col1_verso, col2_verso],
                          onPage=lambda c, d: self._draw(c, d, recto=False)),
        ])

    def _draw_opener(self, canvas, doc, recto):
        """Chapter-opener page: decorative banner box + footer page number, no running header."""
        canvas.saveState()
        # Top decorative rule across full width with cross at center
        rule_left = INNER_M if recto else OUTER_M
        rule_right = PAGE_W - (OUTER_M if recto else INNER_M)
        rule_y = PAGE_H - TOP_M + 4 * mm
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(rule_left, rule_y, rule_right, rule_y)
        # Banner bottom rule (separates banner from body columns)
        banner_bottom_y = PAGE_H - TOP_M - self.BANNER_H + 6 * mm
        canvas.line(rule_left + 25*mm, banner_bottom_y, rule_right - 25*mm, banner_bottom_y)
        canvas.setFont(FONT_BODY, 12)
        canvas.setFillColor(RUBRIC)
        canvas.drawCentredString(PAGE_W / 2, banner_bottom_y - 4*mm, "☩")
        # Footer page number
        canvas.setFont(FONT_BODY_ITALIC, 10)
        canvas.setFillColor(SUBTLE)
        canvas.drawCentredString(PAGE_W / 2, BOTTOM_M / 2 + 2*mm, f"☩  {doc.page}  ☩")
        canvas.restoreState()

    def afterFlowable(self, fl):
        if isinstance(fl, ChapterTitleParagraph):
            t = fl.getPlainText()
            if "VOLUME" in t:
                return
            self._chap = t; self._show = True

    def _draw(self, canvas, doc, recto):
        if not self._show: return
        canvas.saveState()
        # Decorative rule under header
        head_y = PAGE_H - TOP_M + 4 * mm
        rule_left = INNER_M if recto else OUTER_M
        rule_right = PAGE_W - (OUTER_M if recto else INNER_M)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(rule_left, head_y - 2*mm, rule_right, head_y - 2*mm)
        # Header text
        canvas.setFont(FONT_BODY_ITALIC, 9.5)
        canvas.setFillColor(SUBTLE)
        if recto:
            canvas.drawRightString(PAGE_W - OUTER_M, head_y, self._chap)
        else:
            canvas.drawString(OUTER_M, head_y, self.volume_title)
        # Footer — page number flanked by crosses
        canvas.setFont(FONT_BODY_ITALIC, 10)
        canvas.setFillColor(SUBTLE)
        canvas.drawCentredString(PAGE_W / 2, BOTTOM_M / 2 + 2*mm, f"☩  {doc.page}  ☩")
        canvas.restoreState()


def build_lectern_pdf(volume_title, chapter_path, out_path):
    doc = LecternDoc(out_path, volume_title=volume_title)
    banner, body = chapter_to_flowables(Path(chapter_path))
    story = [NextPageTemplate("ChapterOpenRecto")]
    # Small top spacer so heading isn't pinned to the very top of the banner
    story.append(Spacer(1, 6 * mm))
    story.extend(banner)
    # Switch to body templates after the banner page
    story.append(NextPageTemplate(["BodyRecto", "BodyVerso"]))
    story.extend(body)
    doc.build(story)


def main():
    if len(sys.argv) != 4:
        print("Usage: typeset-lectern.py <volume-title> <chapter-md> <out.pdf>"); sys.exit(1)
    vt, cp, out = sys.argv[1:]
    build_lectern_pdf(vt, cp, out)
    print(f"Built {out}")


if __name__ == "__main__":
    main()
