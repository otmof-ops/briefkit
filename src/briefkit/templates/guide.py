"""
briefkit.templates.guide
~~~~~~~~~~~~~~~~~~~~~~~~~
Technical guide template — pixel-perfect match of System Overclocking &
Optimisation Guide visual design.

Exact specifications reverse-engineered from PDF content streams.

Cover page (canvas-drawn):
  - Full-page dark fill #0C1116
  - Blue accent bar at top: #57A5FF, 14.17pt high, full width
  - Horizontal guide grid: #57A5FF 1pt stroke, 34pt spacing
  - Two decorative filled circles: #57A5FF at varying opacity
    - Circle 1: center (453.54, 615.12), r≈170pt, 10% opacity
    - Circle 2: center (113.39, 170.08), r≈127pt, 15% opacity
  - Title: Helvetica-Bold 32pt white at x=70.87, y=657.64
  - Accent rule: #57A5FF 3pt stroke, 70.87→396.85 at y=606.61
  - Keywords: Helvetica 12pt #38D1BF at x=70.87, y=572.60
  - Spec table: rounded rect fill #161A21 stroke #2F363D
    - Header: Helvetica-Bold 8pt #57A5FF "TARGET SYSTEM"
    - Labels: Helvetica-Bold 7pt #38D1BF at x=90.71
    - Values: Helvetica 8.5pt #C8D1D8 at x=175.75
    - Row spacing: ~19.84pt
  - Footer: Helvetica 8pt #6E7580
  - Version badge: rounded rect #57A5FF, Helvetica-Bold 7pt white

Body pages:
  - Header: 34pt dark bar #0C1116, 1.5pt #57A5FF bottom rule
    - Left: Helvetica 7pt #8B949F — title uppercase
    - Right: Helvetica 7pt #57A5FF — hardware info
  - Footer: 0.5pt rule #D0D7DD, Helvetica 7pt #6E7580 three columns
  - TOC numbers: Helvetica-Bold 14pt #57A5FF
  - TOC titles: Helvetica-Bold 10pt #1A1A2D
  - TOC subtitles: Helvetica 7.5pt #6E7580
  - Section headers: bg #F6F7F9, 2pt left accent #57A5FF
  - Table headers: bg #1A2331 (#1A1A2D), text white
  - Warning callouts: 3pt left border #F75049
  - Tip callouts: 3pt left border #38D1BF
"""

from __future__ import annotations

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

from briefkit.elements.callout import build_callout_box
from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
)
from briefkit.styles import (
    _get_brand,
    _ps,
    compute_content_width,
)
from briefkit.templates._helpers import should_skip

# ---------------------------------------------------------------------------
# Exact colors from PDF content stream
# ---------------------------------------------------------------------------

_COVER_BG = "#0C1116"
_BLUE_ACCENT = "#57A5FF"
_TEAL_ACCENT = "#38D1BF"
_SPEC_BOX_FILL = "#161A21"
_SPEC_BOX_STROKE = "#2F363D"
_SPEC_VALUE = "#C8D1D8"
_CAPTION = "#6E7580"
_HEADER_LEFT = "#8B949F"
_FOOTER_RULE = "#D0D7DD"
_TOC_TITLE = "#1A1A2D"
_SECTION_BG = "#F6F7F9"
_TABLE_HEADER_BG = "#1A2331"

# ---------------------------------------------------------------------------
# Module-level state for custom header / footer
# ---------------------------------------------------------------------------

_guide_state: dict = {
    "title": "",
    "header_right": "",
    "date": "",
    "footer_left": "",
    "brand": {},
}


def _guide_header_footer(canvas, doc):
    """Guide header/footer — exact match of PDF body pages."""
    canvas.saveState()
    _get_brand(_guide_state.get("brand"))
    w, h = doc.pagesize

    # Header — dark bar: full width, 34pt tall, top-aligned
    bar_h = 34.016
    bar_y = h - bar_h
    canvas.setFillColor(HexColor(_COVER_BG))
    canvas.rect(0, bar_y, w, bar_h, stroke=0, fill=1)

    # Blue accent line at bottom of header bar
    canvas.setStrokeColor(HexColor(_BLUE_ACCENT))
    canvas.setLineWidth(1.5)
    canvas.line(0, bar_y, w, bar_y)

    # Header text — title left, info right (inside the bar)
    text_y = bar_y + 11.34  # vertically centered in bar
    title = _guide_state.get("title", "")
    if title:
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor(_HEADER_LEFT))
        canvas.drawString(doc.leftMargin, text_y, title.upper()[:60])

    header_right = _guide_state.get("header_right", "")
    if header_right:
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor(_BLUE_ACCENT))
        canvas.drawRightString(w - doc.rightMargin, text_y, header_right[:60])

    # Footer rule
    footer_rule_y = 34.016
    canvas.setStrokeColor(HexColor(_FOOTER_RULE))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, footer_rule_y, w - doc.rightMargin, footer_rule_y)

    # Footer text — three columns at y=22.68
    footer_y = 22.677
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(HexColor(_CAPTION))

    footer_left = _guide_state.get("footer_left", "")
    if footer_left:
        canvas.drawString(doc.leftMargin, footer_y, footer_left[:40])

    date_str = _guide_state.get("date", "")
    if date_str:
        canvas.drawCentredString(w / 2, footer_y, f"Generated {date_str}")

    page_num = canvas.getPageNumber()
    canvas.drawRightString(w - doc.rightMargin, footer_y, f"Page {page_num}")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class GuideTemplate(BaseBriefingTemplate):
    """
    Technical guide template — pixel-perfect System Overclocking style.

    Dark cover with spec table, decorative circles, cyan accents.
    Dark header bar on body pages with hardware info.

    Suitable for: system guides, hardware manuals, optimization guides,
    configuration references, benchmark reports.
    """

    def build_story(self, content: dict) -> list:
        """Assemble the guide story (cover handled by canvas callback)."""
        story: list = []
        subsystems = content.get("subsystems", [])

        cfg = self.config

        # Cover placeholder — canvas draws the actual cover
        story.append(Spacer(1, 200 * mm))
        story.append(PageBreak())

        _toc_start = len(story)

        # TOC — exact match: light bg box with blue left accent
        secondary_c = HexColor(_BLUE_ACCENT)
        toc_title_c = HexColor(_TOC_TITLE)
        caption_c = HexColor(_CAPTION)

        # TOC header box
        toc_header_data = [[
            Paragraph(
                "Table of Contents",
                _ps("GuideTocTitle", brand=self.brand,
                    fontSize=14, fontName="Helvetica-Bold",
                    textColor=secondary_c, leading=16.8),
            ),
        ]]
        toc_header = Table(toc_header_data, colWidths=[self.content_width - 6],
                           rowHeights=[39.685])
        toc_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor(_SECTION_BG)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 14.173),
            ("LINEBELOW", (0, 0), (-1, -1), 2, secondary_c),
        ]))
        story.append(toc_header)
        story.append(Spacer(1, 4 * mm))

        # TOC entries — number left, title+subtitle right, separator line
        for i, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {i}")

            # Extract sub-headings for subtitle
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            sub_items = []
            for block in blocks:
                if block.get("type") == "heading" and block.get("level") in (2, 3):
                    sub_items.append(block["text"])
            subtitle = ", ".join(sub_items[:5])[:80] if sub_items else ""

            # Number + title row
            row_data = [[
                Paragraph(
                    f"<b>{i}</b>",
                    _ps(f"GTocN_{i}", brand=self.brand,
                        fontSize=14, fontName="Helvetica-Bold",
                        textColor=secondary_c, leading=12,
                        alignment=2),
                ),
                Paragraph(
                    f'<b>{name}</b>',
                    _ps(f"GTocT_{i}", brand=self.brand,
                        fontSize=10, fontName="Helvetica-Bold",
                        textColor=toc_title_c, leading=14),
                ),
            ]]
            toc_row = Table(row_data, colWidths=[40, self.content_width - 46],
                            rowHeights=[21.669])
            toc_row.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), 6),
                ("LEFTPADDING", (1, 0), (1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(toc_row)

            if subtitle:
                sub_style = _ps(
                    f"GTocSub_{i}", brand=self.brand,
                    fontSize=7.5, fontName="Helvetica",
                    textColor=caption_c, leading=9, leftIndent=46,
                )
                story.append(Paragraph(subtitle, sub_style))

            # Separator line
            sep_data = [[""]]
            sep = Table(sep_data, colWidths=[self.content_width], rowHeights=[0.5])
            sep.setStyle(TableStyle([
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor("#EFF4F7")),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(sep)
            story.append(Spacer(1, 2 * mm))

        story.append(PageBreak())

        if should_skip(cfg, "toc"):
            del story[_toc_start:]

        # Body sections — each with section header bar
        for idx, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {idx}")

            # Section header bar: bg #F6F7F9, 2pt blue left accent
            sec_data = [[
                Paragraph(
                    f"{idx}.",
                    _ps(f"GSecN_{idx}", brand=self.brand,
                        fontSize=13, fontName="Helvetica-Bold",
                        textColor=secondary_c, leading=15.6),
                ),
                Paragraph(
                    name,
                    _ps(f"GSecT_{idx}", brand=self.brand,
                        fontSize=13, fontName="Helvetica-Bold",
                        textColor=secondary_c, leading=15.6),
                ),
            ]]
            sec_header = Table(sec_data, colWidths=[30, self.content_width - 36],
                               rowHeights=[39.685])
            sec_header.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), HexColor(_SECTION_BG)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, -1), 14.173),
                ("LEFTPADDING", (1, 0), (1, -1), 0),
                ("LINEBELOW", (0, 0), (-1, -1), 2, secondary_c),
            ]))
            story.append(sec_header)
            story.append(Spacer(1, 3 * mm))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                if block["type"] == "heading" and block["level"] <= 1:
                    continue
                # Sub-section headings get their own bar
                if block["type"] == "heading" and block["level"] in (2, 3):
                    sub_text = block["text"]
                    sub_num = f"{idx}.{rendered // 10 + 1}" if rendered > 0 else f"{idx}.1"
                    sub_data = [[
                        Paragraph(
                            f"{sub_num}  {sub_text}",
                            _ps(f"GSubH_{idx}_{rendered}", brand=self.brand,
                                fontSize=11, fontName="Helvetica-Bold",
                                textColor=toc_title_c, leading=13.2),
                        ),
                    ]]
                    sub_header = Table(sub_data, colWidths=[self.content_width - 6],
                                       rowHeights=[25.512])
                    sub_header.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), HexColor(_SECTION_BG)),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 14.173),
                        ("ROUNDEDCORNERS", [1, 1, 0, 0]),
                    ]))
                    story.append(sub_header)
                    story.append(Spacer(1, 2 * mm))
                    rendered += 1
                    continue

                for fl in self.render_blocks([block]):
                    story.append(fl)
                    rendered += 1
                    if rendered >= 100:
                        break
                if rendered >= 100:
                    break

            # Insights as callout boxes
            insights = sub.get("insights", [])
            for insight in insights[:2]:
                story.append(build_callout_box(
                    insight[:500], "insight",
                    brand=self.brand, content_width=self.content_width,
                ))

            story.append(Spacer(1, 4 * mm))

        # Bibliography
        bib = content.get("bibliography", [])
        if bib and not should_skip(cfg, "bibliography"):
            bib_flowables = self.build_bibliography(bib)
            if bib_flowables:
                story.append(PageBreak())
                story.extend(bib_flowables)

        return story

    # ------------------------------------------------------------------
    # generate() — custom cover and header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the guide PDF with dark cover page."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.extract_content()
        title = content.get(
            "title",
            self.target_path.name.replace("-", " ").title(),
        )
        subsystems = content.get("subsystems", [])

        # Doc ID
        doc_ids_cfg = self.config.get("doc_ids", {})
        if doc_ids_cfg.get("enabled", True):
            from briefkit.doc_ids import get_or_assign_doc_id

            self.doc_id = get_or_assign_doc_id(
                self.target_path, self.level,
                title, config=self.config,
            )

        # Template-specific config
        guide_cfg = self.config.get("guide", {})
        spec_rows = guide_cfg.get("spec_table", [])
        subtitle_kw = guide_cfg.get("subtitle_keywords", "")
        classification = guide_cfg.get("classification", "")
        version = guide_cfg.get("version", "1.0")
        header_right = guide_cfg.get("header_right", "")

        # Auto-derive subtitle keywords from subsystem names if not set
        if not subtitle_kw and subsystems:
            kw_list = [sub.get("name", "") for sub in subsystems[:6]]
            subtitle_kw = "  |  ".join(kw_list)

        # Header/footer state
        _guide_state["title"] = title
        _guide_state["header_right"] = header_right
        _guide_state["date"] = self.date.strftime("%d %B %Y")
        _guide_state["footer_left"] = classification
        _guide_state["brand"] = self.brand


        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        page_size = A4
        self.content_width = compute_content_width(page_size, margins)

        b = self.brand
        subject = guide_cfg.get("subject", f"Technical guide: {title}")
        author = guide_cfg.get("author", b.get("org", "Claude Code"))

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=title,
            author=author,
            subject=subject,
            creator="(unspecified)",
            keywords="",
        )

        story = self.build_story(content)

        def _cover_page(canvas, doc_inner):
            """Draw cover — exact match of System Overclocking Guide page 1."""
            canvas.saveState()
            w, h = doc_inner.pagesize

            # Full dark background
            canvas.setFillColor(HexColor(_COVER_BG))
            canvas.rect(0, 0, w, h, stroke=0, fill=1)

            # Blue accent bar at top (14.17pt high)
            canvas.setFillColor(HexColor(_BLUE_ACCENT))
            canvas.rect(0, h - 14.173, w, 14.173, stroke=0, fill=1)

            # Horizontal guide grid (decorative lines)
            canvas.setStrokeColor(HexColor(_BLUE_ACCENT))
            canvas.setLineWidth(1)
            # Graphics state for opacity — use alpha if available
            try:
                canvas.setStrokeAlpha(0.08)
            except AttributeError:
                canvas.setStrokeColor(HexColor("#1A2A3A"))
            y_start = 728.504
            for i in range(20):
                y = y_start - i * 34.016
                if y < 80:
                    break
                canvas.line(left_m, y, w - right_m, y)
            # Reset stroke
            canvas.setStrokeColor(HexColor(_BLUE_ACCENT))
            try:
                canvas.setStrokeAlpha(1.0)
            except AttributeError:
                pass

            # Decorative circle 1 (upper right, large)
            try:
                canvas.setFillAlpha(0.10)
            except AttributeError:
                pass
            canvas.setFillColor(HexColor(_BLUE_ACCENT))
            canvas.circle(453.543, 615.118, 170, stroke=0, fill=1)

            # Decorative circle 2 (lower left, medium)
            try:
                canvas.setFillAlpha(0.15)
            except AttributeError:
                pass
            canvas.circle(113.386, 170.079, 127.559, stroke=0, fill=1)

            # Reset alpha
            try:
                canvas.setFillAlpha(1.0)
            except AttributeError:
                pass

            # Horizontal rules (at specific positions from PDF)
            canvas.setStrokeColor(HexColor(_BLUE_ACCENT))
            canvas.setLineWidth(1)
            canvas.line(left_m, 694.488, w - right_m, 694.488)
            canvas.line(left_m, 660.472, w - right_m, 660.472)

            # Title: Helvetica-Bold 32pt white
            canvas.setFillColor(white)
            canvas.setFont("Helvetica-Bold", 32)
            # Split title into lines
            title_lines = []
            words = title.split()
            current = ""
            for word in words:
                test = f"{current} {word}".strip()
                if canvas.stringWidth(test, "Helvetica-Bold", 32) > (w - left_m - right_m) * 0.85:
                    if current:
                        title_lines.append(current)
                    current = word
                else:
                    current = test
            if current:
                title_lines.append(current)

            title_y = 657.638
            for line in title_lines[:3]:
                canvas.drawString(70.866, title_y, line)
                title_y -= 36.85

            # Blue accent rule under title: 3pt stroke
            canvas.setStrokeColor(HexColor(_BLUE_ACCENT))
            canvas.setLineWidth(3)
            rule_y = title_y + 14.17
            canvas.line(70.866, rule_y, 396.850, rule_y)

            # Subtitle keywords: Helvetica 12pt teal
            if subtitle_kw:
                canvas.setFont("Helvetica", 12)
                canvas.setFillColor(HexColor(_TEAL_ACCENT))
                canvas.drawString(70.866, rule_y - 34, subtitle_kw[:80])

            # Spec table box: rounded rect
            if spec_rows:
                box_x = 70.866
                box_w = w - 2 * 70.866 + 14
                row_h = 19.843
                box_h = (len(spec_rows) + 1) * row_h + 20
                box_y = 360

                canvas.setFillColor(HexColor(_SPEC_BOX_FILL))
                canvas.setStrokeColor(HexColor(_SPEC_BOX_STROKE))
                canvas.setLineWidth(1)
                canvas.roundRect(box_x, box_y, box_w, box_h, 5, stroke=1, fill=1)

                # "TARGET SYSTEM" header
                canvas.setFont("Helvetica-Bold", 8)
                canvas.setFillColor(HexColor(_BLUE_ACCENT))
                canvas.drawString(85.039, box_y + box_h - 20, "TARGET SYSTEM")

                # Spec rows
                for i, row in enumerate(spec_rows[:8]):
                    label = row.get("label", "") if isinstance(row, dict) else str(row)
                    value = row.get("value", "") if isinstance(row, dict) else ""
                    ry = box_y + box_h - 40 - i * row_h

                    canvas.setFont("Helvetica-Bold", 7)
                    canvas.setFillColor(HexColor(_TEAL_ACCENT))
                    canvas.drawString(90.709, ry, label.upper()[:20])

                    canvas.setFont("Helvetica", 8.5)
                    canvas.setFillColor(HexColor(_SPEC_VALUE))
                    canvas.drawString(175.748, ry, str(value)[:60])

            # Footer: date and classification
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(HexColor(_CAPTION))
            canvas.drawString(70.866, 70.866, f"Generated: {self.date.strftime('%d %B %Y')}")
            if classification:
                canvas.drawString(70.866, 51.024, f"Classification: {classification}")

            # Version badge: rounded rect #57A5FF
            badge_text = f"VERSION {version}"
            badge_w = 82.039
            badge_x = w - right_m - badge_w
            badge_y = 51.024
            canvas.setFillColor(HexColor(_BLUE_ACCENT))
            canvas.roundRect(badge_x, badge_y, badge_w, 22.677, 3, stroke=0, fill=1)
            canvas.setFont("Helvetica-Bold", 7)
            canvas.setFillColor(white)
            canvas.drawCentredString(badge_x + badge_w / 2, badge_y + 7.09, badge_text)

            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_cover_page,
            onLaterPages=_guide_header_footer,
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
