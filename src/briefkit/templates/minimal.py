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

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
    build_toc,
)
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
)


def _minimal_header_footer(canvas, doc):
    """Minimal footer: page number centered, no header."""
    canvas.saveState()
    page_width, page_height = doc.pagesize
    bottom = doc.bottomMargin - 6 * mm
    canvas.setFont("Helvetica", 7)
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
            "MinimalMeta", brand=self.brand,
            fontSize=9, textColor=caption_c, alignment=1,
        )
        meta_parts = [self.date_str]
        if self.doc_id:
            meta_parts.append(self.doc_id)
        story.append(Paragraph(" | ".join(meta_parts), meta_style))
        story.append(Spacer(1, 6 * mm))

        # Pre-build body and bibliography
        body_flowables = self._build_minimal_body(content)
        bib_flowables  = self._build_minimal_bibliography(content)

        # TOC
        toc_entries = []
        for i, sub in enumerate(content.get("subsystems", []), 1):
            toc_entries.append((1, f"{i}. {sub.get('name', f'Section {i}')}"))
        if bib_flowables:
            toc_entries.append((1, "Bibliography"))

        if toc_entries:
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
            flowables.append(Paragraph(
                f"{idx}. {sub['name']}", self.styles["STYLE_H1"]
            ))
            flowables.append(Spacer(1, 3 * mm))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
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
                            "MinimalQuote", brand=self.brand,
                            fontSize=10, textColor=_hex(self.brand, "body_text"),
                            leading=14, leftIndent=16,
                            fontName="Helvetica-Oblique",
                        )
                        flowables.append(Paragraph(f"\u201c{text}\u201d", quote_style))
                    continue

                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
                if rendered >= 80:
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
            "MinimalRef", brand=self.brand,
            fontSize=9, textColor=body_c, leading=13,
            leftIndent=14, firstLineIndent=-14, spaceAfter=3,
        )

        def _sort_key(src):
            return (src.get("authors") or "").lower()

        for i, src in enumerate(sorted(sources, key=_sort_key), 1):
            authors = src.get("authors", "") or ""
            year    = src.get("year", "") or ""
            title_  = src.get("title", "") or ""

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

    # ------------------------------------------------------------------
    # Override generate() to use minimal header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """
        Generate the minimal PDF with page-number-only footer.
        """
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.extract_content()

        # Doc ID (optional)
        doc_ids_cfg = self.config.get("doc_ids", {})
        if doc_ids_cfg.get("enabled", True):
            from briefkit.doc_ids import get_or_assign_doc_id
            self.doc_id = get_or_assign_doc_id(
                self.target_path, self.level,
                content.get("title", ""), config=self.config,
            )

        # Header/footer state (minimal: only date, no section name)

        layout   = self.config.get("layout", {})
        margins  = layout.get("margins", {})
        top_m    = margins.get("top",    25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m   = margins.get("left",   20) * mm
        right_m  = margins.get("right",  20) * mm

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=content.get("title", "Briefing"),
            author=self.brand.get("org", "briefkit"),
            subject="Minimal Briefing",
            creator="briefkit",
        )

        story = self.build_story(content)
        doc.build(
            story,
            onFirstPage=_minimal_header_footer,
            onLaterPages=_minimal_header_footer,
        )

        return self.output_path

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
