"""
briefkit.templates.academic
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Academic paper template.

Build order:
  Title Page → Abstract (250-word max) → TOC →
  Introduction → Literature Review → Body →
  Results → Discussion → Conclusion →
  References → Appendices

Key differences:
  - No branding (no org bar, no classification banner, no back cover)
  - Full academic citation formatting (APA style)
  - Abstract strictly limited to 250 words
  - Literature review section auto-populated from bibliography
  - Results section rendered from tables
"""

from __future__ import annotations

import re

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from briefkit.elements.tables import build_data_table
from briefkit.elements.toc import build_toc
from briefkit.extractor import parse_markdown
from briefkit.generator import BaseBriefingTemplate
from briefkit.styles import _hex, _ps, _safe_para
from briefkit.templates._helpers import should_skip


class AcademicTemplate(BaseBriefingTemplate):
    """
    Academic paper template.

    Produces a clean, unbranded academic document with proper
    citation formatting and standard academic section structure.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the academic paper story.
        """
        story = []

        title = content.get("title", self.target_path.name.replace("-", " ").title())
        b = self.brand
        primary   = _hex(b, "primary")
        caption_c = _hex(b, "caption")
        body_c    = _hex(b, "body_text")

        # Update running header

        # --- Title Page (minimalist, no cover graphics) ---
        title_style = _ps(
            "AcadTitle", brand=b,
            fontSize=24, textColor=primary,
            fontName="Helvetica-Bold", alignment=1, leading=30,
        )
        author_style = _ps(
            "AcadAuthor", brand=b,
            fontSize=12, textColor=body_c, alignment=1,
        )
        caption_style = _ps(
            "AcadTitleCaption", brand=b,
            fontSize=10, textColor=caption_c, alignment=1,
        )

        org = b.get("org", "")

        story.append(Spacer(1, 60 * mm))
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 10 * mm))

        if org:
            story.append(Paragraph(org, author_style))

        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(self.date_str, caption_style))

        if self.doc_id:
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(self.doc_id, caption_style))

        story.append(PageBreak())

        # Pre-build sections for TOC
        cfg = self.config
        abstract_text        = self._derive_abstract(content)
        intro_flowables      = [] if should_skip(cfg, "introduction")      else self._build_introduction(content)
        lit_review_flowables = [] if should_skip(cfg, "literature_review") else self._build_literature_review(content)
        body_flowables       = self._build_body(content)
        results_flowables    = [] if should_skip(cfg, "results")           else self._build_results(content)
        discussion_flowables = [] if should_skip(cfg, "discussion")        else self._build_discussion(content)
        conclusion_flowables = [] if should_skip(cfg, "conclusion")        else self._build_conclusion(content)
        appendix_flowables   = [] if should_skip(cfg, "appendices")        else self._build_appendices(content)
        ref_flowables        = [] if should_skip(cfg, "references")        else self._build_references(content)

        # TOC
        if not should_skip(cfg, "toc"):
            story.append(_safe_para("Table of Contents", self.styles["STYLE_H1"]))
            story.append(Spacer(1, 2 * mm))

            toc_entries = []
            if not should_skip(cfg, "abstract"):
                toc_entries.append((1, "Abstract"))
            if intro_flowables:
                toc_entries.append((1, "1. Introduction"))
            if lit_review_flowables:
                toc_entries.append((1, "2. Literature Review"))
            toc_entries.append((1, "3. Content"))
            for i, sub in enumerate(content.get("subsystems", []), 1):
                toc_entries.append((2, f"  3.{i} {sub.get('name', f'Section {i}')}"))
            if results_flowables:
                toc_entries.append((1, "4. Results"))
            if discussion_flowables:
                toc_entries.append((1, "5. Discussion"))
            if conclusion_flowables:
                toc_entries.append((1, "6. Conclusion"))
            if ref_flowables:
                toc_entries.append((1, "References"))
            if appendix_flowables:
                toc_entries.append((1, "Appendices"))

            story.extend(build_toc(toc_entries, brand=b, content_width=self.content_width))
            story.append(PageBreak())

        # Abstract
        if not should_skip(cfg, "abstract"):
            story.append(Paragraph("Abstract", self.styles["STYLE_H1"]))
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(abstract_text, self.styles["STYLE_BODY"]))

            terms = list(content.get("terms", {}).keys())[:8]
            if terms:
                story.append(Spacer(1, 2 * mm))
                kw_style = _ps(
                    "AcadKeywords", brand=b,
                    fontSize=9, textColor=caption_c,
                    fontName="Helvetica-Oblique",
                )
                story.append(Paragraph(
                    "<b>Keywords:</b> " + ", ".join(terms),
                    kw_style,
                ))

            story.append(PageBreak())

        # Body sections
        if intro_flowables:
            story.extend(intro_flowables)
            story.append(PageBreak())

        if lit_review_flowables:
            story.extend(lit_review_flowables)
            story.append(PageBreak())

        story.extend(body_flowables)
        story.append(PageBreak())

        if results_flowables:
            story.extend(results_flowables)
            story.append(PageBreak())

        if discussion_flowables:
            story.extend(discussion_flowables)
            story.append(PageBreak())

        if conclusion_flowables:
            story.extend(conclusion_flowables)
            story.append(PageBreak())

        if ref_flowables:
            story.extend(ref_flowables)
            story.append(PageBreak())

        if appendix_flowables:
            story.extend(appendix_flowables)

        return story

    # ------------------------------------------------------------------
    # Abstract derivation
    # ------------------------------------------------------------------

    def _derive_abstract(self, content: dict) -> str:
        """
        Derive a 250-word-max abstract from content.
        """
        overview    = content.get("overview", "")
        orientation = content.get("orientation", "")
        title       = content.get("title", "this study")
        subsystems  = content.get("subsystems", [])

        parts: list[str] = []

        # Opening: first paragraph of overview or orientation
        if overview:
            paras = [p.strip() for p in re.split(r'\n\n+', overview) if p.strip()]
            for para in paras:
                clean = re.sub(r'#+\s*', '', para).strip()
                if len(clean) > 50:
                    parts.append(clean)
                    break

        if not parts and orientation:
            m = re.search(r'^(?!#)(.{60,})', orientation, re.MULTILINE)
            if m:
                parts.append(m.group(1).strip())

        # Method sentence
        doc_count = len(subsystems)
        if doc_count:
            source_type = content.get("metrics", {}).get("source_type", "ACADEMIC")
            if source_type == "ACADEMIC":
                parts.append(
                    f"This paper analyses {doc_count} source document(s) via systematic "
                    "content extraction and thematic synthesis."
                )
            else:
                parts.append(
                    f"This paper is drawn from {doc_count} source document(s), "
                    "structured into thematic sections for analysis."
                )

        # Findings summary
        findings: list[str] = []
        for sub in subsystems[:3]:
            raw = sub.get("content", "").replace("\n", " ")
            for s in re.split(r'(?<=[.!?])\s+', raw):
                s = s.strip().lstrip("#- *>`|")
                if len(s) > 40 and not s.startswith("```"):
                    findings.append(s[:120])
                    break
        if findings:
            parts.append("Key findings include: " + "; ".join(findings) + ".")

        if not parts:
            parts = [
                f"This paper presents a structured analysis of {title}. "
                "See individual sections for detailed discussion."
            ]

        full_abstract = " ".join(parts)
        words = full_abstract.split()
        if len(words) > 250:
            full_abstract = " ".join(words[:250]) + "\u2026"

        return full_abstract

    # ------------------------------------------------------------------
    # Introduction
    # ------------------------------------------------------------------

    def _build_introduction(self, content: dict) -> list:
        flowables = []
        flowables.append(Paragraph("1. Introduction", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        overview = content.get("overview", "")
        orientation = content.get("orientation", "")
        title = content.get("title", "this study")

        if orientation:
            for block in parse_markdown(orientation[:3000])[:20]:
                flowables.extend(self.render_blocks([block]))
        elif overview:
            for block in parse_markdown(overview)[:15]:
                flowables.extend(self.render_blocks([block]))
        else:
            subsystems = content.get("subsystems", [])
            flowables.append(Paragraph(
                f"This paper presents an analysis of {title}, comprising "
                f"{len(subsystems)} section(s). The following sections present "
                f"literature context, detailed analysis, results, and conclusions.",
                self.styles["STYLE_BODY"],
            ))

        return flowables

    # ------------------------------------------------------------------
    # Literature Review
    # ------------------------------------------------------------------

    def _build_literature_review(self, content: dict) -> list:
        """
        Build a literature review section from the bibliography.
        Only rendered when >= 3 bibliography entries exist.
        """
        bibliography = content.get("bibliography", [])
        if len(bibliography) < 3:
            return []

        flowables = []
        flowables.append(Paragraph("2. Literature Review", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))
        flowables.append(Paragraph(
            "The following sources inform the analysis presented in this paper.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 2 * mm))

        # Group by type
        papers = [s for s in bibliography if s.get("type") == "paper"]
        books  = [s for s in bibliography if s.get("type") == "book"]
        specs  = [s for s in bibliography if s.get("type") == "specification"]
        other  = [s for s in bibliography if s.get("type") not in ("paper", "book", "specification")]

        _hex(self.brand, "caption")
        body_c    = _hex(self.brand, "body_text")

        def _render_group(label: str, sources: list) -> None:
            if not sources:
                return
            flowables.append(Paragraph(label, self.styles["STYLE_H2"]))
            flowables.append(Spacer(1, 1.5 * mm))
            for src in sources[:8]:
                authors = src.get("authors", "") or ""
                year    = src.get("year", "n.d.")
                title_  = src.get("title", "") or ""
                if authors and title_:
                    cite = f"{authors} ({year}). {title_}."
                elif title_:
                    cite = f"{title_} ({year})."
                else:
                    cite = f"({year})."
                flowables.append(Paragraph(cite, _ps(
                    "LitReviewEntry", brand=self.brand,
                    fontSize=10, textColor=body_c, leading=14,
                    leftIndent=12, firstLineIndent=-12, spaceAfter=4,
                )))

        _render_group("Academic Papers", papers)
        _render_group("Books and Monographs", books)
        _render_group("Specifications and Standards", specs)
        if other:
            _render_group("Other Sources", other[:5])

        return flowables

    # ------------------------------------------------------------------
    # Body (content sections)
    # ------------------------------------------------------------------

    def _build_body(self, content: dict) -> list:
        flowables = []
        flowables.append(Paragraph("3. Content", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        subsystems = content.get("subsystems", [])
        if not subsystems:
            overview = content.get("overview", "")
            if overview:
                for block in parse_markdown(overview)[:20]:
                    flowables.extend(self.render_blocks([block]))
            return flowables

        for idx, sub in enumerate(subsystems, 1):
            flowables.append(Paragraph(f"3.{idx} {sub['name']}", self.styles["STYLE_H2"]))
            flowables.append(Spacer(1, 1.5 * mm))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                if block["type"] == "heading" and block["level"] <= 2:
                    continue
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
                if rendered >= 80:
                    break

            flowables.append(Spacer(1, 2 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def _build_results(self, content: dict) -> list:
        """
        Build a results section from all extracted data tables.
        Omitted if no tables found.
        """
        all_tables: list[tuple[str, dict]] = []
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                if tbl.get("headers") and tbl.get("rows"):
                    all_tables.append((sub["name"], tbl))

        if not all_tables:
            return []

        flowables = []
        flowables.append(Paragraph("4. Results", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))
        flowables.append(Paragraph(
            "The following tables present quantitative and structured findings "
            "extracted from the source material.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 2 * mm))

        for i, (section_name, tbl) in enumerate(all_tables[:8], 1):
            flowables.append(Paragraph(
                f"Table {i}: {section_name}", self.styles["STYLE_CAPTION"]
            ))
            flowables.extend(build_data_table(
                tbl["headers"], tbl["rows"], brand=self.brand, content_width=self.content_width
            ))
            flowables.append(Spacer(1, 2 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Discussion
    # ------------------------------------------------------------------

    def _build_discussion(self, content: dict) -> list:
        flowables = []
        flowables.append(Paragraph("5. Discussion", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        title = content.get("title", "the subject matter")
        subsystems = content.get("subsystems", [])

        flowables.append(Paragraph(
            f"The analysis of {title} reveals several notable themes across the "
            f"{len(subsystems)} section(s) examined.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 2 * mm))

        # Derive discussion points from insights (blockquotes)
        for sub in subsystems[:5]:
            for insight in sub.get("insights", [])[:1]:
                if len(insight) > 30:
                    flowables.append(Paragraph(
                        f"<i>{sub['name']}:</i> {insight[:300]}",
                        _ps("DiscussionItem", brand=self.brand,
                            fontSize=10, textColor=_hex(self.brand, "body_text"),
                            leading=14, leftIndent=12, spaceAfter=4),
                    ))

        # Guide content as additional discussion material
        guide = content.get("guide_content", "")
        if guide:
            flowables.append(Spacer(1, 2 * mm))
            for block in parse_markdown(guide[:2000])[:20]:
                flowables.extend(self.render_blocks([block]))

        return flowables

    # ------------------------------------------------------------------
    # Conclusion
    # ------------------------------------------------------------------

    def _build_conclusion(self, content: dict) -> list:
        flowables = []
        flowables.append(Paragraph("6. Conclusion", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        title = content.get("title", "this study")
        subsystems = content.get("subsystems", [])
        terms_count = len(content.get("terms", {}))
        bib_count   = len(content.get("bibliography", []))

        flowables.append(Paragraph(
            f"This paper has presented a structured analysis of {title}, drawing on "
            f"{len(subsystems)} primary content section(s). "
            f"A total of {terms_count} key terms were identified, and "
            f"{bib_count} source(s) were cited.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 2 * mm))

        brilliance = content.get("brilliance_summary", "")
        if brilliance:
            # Use first paragraph of brilliance as concluding insight
            for block in parse_markdown(brilliance)[:3]:
                if block["type"] == "paragraph":
                    flowables.append(Paragraph(
                        block["text"], self.styles["STYLE_BODY"]
                    ))
                    break

        flowables.append(Spacer(1, 2 * mm))
        flowables.append(Paragraph(
            "Further research should examine the cross-cutting themes identified "
            "in the analysis and explore their implications in adjacent domains.",
            self.styles["STYLE_BODY"],
        ))

        return flowables

    # ------------------------------------------------------------------
    # References (APA-style)
    # ------------------------------------------------------------------

    def _build_references(self, content: dict) -> list:
        """
        Build an APA-formatted references section.

        Format: Author, A. A., & Author, B. B. (Year). Title. Source.
        """
        sources = content.get("bibliography", [])
        if not sources:
            return []

        flowables = []
        flowables.append(Paragraph("References", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        body_c = _hex(self.brand, "body_text")
        ref_style = _ps(
            "AcadRef", brand=self.brand,
            fontSize=10, textColor=body_c, leading=14,
            leftIndent=18, firstLineIndent=-18, spaceAfter=6,
        )

        # Sort by author then year
        def _sort_key(src):
            return (
                (src.get("authors") or "").lower(),
                str(src.get("year") or ""),
            )

        for src in sorted(sources, key=_sort_key):
            authors = src.get("authors", "") or ""
            year    = src.get("year", "n.d.") or "n.d."
            title_  = src.get("title", "") or ""
            doi     = src.get("doi", "") or ""
            src_type = src.get("type", "other")

            if src_type == "case":
                citation = f"<i>{title_}</i>."
            elif src_type == "specification":
                citation = f"{authors} ({year}). <i>{title_}</i>."
            else:
                if authors:
                    citation = f"{authors} ({year}). {title_}."
                else:
                    citation = f"{title_} ({year})."

            if doi:
                citation += f" https://doi.org/{doi}"

            flowables.append(Paragraph(citation, ref_style))

        return flowables

    # ------------------------------------------------------------------
    # Appendices
    # ------------------------------------------------------------------

    def _build_appendices(self, content: dict) -> list:
        """
        Build appendices from appendix*.md files or engineering-brilliance.md.
        """
        appendix_files = sorted(
            list(self.target_path.glob("appendix*.md"))
            + list(self.target_path.glob("appendices.md"))
        )
        brilliance = content.get("brilliance_summary", "")

        if not appendix_files and not brilliance:
            return []

        flowables = []
        flowables.append(Paragraph("Appendices", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        if appendix_files:
            for i, fp in enumerate(appendix_files, 1):
                raw = fp.read_text(encoding="utf-8", errors="replace")
                label = fp.stem.replace("-", " ").title()
                flowables.append(Paragraph(
                    f"Appendix {chr(64+i)}: {label}", self.styles["STYLE_H2"]
                ))
                flowables.append(Spacer(1, 1.5 * mm))
                for block in parse_markdown(raw)[:30]:
                    flowables.extend(self.render_blocks([block]))
                flowables.append(Spacer(1, 2 * mm))
        elif brilliance:
            flowables.append(Paragraph(
                "Appendix A: Supplementary Analysis", self.styles["STYLE_H2"]
            ))
            flowables.append(Spacer(1, 1.5 * mm))
            for block in parse_markdown(brilliance)[:20]:
                flowables.extend(self.render_blocks([block]))

        return flowables

    # ------------------------------------------------------------------
    # Suppress branded elements
    # ------------------------------------------------------------------

    def build_at_a_glance(self, *args, **kwargs) -> list:
        return []

    def build_executive_summary(self, *args, **kwargs) -> list:
        return []

    def build_back_cover(self) -> list:
        """No back cover for academic papers — just a colophon line."""
        from reportlab.platypus import Spacer as _Sp
        caption_c = _hex(self.brand, "caption")
        cp_style = _ps(
            "AcadColophon", brand=self.brand,
            fontSize=8, textColor=caption_c, alignment=1,
        )
        return [
            _Sp(1, 20 * mm),
            Paragraph(f"Generated by briefkit on {self.date_str}.", cp_style),
        ]
