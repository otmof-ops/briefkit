"""
briefkit.templates.whitepaper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
White paper template.

Build order:
  Cover → TOC (alphabetic) → Body (A, B, C… sections) → Back Cover

Key differences:
  - NASA-style white paper layout (Letter, Calibri/Arial family)
  - Centered cover page with generous whitespace, no branded bar
  - Alphabetic section numbering: A, B, C… with sub-sections A-1, A-2
  - Justified body text
  - Page number bottom-center only — no top header
  - Generous 10mm spacing between sections
  - No dashboard, no metric blocks, no classification banner
"""

from __future__ import annotations

import string

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from briefkit.elements.back_cover import build_back_cover
from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
    build_toc,
)
from briefkit.styles import (
    _get_brand,
    _hex,
    _ps,
    _safe_para,
    _safe_text,
    compute_content_width,
)
from briefkit.templates._helpers import should_skip

# ---------------------------------------------------------------------------
# Module-level state for custom header / footer
# ---------------------------------------------------------------------------

_wp_state: dict = {
    "brand": {},
}


def _wp_header_footer(canvas, doc):
    """
    White paper header/footer.

    No top header.  Page number bottom-center only.
    """
    canvas.saveState()
    b = _get_brand(_wp_state.get("brand"))
    page_width = doc.pagesize[0]

    # Footer — page number centered
    bottom_y = doc.bottomMargin - 6 * mm
    canvas.setFont(b.get("font_body", "Helvetica"), 8)
    canvas.setFillColor(HexColor(b.get("caption", "#666666")))
    canvas.drawCentredString(
        page_width / 2, bottom_y + 1.5 * mm,
        str(doc.page),
    )

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Alpha-label helper
# ---------------------------------------------------------------------------

_ALPHA = list(string.ascii_uppercase)  # A … Z


def _alpha(index: int) -> str:
    """Return an uppercase letter for *index* (0-based).  Wraps at Z."""
    return _ALPHA[index % 26]


# ---------------------------------------------------------------------------
# Template class
# ---------------------------------------------------------------------------


class WhitepaperTemplate(BaseBriefingTemplate):
    """
    NASA-style white paper template.

    Produces a formal white paper with alphabetic section numbering,
    justified body text, and generous whitespace.  Suitable for
    position papers, technical white papers, and policy papers.
    """

    # ------------------------------------------------------------------
    # Story assembly
    # ------------------------------------------------------------------

    def build_story(self, content: dict) -> list:
        """
        Assemble the whitepaper story:
          Cover → TOC → Body (alpha sections) → Back Cover.
        """
        story: list = []
        title = content.get("title", self.target_path.name.replace("-", " ").title())
        subtitle = content.get("subtitle", "")
        overview = content.get("overview", "")
        subsystems = content.get("subsystems", [])

        cfg = self.config

        # ---- Cover page ----
        story.extend(self._build_cover(title, subtitle, overview, content))
        story.append(PageBreak())

        # ---- Table of contents ----
        if not should_skip(cfg, "toc"):
            story.extend(self._build_toc(subsystems))
            story.append(PageBreak())

        # ---- Body sections ----
        story.extend(self._build_body(subsystems))

        # ---- Back cover ----
        if not should_skip(cfg, "back_cover"):
            story.append(PageBreak())
            story.extend(build_back_cover(
                date=self.date,
                brand=self.brand,
                content_width=self.content_width,
            ))

        return story

    # ------------------------------------------------------------------
    # Cover page
    # ------------------------------------------------------------------

    def _build_cover(
        self,
        title: str,
        subtitle: str,
        overview: str,
        content: dict,
    ) -> list:
        """Centered cover page with generous whitespace."""
        flowables: list = []

        # Push content to ~40% page height
        flowables.append(Spacer(1, 90 * mm))

        # "White Paper" label
        label_style = _ps(
            "WPLabel", brand=self.brand,
            fontSize=24, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "primary"),
            alignment=1, spaceAfter=4,
        )
        flowables.append(Paragraph("White Paper", label_style))
        flowables.append(Spacer(1, 4 * mm))

        # "for"
        for_style = _ps(
            "WPFor", brand=self.brand,
            fontSize=12, fontName="Helvetica-Oblique",
            textColor=_hex(self.brand, "caption"),
            alignment=1, spaceAfter=4,
        )
        flowables.append(Paragraph("for", for_style))
        flowables.append(Spacer(1, 4 * mm))

        # Content title
        title_style = _ps(
            "WPTitle", brand=self.brand,
            fontSize=18, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "primary"),
            alignment=1, spaceAfter=6,
        )
        flowables.append(Paragraph(_safe_text(title), title_style))

        # Subtitle / tagline
        tagline = subtitle or self.brand.get("tagline", "")
        if tagline:
            flowables.append(Spacer(1, 3 * mm))
            sub_style = _ps(
                "WPSubtitle", brand=self.brand,
                fontSize=12, fontName="Helvetica-Oblique",
                textColor=_hex(self.brand, "caption"),
                alignment=1, spaceAfter=4,
            )
            flowables.append(Paragraph(_safe_text(tagline), sub_style))

        # Date
        flowables.append(Spacer(1, 6 * mm))
        date_style = _ps(
            "WPDate", brand=self.brand,
            fontSize=10, textColor=_hex(self.brand, "caption"),
            alignment=1,
        )
        flowables.append(Paragraph(self.date_str, date_style))

        # Project members / org at bottom-left
        org = self.brand.get("org", "")
        if org:
            flowables.append(Spacer(1, 60 * mm))
            member_style = _ps(
                "WPMembers", brand=self.brand,
                fontSize=9, textColor=_hex(self.brand, "body_text"),
                alignment=0,
            )
            flowables.append(Paragraph(
                f"<b>Project Members:</b> {_safe_text(org)}",
                member_style,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Table of Contents (alphabetic)
    # ------------------------------------------------------------------

    def _build_toc(self, subsystems: list[dict]) -> list:
        """
        Build a TOC with alphabetic section labels.

        Format:
          A. Executive Summary .............. 3
            A-1 Overview
        """
        flowables: list = []
        flowables.append(Paragraph("Table of Contents", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 4 * mm))

        toc_entries: list[tuple[int, str]] = []

        for idx, sub in enumerate(subsystems):
            letter_label = _alpha(idx)
            name = sub.get("name", f"Section {idx + 1}")
            toc_entries.append((1, f"{letter_label}. {name}"))

            # Sub-entries from blocks or content headings
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            sub_counter = 0
            for block in blocks:
                if block.get("type") == "heading" and block.get("level", 99) >= 2:
                    sub_counter += 1
                    heading_text = block.get("text", f"Sub-section {sub_counter}")
                    toc_entries.append(
                        (2, f"  {letter_label}-{sub_counter} {heading_text}"),
                    )
                    if sub_counter >= 8:
                        break

        flowables.extend(build_toc(
            toc_entries, brand=self.brand, content_width=self.content_width,
        ))

        return flowables

    # ------------------------------------------------------------------
    # Body sections
    # ------------------------------------------------------------------

    def _build_body(self, subsystems: list[dict]) -> list:
        """Render body sections with alpha-numeric IDs and justified text."""
        flowables: list = []

        # Justified body style
        body_style = _ps(
            "WPBody", brand=self.brand,
            fontSize=11, textColor=_hex(self.brand, "body_text"),
            leading=15, alignment=4,
        )

        for idx, sub in enumerate(subsystems):
            letter_label = _alpha(idx)
            name = sub.get("name", f"Section {idx + 1}")

            # Section heading
            heading_style = _ps(
                f"WPH1_{idx}", brand=self.brand,
                fontSize=14, fontName="Helvetica-Bold",
                textColor=_hex(self.brand, "primary"),
                spaceBefore=6, spaceAfter=4,
            )
            flowables.append(Paragraph(
                f"{letter_label}. {_safe_text(name)}",
                heading_style,
            ))
            flowables.append(Spacer(1, 3 * mm))

            # Render blocks with alpha-numeric sub-section numbering
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            sub_counter = 0
            rendered = 0

            for block in blocks:
                btype = block.get("type", "")

                # Convert sub-headings to alpha-numeric style
                if btype == "heading" and block.get("level", 99) >= 2:
                    sub_counter += 1
                    heading_text = block.get("text", f"Sub-section {sub_counter}")
                    sub_heading_style = _ps(
                        f"WPH2_{idx}_{sub_counter}", brand=self.brand,
                        fontSize=12, fontName="Helvetica-Bold",
                        textColor=_hex(self.brand, "primary"),
                        spaceBefore=4, spaceAfter=2,
                    )
                    flowables.append(Paragraph(
                        f"{letter_label}-{sub_counter} {_safe_text(heading_text)}",
                        sub_heading_style,
                    ))
                    flowables.append(Spacer(1, 2 * mm))
                    rendered += 1
                    continue

                # Skip top-level headings (already rendered as section heading)
                if btype == "heading" and block.get("level", 99) <= 1:
                    continue

                # Paragraphs — use justified style
                if btype == "paragraph":
                    text = block.get("text", "")
                    if text.strip():
                        flowables.append(_safe_para(text, body_style))
                        flowables.append(Spacer(1, 2 * mm))
                        rendered += 1
                else:
                    # All other block types — delegate to base renderer
                    for fl in self.render_blocks([block]):
                        flowables.append(fl)
                        rendered += 1

                if rendered >= 100:
                    break

            # Generous spacing between sections
            flowables.append(Spacer(1, 10 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Override generate() for Letter page size and custom header/footer
    # ------------------------------------------------------------------

    def generate(self):
        """Generate the whitepaper PDF with Letter size and custom footer."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.extract_content()
        title = content.get("title", self.target_path.name.replace("-", " ").title())

        # Doc ID (optional)
        doc_ids_cfg = self.config.get("doc_ids", {})
        if doc_ids_cfg.get("enabled", True):
            from briefkit.doc_ids import get_or_assign_doc_id
            self.doc_id = get_or_assign_doc_id(
                self.target_path, self.level,
                title, config=self.config,
            )

        # Populate module-level state for header/footer
        _wp_state["brand"] = self.brand

        # Recalculate content width for Letter
        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        self.content_width = compute_content_width(letter, margins)

        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        doc = self._build_doc(
            pagesize=letter,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            subject="White Paper",
        )

        story = self.build_story(content)
        story = self._finalize_story(story)
        doc.build(
            story,
            onFirstPage=_wp_header_footer,
            onLaterPages=_wp_header_footer,
        )

        return self.output_path

    # ------------------------------------------------------------------
    # Suppress unused base section builders
    # ------------------------------------------------------------------

    def build_at_a_glance(self, *args, **kwargs) -> list:
        return []

    def build_executive_summary(self, *args, **kwargs) -> list:
        return []

    def build_cross_references(self, *args, **kwargs) -> list:
        return []

    def build_index(self, *args, **kwargs) -> list:
        return []

    def build_bibliography(self, *args, **kwargs) -> list:
        return []
