"""
briefkit.templates.contract
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Legal contract/agreement template.

Build order:
  Title Page → Recitals → Definitions → Operative Clauses →
  Schedules → Execution Block

Key differences:
  - Title page with agreement name and parties
  - Recitals section from README overview
  - Definitions block with auto-extracted bold terms
  - Operative clauses with 1.1/1.2 numbering
  - Schedules from additional content sections
  - Execution page with ruled signature and witness lines
  - Header: agreement name, right-aligned
  - Footer: "Page X of Y" + CONFIDENTIAL notice
  - No TOC for short contracts, optional for long (>20 pages)
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3, A4, legal, letter
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from briefkit.extractor import parse_markdown
from briefkit.generator import BaseBriefingTemplate
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
)

# ---------------------------------------------------------------------------
# Page sizes
# ---------------------------------------------------------------------------

_PAGE_SIZES = {
    "A4": A4,
    "A3": A3,
    "Letter": letter,
    "Legal": legal,
}

# ---------------------------------------------------------------------------
# Bold term extraction regex
# ---------------------------------------------------------------------------

_BOLD_TERM_PATTERN = re.compile(
    r'\*\*([A-Z][A-Za-z\s]{2,40}?)\*\*',
)


def _extract_definitions(content: dict) -> list[tuple[str, str]]:
    """
    Extract bold terms from content and return as (term, context) pairs,
    sorted alphabetically by term.
    """
    all_text = content.get("overview", "")
    for sub in content.get("subsystems", []):
        all_text += "\n" + sub.get("content", "")

    seen: set[str] = set()
    definitions: list[tuple[str, str]] = []

    for match in _BOLD_TERM_PATTERN.finditer(all_text):
        term = match.group(1).strip()
        term_lower = term.lower()
        if term_lower in seen:
            continue
        seen.add(term_lower)

        # Extract surrounding context as a definition hint
        start = max(0, match.start() - 10)
        end = min(len(all_text), match.end() + 120)
        context = all_text[start:end].strip()
        # Clean up markdown
        context = re.sub(r'\*\*', '', context)
        context = re.sub(r'\n+', ' ', context)
        context = context[:150]

        definitions.append((term, context))
        if len(definitions) >= 30:
            break

    definitions.sort(key=lambda x: x[0].lower())
    return definitions


class ContractTemplate(BaseBriefingTemplate):
    """
    Legal contract/agreement template.

    Produces a formal contract-style PDF with title page, recitals,
    definitions, numbered operative clauses, schedules, and an
    execution block with signature lines.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the contract story:
          Title page, recitals, definitions, operative clauses,
          schedules, execution block.
        """
        story = []
        b = self.brand
        _hex(b, "primary")
        _hex(b, "body_text")
        _hex(b, "caption")
        b.get("org", "")
        title = content.get("title", self.target_path.name.replace("-", " ").title())

        # ============================================================
        # Title Page
        # ============================================================
        story.extend(self._build_title_page(content, title))
        story.append(PageBreak())

        # Pre-build sections for TOC length estimation
        recitals = self._build_recitals(content)
        definitions = self._build_definitions(content)
        clauses = self._build_operative_clauses(content)
        schedules = self._build_schedules(content)
        execution = self._build_execution_block()

        # ============================================================
        # Operative Clauses
        # ============================================================
        if recitals:
            story.extend(recitals)
            story.append(Spacer(1, 6 * mm))

        if definitions:
            story.extend(definitions)
            story.append(PageBreak())

        story.extend(clauses)
        story.append(PageBreak())

        # ============================================================
        # Schedules
        # ============================================================
        if schedules:
            story.extend(schedules)
            story.append(PageBreak())

        # ============================================================
        # Execution Block
        # ============================================================
        story.extend(execution)

        return story

    # ------------------------------------------------------------------
    # Title Page
    # ------------------------------------------------------------------

    def _build_title_page(self, content: dict, title: str) -> list:
        """Build the contract title page with agreement name and parties."""
        flowables = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")
        caption_c = _hex(b, "caption")
        org = b.get("org", "")

        flowables.append(Spacer(1, 40 * mm))

        # Agreement name
        title_style = _ps(
            "ContractTitle", brand=b, fontSize=22, textColor=primary,
            fontName="Helvetica-Bold", alignment=1, spaceAfter=8,
        )
        flowables.append(Paragraph(title.upper(), title_style))

        # Divider
        flowables.append(Spacer(1, 4 * mm))
        divider = Table([[""]], colWidths=[self.content_width * 0.5], rowHeights=[2])
        divider.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, -1), 2, HexColor(b.get("primary", "#1B2A4A"))),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        divider.hAlign = "CENTER"
        flowables.append(divider)
        flowables.append(Spacer(1, 8 * mm))

        # Subtitle
        sub_style = _ps(
            "ContractSub", brand=b, fontSize=12, textColor=body_c,
            alignment=1, spaceAfter=4,
        )
        flowables.append(Paragraph("Agreement", sub_style))

        # Parties
        flowables.append(Spacer(1, 15 * mm))
        party_style = _ps(
            "ContractParty", brand=b, fontSize=11, textColor=body_c,
            alignment=1, spaceAfter=3,
        )
        between_style = _ps(
            "ContractBetween", brand=b, fontSize=10, textColor=caption_c,
            alignment=1, fontName="Helvetica-Oblique", spaceAfter=6,
        )

        if org:
            flowables.append(Paragraph(org, party_style))
            flowables.append(Paragraph("(\"First Party\")", between_style))
            flowables.append(Spacer(1, 4 * mm))
            flowables.append(Paragraph("and", between_style))
            flowables.append(Spacer(1, 4 * mm))
            flowables.append(Paragraph("[Counterparty Name]", party_style))
            flowables.append(Paragraph("(\"Second Party\")", between_style))
        else:
            flowables.append(Paragraph("[Party A]", party_style))
            flowables.append(Paragraph("and", between_style))
            flowables.append(Paragraph("[Party B]", party_style))

        # Date
        flowables.append(Spacer(1, 20 * mm))
        date_style = _ps(
            "ContractDate", brand=b, fontSize=10, textColor=caption_c,
            alignment=1,
        )
        flowables.append(Paragraph(f"Dated: {self.date_str}", date_style))

        # Confidential notice
        flowables.append(Spacer(1, 10 * mm))
        conf_style = _ps(
            "ContractConf", brand=b, fontSize=8, textColor=caption_c,
            alignment=1, fontName="Helvetica-Bold",
        )
        flowables.append(Paragraph("CONFIDENTIAL", conf_style))

        return flowables

    # ------------------------------------------------------------------
    # Recitals
    # ------------------------------------------------------------------

    def _build_recitals(self, content: dict) -> list:
        """Build the recitals section from the overview/README content."""
        overview = content.get("overview", "")
        if not overview:
            return []

        flowables = []
        b = self.brand
        primary = _hex(b, "primary")

        h_style = _ps(
            "ContractRecitalsH", brand=b, fontSize=13, textColor=primary,
            fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=6,
        )
        flowables.append(Paragraph("RECITALS", h_style))

        recital_style = _ps(
            "ContractRecital", brand=b, fontSize=10,
            textColor=_hex(b, "body_text"),
            leading=15, spaceAfter=4,
        )

        # Parse overview into paragraphs and prefix with lettering
        blocks = parse_markdown(overview)[:10]
        letter_idx = 0
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for block in blocks:
            if block.get("type") in ("paragraph", "heading"):
                text = block.get("text", "")
                if text and len(text) > 10:
                    prefix = letters[letter_idx] if letter_idx < 26 else str(letter_idx + 1)
                    flowables.append(Paragraph(
                        f"({prefix})&nbsp;&nbsp;{text}", recital_style,
                    ))
                    letter_idx += 1
                    if letter_idx >= 10:
                        break

        return flowables

    # ------------------------------------------------------------------
    # Definitions
    # ------------------------------------------------------------------

    def _build_definitions(self, content: dict) -> list:
        """Build the definitions block from auto-extracted bold terms."""
        defs = _extract_definitions(content)
        if not defs:
            return []

        flowables = []
        b = self.brand
        primary = _hex(b, "primary")

        h_style = _ps(
            "ContractDefsH", brand=b, fontSize=13, textColor=primary,
            fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=6,
        )
        flowables.append(Paragraph("1. DEFINITIONS", h_style))

        intro_style = _ps(
            "ContractDefsIntro", brand=b, fontSize=10,
            textColor=_hex(b, "body_text"), spaceAfter=6,
        )
        flowables.append(Paragraph(
            "In this Agreement, unless the context otherwise requires:",
            intro_style,
        ))

        term_style = _ps(
            "ContractDefTerm", brand=b, fontSize=10,
            textColor=_hex(b, "body_text"), leading=14,
            leftIndent=12, spaceAfter=4,
        )

        for idx, (term, context) in enumerate(defs, 1):
            flowables.append(Paragraph(
                f"1.{idx}&nbsp;&nbsp;<b>{term}</b> means {context}",
                term_style,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Operative Clauses
    # ------------------------------------------------------------------

    def _build_operative_clauses(self, content: dict) -> list:
        """
        Build operative clauses from subsystem content.
        Each subsystem becomes a numbered clause; sub-headings get 1.1 numbering.
        """
        flowables = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")
        subsystems = content.get("subsystems", [])

        if not subsystems:
            overview = content.get("overview", "")
            if overview:
                h_style = _ps(
                    "ContractClauseH", brand=b, fontSize=13, textColor=primary,
                    fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=6,
                )
                flowables.append(Paragraph("1. TERMS", h_style))
                for block in parse_markdown(overview)[:30]:
                    flowables.extend(self.render_blocks([block]))
            return flowables

        # Offset clause numbering if definitions section exists
        has_defs = bool(_extract_definitions(content))
        clause_offset = 1 if has_defs else 0

        clause_h_style = _ps(
            "ContractClauseH", brand=b, fontSize=13, textColor=primary,
            fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6,
        )
        sub_h_style = _ps(
            "ContractSubClauseH", brand=b, fontSize=11, textColor=primary,
            fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=3,
        )
        clause_body_style = _ps(
            "ContractClauseBody", brand=b, fontSize=10, textColor=body_c,
            leading=15, spaceAfter=3, leftIndent=12,
        )

        for clause_idx, sub in enumerate(subsystems, 1 + clause_offset):
            name = sub.get("name", f"Clause {clause_idx}")
            flowables.append(Paragraph(
                f"{clause_idx}. {name.upper()}", clause_h_style,
            ))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            sub_clause_counter = 0
            rendered = 0

            for block in blocks:
                btype = block.get("type", "")

                # Skip top-level headings (already used as clause title)
                if btype == "heading" and block.get("level", 0) <= 1:
                    continue

                # Sub-headings become numbered sub-clauses
                if btype == "heading" and block.get("level", 0) >= 2:
                    sub_clause_counter += 1
                    text = block.get("text", "")
                    flowables.append(Paragraph(
                        f"{clause_idx}.{sub_clause_counter}&nbsp;&nbsp;{text}",
                        sub_h_style,
                    ))
                    continue

                # Paragraphs get indented clause styling
                if btype == "paragraph":
                    text = block.get("text", "")
                    if text:
                        flowables.append(_safe_para(text, clause_body_style))
                    continue

                # Everything else rendered normally
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
                if rendered >= 80:
                    break

            flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Schedules
    # ------------------------------------------------------------------

    def _build_schedules(self, content: dict) -> list:
        """
        Build schedules from subsystems that contain tables or
        supplementary content.
        """
        subsystems = content.get("subsystems", [])
        # Schedules are subsystems that have tables
        schedule_subs = [
            sub for sub in subsystems
            if sub.get("tables")
        ]

        if not schedule_subs:
            return []

        flowables = []
        b = self.brand
        primary = _hex(b, "primary")

        sched_title_style = _ps(
            "ContractSchedTitle", brand=b, fontSize=14, textColor=primary,
            fontName="Helvetica-Bold", alignment=1, spaceBefore=8, spaceAfter=4,
        )
        flowables.append(Paragraph("SCHEDULES", sched_title_style))
        flowables.append(Spacer(1, 6 * mm))

        sched_h_style = _ps(
            "ContractSchedH", brand=b, fontSize=12, textColor=primary,
            fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4,
        )

        from briefkit.elements.tables import build_data_table

        for sched_idx, sub in enumerate(schedule_subs, 1):
            name = sub.get("name", f"Schedule {sched_idx}")
            flowables.append(Paragraph(
                f"Schedule {sched_idx} \u2014 {name}", sched_h_style,
            ))

            for tbl in sub.get("tables", [])[:5]:
                headers = tbl.get("headers", [])
                rows = tbl.get("rows", [])
                if headers and rows:
                    flowables.extend(build_data_table(
                        headers, rows, brand=b, content_width=self.content_width,
                    ))
                    flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Execution Block
    # ------------------------------------------------------------------

    def _build_execution_block(self) -> list:
        """Build signature lines and witness block for contract execution."""
        flowables = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")
        caption_c = _hex(b, "caption")
        org = b.get("org", "")
        rule_c = HexColor(b.get("rule", "#CCCCCC"))

        exec_title_style = _ps(
            "ContractExecTitle", brand=b, fontSize=14, textColor=primary,
            fontName="Helvetica-Bold", alignment=1, spaceBefore=8, spaceAfter=8,
        )
        flowables.append(Paragraph("EXECUTION", exec_title_style))
        flowables.append(Spacer(1, 4 * mm))

        intro_style = _ps(
            "ContractExecIntro", brand=b, fontSize=10, textColor=body_c,
            spaceAfter=8,
        )
        flowables.append(Paragraph(
            "IN WITNESS WHEREOF, the parties have executed this Agreement "
            "as of the date first written above.",
            intro_style,
        ))
        flowables.append(Spacer(1, 8 * mm))

        # Signature block helper
        _ps(
            "ContractSigLabel", brand=b, fontSize=9, textColor=caption_c,
            spaceBefore=2, spaceAfter=1,
        )
        _ps(
            "ContractSigLine", brand=b, fontSize=10, textColor=body_c,
        )

        def _sig_block(party_label: str) -> list:
            """Generate a single party signature block."""
            block = []
            party_h_style = _ps(
                "ContractPartyH", brand=b, fontSize=11, textColor=primary,
                fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4,
            )
            block.append(Paragraph(party_label, party_h_style))
            block.append(Spacer(1, 3 * mm))

            sig_fields = ["Signed by:", "Name:", "Title:", "Date:"]
            for field in sig_fields:
                # Label + ruled line as a table row
                data = [[field, ""]]
                tbl = Table(data, colWidths=[22 * mm, 80 * mm])
                tbl.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (0, 0), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, 0), HexColor(b.get("caption", "#666666"))),
                    ("LINEBELOW", (1, 0), (1, 0), 0.5, rule_c),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ]))
                block.append(tbl)

            block.append(Spacer(1, 6 * mm))
            return block

        # First party
        party_1 = org if org else "[Party A]"
        flowables.extend(_sig_block(f"For and on behalf of {party_1}"))

        # Second party
        flowables.extend(_sig_block("For and on behalf of [Counterparty Name]"))

        # Witness block
        flowables.append(Spacer(1, 6 * mm))
        witness_h_style = _ps(
            "ContractWitnessH", brand=b, fontSize=11, textColor=primary,
            fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4,
        )
        flowables.append(Paragraph("Witness", witness_h_style))
        flowables.append(Spacer(1, 3 * mm))

        witness_fields = ["Witness signature:", "Witness name:"]
        for field in witness_fields:
            data = [[field, ""]]
            tbl = Table(data, colWidths=[30 * mm, 80 * mm])
            tbl.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, 0), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, 0), HexColor(b.get("caption", "#666666"))),
                ("LINEBELOW", (1, 0), (1, 0), 0.5, rule_c),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ]))
            flowables.append(tbl)

        return flowables

    # ------------------------------------------------------------------
    # Override generate() for contract header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the contract PDF with agreement header and confidential footer."""
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

        # Header/footer state

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 22) * mm
        right_m = margins.get("right", 22) * mm

        page_size = _PAGE_SIZES.get(layout.get("page_size", "A4"), A4)

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=title,
            author=self.brand.get("org", "briefkit"),
            subject="Agreement",
            creator="briefkit",
        )

        story = self.build_story(content)

        # Capture title for closure
        agreement_title = title
        brand = self.brand

        def _contract_first_page(canvas, doc):
            """No header on title page, just confidential footer."""
            canvas.saveState()
            page_w, _ = doc.pagesize
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(HexColor(brand.get("caption", "#666666")))
            canvas.drawCentredString(
                page_w / 2, 10 * mm,
                "CONFIDENTIAL",
            )
            canvas.restoreState()

        def _contract_later_pages(canvas, doc):
            """Header with agreement name; footer with page number and confidential."""
            canvas.saveState()
            page_w, page_h = doc.pagesize

            # Header: agreement name, right-aligned
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(HexColor(brand.get("caption", "#666666")))
            canvas.drawRightString(
                page_w - left_m, page_h - 15 * mm,
                agreement_title,
            )

            # Footer: page number and confidential
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(HexColor(brand.get("caption", "#666666")))
            canvas.drawString(
                left_m, 10 * mm,
                f"Page {doc.page}",
            )
            canvas.drawRightString(
                page_w - right_m, 10 * mm,
                "CONFIDENTIAL",
            )
            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_contract_first_page,
            onLaterPages=_contract_later_pages,
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
