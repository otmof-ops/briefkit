"""
briefkit.templates.register
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Table-dominant register template.

Build order:
  Title Page → Consolidated Table → Summary Stats

Key differences:
  - Simple title page (title, org, date — no branded cover, no classification)
  - Consolidates ALL tables from ALL subsystems into one continuous table
  - Uses ReportLab Table with repeatRows=1 so column headers repeat per page
  - Falls back to prose if no tables found
  - Summary stats at the end (total rows, date generated)
  - No TOC, no exec summary, no bibliography, no back cover
  - Header: register name (right-aligned)
  - Footer: "Page X of Y" centered

Suitable for: risk registers, data dictionaries, compliance matrices,
asset registers, audit logs.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer,
    PageBreak,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm

from briefkit.generator import (
    BaseBriefingTemplate,
    _hf_state,
)
from briefkit.styles import (
    _get_brand,
    _safe_para,
    _safe_text,
    _ps,
    _hex,
    build_styles,
    CONTENT_WIDTH,
    MARGIN_TOP,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
)
from briefkit.extractor import parse_markdown


# ---------------------------------------------------------------------------
# Custom header / footer
# ---------------------------------------------------------------------------

_register_state: dict = {
    "title": "",
    "brand": {},
}


def _register_header_footer(canvas, doc):
    """
    Register template header/footer.

    Header: register name right-aligned.
    Footer: "Page X of Y" centered.
    """
    canvas.saveState()
    b = _get_brand(_register_state.get("brand"))
    page_width, page_height = doc.pagesize

    # Header — register name right-aligned
    title = _register_state.get("title", "")
    if title:
        caption_c = HexColor(b.get("caption", "#666666"))
        top_y = page_height - doc.topMargin + 8 * mm
        canvas.setFont(b.get("font_body", "Helvetica"), 8)
        canvas.setFillColor(caption_c)
        canvas.drawRightString(page_width - doc.rightMargin, top_y, title)

        # Thin rule below header
        rule_c = HexColor(b.get("rule", "#CCCCCC"))
        canvas.setStrokeColor(rule_c)
        canvas.setLineWidth(0.4)
        canvas.line(doc.leftMargin, top_y - 3, page_width - doc.rightMargin, top_y - 3)

    # Footer — "Page X of Y" centered
    bottom_y = doc.bottomMargin - 6 * mm
    canvas.setFont(b.get("font_body", "Helvetica"), 7)
    canvas.setFillColor(HexColor(b.get("caption", "#666666")))
    canvas.drawCentredString(
        page_width / 2, bottom_y + 1.5 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


class RegisterTemplate(BaseBriefingTemplate):
    """
    Table-dominant register template.

    Produces a PDF whose body is one large consolidated table built from
    all tables found across subsystem content.  Column headers repeat on
    every page via ReportLab's ``repeatRows`` parameter.

    If no tables are found the content is rendered as regular prose instead.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the register story:
          Title page, consolidated table (or prose fallback), summary stats.
        """
        story: list = []
        title = content.get("title", self.target_path.name.replace("-", " ").title())

        # ---- Simple title page ----
        story.extend(self._build_title_page(title, content))
        story.append(PageBreak())

        # ---- Consolidated table or prose fallback ----
        all_tables = self._collect_tables(content)

        if all_tables:
            story.extend(self._build_consolidated_table(all_tables))
        else:
            story.extend(self._build_prose_fallback(content))

        # ---- Summary stats ----
        total_rows = sum(len(tbl.get("rows", [])) for tbl in all_tables)
        story.append(Spacer(1, 10 * mm))
        story.extend(self._build_summary_stats(total_rows))

        return story

    # ------------------------------------------------------------------
    # Title page
    # ------------------------------------------------------------------

    def _build_title_page(self, title: str, content: dict) -> list:
        """Simple title page: title, org, date. No branded cover."""
        flowables: list = []

        flowables.append(Spacer(1, 40 * mm))

        # Title
        title_style = _ps(
            "RegisterTitle", brand=self.brand,
            fontSize=26, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "primary"),
            alignment=1, spaceAfter=8,
        )
        flowables.append(Paragraph(title, title_style))
        flowables.append(Spacer(1, 6 * mm))

        # Org name
        org = self.brand.get("org", "")
        if org:
            org_style = _ps(
                "RegisterOrg", brand=self.brand,
                fontSize=14, textColor=_hex(self.brand, "caption"),
                alignment=1, spaceAfter=4,
            )
            flowables.append(Paragraph(org, org_style))
            flowables.append(Spacer(1, 4 * mm))

        # Date
        date_style = _ps(
            "RegisterDate", brand=self.brand,
            fontSize=11, textColor=_hex(self.brand, "caption"),
            alignment=1,
        )
        flowables.append(Paragraph(self.date_str, date_style))

        return flowables

    # ------------------------------------------------------------------
    # Collect tables from all subsystems
    # ------------------------------------------------------------------

    def _collect_tables(self, content: dict) -> list[dict]:
        """
        Walk all subsystems and gather every table dict that has headers
        and at least one row.
        """
        tables: list[dict] = []
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                if tbl.get("headers") and tbl.get("rows"):
                    tables.append(tbl)
        return tables

    # ------------------------------------------------------------------
    # Consolidated table
    # ------------------------------------------------------------------

    def _build_consolidated_table(self, tables: list[dict]) -> list:
        """
        Merge compatible tables into one continuous table.

        Tables with the same column headers are merged.  Tables with
        different schemas are rendered sequentially with their own headers.
        """
        flowables: list = []
        styles = build_styles(self.brand)
        primary = _hex(self.brand, "primary")
        rule_c = _hex(self.brand, "rule")
        table_alt = HexColor("#f8f9fa")

        # Group tables by header signature
        groups: dict[tuple, list[dict]] = {}
        for tbl in tables:
            key = tuple(h.strip().lower() for h in tbl["headers"])
            groups.setdefault(key, []).append(tbl)

        for header_key, group in groups.items():
            # Use the first table's headers as canonical
            headers = group[0]["headers"]
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
            for tbl in group:
                for row in tbl.get("rows", []):
                    sanitised = [("" if cell is None else cell) for cell in row]
                    padded = list(sanitised) + [""] * max(0, col_count - len(sanitised))
                    padded = padded[:col_count]
                    table_data.append([
                        _safe_para(str(cell), styles["STYLE_TABLE_BODY"])
                        for cell in padded
                    ])

            t = Table(
                table_data,
                colWidths=[col_width] * col_count,
                repeatRows=1,
            )
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  primary),
                ("TEXTCOLOR",     (0, 0), (-1, 0),  white),
                ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, 0),  9),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 5),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
                ("GRID",          (0, 0), (-1, -1), 0.4, rule_c),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, table_alt]),
            ]))

            flowables.append(t)
            flowables.append(Spacer(1, 6 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Prose fallback
    # ------------------------------------------------------------------

    def _build_prose_fallback(self, content: dict) -> list:
        """Render content as regular prose when no tables are found."""
        flowables: list = []

        subsystems = content.get("subsystems", [])
        if not subsystems:
            overview = content.get("overview", "")
            if overview:
                for block in parse_markdown(overview)[:40]:
                    flowables.extend(self.render_blocks([block]))
            return flowables

        for idx, sub in enumerate(subsystems, 1):
            flowables.append(Paragraph(
                f"{idx}. {sub['name']}", self.styles["STYLE_H2"],
            ))
            flowables.append(Spacer(1, 3 * mm))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                if block["type"] == "heading" and block["level"] == 1:
                    continue
                for fl in self.render_blocks([block]):
                    flowables.append(fl)
                    rendered += 1
                if rendered >= 60:
                    break

            flowables.append(Spacer(1, 6 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Summary stats
    # ------------------------------------------------------------------

    def _build_summary_stats(self, total_rows: int) -> list:
        """Render a small summary block: total rows and generation date."""
        flowables: list = []

        rule_style = _ps(
            "RegisterRule", brand=self.brand,
            fontSize=1, spaceAfter=4,
        )
        flowables.append(Spacer(1, 2 * mm))

        stat_style = _ps(
            "RegisterStat", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "caption"),
            leading=13,
        )

        flowables.append(Paragraph(
            f"Total rows: {total_rows}", stat_style,
        ))
        flowables.append(Paragraph(
            f"Generated: {self.date_str}", stat_style,
        ))

        return flowables

    # ------------------------------------------------------------------
    # Override generate() for custom header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the register PDF with custom header/footer."""
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

        # Populate register header/footer state
        _register_state["title"] = title
        _register_state["brand"] = self.brand

        # Also populate base _hf_state for consistency
        _hf_state["section"] = title
        _hf_state["date"] = self.date_str
        _hf_state["doc_id"] = self.doc_id
        _hf_state["brand"] = self.brand

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=title,
            author=self.brand.get("org", "briefkit"),
            subject="Register",
            creator="briefkit",
        )

        story = self.build_story(content)
        doc.build(
            story,
            onFirstPage=_register_header_footer,
            onLaterPages=_register_header_footer,
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
