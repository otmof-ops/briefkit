"""
briefkit.templates.memo
~~~~~~~~~~~~~~~~~~~~~~~
Memorandum template — grounded in Oregon DEQ Memo format.

Build order:
  "MEMORANDUM" title → horizontal rule → metadata block →
  horizontal rule → body paragraphs → closing

Key differences:
  - No cover page, no TOC, no dashboard, no bibliography, no back cover
  - No header or footer (memo is self-contained)
  - No section headings in body (flat prose)
  - Wider margins (30mm left, 25mm right)
  - All black text, no brand colors in body
  - Single page target
"""

from __future__ import annotations

from reportlab.lib.colors import HexColor, black
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from briefkit.extractor import parse_markdown
from briefkit.generator import BaseBriefingTemplate
from briefkit.styles import (
    _ps,
    _safe_para,
    _safe_text,
)

_GREY_LABEL = HexColor("#666666")


class MemoTemplate(BaseBriefingTemplate):
    """
    Memorandum template.

    Produces a single-page memo with title, metadata block, body
    paragraphs, and closing. No headers, footers, or section headings.
    Wider margins matching standard memo layout conventions.
    """

    pdf_subject = "Memo"
    design_page_size = "Letter"
    margin_overrides_mm = {"left": 30, "right": 25}
    supports_variants = False

    def build_story(self, content: dict) -> list:
        """
        Assemble the memo story:
          Title, rule, metadata, rule, body, closing.
        """
        story: list = []
        b = self.brand
        org = b.get("org", "")
        project = self.config.get("project", {})
        title = content.get("title", "")
        overview = content.get("overview", "")

        # Derive "To" from first line of overview
        to_field = "All Staff"
        if overview:
            first_line = overview.strip().split("\n")[0].strip()
            if len(first_line) < 80:
                to_field = first_line

        from_field = org or project.get("name", "")

        # ---- Styles ----
        title_style = _ps(
            "MemoTitle",
            brand=b,
            fontSize=14,
            textColor=black,
            fontName=self.brand.get("font_heading", "Helvetica-Bold"),
            spaceAfter=2,
        )
        body_style = _ps(
            "MemoBody",
            brand=b,
            fontSize=10,
            textColor=black,
            leading=14,
            spaceAfter=6,
        )
        closing_style = _ps(
            "MemoClosing",
            brand=b,
            fontSize=10,
            textColor=black,
            fontName=self.brand.get("font_caption", "Helvetica-Oblique"),
            spaceBefore=12,
        )

        # ================================================================
        # MEMORANDUM title
        # ================================================================
        story.append(Paragraph("MEMORANDUM", title_style))
        story.append(Spacer(1, 2 * mm))

        # Horizontal rule
        story.append(self._rule())
        story.append(Spacer(1, 4 * mm))

        # ================================================================
        # Metadata block — label:value pairs (not a table)
        # ================================================================
        meta_pairs = [
            ("Date:", self.date_str, False),
            ("To:", to_field, False),
            ("From:", from_field, False),
            ("Subject:", _safe_text(title), True),
        ]
        for label, value, bold_value in meta_pairs:
            line_text = f'<font color="#666666"><b>{label}</b></font>&nbsp;&nbsp;&nbsp;{_safe_text(value)}'
            if bold_value:
                line_text = f'<font color="#666666"><b>{label}</b></font>&nbsp;&nbsp;&nbsp;<b>{_safe_text(value)}</b>'
            # Use body_style as base but with the leading from label_style
            meta_style = _ps(
                f"MemoMeta_{label}",
                brand=b,
                fontSize=10,
                textColor=black,
                leading=16,
            )
            story.append(_safe_para(line_text, meta_style))

        story.append(Spacer(1, 2 * mm))

        # Horizontal rule
        story.append(self._rule())
        story.append(Spacer(1, 6 * mm))

        # ================================================================
        # Body — flat prose, no section headings
        # ================================================================

        # Overview paragraphs (skip first line if used as "To")
        if overview:
            ov_lines = overview.strip().split("\n")
            # If first line was used as "To", start from second line
            body_text = "\n".join(ov_lines[1:]).strip() if len(ov_lines) > 1 else ""
            if body_text:
                for block in parse_markdown(body_text)[:20]:
                    if block.get("type") == "heading":
                        continue
                    story.extend(self._render_flat([block], body_style))

        # Subsystem content — flat (skip headings)
        for sub in content.get("subsystems", []):
            blocks = sub.get("blocks") or parse_markdown(
                sub.get("content", ""),
            )
            limit = self.body_block_limit()
            rendered = 0
            for block in blocks:
                btype = block.get("type", "")
                if btype == "heading":
                    continue
                story.extend(self._render_flat([block], body_style))
                rendered += 1
                if limit and rendered >= limit:
                    break

        # ================================================================
        # Closing
        # ================================================================
        if org:
            story.append(Spacer(1, 6 * mm))
            story.append(Paragraph(org, closing_style))

        return story

    def _rule(self) -> Table:
        """Build a 1pt black horizontal rule spanning content width."""
        rule = Table([[""]], colWidths=[self.content_width], rowHeights=[1])
        rule.setStyle(
            TableStyle(
                [
                    ("LINEABOVE", (0, 0), (-1, -1), 1, black),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return rule

    def _render_flat(self, blocks: list[dict], body_style) -> list:
        """
        Render blocks but force paragraph style to body_style
        (no heading styles). Tables and lists pass through normally.
        """
        flowables: list = []
        for block in blocks:
            btype = block.get("type", "")
            if btype == "paragraph":
                text = block.get("text", "").strip()
                if text:
                    flowables.append(_safe_para(text, body_style))
            elif btype in ("table", "list_item", "code", "blockquote", "rule"):
                flowables.extend(self.render_blocks([block]))
        return flowables

    def header_footer(self, content: dict):
        """A memo is self-contained: no header, no footer."""
        return None, None

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

    def build_back_cover(self) -> list:
        return []
