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

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
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
)
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
    _safe_text,
)

# Canonical 5-column schema for invoice line items
_CANONICAL_HEADERS = ["Qty", "Description", "Rate", "Adjust", "Sub Total"]

# Header-matching patterns for column mapping
_COL_PATTERNS = {
    "qty": re.compile(r"(?i)\b(qty|quantity|hours|hrs|units)\b"),
    "description": re.compile(r"(?i)\b(description|service|item|name|detail)\b"),
    "rate": re.compile(r"(?i)\b(rate|price|cost|unit[\s_-]?price)\b"),
    "adjust": re.compile(r"(?i)\b(adjust|adjustment|discount|disc)\b"),
    "subtotal": re.compile(r"(?i)\b(total|amount|subtotal|sub[\s_-]?total|sum)\b"),
}

# Neutral colours for invoice body (no brand colours)
_HEADER_BG = HexColor("#f2f2f2")
_GRID_COLOR = HexColor("#CCCCCC")
_ROW_ALT = HexColor("#f8f9fa")


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
            ("LINEABOVE", (0, 0), (-1, -1), 1.5, _GRID_COLOR),
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
        story.extend(
            self._build_totals_block(all_tables, body_c, primary, content),
        )
        story.append(Spacer(1, 10 * mm))

        # --- Payment details ---
        story.extend(self._build_payment_details(content, b, caption_c, body_c))

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
                textColor=black, leading=13,
            )
            for block in parse_markdown(guide)[:10]:
                if block.get("type") == "paragraph":
                    story.append(_safe_para(
                        _safe_text(block.get("text", "")), terms_style,
                    ))
                else:
                    story.extend(self.render_blocks([block]))
            story.append(Spacer(1, 6 * mm))

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
                textColor=black, fontName="Helvetica-Bold",
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

    def _build_metadata_block(self, _primary: HexColor, _body_c: HexColor) -> list:
        """Build invoice number, date, and due date metadata."""
        flowables: list = []
        b = self.brand

        label_style = _ps(
            "InvoiceMetaLabel", brand=b, fontSize=9,
            textColor=black, fontName="Helvetica-Bold",
        )
        value_style = _ps(
            "InvoiceMetaValue", brand=b, fontSize=9,
            textColor=black,
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

    # ------------------------------------------------------------------
    # 5-column mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_columns(headers: list[str]) -> dict[str, int] | None:
        """Map source headers to canonical column indices.

        Returns a dict {canonical_key: source_index} or None if mapping
        is impossible.
        """
        mapping: dict[str, int] = {}
        used: set[int] = set()
        for key, pattern in _COL_PATTERNS.items():
            for idx, h in enumerate(headers):
                if idx not in used and pattern.search(str(h)):
                    mapping[key] = idx
                    used.add(idx)
                    break
        return mapping if mapping else None

    @staticmethod
    def _row_to_canonical(row: list, mapping: dict[str, int]) -> list[str]:
        """Convert a source row to the 5-column canonical order."""
        keys = ["qty", "description", "rate", "adjust", "subtotal"]
        result: list[str] = []
        for k in keys:
            idx = mapping.get(k)
            if idx is not None and idx < len(row):
                result.append(str(row[idx]) if row[idx] is not None else "")
            else:
                result.append("\u2014")
        return result

    def _build_line_items(self, tables: list[dict]) -> tuple[list[list[str]], bool]:
        """Normalise tables into canonical 5-column rows.

        Returns (data_rows_without_header, has_numeric_subtotal).
        """
        rows: list[list[str]] = []
        for tbl in tables:
            headers = tbl["headers"]
            col_count = len(headers)

            if col_count == 5:
                # Use directly
                for row in tbl.get("rows", []):
                    sanitised = [
                        str(c) if c is not None else "" for c in row
                    ]
                    padded = (sanitised + [""] * 5)[:5]
                    rows.append(padded)
            else:
                mapping = self._map_columns(headers)
                if mapping:
                    for row in tbl.get("rows", []):
                        rows.append(self._row_to_canonical(row, mapping))
                else:
                    # Unmappable — flatten all rows as description lines
                    for row in tbl.get("rows", []):
                        desc = " | ".join(
                            str(c) for c in row if c is not None
                        )
                        rows.append(["1", desc, "\u2014", "\u2014", "\u2014"])

        return rows

    def _build_line_items_table(self, tables: list[dict]) -> list:
        """Render extracted tables as a professional 5-column invoice table.

        Columns: Qty | Description | Rate | Adjust | Sub Total
        Header: light grey background, black text, Helvetica-Bold 9pt.
        Body: black text on white, light grey grid.
        """
        flowables: list = []
        b = self.brand

        header_style = _ps(
            "InvTblHeader", brand=b, fontSize=9,
            textColor=black, fontName="Helvetica-Bold",
        )
        body_style = _ps(
            "InvTblBody", brand=b, fontSize=9,
            textColor=black, fontName="Helvetica",
        )

        data_rows = self._build_line_items(tables)

        # Build header row
        header_row = [
            Paragraph(f"<b>{h}</b>", header_style)
            for h in _CANONICAL_HEADERS
        ]
        table_data = [header_row]

        for row in data_rows:
            table_data.append([
                _safe_para(_safe_text(str(cell)), body_style)
                for cell in row
            ])

        # Column widths: Qty 10%, Description 40%, Rate 15%, Adjust 15%, Sub Total 20%
        col_widths = [
            self.content_width * 0.10,
            self.content_width * 0.40,
            self.content_width * 0.15,
            self.content_width * 0.15,
            self.content_width * 0.20,
        ]

        line_table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1,
        )
        line_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), black),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.4, _GRID_COLOR),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, _ROW_ALT]),
        ]))

        flowables.append(line_table)
        flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Fallback: subsystem content as line items
    # ------------------------------------------------------------------

    def _build_line_items_from_subsystems(self, content: dict) -> list:
        """Render subsystem names as 5-column line items when no tables found.

        Each subsystem becomes: Qty=1, Description=name, Rate/Adjust/Sub Total = em-dash.
        """
        flowables: list = []
        b = self.brand

        subsystems = content.get("subsystems", [])
        if not subsystems:
            return flowables

        header_style = _ps(
            "InvTblHeader", brand=b, fontSize=9,
            textColor=black, fontName="Helvetica-Bold",
        )
        body_style = _ps(
            "InvTblBody", brand=b, fontSize=9,
            textColor=black, fontName="Helvetica",
        )

        header_row = [
            Paragraph(f"<b>{h}</b>", header_style)
            for h in _CANONICAL_HEADERS
        ]
        table_data = [header_row]

        for sub in subsystems[:30]:
            name = sub.get("name", "Item")
            table_data.append([
                _safe_para("1", body_style),
                _safe_para(_safe_text(name), body_style),
                _safe_para("\u2014", body_style),
                _safe_para("\u2014", body_style),
                _safe_para("\u2014", body_style),
            ])

        col_widths = [
            self.content_width * 0.10,
            self.content_width * 0.40,
            self.content_width * 0.15,
            self.content_width * 0.15,
            self.content_width * 0.20,
        ]

        item_table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1,
        )
        item_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), black),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.4, _GRID_COLOR),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, _ROW_ALT]),
        ]))

        flowables.append(item_table)
        flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Totals block
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_currency(value: str) -> float | None:
        """Try to extract a numeric amount from a string like '$1,234.56'."""
        cleaned = str(value).strip().replace(",", "").replace("$", "")
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def _compute_totals(
        self, tables: list[dict], content: dict | None = None,
    ) -> tuple[str, str, str]:
        """Compute Sub Total, Tax, and Total from the rightmost column.

        Tax rate defaults to 10 % but can be overridden via
        content['metadata']['tax_rate'] (as a decimal, e.g. 0.15 for 15 %).
        """
        row_total = 0.0
        has_numeric = False
        for tbl in tables:
            for row in tbl.get("rows", []):
                if row:
                    amount = self._parse_currency(str(row[-1]))
                    if amount is not None:
                        row_total += amount
                        has_numeric = True

        if has_numeric:
            # Determine tax rate
            tax_rate = 0.10
            if content:
                meta = content.get("metadata", {})
                if isinstance(meta, dict):
                    custom_rate = meta.get("tax_rate")
                    if custom_rate is not None:
                        try:
                            tax_rate = float(custom_rate)
                        except (ValueError, TypeError):
                            pass

            tax_amount = row_total * tax_rate
            total_amount = row_total + tax_amount
            return (
                f"${row_total:,.2f}",
                f"${tax_amount:,.2f}",
                f"${total_amount:,.2f}",
            )

        return ("See line items", "\u2014", "See line items")

    def _build_totals_block(
        self, tables: list[dict], body_c: HexColor, primary: HexColor,
        content: dict | None = None,
    ) -> list:
        """Build Sub Total -> Tax -> Total right-aligned below the table.

        All text is black; only the Total row is bold with a top border.
        """
        flowables: list = []
        b = self.brand

        label_style = _ps(
            "InvoiceTotalLabel", brand=b, fontSize=10,
            textColor=black,
        )
        total_label_style = _ps(
            "InvoiceTotalBold", brand=b, fontSize=11,
            textColor=black, fontName="Helvetica-Bold",
        )
        value_style = _ps(
            "InvoiceTotalValue", brand=b, fontSize=10,
            textColor=black, alignment=2,
        )
        total_value_style = _ps(
            "InvoiceTotalValueBold", brand=b, fontSize=11,
            textColor=black, fontName="Helvetica-Bold",
            alignment=2,
        )

        subtotal_str, tax_str, total_str = self._compute_totals(tables, content)

        totals_data = [
            [
                Paragraph("Sub Total:", label_style),
                Paragraph(subtotal_str, value_style),
            ],
            [
                Paragraph("Tax:", label_style),
                Paragraph(tax_str, value_style),
            ],
            [
                Paragraph("TOTAL:", total_label_style),
                Paragraph(total_str, total_value_style),
            ],
        ]

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
            ("LINEABOVE", (0, 0), (-1, 0), 0.4, _GRID_COLOR),
            ("LINEABOVE", (0, -1), (-1, -1), 1, black),
        ]))

        flowables.append(Spacer(1, 2 * mm))
        flowables.append(totals_table)

        return flowables

    # ------------------------------------------------------------------
    # Payment details block
    # ------------------------------------------------------------------

    def _build_payment_details(
        self, content: dict, brand: dict,
        caption_c: HexColor, body_c: HexColor,
    ) -> list:
        """Build a PAYMENT DETAILS section from guide_content or placeholder."""
        flowables: list = []

        label_style = _ps(
            "InvoicePayLabel", brand=brand, fontSize=9,
            textColor=caption_c, fontName="Helvetica-Bold",
            spaceAfter=3,
        )
        detail_style = _ps(
            "InvoicePayDetail", brand=brand, fontSize=9,
            textColor=black, leading=13,
        )

        flowables.append(Paragraph("PAYMENT DETAILS", label_style))

        guide = content.get("guide_content", "")
        if guide:
            for block in parse_markdown(guide)[:10]:
                if block.get("type") == "paragraph":
                    flowables.append(_safe_para(
                        _safe_text(block.get("text", "")), detail_style,
                    ))
                else:
                    flowables.extend(self.render_blocks([block]))
        else:
            flowables.append(
                Paragraph("Payment details available upon request.", detail_style),
            )

        flowables.append(Spacer(1, 6 * mm))
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

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 20) * mm
        bottom_m = margins.get("bottom", 20) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        doc = self._build_doc(
            pagesize=A4,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            subject="Invoice",
        )

        story = self.build_story(content)
        story = self._finalize_story(story)

        caption_color = HexColor(self.brand.get("caption", "#666666"))
        org = self.brand.get("org", "")

        def _invoice_footer(canvas, doc_inner):
            """Footer: payment terms left, page number right."""
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(caption_color)

            # Payment terms line
            terms_y = 14 * mm
            canvas.drawString(
                doc_inner.leftMargin, terms_y,
                "Payment is due within 30 days from date of invoice.",
            )

            # Org name and page number
            footer_y = 10 * mm
            if org:
                canvas.drawString(
                    doc_inner.leftMargin, footer_y, org,
                )
            canvas.drawRightString(
                doc_inner.pagesize[0] - doc_inner.rightMargin, footer_y,
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
