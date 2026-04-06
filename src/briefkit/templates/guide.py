"""
briefkit.templates.guide
~~~~~~~~~~~~~~~~~~~~~~~~~
Technical guide template — dark cover with spec table, hardware-style layout.

Grounded in System Overclocking & Optimisation Guide visual design.

Build order:
  Dark cover (canvas) → TOC → Body sections → Bibliography → Back page

Design norms:
  - Full-page dark cover with decorative circles, spec table, version badge
  - Dark header bar on body pages (doc title left, custom info right)
  - Cyan/teal accent colors for section numbers and labels
  - Red-bordered critical callout boxes
  - Standard data tables with primary-colored headers
  - Footer: system info left, date center, page right
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
from briefkit.elements.toc import build_toc
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
    compute_content_width,
)

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
    """Guide header/footer — dark top bar, three-column footer."""
    canvas.saveState()
    b = _get_brand(_guide_state.get("brand"))
    w, h = doc.pagesize

    primary_c = HexColor(b.get("primary", "#1A2332"))
    secondary_c = HexColor(b.get("secondary", "#2EC4B6"))
    caption_c = HexColor(b.get("caption", "#8899AA"))
    heading_font = b.get("font_heading", "Helvetica-Bold")
    body_font = b.get("font_body", "Helvetica")

    # Header — dark top bar
    bar_h = 10 * mm
    top_y = h - doc.topMargin + bar_h + 2 * mm
    canvas.setFillColor(primary_c)
    canvas.rect(0, top_y - bar_h, w, bar_h, stroke=0, fill=1)

    # Header text — title left, info right
    text_y = top_y - bar_h + 3 * mm
    title = _guide_state.get("title", "")
    if title:
        canvas.setFont(body_font, 7)
        canvas.setFillColor(HexColor("#CCCCCC"))
        canvas.drawString(doc.leftMargin + 2 * mm, text_y, title.upper()[:60])

    header_right = _guide_state.get("header_right", "")
    if header_right:
        canvas.setFont(heading_font, 7)
        canvas.setFillColor(secondary_c)
        canvas.drawRightString(
            w - doc.rightMargin - 2 * mm, text_y, header_right[:60],
        )

    # Footer — three columns
    footer_y = doc.bottomMargin - 6 * mm
    canvas.setFont(body_font, 7)
    canvas.setFillColor(caption_c)

    footer_left = _guide_state.get("footer_left", "")
    if footer_left:
        canvas.drawString(doc.leftMargin, footer_y, footer_left[:40])

    date_str = _guide_state.get("date", "")
    if date_str:
        canvas.drawCentredString(w / 2, footer_y, f"Generated {date_str}")

    page_num = canvas.getPageNumber()
    canvas.drawRightString(
        w - doc.rightMargin, footer_y, f"Page {page_num}",
    )

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class GuideTemplate(BaseBriefingTemplate):
    """
    Technical guide template.

    Produces a hardware/software guide with a dark cover page featuring
    a spec table, decorative circles, and version badge. Body pages use
    a dark header bar with document title and configurable right-side info.

    Suitable for: system guides, hardware manuals, optimization guides,
    configuration references, benchmark reports.
    """

    def build_story(self, content: dict) -> list:
        """Assemble the guide story (cover handled by canvas callback)."""
        story: list = []
        subsystems = content.get("subsystems", [])

        # Cover placeholder — canvas draws the actual cover
        story.append(Spacer(1, 200 * mm))
        story.append(PageBreak())

        # TOC
        story.append(Paragraph("Table of Contents", self.styles["STYLE_H1"]))
        story.append(Spacer(1, 4 * mm))

        toc_entries = []
        for i, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {i}")
            toc_entries.append((1, f"{i}  {name}"))
            # Add first-level sub-items from headings
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            sub_items = []
            for block in blocks:
                if block.get("type") == "heading" and block.get("level") in (2, 3):
                    sub_items.append(block["text"])
            if sub_items:
                summary = ", ".join(sub_items[:5])
                toc_entries.append((2, summary[:80]))

        story.extend(build_toc(
            toc_entries, brand=self.brand, content_width=self.content_width,
        ))
        story.append(PageBreak())

        # Body sections
        for idx, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {idx}")

            # Section heading with number
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
        if bib:
            bib_flowables = self.build_bibliography(bib)
            if bib_flowables:
                story.append(PageBreak())
                story.extend(bib_flowables)

        # Back page
        story.extend(self._build_back_page())

        return story

    def _build_back_page(self) -> list:
        """Simple back page with brand bar."""
        flowables: list = []
        flowables.append(Spacer(1, 60 * mm))

        bar_data = [[""]]
        bar = Table(bar_data, colWidths=[self.content_width], rowHeights=[4])
        bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _hex(self.brand, "secondary")),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        flowables.append(bar)
        flowables.append(Spacer(1, 8 * mm))

        attr_style = _ps(
            "GuideBackAttr", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "caption"),
            alignment=1,
        )
        flowables.append(_safe_para("Generated by briefkit", attr_style))

        return flowables

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
        _guide_state["date"] = self.date_str
        _guide_state["footer_left"] = classification
        _guide_state["brand"] = self.brand

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
        subject = b.get("subject", f"Technical guide: {title}")
        author = b.get("org", "briefkit")

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
            creator="briefkit",
            keywords=self.doc_id or "briefkit",
        )

        story = self.build_story(content)

        primary_color = HexColor(b.get("primary", "#1A2332"))
        secondary_color = HexColor(b.get("secondary", "#2EC4B6"))
        accent_color = HexColor(b.get("accent", "#5CE0D2"))
        caption_color = HexColor(b.get("caption", "#8899AA"))

        def _cover_page(canvas, doc_inner):
            """Draw the dark cover page with decorative circles and spec table."""
            canvas.saveState()
            w, h = doc_inner.pagesize

            # Full dark background
            canvas.setFillColor(primary_color)
            canvas.rect(0, 0, w, h, stroke=0, fill=1)

            # Top accent bar
            canvas.setFillColor(secondary_color)
            canvas.rect(0, h - 8, w, 8, stroke=0, fill=1)

            # Decorative circles (subtle, low opacity)
            canvas.saveState()
            canvas.setStrokeColor(HexColor("#2A3A52"))
            canvas.setLineWidth(1.5)
            canvas.setFillColor(HexColor("#1F2D42"))
            # Large circle bottom-left
            canvas.circle(80, 120, 180, stroke=1, fill=1)
            # Medium circle top-right
            canvas.circle(w - 60, h - 200, 120, stroke=1, fill=1)
            # Small circle center-right
            canvas.circle(w - 100, h / 2 - 40, 60, stroke=1, fill=1)
            canvas.restoreState()

            # Horizontal rule
            rule_y = h - 120
            canvas.setStrokeColor(HexColor("#2A3A52"))
            canvas.setLineWidth(0.5)
            canvas.line(left_m, rule_y, w - right_m, rule_y)

            # Title
            canvas.setFillColor(white)
            canvas.setFont("Helvetica-Bold", 32)
            # Split title into lines if needed
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

            title_y = h - 160
            for line in title_lines[:3]:
                canvas.drawString(left_m, title_y, line)
                title_y -= 42

            # Accent rule under title
            canvas.setStrokeColor(secondary_color)
            canvas.setLineWidth(3)
            canvas.line(left_m, title_y + 10, left_m + 120, title_y + 10)

            # Subtitle keywords
            if subtitle_kw:
                canvas.setFont("Helvetica", 11)
                canvas.setFillColor(accent_color)
                canvas.drawString(left_m, title_y - 20, subtitle_kw[:80])

            # Spec table (if provided)
            if spec_rows:
                table_y = h * 0.38
                canvas.setStrokeColor(HexColor("#2A3A52"))
                canvas.setLineWidth(0.5)
                box_x = left_m + 10
                box_w = w - left_m - right_m - 20
                row_h = 22
                box_h = (len(spec_rows) + 1) * row_h + 16
                canvas.roundRect(box_x, table_y - box_h, box_w, box_h, 4, stroke=1, fill=0)

                # Table header
                canvas.setFont("Helvetica-Bold", 9)
                canvas.setFillColor(secondary_color)
                canvas.drawString(box_x + 12, table_y - 20, "TARGET SYSTEM")

                # Table rows
                for i, row in enumerate(spec_rows[:8]):
                    label = row.get("label", "") if isinstance(row, dict) else str(row)
                    value = row.get("value", "") if isinstance(row, dict) else ""
                    ry = table_y - 42 - i * row_h

                    canvas.setFont("Helvetica-Bold", 8)
                    canvas.setFillColor(secondary_color)
                    canvas.drawString(box_x + 12, ry, label.upper()[:20])

                    canvas.setFont("Helvetica", 9)
                    canvas.setFillColor(HexColor("#CCCCCC"))
                    canvas.drawString(box_x + 120, ry, str(value)[:60])

            # Date and classification footer
            footer_y = 50
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(caption_color)
            canvas.drawString(left_m, footer_y, f"Generated: {self.date_str}")
            if classification:
                canvas.drawString(left_m, footer_y - 14, f"Classification: {classification}")

            # Version badge
            badge_text = f"VERSION {version}"
            badge_w = canvas.stringWidth(badge_text, "Helvetica-Bold", 8) + 20
            badge_x = w - right_m - badge_w
            badge_y = footer_y - 4
            canvas.setFillColor(secondary_color)
            canvas.roundRect(badge_x, badge_y - 4, badge_w, 18, 4, stroke=0, fill=1)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.setFillColor(white)
            canvas.drawCentredString(badge_x + badge_w / 2, badge_y + 2, badge_text)

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
