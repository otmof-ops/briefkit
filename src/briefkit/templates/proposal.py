"""
briefkit.templates.proposal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Business proposal template.

Build order:
  Cover Page → TOC → Executive Summary → Scope & Objectives →
  Deliverables → Timeline → Pricing/Budget → Terms & Conditions →
  Acceptance Block → Back Cover

Key differences:
  - Professional cover page with "PROPOSAL" subtitle
  - Executive summary drawn from overview
  - Deliverables derived from subsystems
  - Timeline section auto-detected from tables with date-like data
  - Pricing/budget section auto-detected from tables with currency/number data
  - Terms & conditions from guide_content
  - Formal acceptance/sign-off block
  - Back cover with brand bar
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, white
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
from briefkit.templates._helpers import should_skip

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
# Heuristic patterns for table classification
# ---------------------------------------------------------------------------

_CURRENCY_PATTERN = re.compile(r'[\$\£\€\¥]|USD|AUD|GBP|EUR|cost|price|budget|total|amount', re.IGNORECASE)
_DATE_PATTERN = re.compile(r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b|Q[1-4]|phase|week|month|milestone|timeline', re.IGNORECASE)


def _classify_table(tbl: dict) -> str:
    """
    Classify a table as 'timeline', 'pricing', or 'general' based on
    header and cell content heuristics.
    """
    headers_text = " ".join(tbl.get("headers", []))
    rows_text = " ".join(
        " ".join(str(c) for c in row)
        for row in tbl.get("rows", [])[:5]
    )
    combined = headers_text + " " + rows_text

    if _CURRENCY_PATTERN.search(combined):
        return "pricing"
    if _DATE_PATTERN.search(combined):
        return "timeline"
    return "general"


class ProposalTemplate(BaseBriefingTemplate):
    """
    Business proposal template.

    Produces a professional proposal PDF with cover page, executive
    summary, scope, deliverables, timeline, pricing, terms, and an
    acceptance sign-off block.  Suitable for project proposals, RFP
    responses, and commercial offers.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the proposal story:
          Cover, TOC, Executive Summary, Scope & Objectives,
          Deliverables, Timeline, Pricing, Terms, Acceptance, Back Cover.
        """
        story = []
        b = self.brand
        title = content.get("title", self.target_path.name.replace("-", " ").title())

        # ============================================================
        # Cover Page
        # ============================================================
        story.extend(self._build_cover_page(content, title))
        story.append(PageBreak())

        # ============================================================
        # Pre-build sections for TOC
        # ============================================================
        cfg = self.config
        exec_summary = [] if should_skip(cfg, "executive_summary") else self._build_executive_summary(content)
        scope = [] if should_skip(cfg, "scope") else self._build_scope(content)
        deliverables = self._build_deliverables(content)
        timeline = self._build_timeline(content)
        pricing = self._build_pricing(content)
        terms = self._build_terms(content)
        acceptance = self._build_acceptance_block()

        # ============================================================
        # Table of Contents
        # ============================================================
        if not should_skip(cfg, "toc"):
            story.extend(self._heading_with_rule("Table of Contents", "STYLE_H1"))

            toc_entries = []
            if exec_summary:
                toc_entries.append((1, "Executive Summary"))
            if scope:
                toc_entries.append((1, "Scope & Objectives"))
            toc_entries.append((1, "Deliverables"))
            for i, sub in enumerate(content.get("subsystems", []), 1):
                toc_entries.append((2, f"  {i}. {sub.get('name', f'Deliverable {i}')}"))
            if timeline:
                toc_entries.append((1, "Timeline"))
            if pricing:
                toc_entries.append((1, "Pricing & Budget"))
            if terms:
                toc_entries.append((1, "Terms & Conditions"))
            toc_entries.append((1, "Acceptance & Sign-off"))

            from briefkit.generator import build_toc
            story.extend(build_toc(toc_entries, brand=b, content_width=self.content_width))
            story.append(PageBreak())

        # ============================================================
        # Body Sections
        # ============================================================
        if exec_summary:
            story.extend(exec_summary)
            story.append(PageBreak())

        if scope:
            story.extend(scope)
            story.append(Spacer(1, 6 * mm))

        story.extend(deliverables)
        story.append(PageBreak())

        if timeline:
            story.extend(timeline)
            story.append(PageBreak())

        if pricing:
            story.extend(pricing)
            story.append(PageBreak())

        if terms:
            story.extend(terms)
            story.append(PageBreak())

        story.extend(acceptance)
        story.append(PageBreak())

        # ============================================================
        # Back Cover
        # ============================================================
        if not should_skip(cfg, "back_cover"):
            story.extend(self._build_back_cover_page())

        return story

    # ------------------------------------------------------------------
    # Cover Page
    # ------------------------------------------------------------------

    def _build_cover_page(self, content: dict, title: str) -> list:
        """Build professional cover page with project title and org branding."""
        flowables: list = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")
        caption_c = _hex(b, "caption")
        org = b.get("org", "")

        flowables.append(Spacer(1, 35 * mm))

        # Org name
        if org:
            org_style = _ps(
                "ProposalCoverOrg", brand=b, fontSize=14, textColor=primary,
                fontName="Helvetica-Bold", alignment=1, spaceAfter=6,
            )
            flowables.append(Paragraph(org, org_style))
            flowables.append(Spacer(1, 8 * mm))

        # PROPOSAL — large prominent heading
        proposal_style = _ps(
            "ProposalCoverLabel", brand=b, fontSize=28, textColor=primary,
            fontName="Helvetica-Bold", alignment=1, spaceAfter=6,
        )
        flowables.append(Paragraph("PROPOSAL", proposal_style))

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

        # Project title — smaller, below PROPOSAL
        title_style = _ps(
            "ProposalCoverTitle", brand=b, fontSize=16, textColor=primary,
            fontName="Helvetica-Bold", alignment=1, spaceAfter=8,
        )
        flowables.append(Paragraph(title, title_style))

        # Date
        flowables.append(Spacer(1, 20 * mm))
        date_style = _ps(
            "ProposalCoverDate", brand=b, fontSize=10, textColor=body_c,
            alignment=1,
        )
        flowables.append(Paragraph(self.date_str, date_style))

        # Project tagline if available
        project = self.config.get("project", {})
        tagline = project.get("tagline", "")
        if tagline:
            flowables.append(Spacer(1, 6 * mm))
            tag_style = _ps(
                "ProposalCoverTag", brand=b, fontSize=9, textColor=caption_c,
                fontName="Helvetica-Oblique", alignment=1,
            )
            flowables.append(Paragraph(tagline, tag_style))

        # -- Cover footer band (secondary/cyan) with contact info --
        secondary = _hex(b, "secondary")
        contact_parts = []
        if org:
            contact_parts.append(org)
        email = b.get("email", "")
        if email:
            contact_parts.append(email)
        phone = b.get("phone", "")
        if phone:
            contact_parts.append(phone)
        contact_text = "  |  ".join(contact_parts) if contact_parts else ""

        if contact_text:
            flowables.append(Spacer(1, 30 * mm))
            band_style = _ps(
                "ProposalCoverBand", brand=b, fontSize=9, textColor=white,
                fontName="Helvetica", alignment=1,
            )
            band_data = [[Paragraph(contact_text, band_style)]]
            band = Table(
                band_data,
                colWidths=[self.content_width],
                rowHeights=None,
            )
            band.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), secondary),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]))
            flowables.append(band)

        return flowables

    # ------------------------------------------------------------------
    # Executive Summary
    # ------------------------------------------------------------------

    def _build_executive_summary(self, content: dict) -> list:
        """Build executive summary from the overview content."""
        flowables: list = []

        flowables.extend(self._heading_with_rule("Executive Summary", "STYLE_H1"))

        overview = content.get("overview", "")
        if overview:
            for block in parse_markdown(overview)[:20]:
                flowables.extend(self.render_blocks([block]))
        else:
            title = content.get("title", "this project")
            fallback = (
                f"This proposal outlines the scope, deliverables, and terms for "
                f"{title}. The following sections detail our approach, timeline, "
                f"and investment required."
            )
            flowables.append(Paragraph(fallback, self.styles["STYLE_BODY"]))

        return flowables

    # ------------------------------------------------------------------
    # Scope & Objectives
    # ------------------------------------------------------------------

    def _build_scope(self, content: dict) -> list:
        """Build scope and objectives section."""
        flowables: list = []
        b = self.brand

        flowables.extend(self._heading_with_rule("Scope &amp; Objectives", "STYLE_H1"))

        orientation = content.get("orientation", "")
        subsystems = content.get("subsystems", [])
        title = content.get("title", "this project")

        if orientation:
            for block in parse_markdown(orientation)[:15]:
                flowables.extend(self.render_blocks([block]))
        else:
            scope_text = (
                f"The scope of this proposal covers {len(subsystems)} "
                f"deliverable area(s) for {title}."
            )
            flowables.append(Paragraph(scope_text, self.styles["STYLE_BODY"]))

        # Objectives as bullet list from subsystem names
        if subsystems:
            flowables.append(Spacer(1, 2 * mm))
            flowables.extend(self._heading_with_rule("Key Objectives", "STYLE_H2"))
            obj_style = _ps(
                "ProposalObjective", brand=b, fontSize=10,
                textColor=_hex(b, "body_text"), leading=14, leftIndent=12,
            )
            for sub in subsystems:
                name = sub.get("name", "")
                if name:
                    flowables.append(_safe_para(f"\u2022 {name}", obj_style))

        return flowables

    # ------------------------------------------------------------------
    # Deliverables
    # ------------------------------------------------------------------

    def _build_deliverables(self, content: dict) -> list:
        """Build deliverables section — one subsection per subsystem."""
        flowables: list = []

        flowables.extend(self._heading_with_rule("Deliverables", "STYLE_H1"))

        subsystems = content.get("subsystems", [])
        if not subsystems:
            overview = content.get("overview", "Deliverables to be confirmed.")
            flowables.append(Paragraph(overview[:2000], self.styles["STYLE_BODY"]))
            return flowables

        for idx, sub in enumerate(subsystems, start=1):
            name = sub.get("name", f"Deliverable {idx}")
            flowables.extend(self._heading_with_rule(f"{idx}. {name}", "STYLE_H2"))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                btype = block.get("type", "")
                if btype == "heading" and block.get("level", 1) <= 1:
                    continue
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
                    if rendered >= 80:
                        break
                if rendered >= 80:
                    break

            flowables.append(Spacer(1, 3 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------

    def _build_timeline(self, content: dict) -> list:
        """Build timeline section from tables with date-like data."""
        timeline_tables = self._collect_tables(content, "timeline")
        if not timeline_tables:
            return []

        flowables: list = []
        flowables.extend(self._heading_with_rule("Timeline", "STYLE_H1"))
        flowables.append(Paragraph(
            "The following timeline outlines the key milestones and phases.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 2 * mm))

        from briefkit.elements.tables import build_data_table

        secondary = _hex(self.brand, "secondary")
        for name, tbl in timeline_tables[:5]:
            if name:
                flowables.append(Paragraph(name, self.styles["STYLE_H2"]))
            flowables.extend(build_data_table(
                tbl["headers"], tbl["rows"],
                brand=self.brand, content_width=self.content_width,
                header_color=secondary,
            ))
            flowables.append(Spacer(1, 3 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Pricing / Budget
    # ------------------------------------------------------------------

    def _build_pricing(self, content: dict) -> list:
        """Build pricing/budget section from tables with currency/number data."""
        pricing_tables = self._collect_tables(content, "pricing")
        if not pricing_tables:
            return []

        flowables: list = []
        flowables.extend(self._heading_with_rule("Pricing &amp; Budget", "STYLE_H1"))
        flowables.append(Paragraph(
            "The following table(s) detail the proposed investment.",
            self.styles["STYLE_BODY"],
        ))
        flowables.append(Spacer(1, 2 * mm))

        from briefkit.elements.tables import build_data_table

        secondary = _hex(self.brand, "secondary")
        for name, tbl in pricing_tables[:5]:
            if name:
                flowables.append(Paragraph(name, self.styles["STYLE_H2"]))
            flowables.extend(build_data_table(
                tbl["headers"], tbl["rows"],
                brand=self.brand, content_width=self.content_width,
                header_color=secondary,
            ))
            flowables.append(Spacer(1, 3 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Terms & Conditions
    # ------------------------------------------------------------------

    def _build_terms(self, content: dict) -> list:
        """Build terms and conditions from guide_content."""
        guide = content.get("guide_content", "")
        if not guide:
            return []

        flowables: list = []
        flowables.extend(self._heading_with_rule("Terms &amp; Conditions", "STYLE_H1"))

        for block in parse_markdown(guide)[:40]:
            flowables.extend(self.render_blocks([block]))

        return flowables

    # ------------------------------------------------------------------
    # Acceptance / Sign-off Block
    # ------------------------------------------------------------------

    def _build_acceptance_block(self) -> list:
        """Build formal acceptance and sign-off section."""
        flowables: list = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")
        org = b.get("org", "")
        rule_c = HexColor(b.get("rule", "#CCCCCC"))

        flowables.extend(self._heading_with_rule("Acceptance &amp; Sign-off", "STYLE_H1"))

        intro_style = _ps(
            "ProposalAcceptIntro", brand=b, fontSize=10, textColor=body_c,
            spaceAfter=8,
        )
        flowables.append(Paragraph(
            "By signing below, the parties acknowledge acceptance of this "
            "proposal including all terms, deliverables, and pricing as described.",
            intro_style,
        ))
        flowables.append(Spacer(1, 6 * mm))

        def _sig_block(party_label: str) -> list:
            """Generate a single party signature block."""
            block: list = []
            party_h = _ps(
                "ProposalPartyH", brand=b, fontSize=11, textColor=primary,
                fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4,
            )
            block.append(Paragraph(party_label, party_h))
            block.append(Spacer(1, 3 * mm))

            for field in ["Signed by:", "Name:", "Title:", "Date:"]:
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

        # Proposer
        proposer = org if org else "[Proposer]"
        flowables.extend(_sig_block(f"For and on behalf of {proposer}"))

        # Client
        flowables.extend(_sig_block("For and on behalf of [Client]"))

        return flowables

    # ------------------------------------------------------------------
    # Back Cover
    # ------------------------------------------------------------------

    def _build_back_cover_page(self) -> list:
        """Build back cover with brand bar."""
        flowables: list = []
        b = self.brand
        primary = _hex(b, "primary")
        caption_c = _hex(b, "caption")
        org = b.get("org", "")

        flowables.append(Spacer(1, 80 * mm))

        # Brand bar
        bar_data = [[""]]
        bar = Table(bar_data, colWidths=[self.content_width], rowHeights=[4])
        bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor(b.get("primary", "#1B2A4A"))),
        ]))
        flowables.append(bar)
        flowables.append(Spacer(1, 10 * mm))

        # Org name
        if org:
            org_style = _ps(
                "ProposalBackOrg", brand=b, fontSize=14, textColor=primary,
                fontName="Helvetica-Bold", alignment=1,
            )
            flowables.append(Paragraph(org, org_style))

        # Colophon
        flowables.append(Spacer(1, 4 * mm))
        colophon_style = _ps(
            "ProposalColophon", brand=b, fontSize=8, textColor=caption_c,
            alignment=1,
        )
        flowables.append(Paragraph(
            f"Generated by briefkit on {self.date_str}.",
            colophon_style,
        ))

        return flowables

    # ------------------------------------------------------------------
    # Heading with underline rule
    # ------------------------------------------------------------------

    def _heading_with_rule(self, text: str, style_key: str = "STYLE_H1") -> list:
        """Return a heading paragraph followed by a thin secondary-colored rule."""
        secondary = _hex(self.brand, "secondary")
        flowables = [
            _safe_para(text, self.styles[style_key]),
            Spacer(1, 1 * mm),
        ]
        rule = Table([[""]], colWidths=[self.content_width], rowHeights=[0.5])
        rule.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, secondary),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        flowables.append(rule)
        flowables.append(Spacer(1, 2 * mm))
        return flowables

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _collect_tables(self, content: dict, category: str) -> list[tuple[str, dict]]:
        """
        Collect tables from subsystems matching the given category
        ('timeline' or 'pricing').
        """
        results: list[tuple[str, dict]] = []
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                if tbl.get("headers") and tbl.get("rows"):
                    if _classify_table(tbl) == category:
                        results.append((sub.get("name", ""), tbl))
        return results

    # ------------------------------------------------------------------
    # Override generate() for proposal header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the proposal PDF with branded header and footer."""
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

        doc = self._build_doc(
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            subject="Proposal",
        )

        story = self.build_story(content)
        story = self._finalize_story(story)

        proposal_title = title
        brand = self.brand

        def _proposal_first_page(canvas, doc_inner):
            """No header on cover page."""
            canvas.saveState()
            canvas.restoreState()

        def _proposal_later_pages(canvas, doc_inner):
            """Header with proposal title; footer with page number."""
            canvas.saveState()
            page_w, page_h = doc_inner.pagesize

            # Header
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(HexColor(brand.get("caption", "#666666")))
            canvas.drawRightString(
                page_w - right_m, page_h - 15 * mm,
                proposal_title,
            )

            # Footer
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(HexColor(brand.get("caption", "#666666")))
            canvas.drawCentredString(
                page_w / 2, 10 * mm,
                f"Page {doc_inner.page}",
            )
            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_proposal_first_page,
            onLaterPages=_proposal_later_pages,
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

    def build_back_cover(self) -> list:
        return []
