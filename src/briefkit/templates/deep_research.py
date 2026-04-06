"""
briefkit.templates.deep_research
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Deep research report template — minimalist dark cover with arc decorations.

Grounded in AI Simulations With Progressive Learning visual design.

Build order:
  Dark cover (canvas) → Contents page → Body sections → Back page

Design norms:
  - Full-page dark cover with decorative arc strokes, teal accent rule
  - Minimalist white body pages, clean typography
  - Thin-rule header: title left, "RESEARCH REPORT {year}" right
  - Centered em-dash page numbers "— n —"
  - Numbered TOC with teal chapter numbers and italic subtopics
  - No dashboard, no callouts — pure text focus
  - Teal bottom strip on cover
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
    _hf_state,
)
from briefkit.styles import (
    _get_brand,
    _hex,
    _ps,
    _safe_para,
    _safe_text,
    compute_content_width,
)

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
    """Deep research header/footer — thin rule header, centered page number."""
    canvas.saveState()
    b = _get_brand(_dr_state.get("brand"))
    w, h = doc.pagesize

    caption_c = HexColor(b.get("caption", "#888888"))
    rule_c = HexColor(b.get("rule", "#00D4AA"))
    body_font = b.get("font_body", "Helvetica")

    # Header — title left, report type + year right
    header_y = h - doc.topMargin + 8 * mm

    title = _dr_state.get("title", "")
    if title:
        canvas.setFont(body_font, 7)
        canvas.setFillColor(caption_c)
        canvas.drawString(doc.leftMargin, header_y, title.upper()[:50])

    report_label = _dr_state.get("report_type", "RESEARCH REPORT")
    year = _dr_state.get("year", "2026")
    canvas.setFont(body_font, 7)
    canvas.setFillColor(caption_c)
    canvas.drawRightString(
        w - doc.rightMargin, header_y, f"{report_label} {year}",
    )

    # Header rule
    canvas.setStrokeColor(rule_c)
    canvas.setLineWidth(0.5)
    canvas.line(
        doc.leftMargin, header_y - 4,
        w - doc.rightMargin, header_y - 4,
    )

    # Footer — centered page number with em-dashes
    footer_y = doc.bottomMargin - 6 * mm
    page_num = canvas.getPageNumber()
    canvas.setFont(body_font, 8)
    canvas.setFillColor(caption_c)
    canvas.drawCentredString(w / 2, footer_y, f"\u2014 {page_num} \u2014")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class DeepResearchTemplate(BaseBriefingTemplate):
    """
    Deep research report template.

    Produces a minimalist research report with a dark cover page,
    decorative arc strokes, and clean body typography. Designed for
    academic deep-dives, literature surveys, and research compilations.

    Suitable for: research reports, literature reviews, survey papers,
    technical deep-dives, white-paper-style analysis.
    """

    def build_story(self, content: dict) -> list:
        """Assemble the research report story."""
        story: list = []
        subsystems = content.get("subsystems", [])

        # Cover placeholder — canvas draws the actual cover
        story.append(Spacer(1, 200 * mm))
        story.append(PageBreak())

        # Contents page
        story.append(Paragraph("Contents", self.styles["STYLE_H1"]))
        story.append(Spacer(1, 2 * mm))

        # Teal rule under "Contents"
        rule_data = [[""]]
        rule = Table(rule_data, colWidths=[self.content_width], rowHeights=[2])
        rule.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _hex(self.brand, "secondary")),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(rule)
        story.append(Spacer(1, 6 * mm))

        # Build TOC entries
        secondary_c = _hex(self.brand, "secondary")
        caption_c = _hex(self.brand, "caption")

        for i, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {i}")

            # Number + title row
            num_style = _ps(
                f"DRTocNum_{i}", brand=self.brand,
                fontSize=12, fontName=self.brand.get("font_heading", "Helvetica-Bold"),
                textColor=secondary_c, leading=16, spaceBefore=8, spaceAfter=2,
            )
            story.append(Paragraph(
                f'<font color="{self.brand.get("secondary", "#00D4AA")}"><b>{i}</b></font>'
                f'&nbsp;&nbsp;&nbsp;{_safe_text(name)}',
                num_style,
            ))

            # Extract sub-headings as italic subtopic line
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            sub_items = []
            for block in blocks:
                if block.get("type") == "heading" and block.get("level") in (2, 3):
                    sub_items.append(block["text"])
            if sub_items:
                summary = " \u00b7 ".join(sub_items[:5])
                sub_style = _ps(
                    f"DRTocSub_{i}", brand=self.brand,
                    fontSize=9, fontName=self.brand.get("font_caption", "Helvetica-Oblique"),
                    textColor=caption_c, leading=12, leftIndent=24, spaceAfter=4,
                )
                story.append(Paragraph(summary[:100], sub_style))

        story.append(PageBreak())

        # Body sections
        for idx, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {idx}")

            story.append(Paragraph(
                f"{idx}.  {name}", self.styles["STYLE_H1"],
            ))
            story.append(Spacer(1, 2 * mm))

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

        # Back page
        story.append(Spacer(1, 60 * mm))
        attr_style = _ps(
            "DRBackAttr", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "caption"),
            alignment=1,
        )
        story.append(_safe_para("Generated by briefkit", attr_style))

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
        _dr_state["title"] = title
        _dr_state["year"] = year
        _dr_state["report_type"] = report_type.upper()
        _dr_state["brand"] = self.brand

        _hf_state["section"] = title
        _hf_state["date"] = self.date_str
        _hf_state["doc_id"] = self.doc_id
        _hf_state["brand"] = self.brand

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        page_size = A4
        self.content_width = compute_content_width(page_size, margins)

        b = self.brand
        cfg_author = dr_cfg.get("author", "")
        cfg_subject = dr_cfg.get("subject", "")

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=title,
            author=cfg_author or b.get("org", "(anonymous)"),
            subject=cfg_subject or "(unspecified)",
            creator="briefkit",
            keywords=self.doc_id or "briefkit",
        )

        story = self.build_story(content)

        primary_color = HexColor(b.get("primary", "#1E2530"))
        secondary_color = HexColor(b.get("secondary", "#00D4AA"))
        caption_color = HexColor(b.get("caption", "#888888"))

        def _cover_page(canvas, doc_inner):
            """Draw the minimalist dark cover with arc decorations."""
            canvas.saveState()
            w, h = doc_inner.pagesize

            # Full dark background
            canvas.setFillColor(primary_color)
            canvas.rect(0, 0, w, h, stroke=0, fill=1)

            # Decorative arc strokes (top-right quarter circles)
            canvas.setStrokeColor(HexColor("#2A3A4A"))
            canvas.setLineWidth(1)
            # Large arc
            cx, cy = w - 40, h - 40
            r = 300
            canvas.arc(
                cx - r, cy - r, cx + r, cy + r,
                startAng=180, extent=90,
            )
            # Smaller arc
            r2 = 200
            canvas.arc(
                cx - r2, cy - r2, cx + r2, cy + r2,
                startAng=180, extent=90,
            )

            # Title — large bold white
            canvas.setFillColor(white)
            canvas.setFont("Helvetica-Bold", 30)
            title_y = h * 0.52

            # Word-wrap title
            title_lines = []
            words = title.split()
            current = ""
            max_w = w * 0.6
            for word in words:
                test = f"{current} {word}".strip()
                if canvas.stringWidth(test, "Helvetica-Bold", 30) > max_w:
                    if current:
                        title_lines.append(current)
                    current = word
                else:
                    current = test
            if current:
                title_lines.append(current)

            for line in title_lines[:3]:
                canvas.drawString(left_m, title_y, line)
                title_y -= 40

            # Subtitle
            if subtitle:
                canvas.setFont("Helvetica", 12)
                canvas.setFillColor(HexColor("#AAAAAA"))
                # Word-wrap subtitle
                sub_lines = []
                sub_words = subtitle.split()
                current = ""
                for word in sub_words:
                    test = f"{current} {word}".strip()
                    if canvas.stringWidth(test, "Helvetica", 12) > max_w:
                        if current:
                            sub_lines.append(current)
                        current = word
                    else:
                        current = test
                if current:
                    sub_lines.append(current)

                sub_y = title_y - 10
                for line in sub_lines[:2]:
                    canvas.drawString(left_m, sub_y, line)
                    sub_y -= 16

            # Accent horizontal rule
            rule_y = h * 0.32
            canvas.setStrokeColor(secondary_color)
            canvas.setLineWidth(2)
            canvas.line(left_m, rule_y, left_m + 100, rule_y)

            # Metadata line
            meta_y = rule_y - 20
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(caption_color)
            month_year = self.date.strftime("%B %Y")
            canvas.drawString(
                left_m, meta_y,
                f"Compiled {month_year} \u00b7 {report_type}",
            )

            # Topic tags
            if topics:
                topic_str = "Covering: " + " \u00b7 ".join(t[:30] for t in topics[:6])
                canvas.setFont("Helvetica", 7)
                canvas.setFillColor(caption_color)

                # Word-wrap if needed
                tag_lines = []
                tag_words = topic_str.split()
                current = ""
                for word in tag_words:
                    test = f"{current} {word}".strip()
                    if canvas.stringWidth(test, "Helvetica", 7) > max_w:
                        if current:
                            tag_lines.append(current)
                        current = word
                    else:
                        current = test
                if current:
                    tag_lines.append(current)

                tag_y = meta_y - 16
                for line in tag_lines[:2]:
                    canvas.drawString(left_m, tag_y, line)
                    tag_y -= 12

            # Dot row decoration
            dot_y = 90
            canvas.setFillColor(HexColor("#3A4A5A"))
            dot_spacing = (w - left_m - right_m) / 8
            for i in range(8):
                dx = left_m + dot_spacing * i + dot_spacing / 2
                canvas.circle(dx, dot_y, 2, stroke=0, fill=1)

            # Bottom teal strip
            canvas.setFillColor(secondary_color)
            canvas.rect(0, 0, w, 4, stroke=0, fill=1)

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
