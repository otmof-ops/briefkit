"""
briefkit.templates.invoice
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Professional invoice template — compact header, line items, totals.

Build order:
  Header → Invoice Metadata → Bill To → Line Items Table → Totals → Payment Terms → Footer

Key differences:
  - No cover page, no TOC, no executive summary, no bibliography
  - Compact header with company name left and "INVOICE" title right
  - Invoice metadata block (invoice number, date, due date)
  - Bill-to section from overview/README content
  - Line items table from subsystem markdown tables
  - Subtotal, tax, total footer below table
  - Payment terms from guide_content or closing paragraph
  - Minimal footer with org name
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
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


class InvoiceTemplate(BaseBriefingTemplate):
    """
    Professional invoice template.

    Produces a clean invoice PDF with company branding, invoice metadata,
    bill-to section, line items table, totals, and payment terms.
    Suitable for invoices, billing statements, and fee schedules.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the invoice story:
          Header, metadata, bill-to, line items, totals, payment terms, footer.
        """
        story: list = []
        b = self.brand
        primary = _hex(b, "primary")
        caption_c = _hex(b, "caption")
        body_c = _hex(b, "body_text")
        org = b.get("org", "")
        project = self.config.get("project", {})

        # --- Compact header: company left, INVOICE right ---
        header_data = self._build_header_row(org, project, primary, caption_c)
        story.extend(header_data)

        # Divider line
        story.append(Spacer(1, 3 * mm))
        divider = Table([[""]], colWidths=[self.content_width], rowHeights=[1.5])
        divider.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, -1), 1.5, HexColor(b.get("primary", "#1B2A4A"))),
        ]))
        story.append(divider)
        story.append(Spacer(1, 6 * mm))

        # --- Invoice metadata ---
        story.extend(self._build_metadata_block(primary, body_c))
        story.append(Spacer(1, 6 * mm))

        # --- Bill To ---
        overview = content.get("overview", "")
        if overview:
            bill_to_label = _ps(
                "InvoiceBillToLabel", brand=b, fontSize=9,
                textColor=caption_c, fontName="Helvetica-Bold",
                spaceAfter=2,
            )
            story.append(Paragraph("BILL TO", bill_to_label))

            for block in parse_markdown(overview)[:10]:
                story.extend(self.render_blocks([block]))
            story.append(Spacer(1, 6 * mm))

        # --- Line items table ---
        all_tables = self._collect_tables(content)
        if all_tables:
            story.extend(self._build_line_items_table(all_tables))
        else:
            story.extend(self._build_line_items_from_subsystems(content))

        # --- Totals ---
        story.extend(self._build_totals_block(all_tables, body_c, primary))
        story.append(Spacer(1, 10 * mm))

        # --- Payment terms ---
        guide = content.get("guide_content", "")
        if guide:
            terms_label = _ps(
                "InvoiceTermsLabel", brand=b, fontSize=9,
                textColor=caption_c, fontName="Helvetica-Bold",
                spaceAfter=3,
            )
            story.append(Paragraph("PAYMENT TERMS", terms_label))

            terms_style = _ps(
                "InvoiceTerms", brand=b, fontSize=9,
                textColor=body_c, leading=13,
            )
            for block in parse_markdown(guide)[:10]:
                if block.get("type") == "paragraph":
                    story.append(_safe_para(
                        _safe_text(block.get("text", "")), terms_style,
                    ))
                else:
                    story.extend(self.render_blocks([block]))
            story.append(Spacer(1, 6 * mm))

        # --- Footer ---
        if org:
            footer_style = _ps(
                "InvoiceFooter", brand=b, fontSize=8,
                textColor=caption_c, alignment=1,
            )
            story.append(Spacer(1, 10 * mm))
            story.append(Paragraph(org, footer_style))

        return story

    # ------------------------------------------------------------------
    # Header row: company left, INVOICE right
    # ------------------------------------------------------------------

    def _build_header_row(
        self, org: str, project: dict, primary: HexColor, caption_c: HexColor,
    ) -> list:
        """Build the compact header with company info left and INVOICE title right."""
        flowables: list = []
        b = self.brand

        # Build left-side content (company info)
        left_parts: list = []
        if org:
            org_style = _ps(
                "InvoiceOrg", brand=b, fontSize=14,
                textColor=primary, fontName="Helvetica-Bold",
            )
            left_parts.append(Paragraph(org, org_style))

        address_parts = []
        for key in ("address", "city", "phone", "email"):
            val = project.get(key, "")
            if val:
                address_parts.append(val)
        if address_parts:
            addr_style = _ps(
                "InvoiceAddr", brand=b, fontSize=8,
                textColor=caption_c, leading=11,
            )
            left_parts.append(Paragraph(
                "<br/>".join(_safe_text(p) for p in address_parts),
                addr_style,
            ))

        # Build right-side content (INVOICE title)
        title_style = _ps(
            "InvoiceTitle", brand=b, fontSize=24,
            textColor=primary, fontName="Helvetica-Bold",
            alignment=2,
        )
        right_content = Paragraph("INVOICE", title_style)

        if left_parts:
            # Combine left and right in a table
            left_cell = left_parts if len(left_parts) > 1 else left_parts[0]
            if isinstance(left_cell, list):
                # Stack paragraphs vertically using a nested table
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
    # Invoice metadata
    # ------------------------------------------------------------------

    def _build_metadata_block(self, primary: HexColor, body_c: HexColor) -> list:
        """Build invoice number, date, and due date metadata."""
        flowables: list = []
        b = self.brand

        label_style = _ps(
            "InvoiceMetaLabel", brand=b, fontSize=9,
            textColor=primary, fontName="Helvetica-Bold",
        )
        value_style = _ps(
            "InvoiceMetaValue", brand=b, fontSize=9,
            textColor=body_c,
        )

        meta_rows = []
        if self.doc_id:
            meta_rows.append([
                Paragraph("Invoice #:", label_style),
                Paragraph(str(self.doc_id), value_style),
            ])
        meta_rows.append([
            Paragraph("Date:", label_style),
            Paragraph(self.date_str, value_style),
        ])
        meta_rows.append([
            Paragraph("Due Date:", label_style),
            Paragraph("Upon receipt", value_style),
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
    # Line items table from markdown tables
    # ------------------------------------------------------------------

    def _build_line_items_table(self, tables: list[dict]) -> list:
        """Render extracted tables as a professional invoice line-items table."""
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

            line_table = Table(
                table_data,
                colWidths=[col_width] * col_count,
                repeatRows=1,
            )
            line_table.setStyle(TableStyle([
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

            flowables.append(line_table)
            flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Fallback: subsystem content as line items
    # ------------------------------------------------------------------

    def _build_line_items_from_subsystems(self, content: dict) -> list:
        """Render subsystem content as line items when no tables found."""
        flowables: list = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")

        subsystems = content.get("subsystems", [])
        if not subsystems:
            return flowables

        # Build a simple description table from subsystem names
        label_style = _ps(
            "InvoiceItemLabel", brand=b, fontSize=9,
            textColor=body_c,
        )
        header_style = _ps(
            "InvoiceItemHeader", brand=b, fontSize=9,
            textColor=white, fontName="Helvetica-Bold",
        )

        table_data = [[
            Paragraph("Description", header_style),
            Paragraph("Details", header_style),
        ]]

        for sub in subsystems[:30]:
            name = sub.get("name", "Item")
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            detail = ""
            for block in blocks[:3]:
                if block.get("type") == "paragraph":
                    detail = block.get("text", "")
                    break

            table_data.append([
                _safe_para(_safe_text(name), label_style),
                _safe_para(_safe_text(detail)[:200], label_style),
            ])

        item_table = Table(
            table_data,
            colWidths=[self.content_width * 0.35, self.content_width * 0.65],
            repeatRows=1,
        )
        rule_c = _hex(b, "rule")
        item_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.4, rule_c),
        ]))

        flowables.append(item_table)
        flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Totals block
    # ------------------------------------------------------------------

    def _build_totals_block(
        self, tables: list[dict], body_c: HexColor, primary: HexColor,
    ) -> list:
        """Build subtotal, tax, and total lines right-aligned below the table."""
        flowables: list = []
        b = self.brand

        label_style = _ps(
            "InvoiceTotalLabel", brand=b, fontSize=10,
            textColor=body_c,
        )
        total_label_style = _ps(
            "InvoiceTotalBold", brand=b, fontSize=11,
            textColor=primary, fontName="Helvetica-Bold",
        )
        value_style = _ps(
            "InvoiceTotalValue", brand=b, fontSize=10,
            textColor=body_c, alignment=2,
        )
        total_value_style = _ps(
            "InvoiceTotalValueBold", brand=b, fontSize=11,
            textColor=primary, fontName="Helvetica-Bold",
            alignment=2,
        )

        # Attempt to compute totals from numeric last-column values
        row_total = 0.0
        has_numeric = False
        for tbl in tables:
            for row in tbl.get("rows", []):
                if row:
                    last_cell = str(row[-1]).strip().replace(",", "").replace("$", "")
                    try:
                        row_total += float(last_cell)
                        has_numeric = True
                    except (ValueError, TypeError):
                        pass

        if has_numeric:
            subtotal_str = f"${row_total:,.2f}"
            tax_str = "—"
            total_str = subtotal_str
        else:
            subtotal_str = "—"
            tax_str = "—"
            total_str = "See line items"

        totals_data = [
            [Paragraph("Subtotal:", label_style), Paragraph(subtotal_str, value_style)],
            [Paragraph("Tax:", label_style), Paragraph(tax_str, value_style)],
            [
                Paragraph("TOTAL:", total_label_style),
                Paragraph(total_str, total_value_style),
            ],
        ]

        rule_c = _hex(b, "rule")
        totals_table = Table(
            totals_data,
            colWidths=[self.content_width * 0.15, self.content_width * 0.2],
            hAlign="RIGHT",
        )
        totals_table.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEABOVE", (0, 0), (-1, 0), 0.4, rule_c),
            ("LINEABOVE", (0, -1), (-1, -1), 1, primary),
        ]))

        flowables.append(Spacer(1, 2 * mm))
        flowables.append(totals_table)

        return flowables

    # ------------------------------------------------------------------
    # Override generate() for invoice-specific header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the invoice PDF with minimal footer."""
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
            title=content.get("title", "Invoice"),
            author=self.brand.get("org", "briefkit"),
            subject="Invoice",
            creator="briefkit",
        )

        story = self.build_story(content)

        caption_color = HexColor(self.brand.get("caption", "#666666"))
        org = self.brand.get("org", "")

        def _invoice_footer(canvas, doc_inner):
            """Minimal footer: org name left, page number right."""
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
            onFirstPage=_invoice_footer,
            onLaterPages=_invoice_footer,
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
