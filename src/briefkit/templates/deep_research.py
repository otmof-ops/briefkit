"""
briefkit.templates.deep_research
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Deep research report template — pixel-perfect match of AI Simulations
With Progressive Learning visual design.

Exact specifications reverse-engineered from PDF content streams.

Cover page (canvas-drawn):
  - Full-page dark fill #0F1318
  - Three decorative arc strokes: #00D4AA, varying radii + opacity
    - Arc 1: center (510.24, 742.68), r≈170pt, stroke only
    - Arc 2: center (538.58, 771.02), r≈255pt, 10% opacity
    - Arc 3: center (566.93, 799.37), r≈340pt, 15% opacity
  - Title: Helvetica-Bold 28pt white at x=68.36, y=555.29
  - Subtitle: Helvetica 13pt #93A3B8 at x=68.36, y=502.28
  - Accent rule: #00D4AA rounded rect 155.9x2.5pt at y=445.93
  - Metadata: Helvetica 9pt #64748A at y=410.25
  - Topics: Helvetica 9pt #93A3B8 at y=375.74
  - Dot row: 8 dots r=1.5pt #00D4AA at y=170.08, spacing ~51pt
  - Bottom strip: #00D4AA 1.5pt at y=79.37

Body pages:
  - Header: #00D4AA 1.5pt rule at y=802.20
    - Left: Helvetica 7.5pt #6B7280 — title uppercase
    - Right: Helvetica 7.5pt #6B7280 — "RESEARCH REPORT {year}"
  - Footer: 0.5pt #D1D4DB rule at y=45.35
    - Center: Helvetica 8pt #6B7280 — "— {n} —"
  - Contents: Helvetica-Bold 22pt #1A1A2D, teal rule below
  - TOC entries: number Helvetica-Bold 10.5pt #00D4AA, title 10.5pt #2C2C2C
  - TOC subtitles: Helvetica-Oblique 9.5pt #6B7280
  - Section headers: "01" Helvetica-Bold 22pt #00D4AA + title 20pt #1A1A2D
  - H2: Helvetica-Bold 14pt #16213D
  - Body: Helvetica 10pt #2C2C2C, 15.5pt leading, justified
  - Table headers: bg #00D4AA, white text
  - Callout: left border #00D4AA, bg #EFFDF9
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
)
from briefkit.styles import (
    _get_brand,
    _ps,
    _safe_text,
    compute_content_width,
)
from briefkit.templates._helpers import should_skip

# ---------------------------------------------------------------------------
# Exact colors from PDF content stream
# ---------------------------------------------------------------------------

_COVER_BG = "#0F1318"
_TEAL = "#00D4AA"
_SUBTITLE_GRAY = "#93A3B8"
_META_GRAY = "#64748A"
_HEADER_CAPTION = "#6B7280"
_FOOTER_RULE = "#D1D4DB"
_TOC_TITLE = "#1A1A2D"
_BODY_TEXT = "#2C2C2C"
_H2_COLOR = "#16213D"
_CALLOUT_BG = "#EFFDF9"

# ---------------------------------------------------------------------------
# Module-level state for custom header / footer
# ---------------------------------------------------------------------------

_dr_state: dict = {
    "title": "",
    "year": "2026",
    "report_type": "RESEARCH REPORT",
    "brand": {},
}


def _dr_header_footer(canvas, doc):
    """Deep research header/footer — exact match of PDF body pages."""
    canvas.saveState()
    _get_brand(_dr_state.get("brand"))
    w, h = doc.pagesize

    # Header rule: teal 1.5pt at y=802.20
    canvas.setStrokeColor(HexColor(_TEAL))
    canvas.setLineWidth(1.5)
    canvas.line(62.362, 802.205, 532.913, 802.205)

    # Header text at y=807.87
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(HexColor(_HEADER_CAPTION))
    title = _dr_state.get("title", "")
    if title:
        canvas.drawString(62.362, 807.874, title.upper()[:50])

    report_label = _dr_state.get("report_type", "RESEARCH REPORT")
    year = _dr_state.get("year", "2026")
    canvas.drawRightString(532.913, 807.874, f"{report_label} {year}")

    # Footer rule: 0.5pt #D1D4DB at y=45.35
    canvas.setStrokeColor(HexColor(_FOOTER_RULE))
    canvas.setLineWidth(0.5)
    canvas.line(62.362, 45.354, 532.913, 45.354)

    # Footer page number: centered "— n —"
    page_num = canvas.getPageNumber()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor(_HEADER_CAPTION))
    canvas.drawCentredString(285.190, 28.346, f"\u2014 {page_num} \u2014")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class DeepResearchTemplate(BaseBriefingTemplate):
    """
    Deep research report template — pixel-perfect AI Simulations style.

    Minimalist dark cover with decorative arc strokes, teal accents,
    clean white body pages with centered em-dash page numbers.

    Suitable for: research reports, literature reviews, survey papers,
    technical deep-dives, white-paper-style analysis.
    """

    def build_story(self, content: dict) -> list:
        """Assemble the research report story."""
        story: list = []
        subsystems = content.get("subsystems", [])

        cfg = self.config

        # Cover placeholder — canvas draws the actual cover
        story.append(Spacer(1, 200 * mm))
        story.append(PageBreak())

        _toc_start = len(story)

        # Contents page
        # "Contents" heading: Helvetica-Bold 22pt #1A1A2D
        contents_style = _ps(
            "DRContents", brand=self.brand,
            fontSize=22, fontName="Helvetica-Bold",
            textColor=HexColor(_TOC_TITLE), leading=26,
        )
        story.append(Paragraph("Contents", contents_style))
        story.append(Spacer(1, 2 * mm))

        # Teal rule under "Contents"
        rule_data = [[""]]
        rule = Table(rule_data, colWidths=[470.551], rowHeights=[1.2])
        rule.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor(_TEAL)),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(rule)
        story.append(Spacer(1, 4 * mm))

        # TOC entries: number 10.5pt teal bold, title 10.5pt #2C2C2C
        for i, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {i}")

            # Number + title: Helvetica-Bold 10.5pt
            entry_style = _ps(
                f"DRTocEntry_{i}", brand=self.brand,
                fontSize=10.5, fontName="Helvetica",
                textColor=HexColor(_BODY_TEXT), leading=20,
                leftIndent=22.677,
            )
            story.append(Paragraph(
                f'<font name="Helvetica-Bold" color="{_TEAL}">{i}</font>'
                f'&nbsp;&nbsp;&nbsp;{_safe_text(name)}',
                entry_style,
            ))

            # Extract sub-headings as italic subtitle
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            sub_items = []
            for block in blocks:
                if block.get("type") == "heading" and block.get("level") in (2, 3):
                    sub_items.append(block["text"])
            if sub_items:
                summary = " \u00b7 ".join(sub_items[:5])
                sub_style = _ps(
                    f"DRTocSub_{i}", brand=self.brand,
                    fontSize=9.5, fontName="Helvetica-Oblique",
                    textColor=HexColor(_HEADER_CAPTION), leading=20,
                    leftIndent=45.354,
                )
                story.append(Paragraph(summary[:100], sub_style))

        story.append(PageBreak())

        if should_skip(cfg, "toc"):
            del story[_toc_start:]

        # Body sections
        for idx, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {idx}")

            # Teal rule before section
            rule_data2 = [[""]]
            rule2 = Table(rule_data2, colWidths=[470.551], rowHeights=[1])
            rule2.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), HexColor(_TEAL)),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(rule2)
            story.append(Spacer(1, 6 * mm))

            # Section header: "01" teal 22pt + title 20pt dark
            sec_style = _ps(
                f"DRSecH_{idx}", brand=self.brand,
                fontSize=20, fontName="Helvetica-Bold",
                textColor=HexColor(_TOC_TITLE), leading=26,
            )
            story.append(Paragraph(
                f'<font name="Helvetica-Bold" size="22" color="{_TEAL}">'
                f'{idx:02d}</font>'
                f'&nbsp;&nbsp;&nbsp;{_safe_text(name)}',
                sec_style,
            ))
            story.append(Spacer(1, 3 * mm))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                if block["type"] == "heading" and block["level"] <= 1:
                    continue
                for fl in self.render_blocks([block]):
                    story.append(fl)
                    rendered += 1
                    if rendered >= 100:
                        break
                if rendered >= 100:
                    break

            story.append(Spacer(1, 4 * mm))

        return story

    # ------------------------------------------------------------------
    # generate() — custom cover and header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the deep research PDF with minimalist dark cover."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.extract_content()
        title = content.get(
            "title",
            self.target_path.name.replace("-", " ").title(),
        )
        subsystems = content.get("subsystems", [])
        overview = content.get("overview", "")

        # Doc ID
        doc_ids_cfg = self.config.get("doc_ids", {})
        if doc_ids_cfg.get("enabled", True):
            from briefkit.doc_ids import get_or_assign_doc_id

            self.doc_id = get_or_assign_doc_id(
                self.target_path, self.level,
                title, config=self.config,
            )

        # Template-specific config
        dr_cfg = self.config.get("deep_research", {})
        report_type = dr_cfg.get("report_type", "Deep Research Report")
        topics = dr_cfg.get("topics", [])
        subtitle = dr_cfg.get("subtitle", "")

        # Auto-derive subtitle from first overview sentence if not set
        if not subtitle and overview:
            first_line = overview.strip().split("\n")[0]
            for sep in (".", "!", "?"):
                idx = first_line.find(sep)
                if 0 < idx < 200:
                    first_line = first_line[:idx + 1]
                    break
            subtitle = re.sub(r'^#+\s*', '', first_line)[:200]

        # Auto-derive topics from subsystem names
        if not topics and subsystems:
            topics = [sub.get("name", "") for sub in subsystems[:6]]

        year = str(self.date.year)

        # Header/footer state
        _dr_state["title"] = dr_cfg.get("header_title", title)
        _dr_state["year"] = year
        _dr_state["report_type"] = report_type.upper()
        _dr_state["brand"] = self.brand


        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        page_size = A4
        self.content_width = compute_content_width(page_size, margins)

        cfg_author = dr_cfg.get("author", "(anonymous)")
        cfg_subject = dr_cfg.get("subject", "(unspecified)")
        cfg_title = dr_cfg.get("pdf_title", "(anonymous)")

        doc = self._build_doc(
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
        )

        story = self.build_story(content)
        story = self._finalize_story(story)

        def _cover_page(canvas, doc_inner):
            """Draw cover — exact match of AI Simulations page 1."""
            canvas.saveState()
            w, h = doc_inner.pagesize

            # Full dark background
            canvas.setFillColor(HexColor(_COVER_BG))
            canvas.rect(0, 0, w, h, stroke=0, fill=1)

            # Decorative arcs (stroke only, teal)
            canvas.setStrokeColor(HexColor(_TEAL))
            canvas.setFillColor(HexColor(_TEAL))
            canvas.setLineWidth(0)

            # Arc 1: center (510.24, 742.68), r≈170pt
            r1 = 170
            cx1, cy1 = 510.236, 742.677
            canvas.arc(cx1 - r1, cy1 - r1, cx1 + r1, cy1 + r1, 0, 360)

            # Arc 2: center (538.58, 771.02), r≈255pt (10% opacity)
            try:
                canvas.setStrokeAlpha(0.5)
            except AttributeError:
                pass
            r2 = 255.118
            cx2, cy2 = 538.583, 771.024
            canvas.arc(cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2, 0, 360)

            # Arc 3: center (566.93, 799.37), r≈340pt (15% opacity)
            try:
                canvas.setStrokeAlpha(0.3)
            except AttributeError:
                pass
            r3 = 340.157
            cx3, cy3 = 566.929, 799.370
            canvas.arc(cx3 - r3, cy3 - r3, cx3 + r3, cy3 + r3, 0, 360)

            try:
                canvas.setStrokeAlpha(1.0)
            except AttributeError:
                pass

            # Title: Helvetica-Bold 28pt white at x=68.36
            canvas.setFillColor(white)
            canvas.setFont("Helvetica-Bold", 28)

            # Word-wrap title
            title_lines = []
            words = title.split()
            current = ""
            max_w = w * 0.6
            for word in words:
                test = f"{current} {word}".strip()
                if canvas.stringWidth(test, "Helvetica-Bold", 28) > max_w:
                    if current:
                        title_lines.append(current)
                    current = word
                else:
                    current = test
            if current:
                title_lines.append(current)

            title_y = 595.291
            for line in title_lines[:3]:
                canvas.drawString(68.362, title_y, line)
                title_y -= 34

            # Subtitle: Helvetica 13pt #93A3B8
            if subtitle:
                canvas.setFont("Helvetica", 13)
                canvas.setFillColor(HexColor(_SUBTITLE_GRAY))
                sub_lines = []
                sub_words = subtitle.split()
                current = ""
                for word in sub_words:
                    test = f"{current} {word}".strip()
                    if canvas.stringWidth(test, "Helvetica", 13) > max_w:
                        if current:
                            sub_lines.append(current)
                        current = word
                    else:
                        current = test
                if current:
                    sub_lines.append(current)

                sub_y = 525.283
                for line in sub_lines[:2]:
                    canvas.drawString(68.362, sub_y, line)
                    sub_y -= 18

            # Accent rule: teal rounded rect ~156x2.5pt at y=445.93
            canvas.setFillColor(HexColor(_TEAL))
            canvas.roundRect(68.362, 445.925, 155.906, 2.5, 0.75, stroke=0, fill=1)

            # Metadata: Helvetica 9pt #64748A
            canvas.setFont("Helvetica", 9)
            canvas.setFillColor(HexColor(_META_GRAY))
            month_year = self.date.strftime("%B %Y")
            canvas.drawString(68.362, 414.248, f"Compiled {month_year} \u00b7 {report_type}")

            # Topics: Helvetica 9pt #93A3B8
            if topics:
                topic_str = "Covering: " + " \u00b7 ".join(t[:30] for t in topics[:6])
                canvas.setFont("Helvetica", 9)
                canvas.setFillColor(HexColor(_SUBTITLE_GRAY))
                # Word-wrap
                tag_lines = []
                tag_words = topic_str.split()
                current = ""
                for word in tag_words:
                    test = f"{current} {word}".strip()
                    if canvas.stringWidth(test, "Helvetica", 9) > max_w:
                        if current:
                            tag_lines.append(current)
                        current = word
                    else:
                        current = test
                if current:
                    tag_lines.append(current)

                tag_y = 392.744
                for line in tag_lines[:2]:
                    canvas.drawString(68.362, tag_y, line)
                    tag_y -= 13

            # Dot row: 8 dots at y=170.08, spacing ~51.024pt
            try:
                canvas.setFillAlpha(0.6)
            except AttributeError:
                pass
            canvas.setFillColor(HexColor(_TEAL))
            dots_x = [62.362, 113.386, 164.409, 215.433, 266.457, 317.480, 368.504, 419.528]
            for dx in dots_x:
                canvas.circle(dx, 170.079, 1.5, stroke=0, fill=1)

            try:
                canvas.setFillAlpha(1.0)
            except AttributeError:
                pass

            # Bottom teal strip: 1.5pt at y=79.37
            canvas.setFillColor(HexColor(_TEAL))
            canvas.rect(0, 79.370, w, 1.5, stroke=0, fill=1)

            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_cover_page,
            onLaterPages=_dr_header_footer,
        )

        return self.output_path

    # ------------------------------------------------------------------
    # Suppress unused base section builders
    # ------------------------------------------------------------------

    def build_body(self, content: dict) -> list:
        return []

    def build_at_a_glance(self, *args, **kwargs) -> list:
        return []

    def build_executive_summary(self, *args, **kwargs) -> list:
        return []

    def build_back_cover(self) -> list:
        return []
