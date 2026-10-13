# SPDX-FileCopyrightText: 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
# SPDX-License-Identifier: BSD-3-Clause
"""
briefkit.templates.witness
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Legal witness statement template — clean, formal, no decorative elements.

Build order:
  Header block → Body (all sections rendered sequentially) → Execution block

Key differences:
  - No cover page, no dashboard, no callout boxes
  - Formal header with document reference, matter, deponent details
  - Body content rendered as continuous legal prose with paragraph numbering
  - Tables rendered cleanly (definitions, vehicle particulars, CV schedule)
  - Serif font (Times) for body, sans-serif for headings
  - Crimson/dark red accent line — legal style
  - Page numbers in footer with doc reference
  - No "Executive Summary", "At a Glance", or other briefing chrome
"""

from __future__ import annotations

import functools
import html

from reportlab.lib.colors import HexColor
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
    _get_brand,
    _hex,
    _ps,
)


def _decode_html_entities(text: str) -> str:
    """Decode HTML entities like &emsp; &ensp; &middot; etc."""
    if not text:
        return text
    return html.unescape(text)


def _witness_header_footer(canvas, doc, state):
    """Legal-style header/footer: thin rule, doc ref, page number."""
    b = _get_brand(state.get("brand"))
    canvas.saveState()
    pw, ph = doc.pagesize
    lm = doc.leftMargin
    rm = doc.rightMargin

    # Header: thin crimson rule
    canvas.setStrokeColor(HexColor("#8B0000"))
    canvas.setLineWidth(0.75)
    canvas.line(lm, ph - doc.topMargin + 8 * mm, pw - rm, ph - doc.topMargin + 8 * mm)

    # Header right: doc title
    canvas.setFont(b.get("font_body", "Helvetica"), 7)
    canvas.setFillColor(HexColor("#333333"))
    title = state.get("title", "Witness Statement")
    canvas.drawRightString(pw - rm, ph - doc.topMargin + 10 * mm, title)

    # Footer: page number center, doc ref right
    bottom_y = doc.bottomMargin - 6 * mm
    canvas.setFont(b.get("font_body", "Helvetica"), 7)
    canvas.setFillColor(HexColor("#666666"))
    canvas.drawCentredString(pw / 2, bottom_y + 1.5 * mm, f"Page {doc.page}")

    doc_ref = state.get("doc_ref", "")
    if doc_ref:
        canvas.drawRightString(pw - rm, bottom_y + 1.5 * mm, doc_ref)

    # Footer rule
    canvas.setStrokeColor(HexColor("#CCCCCC"))
    canvas.setLineWidth(0.5)
    canvas.line(lm, bottom_y + 5 * mm, pw - rm, bottom_y + 5 * mm)

    canvas.restoreState()


class WitnessTemplate(BaseBriefingTemplate):
    """
    Legal witness statement template.

    Renders all numbered markdown files as continuous legal prose.
    No briefing chrome. Clean, formal, court-ready.
    """

    pdf_subject = "Witness Statement"
    design_page_size = "A4"
    design_margins_mm = {"top": 28, "bottom": 22, "left": 22, "right": 22}
    supports_variants = False
    assigns_doc_id = False

    name = "witness"

    def build_story(self, content: dict) -> list:
        story = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")

        title = content.get("title", "Witness Statement")
        overview = content.get("overview", "")

        # --- Title ---
        title_style = _ps(
            "WitnessTitle",
            brand=b,
            fontSize=18,
            textColor=primary,
            fontName=self.brand.get("font_heading", "Helvetica-Bold"),
            alignment=1,
            spaceAfter=4,
        )
        story.append(Spacer(1, 10 * mm))
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 3 * mm))

        # Subtitle / overview
        if overview:
            sub_style = _ps(
                "WitnessSub",
                brand=b,
                fontSize=10,
                textColor=body_c,
                fontName=self.brand.get("font_body", "Helvetica"),
                alignment=1,
                spaceAfter=6,
                leading=14,
            )
            story.append(Paragraph(overview, sub_style))

        # Thin rule
        rule_data = [[""]]
        rule = Table(rule_data, colWidths=[self.content_width])
        rule.setStyle(
            TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, -1), 1, HexColor("#8B0000")),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(rule)
        story.append(Spacer(1, 6 * mm))

        # --- Preamble (00-preamble.md content) ---
        subsystems = content.get("subsystems", [])

        # --- Body: render every subsystem ---
        for idx, sub in enumerate(subsystems):
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))

            # Render all blocks — no limit, no separate section heading
            # (the markdown already contains ## headings which render as H2)
            for block in blocks:
                # Decode HTML entities in all text fields
                if "text" in block:
                    block["text"] = _decode_html_entities(block["text"])

                # Skip level-1 headings that duplicate the file-derived name
                if block["type"] == "heading" and block.get("level") == 1:
                    continue
                # Render heading level 2 as section heading
                if block["type"] == "heading" and block.get("level") == 2:
                    sh_style = _ps(
                        "WitnessH2",
                        brand=b,
                        fontSize=13,
                        textColor=primary,
                        fontName=self.brand.get("font_heading", "Helvetica-Bold"),
                        spaceBefore=10,
                        spaceAfter=4,
                    )
                    story.append(Paragraph(block.get("text", ""), sh_style))
                    continue
                # Render heading level 3
                if block["type"] == "heading" and block.get("level") == 3:
                    sh3_style = _ps(
                        "WitnessH3",
                        brand=b,
                        fontSize=11,
                        textColor=body_c,
                        fontName=self.brand.get("font_heading", "Helvetica-Bold"),
                        spaceBefore=6,
                        spaceAfter=2,
                    )
                    story.append(Paragraph(block.get("text", ""), sh3_style))
                    continue
                # Render heading level 4+
                if block["type"] == "heading" and block.get("level", 4) >= 4:
                    sh4_style = _ps(
                        "WitnessH4",
                        brand=b,
                        fontSize=10,
                        textColor=body_c,
                        fontName=self.brand.get("font_heading", "Helvetica-Bold"),
                        spaceBefore=4,
                        spaceAfter=2,
                    )
                    story.append(Paragraph(block.get("text", ""), sh4_style))
                    continue
                # Blockquotes as indented formal text
                if block["type"] == "blockquote":
                    text = block.get("text", "")
                    if text:
                        text = _decode_html_entities(text)
                        bq_style = _ps(
                            "WitnessBlockquote",
                            brand=b,
                            fontSize=9.5,
                            textColor=body_c,
                            leading=13,
                            leftIndent=20,
                            rightIndent=20,
                            fontName=self.brand.get("font_caption", "Helvetica-Oblique"),
                            spaceBefore=4,
                            spaceAfter=4,
                        )
                        story.append(Paragraph(text, bq_style))
                    continue

                for fl in self.render_blocks([block]):
                    story.append(fl)

            story.append(Spacer(1, 4 * mm))

        return story

    def extract_content(self) -> dict:
        """Force level 3 extraction — doc_set level with numbered files."""
        from briefkit.extractor import extract_content as _ec

        self.content = _ec(self.target_path, level=3, config=self.config)
        return self.content

    def prepare(self, content: dict) -> None:
        self.hf_ctx["title"] = content.get("title", "Witness Statement")
        self.hf_ctx["doc_ref"] = self.config.get("project", {}).get("doc_id_format", "")
        self.hf_ctx["brand"] = self.brand

    def header_footer(self, content: dict):
        callback = functools.partial(_witness_header_footer, state=self.hf_ctx)
        return callback, callback

    def build_at_a_glance(self, *a, **kw):
        return []

    def build_executive_summary(self, *a, **kw):
        return []

    def build_cross_references(self, *a, **kw):
        return []

    def build_index(self, *a, **kw):
        return []

    def build_bibliography(self, *a, **kw):
        return []

    def build_back_cover(self):
        return []
