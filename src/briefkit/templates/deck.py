# SPDX-FileCopyrightText: 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
# SPDX-License-Identifier: BSD-3-Clause
"""
briefkit.templates.deck
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Deck template — landscape slide-deck format, one subsystem per slide.

Grounded in Sequoia Capital Pitch Deck (13pg, landscape, FranklinGothic).

Build order:
  Cover slide → Content slides (reordered by Sequoia flow) → Closing slide

Design norms:
  - Landscape orientation (swap width/height)
  - Each subsystem = one slide (one page)
  - Title bar: full-width band at top, primary background, white text
  - Body: large text (14pt body, 18pt first paragraph), max 4-5 bullets
  - Cover: full primary background, org top-left, title centered, subtitle
  - Closing slide: "Thank You" / org / URL / date
  - Content reordered by Sequoia keyword matching
  - NO TOC, NO bibliography, NO back cover
  - Footer: org bottom-left, slide number bottom-right
"""

from __future__ import annotations

import re

from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
)
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
    _safe_text,
)

# ---------------------------------------------------------------------------
# Page size helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Sequoia flow ordering
# ---------------------------------------------------------------------------

_SEQUOIA_PATTERNS: list[tuple[str, int]] = [
    (r"purpose|mission|vision", 1),
    (r"problem|challenge|pain", 2),
    (r"solution|product|service", 3),
    (r"market|opportunity|size", 4),
    (r"competition|landscape|differentiat", 5),
    (r"model|revenue|pricing", 6),
    (r"team|people|founder", 7),
    (r"financial|projections|traction", 8),
]


def _sequoia_sort_key(sub: dict, original_idx: int) -> tuple[int, int]:
    """Return a sort key (sequoia_rank, original_index) for ordering."""
    name = sub.get("name", "").lower()
    for pattern, rank in _SEQUOIA_PATTERNS:
        if re.search(pattern, name):
            return (rank, original_idx)
    # Unmatched subsystems sort after matched ones, preserving order
    return (100 + original_idx, original_idx)


def _reorder_subsystems(subsystems: list[dict]) -> list[dict]:
    """Reorder subsystems by Sequoia flow keyword matching."""
    indexed = [(sub, idx) for idx, sub in enumerate(subsystems)]
    indexed.sort(key=lambda pair: _sequoia_sort_key(pair[0], pair[1]))
    return [sub for sub, _idx in indexed]


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class DeckTemplate(BaseBriefingTemplate):
    """
    Deck template.

    Produces a landscape slide-deck PDF with one subsystem per slide,
    full-width title bars, large body text, and Sequoia-flow content
    ordering. Suitable for pitch decks, presentations, and briefing
    slide sets.
    """

    pdf_subject = "Deck"
    orientation_lock = "landscape"
    design_margins_mm = {"top": 15, "bottom": 15, "left": 25, "right": 25}
    supports_variants = False

    # ------------------------------------------------------------------
    # Single slide builder
    # ------------------------------------------------------------------

    def _build_slide(self, sub: dict, slide_num: int) -> list:
        """Build a single content slide for one subsystem."""
        flowables: list = []
        primary = _hex(self.brand, "primary")
        body_c = _hex(self.brand, "body_text")
        name = sub.get("name", f"Slide {slide_num}")

        # Title bar — full-width band
        title_style = _ps(
            f"DKSlideTitle{slide_num}",
            brand=self.brand,
            fontSize=20,
            fontName=self.brand.get("font_heading", "Helvetica-Bold"),
            textColor=white,
            alignment=0,
            spaceBefore=0,
            spaceAfter=0,
        )
        title_para = Paragraph(_safe_text(name), title_style)

        title_bar = Table(
            [[title_para]],
            colWidths=[self.content_width],
            rowHeights=[14 * mm],
        )
        title_bar.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), primary),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 15),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 15),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        flowables.append(title_bar)
        flowables.append(Spacer(1, 8 * mm))

        # Body content — large text, limited bullets
        blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
        rendered = 0
        is_first_para = True

        for block in blocks:
            if rendered >= 5:
                break

            btype = block.get("type", "")

            # Skip top-level headings
            if btype == "heading" and block.get("level", 1) <= 2:
                continue

            if btype == "paragraph":
                text = block.get("text", "")
                if not text.strip():
                    continue
                fs = 18 if is_first_para else 14
                para_style = _ps(
                    f"DKBody{slide_num}_{rendered}",
                    brand=self.brand,
                    fontSize=fs,
                    textColor=body_c,
                    leading=fs + 6,
                    spaceAfter=6,
                    fontName=self.brand.get("font_body", "Helvetica"),
                )
                flowables.append(_safe_para(text, para_style, True))
                is_first_para = False
                rendered += 1
                continue

            if btype == "list":
                items = block.get("items", [])
                for item in items[: 5 - rendered]:
                    item_text = item if isinstance(item, str) else item.get("text", "")
                    bullet_style = _ps(
                        f"DKBullet{slide_num}_{rendered}",
                        brand=self.brand,
                        fontSize=14,
                        textColor=body_c,
                        leading=20,
                        spaceAfter=4,
                        leftIndent=10,
                        bulletIndent=0,
                        fontName=self.brand.get("font_body", "Helvetica"),
                    )
                    flowables.append(
                        _safe_para(
                            f"\u2022  {_safe_text(str(item_text))}",
                            bullet_style,
                        )
                    )
                    rendered += 1
                    is_first_para = False
                continue

            if btype == "table":
                flowables.extend(self._render_slide_table(block, slide_num))
                rendered += 1
                is_first_para = False
                continue

            # Other block types — delegate to base
            for fl in self.render_blocks([block]):
                flowables.append(fl)
                rendered += 1
                is_first_para = False
                if rendered >= 5:
                    break

        return flowables

    # ------------------------------------------------------------------
    # Slide table renderer
    # ------------------------------------------------------------------

    def _render_slide_table(self, block: dict, slide_num: int) -> list:
        """Render a table at full landscape width."""
        flowables: list = []
        rows = block.get("rows", [])
        headers = block.get("headers", [])
        if not rows and not headers:
            return flowables

        secondary = _hex(self.brand, "secondary")
        body_c = _hex(self.brand, "body_text")

        header_style = _ps(
            f"DKTblH{slide_num}",
            brand=self.brand,
            fontSize=10,
            fontName=self.brand.get("font_heading", "Helvetica-Bold"),
            textColor=white,
            alignment=0,
        )
        cell_style = _ps(
            f"DKTblC{slide_num}",
            brand=self.brand,
            fontSize=10,
            textColor=body_c,
            alignment=0,
        )

        data: list[list] = []
        if headers:
            data.append([_safe_para(str(h), header_style, True) for h in headers])

        for row in rows:
            cells = row if isinstance(row, list) else row.get("cells", [])
            data.append([_safe_para(str(c), cell_style, True) for c in cells])

        if not data:
            return flowables

        n_cols = max(len(r) for r in data)
        col_w = self.content_width / max(n_cols, 1)
        tbl = Table(data, colWidths=[col_w] * n_cols)

        style_cmds: list = [
            ("GRID", (0, 0), (-1, -1), 0.5, _hex(self.brand, "rule")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        if headers:
            style_cmds.append(
                ("BACKGROUND", (0, 0), (-1, 0), secondary),
            )
        tbl.setStyle(TableStyle(style_cmds))
        flowables.append(tbl)

        return flowables

    # ------------------------------------------------------------------
    # Closing slide
    # ------------------------------------------------------------------

    def _build_closing_slide(self, content: dict) -> list:
        """Build the closing slide with thank you / org / URL / date."""
        flowables: list = []
        org = self.brand.get("org", "")
        url = self.brand.get("url", "")
        primary = _hex(self.brand, "primary")
        caption_c = _hex(self.brand, "caption")

        # Check guide_content for closing text
        guide = content.get("guide_content", "")
        closing_text = "Thank You"
        if guide:
            lower_guide = guide.lower()
            for marker in ("thank", "closing", "conclusion"):
                idx = lower_guide.find(marker)
                if idx >= 0:
                    snippet = guide[idx : idx + 100].split("\n")[0].strip()
                    if snippet:
                        closing_text = snippet
                    break

        flowables.append(Spacer(1, 40 * mm))

        # Closing text
        close_style = _ps(
            "DKClosing",
            brand=self.brand,
            fontSize=28,
            fontName=self.brand.get("font_heading", "Helvetica-Bold"),
            textColor=primary,
            alignment=1,
            spaceAfter=10,
        )
        flowables.append(_safe_para(_safe_text(closing_text), close_style))
        flowables.append(Spacer(1, 10 * mm))

        # Org name
        if org:
            org_style = _ps(
                "DKCloseOrg",
                brand=self.brand,
                fontSize=16,
                fontName=self.brand.get("font_heading", "Helvetica-Bold"),
                textColor=primary,
                alignment=1,
                spaceAfter=4,
            )
            flowables.append(_safe_para(_safe_text(org), org_style))

        # URL
        if url:
            url_style = _ps(
                "DKCloseURL",
                brand=self.brand,
                fontSize=12,
                textColor=caption_c,
                alignment=1,
                spaceAfter=4,
            )
            flowables.append(_safe_para(_safe_text(url), url_style))

        # Date
        date_style = _ps(
            "DKCloseDate",
            brand=self.brand,
            fontSize=11,
            textColor=caption_c,
            alignment=1,
        )
        flowables.append(_safe_para(self.date_str, date_style))

        return flowables

    def prepare(self, content: dict) -> None:
        overview = content.get("overview", "")
        subtitle = ""
        if overview:
            first_line = overview.strip().split("\n")[0]
            for sep in (".", "!", "?"):
                idx = first_line.find(sep)
                if idx > 0:
                    first_line = first_line[: idx + 1]
                    break
            subtitle = first_line[:200]
        self.hf_ctx["title"] = content.get("title", self.target_path.name.replace("-", " ").title())
        self.hf_ctx["subtitle"] = subtitle

    def build_story(self, content: dict) -> list:
        """Cover slide (drawn by the page callback), one slide per subsystem in Sequoia order, closing slide."""
        story: list = [Spacer(1, self.geometry.frame_height - 10 * mm), PageBreak()]
        ordered = _reorder_subsystems(content.get("subsystems", []))
        for slide_idx, sub in enumerate(ordered, 2):
            story.extend(self._build_slide(sub, slide_idx))
            story.append(PageBreak())
        story.extend(self._build_closing_slide(content))
        return story

    def header_footer(self, content: dict):
        title = self.hf_ctx.get("title", "")
        subtitle = self.hf_ctx.get("subtitle", "")
        primary_color = HexColor(self.brand.get("primary", "#1B2A4A"))
        org = self.brand.get("org", "")
        caption_c = self.brand.get("caption", "#999999")
        left_m = self.geometry.margins.left
        right_m = self.geometry.margins.right
        body_font = self.brand.get("font_body", "Helvetica")
        heading_font = self.brand.get("font_heading", "Helvetica-Bold")

        def _cover(canvas, doc_inner):
            """Draw the cover slide — full primary background."""
            canvas.saveState()
            w, h = doc_inner.pagesize

            # Full primary background
            canvas.setFillColor(primary_color)
            canvas.rect(0, 0, w, h, stroke=0, fill=1)

            # Org name top-left
            if org:
                canvas.setFillColor(white)
                canvas.setFont(body_font, 12)
                canvas.drawString(left_m, h - 20 * mm, org)

            # Title centered
            canvas.setFillColor(white)
            canvas.setFont(heading_font, 36)
            title_y = h * 0.55
            canvas.drawCentredString(w / 2, title_y, title[:80])

            # Subtitle
            if subtitle:
                canvas.setFont(body_font, 16)
                canvas.drawCentredString(w / 2, title_y - 28, subtitle[:120])

            canvas.restoreState()

        def _slide_footer(canvas, doc_inner):
            """Footer: org bottom-left, slide number bottom-right."""
            canvas.saveState()
            w = doc_inner.pagesize[0]
            y = 8 * mm

            canvas.setFont(body_font, 8)
            canvas.setFillColor(HexColor(caption_c))

            # Org name bottom-left
            if org:
                canvas.drawString(left_m, y, org)

            # Slide number bottom-right
            page_num = canvas.getPageNumber()
            canvas.drawRightString(w - right_m, y, str(page_num))

            canvas.restoreState()

        return _cover, _slide_footer

    # ------------------------------------------------------------------
    # Suppress unused base section builders
    # ------------------------------------------------------------------

    def build_body(self, content: dict) -> list:
        return []

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
