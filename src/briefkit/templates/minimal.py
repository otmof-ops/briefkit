# SPDX-FileCopyrightText: 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
# SPDX-License-Identifier: BSD-3-Clause
"""
briefkit.templates.minimal
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Stripped-down template — smallest possible output.

Build order:
  Title → TOC → Body → Bibliography

Key differences:
  - No cover page
  - No dashboard
  - No callout boxes
  - No classification banner
  - No back cover
  - No key terms index
  - No cross-references section
  - Page numbers in footer only (no header)
  - Single-pass, no decorative elements
"""

from __future__ import annotations

import functools

from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Spacer,
)

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
)
from briefkit.templates._helpers import should_skip


def _minimal_header_footer(canvas, doc, state):
    """Minimal footer: page number centered, no header."""
    b = _get_brand(state.get("brand"))
    canvas.saveState()
    page_width, page_height = doc.pagesize
    bottom = doc.bottomMargin - 6 * mm
    canvas.setFont(b.get("font_body", "Helvetica"), 7)
    canvas.setFillColorRGB(0.4, 0.4, 0.4)
    canvas.drawCentredString(page_width / 2, bottom + 1.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


class MinimalTemplate(BaseBriefingTemplate):
    """
    Minimal briefing template.

    Produces the smallest possible PDF: a title heading, table of contents,
    body content (one section per subsystem), and a bibliography.  No
    decorative elements, no cover, no branding.

    Useful for plain-text-style exports, draft documents, or when embedding
    briefkit output into a larger pipeline that adds its own chrome.
    """

    pdf_subject = "Minimal Briefing"
    design_page_size = "A4"
    supports_variants = False

    def build_story(self, content: dict) -> list:
        """
        Assemble the minimal story:
          Title heading, TOC, body sections, bibliography.
        """
        story = []
        title = content.get("title", self.target_path.name.replace("-", " ").title())

        # Title heading
        story.append(Paragraph(title, self.styles["STYLE_TITLE"]))
        story.append(Spacer(1, 4 * mm))

        # Optional subtitle line: date + doc ID
        caption_c = _hex(self.brand, "caption")
        meta_style = _ps(
            "MinimalMeta",
            brand=self.brand,
            fontSize=9,
            textColor=caption_c,
            alignment=1,
        )
        meta_parts = [self.date_str]
        if self.doc_id:
            meta_parts.append(self.doc_id)
        story.append(Paragraph(" | ".join(meta_parts), meta_style))
        story.append(Spacer(1, 6 * mm))

        cfg = self.config
        # Pre-build body and bibliography
        body_flowables = self._build_minimal_body(content)
        bib_flowables = [] if should_skip(cfg, "bibliography") else self._build_minimal_bibliography(content)

        # TOC
        toc_entries = []
        for i, sub in enumerate(content.get("subsystems", []), 1):
            toc_entries.append((1, f"{i}. {sub.get('name', f'Section {i}')}"))
        if bib_flowables:
            toc_entries.append((1, "Bibliography"))

        if toc_entries and not should_skip(cfg, "toc"):
            story.append(_safe_para("Contents", self.styles["STYLE_H2"]))
            story.append(Spacer(1, 2 * mm))
            story.extend(build_toc(toc_entries, brand=self.brand, content_width=self.content_width))
            story.append(PageBreak())

        # Body
        story.extend(body_flowables)

        # Bibliography
        if bib_flowables:
            story.append(PageBreak())
            story.extend(bib_flowables)

        return story

    # ------------------------------------------------------------------
    # Minimal body
    # ------------------------------------------------------------------

    def _build_minimal_body(self, content: dict) -> list:
        """
        Render each subsystem as a numbered section.

        No callout boxes, no dashboards, no decorative elements.
        Plain paragraph, table, list, code, and heading rendering only.
        """
        flowables = []
        subsystems = content.get("subsystems", [])

        if not subsystems:
            overview = content.get("overview", "")
            if overview:
                for block in parse_markdown(overview)[:30]:
                    flowables.extend(self.render_blocks([block]))
            return flowables

        for idx, sub in enumerate(subsystems, 1):
            flowables.append(Paragraph(f"{idx}. {sub['name']}", self.styles["STYLE_H1"]))
            flowables.append(Spacer(1, 3 * mm))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            limit = self.body_block_limit()
            rendered = 0
            for block in blocks:
                # Skip heading level 1 (already used as section title)
                if block["type"] == "heading" and block["level"] == 1:
                    continue
                # Render blockquotes as plain paragraphs (no callout boxes)
                if block["type"] == "blockquote":
                    text = block.get("text", "")
                    if text:
                        quote_style = _ps(
                            "MinimalQuote",
                            brand=self.brand,
                            fontSize=10,
                            textColor=_hex(self.brand, "body_text"),
                            leading=14,
                            leftIndent=16,
                            fontName=self.brand.get("font_caption", "Helvetica-Oblique"),
                        )
                        flowables.append(Paragraph(f"\u201c{text}\u201d", quote_style))
                    continue

                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
                if limit and rendered >= limit:
                    break

            flowables.append(Spacer(1, 6 * mm))

        # Brilliance
        brilliance = content.get("brilliance_summary", "")
        if brilliance:
            flowables.append(Paragraph("Notes", self.styles["STYLE_H1"]))
            flowables.append(Spacer(1, 3 * mm))
            for block in parse_markdown(brilliance)[:15]:
                if block["type"] not in ("blockquote",):
                    flowables.extend(self.render_blocks([block]))

        return flowables

    # ------------------------------------------------------------------
    # Minimal bibliography
    # ------------------------------------------------------------------

    def _build_minimal_bibliography(self, content: dict) -> list:
        """
        Render bibliography as a plain numbered list.

        No section headers by type, no group labels.
        """
        sources = content.get("bibliography", [])
        if not sources:
            return []

        flowables = []
        flowables.append(Paragraph("Bibliography", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        body_c = _hex(self.brand, "body_text")
        ref_style = _ps(
            "MinimalRef",
            brand=self.brand,
            fontSize=9,
            textColor=body_c,
            leading=13,
            leftIndent=14,
            firstLineIndent=-14,
            spaceAfter=3,
        )

        def _sort_key(src):
            return (src.get("authors") or "").lower()

        for i, src in enumerate(sorted(sources, key=_sort_key), 1):
            authors = src.get("authors", "") or ""
            year = src.get("year", "") or ""
            title_ = src.get("title", "") or ""

            if authors and title_:
                entry = f"{i}. {authors} ({year}). {title_}."
            elif title_:
                entry = f"{i}. {title_} ({year})." if year else f"{i}. {title_}."
            elif authors:
                entry = f"{i}. {authors} ({year})."
            else:
                continue

            doi = src.get("doi", "")
            if doi:
                entry += f" DOI: {doi}"

            flowables.append(Paragraph(entry, ref_style))

        return flowables

    def prepare(self, content: dict) -> None:
        self.hf_ctx["brand"] = self.brand

    def header_footer(self, content: dict):
        callback = functools.partial(_minimal_header_footer, state=self.hf_ctx)
        return callback, callback

    # ------------------------------------------------------------------
    # Suppress all unused base section builders
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
