"""
briefkit.templates.quote
~~~~~~~~~~~~~~~~~~~~~~~~~
Professional quote/estimate template — company branding, scope, pricing, terms.

Build order:
  Header → Quote Metadata → Client Info → Scope of Work → Pricing Table
  → Terms and Conditions → Acceptance Block

Key differences:
  - No cover page, no TOC, no dashboard
  - Header with company branding and "QUOTE" title
  - Quote metadata block (quote number, date, validity period)
  - Client information from overview content
  - Scope of work rendered from subsystem sections
  - Pricing table from markdown tables
  - Terms and conditions from guide_content
  - Acceptance/signature block at bottom
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from briefkit.extractor import parse_markdown
from briefkit.generator import (
    BaseBriefingTemplate,
    _hf_state,
)
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
    _safe_text,
    build_styles,
)


class QuoteTemplate(BaseBriefingTemplate):
    """
    Professional quote/estimate template.

    Produces a clean quote PDF with company branding, quote metadata,
    client info, scope of work, pricing table, terms and conditions,
    and an acceptance/signature block. Suitable for project quotes,
    estimates, proposals, and fee schedules.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the quote story:
          Header, metadata, client info, scope, pricing, terms, acceptance.
        """
        story: list = []
        b = self.brand
        primary = _hex(b, "primary")
        caption_c = _hex(b, "caption")
        body_c = _hex(b, "body_text")
        org = b.get("org", "")
        project = self.config.get("project", {})

        # --- Header: company branding + QUOTE title ---
        story.extend(self._build_header(org, project, primary, caption_c))

        # Divider line
        story.append(Spacer(1, 3 * mm))
        divider = Table([[""]], colWidths=[self.content_width], rowHeights=[1.5])
        divider.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, -1), 1.5, HexColor(b.get("primary", "#1B2A4A"))),
        ]))
        story.append(divider)
        story.append(Spacer(1, 6 * mm))

        # --- Quote metadata ---
        story.extend(self._build_metadata(primary, body_c))
        story.append(Spacer(1, 8 * mm))

        # --- Client info from overview ---
        overview = content.get("overview", "")
        if overview:
            client_label = _ps(
                "QuoteClientLabel", brand=b, fontSize=10,
                textColor=primary, fontName="Helvetica-Bold",
                spaceAfter=3,
            )
            story.append(Paragraph("CLIENT", client_label))

            for block in parse_markdown(overview)[:10]:
                story.extend(self.render_blocks([block]))
            story.append(Spacer(1, 8 * mm))

        # --- Scope of work from subsystems ---
        subsystems = content.get("subsystems", [])
        if subsystems:
            scope_label = _ps(
                "QuoteScopeLabel", brand=b, fontSize=12,
                textColor=primary, fontName="Helvetica-Bold",
                spaceAfter=4,
            )
            story.append(Paragraph("SCOPE OF WORK", scope_label))
            story.append(Spacer(1, 2 * mm))
            story.extend(self._build_scope_sections(subsystems))
            story.append(Spacer(1, 6 * mm))

        # --- Pricing table from markdown tables ---
        all_tables = self._collect_tables(content)
        if all_tables:
            pricing_label = _ps(
                "QuotePricingLabel", brand=b, fontSize=12,
                textColor=primary, fontName="Helvetica-Bold",
                spaceAfter=4,
            )
            story.append(Paragraph("PRICING", pricing_label))
            story.append(Spacer(1, 2 * mm))
            story.extend(self._build_pricing_table(all_tables))
            story.append(Spacer(1, 8 * mm))

        # --- Terms and conditions ---
        guide = content.get("guide_content", "")
        if guide:
            story.extend(self._build_terms_section(guide))
            story.append(Spacer(1, 8 * mm))

        # --- Acceptance / signature block ---
        story.extend(self._build_acceptance_block(org, body_c, caption_c, primary))

        return story

    # ------------------------------------------------------------------
    # Header: company branding + QUOTE title
    # ------------------------------------------------------------------

    def _build_header(
        self, org: str, project: dict, primary: HexColor, caption_c: HexColor,
    ) -> list:
        """Build header with company info left and QUOTE title right."""
        flowables: list = []
        b = self.brand

        # Left side: company info
        left_parts: list = []
        if org:
            org_style = _ps(
                "QuoteOrg", brand=b, fontSize=14,
                textColor=primary, fontName="Helvetica-Bold",
            )
            left_parts.append(Paragraph(org, org_style))

        tagline = project.get("tagline", "")
        if tagline:
            tag_style = _ps(
                "QuoteTagline", brand=b, fontSize=9,
                textColor=caption_c, fontName="Helvetica-Oblique",
            )
            left_parts.append(Paragraph(tagline, tag_style))

        address_parts = []
        for key in ("address", "city", "phone", "email"):
            val = project.get(key, "")
            if val:
                address_parts.append(val)
        if address_parts:
            addr_style = _ps(
                "QuoteAddr", brand=b, fontSize=8,
                textColor=caption_c, leading=11,
            )
            left_parts.append(Paragraph(
                "<br/>".join(_safe_text(p) for p in address_parts),
                addr_style,
            ))

        # Right side: QUOTE title
        title_style = _ps(
            "QuoteTitle", brand=b, fontSize=24,
            textColor=primary, fontName="Helvetica-Bold",
            alignment=2,
        )
        right_content = Paragraph("QUOTE", title_style)

        if left_parts:
            left_cell = left_parts if len(left_parts) > 1 else left_parts[0]
            if isinstance(left_cell, list):
                left_cell = Table(
                    [[p] for p in left_cell],
                    colWidths=[self.content_width * 0.6],
                )
                left_cell.setStyle(TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]))

            header_table = Table(
                [[left_cell, right_content]],
                colWidths=[self.content_width * 0.6, self.content_width * 0.4],
            )
            header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            flowables.append(header_table)
        else:
            flowables.append(right_content)

        return flowables

    # ------------------------------------------------------------------
    # Quote metadata
    # ------------------------------------------------------------------

    def _build_metadata(self, primary: HexColor, body_c: HexColor) -> list:
        """Build quote number, date, and validity metadata."""
        flowables: list = []
        b = self.brand

        label_style = _ps(
            "QuoteMetaLabel", brand=b, fontSize=9,
            textColor=primary, fontName="Helvetica-Bold",
        )
        value_style = _ps(
            "QuoteMetaValue", brand=b, fontSize=9,
            textColor=body_c,
        )

        meta_rows = []
        if self.doc_id:
            meta_rows.append([
                Paragraph("Quote #:", label_style),
                Paragraph(str(self.doc_id), value_style),
            ])
        meta_rows.append([
            Paragraph("Date:", label_style),
            Paragraph(self.date_str, value_style),
        ])
        meta_rows.append([
            Paragraph("Valid Until:", label_style),
            Paragraph("Valid for 30 days", value_style),
        ])

        if meta_rows:
            meta_table = Table(
                meta_rows,
                colWidths=[self.content_width * 0.15, self.content_width * 0.35],
                hAlign="RIGHT",
            )
            meta_table.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            flowables.append(meta_table)

        return flowables

    # ------------------------------------------------------------------
    # Scope of work sections
    # ------------------------------------------------------------------

    def _build_scope_sections(self, subsystems: list[dict]) -> list:
        """Render subsystem content as scope-of-work sections."""
        flowables: list = []
        b = self.brand
        primary = _hex(b, "primary")

        for idx, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {idx}")
            heading_style = _ps(
                "QuoteScopeH", brand=b, fontSize=11,
                textColor=primary, fontName="Helvetica-Bold",
                spaceBefore=6, spaceAfter=3,
            )
            flowables.append(_safe_para(f"{idx}. {_safe_text(name)}", heading_style))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                btype = block.get("type", "")
                # Skip top-level headings (already rendered as section name)
                if btype == "heading" and block.get("level", 1) <= 1:
                    continue
                # Skip tables (rendered separately in pricing section)
                if btype == "table":
                    continue
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
                if rendered >= 40:
                    break

            flowables.append(Spacer(1, 3 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Collect tables from subsystems
    # ------------------------------------------------------------------

    def _collect_tables(self, content: dict) -> list[dict]:
        """Gather tables with headers and rows from all subsystems."""
        tables: list[dict] = []
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                if tbl.get("headers") and tbl.get("rows"):
                    tables.append(tbl)
        return tables

    # ------------------------------------------------------------------
    # Pricing table
    # ------------------------------------------------------------------

    def _build_pricing_table(self, tables: list[dict]) -> list:
        """Render extracted tables as a professional pricing table."""
        flowables: list = []
        b = self.brand
        styles = build_styles(b)
        primary = _hex(b, "primary")
        rule_c = _hex(b, "rule")
        table_alt = HexColor("#f8f9fa")

        for tbl in tables:
            headers = tbl["headers"]
            col_count = len(headers)
            col_width = self.content_width / col_count

            header_row = [
                _safe_para(
                    f"<b>{_safe_text(str(h))}</b>",
                    styles["STYLE_TABLE_HEADER"],
                )
                for h in headers
            ]

            table_data = [header_row]
            for row in tbl.get("rows", []):
                sanitised = [("" if cell is None else cell) for cell in row]
                padded = list(sanitised) + [""] * max(0, col_count - len(sanitised))
                padded = padded[:col_count]
                table_data.append([
                    _safe_para(str(cell), styles["STYLE_TABLE_BODY"])
                    for cell in padded
                ])

            pricing_tbl = Table(
                table_data,
                colWidths=[col_width] * col_count,
                repeatRows=1,
            )
            pricing_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), primary),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.4, rule_c),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, table_alt]),
            ]))

            flowables.append(pricing_tbl)
            flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Terms and conditions
    # ------------------------------------------------------------------

    def _build_terms_section(self, guide: str) -> list:
        """Render guide_content as terms and conditions."""
        flowables: list = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")

        terms_label = _ps(
            "QuoteTermsLabel", brand=b, fontSize=12,
            textColor=primary, fontName="Helvetica-Bold",
            spaceAfter=4,
        )
        flowables.append(Paragraph("TERMS AND CONDITIONS", terms_label))
        flowables.append(Spacer(1, 2 * mm))

        terms_style = _ps(
            "QuoteTerms", brand=b, fontSize=9,
            textColor=body_c, leading=13,
        )
        for block in parse_markdown(guide)[:20]:
            if block.get("type") == "paragraph":
                flowables.append(_safe_para(
                    _safe_text(block.get("text", "")), terms_style,
                ))
            else:
                flowables.extend(self.render_blocks([block]))

        return flowables

    # ------------------------------------------------------------------
    # Acceptance / signature block
    # ------------------------------------------------------------------

    def _build_acceptance_block(
        self, org: str, body_c: HexColor, caption_c: HexColor, primary: HexColor,
    ) -> list:
        """Build an acceptance/signature block at the bottom of the quote."""
        flowables: list = []
        b = self.brand

        accept_label = _ps(
            "QuoteAcceptLabel", brand=b, fontSize=12,
            textColor=primary, fontName="Helvetica-Bold",
            spaceAfter=4,
        )
        flowables.append(Paragraph("ACCEPTANCE", accept_label))
        flowables.append(Spacer(1, 2 * mm))

        accept_body = _ps(
            "QuoteAcceptBody", brand=b, fontSize=9,
            textColor=body_c, leading=13,
        )
        flowables.append(Paragraph(
            "By signing below, the client accepts this quote and agrees to the "
            "terms and conditions outlined above.",
            accept_body,
        ))
        flowables.append(Spacer(1, 10 * mm))

        # Signature lines
        sig_label = _ps(
            "QuoteSigLabel", brand=b, fontSize=8,
            textColor=caption_c,
        )

        sig_data = [
            [
                Paragraph("Signature: ____________________________", sig_label),
                Paragraph("Date: ____________________", sig_label),
            ],
            [
                Paragraph("Name: ____________________________", sig_label),
                Paragraph("Title: ____________________", sig_label),
            ],
        ]

        sig_table = Table(
            sig_data,
            colWidths=[self.content_width * 0.55, self.content_width * 0.45],
        )
        sig_table.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ]))

        flowables.append(KeepTogether([sig_table]))

        return flowables

    # ------------------------------------------------------------------
    # Override generate() for quote-specific header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the quote PDF with minimal header/footer."""
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

        # Header/footer state
        _hf_state["section"] = ""
        _hf_state["date"] = self.date_str
        _hf_state["doc_id"] = ""
        _hf_state["brand"] = self.brand

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 20) * mm
        bottom_m = margins.get("bottom", 20) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=content.get("title", "Quote"),
            author=self.brand.get("org", "briefkit"),
            subject="Quote",
            creator="briefkit",
        )

        story = self.build_story(content)

        caption_color = HexColor(self.brand.get("caption", "#666666"))
        org = self.brand.get("org", "")

        def _quote_footer(canvas, doc_inner):
            """Footer: org name left, page number right."""
            canvas.saveState()
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(caption_color)
            if org:
                canvas.drawString(
                    doc_inner.leftMargin, 10 * mm, org,
                )
            canvas.drawRightString(
                doc_inner.pagesize[0] - doc_inner.rightMargin, 10 * mm,
                f"Page {doc_inner.page}",
            )
            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_quote_footer,
            onLaterPages=_quote_footer,
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
