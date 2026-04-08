"""
briefkit.templates.book
~~~~~~~~~~~~~~~~~~~~~~~~
Long-form book template.

Build order:
  Half Title → Title Page → Copyright Page → TOC → Preface →
  Chapters (each starting on a new page) → Glossary →
  Bibliography → Index → Colophon

Key differences:
  - Front matter uses roman numeral page numbering convention
    (simulated via section labels — ReportLab doesn't support
    mid-document numbering resets without PageTemplates, which
    would require a multi-pass build; we note it in the TOC)
  - Each chapter starts on a new page
  - Running headers show chapter title
  - Preface sourced from README overview or preface.md
  - Glossary from terms dict
"""

from __future__ import annotations

from reportlab.lib.pagesizes import A3, A4, legal, letter
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer

from briefkit.elements.header_footer import make_header_footer
from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
    build_toc,
)
from briefkit.styles import (
    CONTENT_WIDTH,
    _hex,
    _ps,
    _safe_para,
)


class BookTemplate(BaseBriefingTemplate):
    """
    Long-form book template.

    Structured as a proper book with front matter (half-title, title page,
    copyright), body chapters, back matter (glossary, bibliography, index,
    colophon).
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the complete book story.
        """
        story = []

        title = content.get("title", self.target_path.name.replace("-", " ").title())
        b     = self.brand
        primary   = _hex(b, "primary")
        secondary = _hex(b, "secondary")
        caption_c = _hex(b, "caption")
        org = b.get("org", "")
        year = self.date.year
        copyright_str = b.get("copyright", f"\u00a9 {year}")

        # --- Half-title page ---
        cw = getattr(self, 'content_width', CONTENT_WIDTH)
        ht_size = 24
        while stringWidth(title, "Helvetica-Bold", ht_size) > cw * 0.85 and ht_size > 16:
            ht_size -= 1
        half_title_style = _ps(
            "HalfTitle", brand=b,
            fontSize=ht_size, textColor=primary,
            fontName="Helvetica-Bold", alignment=1,
        )
        story.append(Spacer(1, 80 * mm))
        story.append(Paragraph(title, half_title_style))
        story.append(PageBreak())

        # --- Full title page ---
        ft_size = 32
        while stringWidth(title, "Helvetica-Bold", ft_size) > cw * 0.80 and ft_size > 18:
            ft_size -= 1
        title_style = _ps(
            "BookTitle", brand=b,
            fontSize=ft_size, textColor=primary,
            fontName="Helvetica-Bold", alignment=1,
            leading=ft_size + 8,
            spaceAfter=6 * mm,
        )
        subtitle_text = self.config.get("project", {}).get("tagline", "")
        sub_style = _ps(
            "BookSubtitle", brand=b,
            fontSize=16, textColor=secondary,
            fontName="Helvetica-Oblique", alignment=1,
        )
        author_style = _ps(
            "BookAuthor", brand=b,
            fontSize=14, textColor=caption_c, alignment=1,
        )
        story.append(Spacer(1, 50 * mm))
        story.append(Paragraph(title, title_style))
        if subtitle_text:
            story.append(Paragraph(subtitle_text, sub_style))
        story.append(Spacer(1, 20 * mm))
        if org:
            story.append(Paragraph(org, author_style))
        story.append(Spacer(1, 30 * mm))
        story.append(Paragraph(str(year), author_style))
        story.append(PageBreak())

        # --- Copyright page ---
        cp_style = _ps(
            "CopyrightPage", brand=b,
            fontSize=9, textColor=caption_c, leading=14,
        )
        story.append(Spacer(1, 120 * mm))
        story.append(Paragraph(f"First published {year}", cp_style))
        story.append(Paragraph(copyright_str, cp_style))
        story.append(Paragraph(
            "All rights reserved. No part of this publication may be reproduced, "
            "stored in a retrieval system, or transmitted in any form or by any means, "
            "without the prior written permission of the publisher.",
            cp_style,
        ))
        story.append(Spacer(1, 10 * mm))
        if self.doc_id:
            story.append(Paragraph(f"Document ID: {self.doc_id}", cp_style))
        if b.get("url"):
            story.append(Paragraph(b["url"], cp_style))
        story.append(PageBreak())

        # Pre-build sections for dynamic TOC
        preface_flowables   = self._build_preface(content)
        chapters            = self._build_chapters(content)
        glossary_flowables  = self._build_glossary(content)
        bib_flowables       = self.build_bibliography(
            content.get("bibliography", []),
            source_type=content.get("metrics", {}).get("source_type", "ACADEMIC"),
        )
        index_flowables     = self._build_index(content)

        # --- TOC ---
        story.append(_safe_para("Contents", self.styles["STYLE_H1"]))
        story.append(Spacer(1, 2 * mm))

        toc_entries = [(1, "Preface")]
        for chapter_title, _ in chapters:
            toc_entries.append((1, chapter_title))
        if glossary_flowables:
            toc_entries.append((1, "Glossary"))
        if bib_flowables:
            toc_entries.append((1, "Bibliography"))
        if index_flowables:
            toc_entries.append((1, "Index"))

        story.extend(build_toc(toc_entries, brand=b, content_width=self.content_width))
        story.append(PageBreak())

        # --- Preface ---
        story.extend(preface_flowables)
        story.append(PageBreak())

        # --- Chapters (recto — each on new page) ---
        for chapter_title, chapter_flowables in chapters:
            # Update running header for this chapter
            if hasattr(self, '_hf_state'):
                self._hf_state["section"] = chapter_title

            # Wrap the chapter title with its first content flowable in a
            # KeepTogether block. Without this, a chapter whose first real
            # content is a large table (bigger than the remaining page space)
            # can orphan the H1 title on an otherwise-empty page: the H1's
            # keepWithNext chain breaks at the table's page break, stranding
            # the title alone above a sea of whitespace.
            title_para = Paragraph(chapter_title, self.styles["STYLE_H1"])
            if chapter_flowables:
                # Clear keepWithNext on the first content flowable before
                # wrapping — otherwise the KeepTogether inherits the chain,
                # tries to stay glued to a huge following table, and splits
                # anyway (stranding the H1 title alone on the previous page).
                first = chapter_flowables[0]
                if hasattr(first, "keepWithNext"):
                    first.keepWithNext = False
                story.append(KeepTogether(
                    [title_para, Spacer(1, 2 * mm), first]
                ))
                story.extend(chapter_flowables[1:])
            else:
                story.append(title_para)
                story.append(Spacer(1, 2 * mm))
            story.append(PageBreak())

        # Reset running header
        if hasattr(self, '_hf_state'):
            self._hf_state["section"] = content.get("title", "")

        # --- Back matter ---
        if glossary_flowables:
            story.extend(glossary_flowables)
            story.append(PageBreak())

        if bib_flowables:
            story.extend(bib_flowables)
            story.append(PageBreak())

        if index_flowables:
            story.extend(index_flowables)
            story.append(PageBreak())

        # --- Colophon ---
        story.extend(self._build_colophon(title, org, year, copyright_str))

        return story

    # ------------------------------------------------------------------
    # Preface
    # ------------------------------------------------------------------

    def _build_preface(self, content: dict) -> list:
        """
        Build the preface.  Sources:
          1. preface.md in target directory
          2. README.md overview (first 600 words)
          3. Synthesized from content metadata
        """
        preface_path = self.target_path / "preface.md"

        flowables = []
        flowables.append(Paragraph("Preface", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        if preface_path.exists():
            raw = preface_path.read_text(encoding="utf-8", errors="replace")
            for block in parse_markdown(raw)[:40]:
                flowables.extend(self.render_blocks([block]))
        else:
            overview = content.get("overview", "")
            orientation = content.get("orientation", "")
            title = content.get("title", "this work")

            if overview:
                # Use first ~600 words of overview
                words  = overview.split()
                excerpt = " ".join(words[:600])
                for block in parse_markdown(excerpt)[:20]:
                    flowables.extend(self.render_blocks([block]))
            elif orientation:
                for block in parse_markdown(orientation[:2000])[:20]:
                    flowables.extend(self.render_blocks([block]))
            else:
                subsystems = content.get("subsystems", [])
                flowables.append(Paragraph(
                    f"This volume presents a comprehensive treatment of {title}. "
                    f"It comprises {len(subsystems)} chapter(s), each addressing a "
                    f"distinct aspect of the subject matter.",
                    self.styles["STYLE_BODY"],
                ))

        return flowables

    # ------------------------------------------------------------------
    # Chapters
    # ------------------------------------------------------------------

    def _build_chapters(self, content: dict) -> list[tuple[str, list]]:
        """
        Build chapters — one per subsystem.

        Returns a list of (chapter_title, flowables) tuples.
        """
        subsystems = content.get("subsystems", [])
        chapters: list[tuple[str, list]] = []

        for sub in subsystems:
            chapter_title = sub.get("name", "Chapter")
            chap_flowables: list = []

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0

            # Use the first H1 heading from content as the chapter title
            # (preserves special characters and original formatting)
            for block in blocks:
                if block["type"] == "heading" and block["level"] == 1:
                    chapter_title = block["text"]
                    break

            for block in blocks:
                # Skip H1 headings — chapter title already rendered by build_story
                if block["type"] == "heading" and block["level"] == 1:
                    continue

                rendered_items = self.render_blocks([block])

                # Keep headings with the next content (prevent orphaned chapter titles)
                if block["type"] == "heading":
                    for fl in rendered_items:
                        fl.keepWithNext = True
                        chap_flowables.append(fl)
                else:
                    for fl in rendered_items:
                        chap_flowables.append(fl)

                rendered += len(rendered_items)

                # No flowable cap — render all content in chapter

            chapters.append((chapter_title, chap_flowables))

        return chapters

    # ------------------------------------------------------------------
    # Glossary
    # ------------------------------------------------------------------

    def _build_glossary(self, content: dict) -> list:
        """
        Build the glossary.  Sources:
          1. glossary.md in target directory (preferred — renders as prose)
          2. Extracted terms dict (fallback)
        """
        glossary_path = self.target_path / "glossary.md"
        if glossary_path.exists():
            raw = glossary_path.read_text(encoding="utf-8", errors="replace")
            flowables = []
            for block in parse_markdown(raw):
                flowables.extend(self.render_blocks([block]))
            return flowables

        terms = content.get("terms", {})
        if not terms:
            return []

        flowables = []
        flowables.append(Paragraph("Glossary", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))
        flowables.append(Paragraph(
            "Definitions of key technical terms used throughout this work.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 3 * mm))

        primary = _hex(self.brand, "primary")
        entry_style = _ps(
            "GlossaryEntry", brand=self.brand,
            fontSize=10, textColor=_hex(self.brand, "body_text"),
            leading=14, spaceAfter=4,
        )
        letter_style = _ps(
            "GlossaryLetter", brand=self.brand,
            fontName="Helvetica-Bold", fontSize=12,
            textColor=primary, spaceBefore=8, spaceAfter=2,
        )

        sorted_terms = sorted(terms.items(), key=lambda x: x[0].lower())
        current_letter = ""

        for term, defn in sorted_terms:
            first = term[0].upper() if term else ""
            if first != current_letter:
                current_letter = first
                flowables.append(Paragraph(first, letter_style))

            if defn:
                flowables.append(Paragraph(
                    f"<b>{term}</b>: {defn}", entry_style
                ))
            else:
                flowables.append(Paragraph(
                    f"<b>{term}</b>", entry_style
                ))

        return flowables

    # ------------------------------------------------------------------
    # Index
    # ------------------------------------------------------------------

    def _build_index(self, content: dict) -> list:
        """
        Build an alphabetical index using the same 2-column layout as
        BaseBriefingTemplate.build_index(), but labelled 'Index'.

        Suppressed when a glossary.md file exists (the glossary replaces
        the auto-generated index for book-template outputs).
        """
        glossary_path = self.target_path / "glossary.md"
        if glossary_path.exists():
            return []

        terms = content.get("terms", {})
        if not terms:
            return []
        return self.build_index(terms)

    # ------------------------------------------------------------------
    # Colophon
    # ------------------------------------------------------------------

    def _build_colophon(
        self, title: str, org: str, year: int, copyright_str: str
    ) -> list:
        """
        Build the colophon (final page: typesetting and production notes).
        """
        cp_style = _ps(
            "Colophon", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "caption"),
            leading=14, alignment=1,
        )
        flowables = []
        flowables.append(Spacer(1, 100 * mm))
        flowables.append(Paragraph(title, cp_style))
        if org:
            flowables.append(Paragraph(org, cp_style))
        flowables.append(Paragraph(copyright_str, cp_style))
        flowables.append(Paragraph(
            f"Typeset by briefkit on {self.date_str}.", cp_style
        ))
        return flowables

    # ------------------------------------------------------------------
    # Override generate() to suppress headers/footers on front matter
    # ------------------------------------------------------------------

    def generate(self):
        """Generate the book PDF with clean front matter (no headers/footers)."""
        import sys

        from briefkit.doc_ids import get_or_assign_doc_id
        from briefkit.extractor import extract_content

        verbose = self.config.get("_cli", {}).get("verbose", False)

        content = extract_content(
            str(self.target_path), config=self.config, level=self.level
        )
        if verbose:
            n_sub = len(content.get("subsystems", []))
            wc = content.get("metrics", {}).get("word_count", 0)
            print(f"  Extracted: {n_sub} subsystems, {wc} words", file=sys.stderr)

        # Doc IDs
        if self.config.get("doc_ids", {}).get("enabled", True):
            self.doc_id = get_or_assign_doc_id(
                self.target_path, level=self.level,
                title=content.get("title", self.target_path.name),
                config=self.config,
            )
        else:
            self.doc_id = ""

        # Build header/footer for body pages only
        # Store on self so build_story can update the running section header
        self._hf_state = {
            "section": content.get("title", self.target_path.name),
            "date": self.date_str,
            "doc_id": self.doc_id,
        }
        hf = make_header_footer(self._hf_state, brand=self.brand)

        # Page setup
        _PAGE_SIZES = {"A4": A4, "A3": A3, "Letter": letter, "Legal": legal}
        layout = self.config.get("layout", {})
        page_size = _PAGE_SIZES.get(layout.get("page_size", "A4"), A4)
        margins = layout.get("margins", {})

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=margins.get("top", 25) * mm,
            bottomMargin=margins.get("bottom", 22) * mm,
            leftMargin=margins.get("left", 20) * mm,
            rightMargin=margins.get("right", 20) * mm,
            title=content.get("title", ""),
            author=self.brand.get("org", "briefkit"),
            creator="briefkit",
        )

        story = self.build_story(content)

        if verbose:
            print(f"  Building PDF: {len(story)} flowables", file=sys.stderr)

        # NO header/footer on first page (half-title), apply from later pages
        def _blank_page(canvas, doc):
            """Completely blank — no header, no footer."""
            pass

        doc.build(story, onFirstPage=_blank_page, onLaterPages=hf)
        return self.output_path

    # ------------------------------------------------------------------
    # Suppress unused base methods
    # ------------------------------------------------------------------

    def build_at_a_glance(self, *args, **kwargs) -> list:
        return []

    def build_executive_summary(self, *args, **kwargs) -> list:
        return []
