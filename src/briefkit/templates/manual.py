"""
briefkit.templates.manual
~~~~~~~~~~~~~~~~~~~~~~~~~
Technical manual template.

Build order:
  Cover → Revision History → TOC → Safety Warnings → Scope →
  Procedures (body) → Reference Tables → Troubleshooting →
  Bibliography → Back Cover

Key differences:
  - Safety warnings auto-extracted (WARNING/CAUTION/DANGER patterns)
  - Procedures rendered as numbered steps
  - Troubleshooting auto-extracted (FAQ / Q: A: patterns)
  - Revision history from CHANGELOG.md or synthesized
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
    build_callout_box,
    build_classification_banner,
    build_cover_page,
    build_data_table,
    build_toc,
)
from briefkit.styles import _hex, _ps, _safe_para

# Regex patterns for safety extractions
_WARNING_PATTERN = re.compile(
    r'(?:^|\n)[\*\-]?\s*(?:>?\s*)?(WARNING|CAUTION|DANGER|NOTICE|IMPORTANT)[:\s]+([^\n]{20,300})',
    re.IGNORECASE | re.MULTILINE,
)

# FAQ / troubleshooting patterns
_FAQ_PATTERN = re.compile(
    r'(?:^|\n)(?:\*\*)?(?:Q:|Question:)\s*(.{10,200}?)\n+(?:\*\*)?(?:A:|Answer:)\s*(.{10,400})',
    re.IGNORECASE | re.MULTILINE,
)
_STEP_PATTERN = re.compile(
    r'(?:^|\n)\d+[\.\)]\s+(.{10,300})',
    re.MULTILINE,
)


class ManualTemplate(BaseBriefingTemplate):
    """
    Technical manual template.

    Intended for procedural documentation: installation guides,
    maintenance manuals, operator handbooks.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the manual story.
        """
        story = []

        # Cover
        story.extend(build_cover_page(
            title    = content.get("title", self.target_path.name.replace("-", " ").title()),
            subtitle = "Technical Manual",
            path     = str(self.target_path),
            level    = self.level,
            date     = self.date,
            doc_id   = self.doc_id,
            brand    = self.brand,
            content_width = self.content_width,
        ))

        # Classification banner
        story.append(build_classification_banner(
            self.level, str(self.target_path), brand=self.brand, content_width=self.content_width
        ))
        story.append(Spacer(1, 2 * mm))

        # Pre-build sections
        revision_flowables    = self._build_revision_history(content)
        safety_flowables      = self._build_safety_warnings(content)
        scope_flowables       = self._build_scope(content)
        procedures_flowables  = self._build_procedures(content)
        ref_tables_flowables  = self._build_reference_tables(content)
        troubleshoot_flowables = self._build_troubleshooting(content)
        bib_flowables         = self.build_bibliography(
            content.get("bibliography", []),
            source_type=content.get("metrics", {}).get("source_type", "DOCUMENTATION"),
        )

        # TOC
        story.append(_safe_para("Table of Contents", self.styles["STYLE_H1"]))
        story.append(Spacer(1, 2 * mm))

        toc_entries: list[tuple[int, str]] = []
        if revision_flowables:
            toc_entries.append((1, "Revision History"))
        if safety_flowables:
            toc_entries.append((1, "Safety Warnings"))
        toc_entries.append((1, "Scope"))
        toc_entries.append((1, "Procedures"))
        for i, sub in enumerate(content.get("subsystems", []), 1):
            toc_entries.append((2, f"  {i}. {sub.get('name', f'Procedure {i}')}"))
        if ref_tables_flowables:
            toc_entries.append((1, "Reference Tables"))
        if troubleshoot_flowables:
            toc_entries.append((1, "Troubleshooting"))
        if bib_flowables:
            toc_entries.append((1, "Bibliography"))

        story.extend(build_toc(toc_entries, brand=self.brand, content_width=self.content_width))
        story.append(PageBreak())

        # Revision History
        if revision_flowables:
            story.extend(revision_flowables)
            story.append(PageBreak())

        # Safety Warnings (immediately before procedures — critical placement)
        if safety_flowables:
            story.extend(safety_flowables)
            story.append(PageBreak())

        # Scope
        story.extend(scope_flowables)
        story.append(PageBreak())

        # Procedures
        story.extend(procedures_flowables)
        story.append(PageBreak())

        # Reference Tables
        if ref_tables_flowables:
            story.extend(ref_tables_flowables)
            story.append(PageBreak())

        # Troubleshooting
        if troubleshoot_flowables:
            story.extend(troubleshoot_flowables)
            story.append(PageBreak())

        # Bibliography
        if bib_flowables:
            story.extend(bib_flowables)

        # Back cover
        story.extend(self.build_back_cover())

        return story

    # ------------------------------------------------------------------
    # Revision History
    # ------------------------------------------------------------------

    def _build_revision_history(self, content: dict) -> list:
        """
        Build revision history from CHANGELOG.md or version file.
        Returns empty list if no source found.
        """
        changelog_candidates = [
            self.target_path / "CHANGELOG.md",
            self.target_path / "CHANGES.md",
            self.target_path / "HISTORY.md",
        ]
        found: Path | None = None
        for cand in changelog_candidates:
            if cand.exists():
                found = cand
                break

        if not found:
            return []

        flowables = []
        flowables.append(Paragraph("Revision History", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        raw = found.read_text(encoding="utf-8", errors="replace")

        # Extract version entries as a table: Version | Date | Description
        version_pattern = re.compile(
            r'##\s+(?:v?(\d[\d\.\-]+))\s*[\-–]\s*([^\n]+)\n+([\s\S]+?)(?=##|\Z)',
            re.MULTILINE,
        )

        rows: list[list[str]] = []
        for m in version_pattern.finditer(raw):
            ver, date_str, desc = m.group(1), m.group(2).strip(), m.group(3).strip()
            # Truncate description
            desc_clean = re.sub(r'\n+', ' ', desc)[:120]
            rows.append([ver, date_str, desc_clean])

        if rows:
            flowables.extend(build_data_table(
                ["Version", "Date", "Description"], rows,
                title="Document Revision History",
                brand=self.brand,
                content_width=self.content_width,
            ))
        else:
            # Fallback: render raw content as blocks
            for block in parse_markdown(raw[:2000])[:30]:
                flowables.extend(self.render_blocks([block]))

        return flowables

    # ------------------------------------------------------------------
    # Safety Warnings
    # ------------------------------------------------------------------

    def _build_safety_warnings(self, content: dict) -> list:
        """
        Auto-extract WARNING/CAUTION/DANGER/NOTICE paragraphs from all content.
        """
        all_text = ""
        for sub in content.get("subsystems", []):
            all_text += "\n" + sub.get("content", "")
        all_text += "\n" + content.get("overview", "")
        all_text += "\n" + content.get("guide_content", "")

        # Also check SAFETY.md
        safety_path = self.target_path / "SAFETY.md"
        if safety_path.exists():
            all_text += "\n" + safety_path.read_text(encoding="utf-8", errors="replace")

        warnings: list[tuple[str, str]] = []
        for m in _WARNING_PATTERN.finditer(all_text):
            level_str = m.group(1).upper()
            text      = m.group(2).strip()
            if (level_str, text[:40]) not in {(w, t[:40]) for w, t in warnings}:
                warnings.append((level_str, text))
            if len(warnings) >= 15:
                break

        if not warnings:
            return []

        # Map levels to callout box types
        level_to_box = {
            "WARNING":   "warning",
            "DANGER":    "warning",
            "CAUTION":   "takeaway",
            "NOTICE":    "insight",
            "IMPORTANT": "insight",
        }

        flowables = []
        flowables.append(Paragraph("Safety Warnings", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))
        flowables.append(Paragraph(
            "Read all safety warnings before operating or working with this system. "
            "Failure to observe these warnings may result in personal injury, equipment "
            "damage, or hazardous conditions.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 3 * mm))

        for level_str, text in warnings:
            box_type = level_to_box.get(level_str, "warning")
            flowables.append(build_callout_box(
                f"{level_str}: {text}", box_type, brand=self.brand, content_width=self.content_width
            ))

        return flowables

    # ------------------------------------------------------------------
    # Scope
    # ------------------------------------------------------------------

    def _build_scope(self, content: dict) -> list:
        """
        Build the scope section (purpose and applicability of the manual).
        """
        flowables = []
        flowables.append(Paragraph("Scope", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        overview = content.get("overview", "")
        title    = content.get("title", "this document")

        if overview:
            for block in parse_markdown(overview[:1500])[:15]:
                flowables.extend(self.render_blocks([block]))
        else:
            flowables.append(Paragraph(
                f"This technical manual covers {title}. "
                "It is intended for qualified personnel responsible for installation, "
                "operation, and maintenance.",
                self.styles["STYLE_BODY"],
            ))

        # Applicability table if multiple subsystems
        subsystems = content.get("subsystems", [])
        if len(subsystems) > 1:
            rows = [[str(i), sub["name"], "See Procedures section"]
                    for i, sub in enumerate(subsystems, 1)]
            flowables.append(Spacer(1, 3 * mm))
            flowables.extend(build_data_table(
                ["#", "Subsystem", "Coverage"],
                rows,
                title="Applicability",
                brand=self.brand,
                content_width=self.content_width,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Procedures
    # ------------------------------------------------------------------

    def _build_procedures(self, content: dict) -> list:
        """
        Build the procedures section.

        Each subsystem is rendered as a numbered procedure section.
        List items are rendered as numbered steps.
        """
        flowables = []
        flowables.append(Paragraph("Procedures", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))

        subsystems = content.get("subsystems", [])
        if not subsystems:
            flowables.append(Paragraph(
                "No procedure documents found.", self.styles["STYLE_BODY"]
            ))
            return flowables

        step_style = _ps(
            "ProcedureStep", brand=self.brand,
            fontSize=10, textColor=_hex(self.brand, "body_text"),
            leading=15, leftIndent=16, spaceBefore=2, spaceAfter=2,
        )
        _ps(
            "ProcedureNote", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "caption"),
            fontName="Helvetica-Oblique", leftIndent=16,
        )

        for proc_num, sub in enumerate(subsystems, 1):
            flowables.append(Paragraph(
                f"{proc_num}. {sub['name']}", self.styles["STYLE_H2"]
            ))
            flowables.append(Spacer(1, 1.5 * mm))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            step_counter = 0

            for block in blocks:
                btype = block["type"]

                if btype == "heading" and block["level"] <= 2:
                    continue

                if btype == "list_item":
                    step_counter += 1
                    text = block.get("text", "")
                    flowables.append(Paragraph(
                        f"Step {step_counter}: {text}", step_style
                    ))

                elif btype == "blockquote":
                    # Notes/warnings inline in procedure
                    flowables.append(build_callout_box(
                        block.get("text", ""), "insight", brand=self.brand, content_width=self.content_width
                    ))

                else:
                    for fl in self.render_blocks([block]):
                        flowables.append(fl)

            flowables.append(Spacer(1, 3 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Reference Tables
    # ------------------------------------------------------------------

    def _build_reference_tables(self, content: dict) -> list:
        """
        Consolidate all data tables from all subsystems into a reference section.
        """
        all_tables: list[tuple[str, dict]] = []
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                if tbl.get("headers") and tbl.get("rows"):
                    all_tables.append((sub["name"], tbl))

        if not all_tables:
            return []

        flowables = []
        flowables.append(Paragraph("Reference Tables", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))
        flowables.append(Paragraph(
            "Consolidated reference tables extracted from the documentation.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 2 * mm))

        for section_name, tbl in all_tables[:10]:
            flowables.append(Paragraph(section_name, self.styles["STYLE_H3"]))
            flowables.extend(build_data_table(
                tbl["headers"], tbl["rows"], brand=self.brand, content_width=self.content_width
            ))
            flowables.append(Spacer(1, 2 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Troubleshooting
    # ------------------------------------------------------------------

    def _build_troubleshooting(self, content: dict) -> list:
        """
        Auto-extract FAQ/Q:A: patterns from content for troubleshooting.
        """
        all_text = "\n".join(
            sub.get("content", "") for sub in content.get("subsystems", [])
        )

        # Check for a dedicated troubleshooting.md
        trouble_path = self.target_path / "troubleshooting.md"
        if trouble_path.exists():
            all_text = trouble_path.read_text(encoding="utf-8", errors="replace") + "\n" + all_text

        faq_pairs: list[tuple[str, str]] = []
        for m in _FAQ_PATTERN.finditer(all_text):
            q = m.group(1).strip()
            a = m.group(2).strip()
            if len(q) > 10 and len(a) > 10:
                faq_pairs.append((q, a[:300]))
            if len(faq_pairs) >= 12:
                break

        # Also look for "Problem / Solution" bullet patterns
        problem_pattern = re.compile(
            r'(?:Problem|Issue|Error|Symptom):\s*(.{10,200}?)[\n\r]+(?:Solution|Fix|Resolution|Cause):\s*(.{10,300})',
            re.IGNORECASE | re.MULTILINE,
        )
        for m in problem_pattern.finditer(all_text):
            q = "Problem: " + m.group(1).strip()
            a = m.group(2).strip()
            faq_pairs.append((q, a[:300]))
            if len(faq_pairs) >= 12:
                break

        if not faq_pairs:
            return []

        flowables = []
        flowables.append(Paragraph("Troubleshooting", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 2 * mm))
        flowables.append(Paragraph(
            "Common issues and their solutions.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 2 * mm))

        q_style = _ps(
            "TroubleshootQ", brand=self.brand,
            fontName="Helvetica-Bold", fontSize=10,
            textColor=_hex(self.brand, "primary"), leading=14,
            spaceBefore=6, spaceAfter=2,
        )
        a_style = _ps(
            "TroubleshootA", brand=self.brand,
            fontSize=10, textColor=_hex(self.brand, "body_text"),
            leading=14, leftIndent=12,
        )

        for q, a in faq_pairs:
            flowables.append(Paragraph(f"Q: {q}", q_style))
            flowables.append(Paragraph(f"A: {a}", a_style))

        return flowables

    # ------------------------------------------------------------------
    # Suppress unused base methods
    # ------------------------------------------------------------------

    def build_at_a_glance(self, *args, **kwargs) -> list:
        return []

    def build_executive_summary(self, *args, **kwargs) -> list:
        return []
