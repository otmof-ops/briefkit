"""
briefkit.templates.datasheet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Technical datasheet / specification template.

Build order:
  Title + Org Grid → Project Sections → Technical Specifications

Key differences:
  - No cover page — starts directly with content
  - Smartsheet IT-spec style with colored section banners
  - Organization metadata grid (teal/secondary header)
  - Project section with label|value rows (overview, objective, etc.)
  - Technical specifications rendered as component tables
  - Running header: title left, page number right
  - Body text 9pt, bold labels in secondary color, grid borders 0.4pt grey
  - No TOC, no bibliography, no back cover
  - Uses brand SECONDARY color for section banners (teal/cyan)

Suitable for: technical specs, data sheets, product sheets, IT specifications.
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
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
    _get_brand,
    _hex,
    _ps,
    _safe_text,
    compute_content_width,
)

# ---------------------------------------------------------------------------
# Module-level state for custom header / footer
# ---------------------------------------------------------------------------

_ds_state: dict = {
    "title": "",
    "brand": {},
}


def _ds_header_footer(canvas, doc):
    """
    Datasheet header/footer.

    Header: title left-aligned, page number right-aligned.
    """
    canvas.saveState()
    b = _get_brand(_ds_state.get("brand"))
    page_width, page_height = doc.pagesize

    caption_c = HexColor(b.get("caption", "#666666"))
    top_y = page_height - doc.topMargin + 8 * mm

    # Header — title left
    title = _ds_state.get("title", "")
    if title:
        canvas.setFont(b.get("font_body", "Helvetica"), 8)
        canvas.setFillColor(caption_c)
        canvas.drawString(doc.leftMargin, top_y, title)

    # Header — page number right
    canvas.setFont(b.get("font_body", "Helvetica"), 8)
    canvas.setFillColor(caption_c)
    canvas.drawRightString(
        page_width - doc.rightMargin, top_y,
        f"Page {doc.page}",
    )

    # Thin rule below header
    rule_c = HexColor(b.get("rule", "#CCCCCC"))
    canvas.setStrokeColor(rule_c)
    canvas.setLineWidth(0.4)
    canvas.line(
        doc.leftMargin, top_y - 3,
        page_width - doc.rightMargin, top_y - 3,
    )

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Keyword categories for project section extraction
# ---------------------------------------------------------------------------

_PROJECT_CATEGORIES = [
    ("OVERVIEW", ["overview", "introduction", "background", "summary", "about"]),
    ("OBJECTIVE", ["objective", "goal", "purpose", "aim", "mission"]),
    ("BUSINESS CASE", ["business", "case", "justification", "rationale", "value"]),
    ("RISKS", ["risk", "threat", "vulnerability", "concern", "issue"]),
    ("OUT OF SCOPE", ["scope", "exclusion", "limitation", "boundary", "constraint"]),
]


def _categorize_subsystem(name: str) -> str | None:
    """Match a subsystem name to a project category by keyword."""
    lower = name.lower()
    for category, keywords in _PROJECT_CATEGORIES:
        for kw in keywords:
            if kw in lower:
                return category
    return None


# ---------------------------------------------------------------------------
# Template class
# ---------------------------------------------------------------------------


class DatasheetTemplate(BaseBriefingTemplate):
    """
    Technical datasheet / specification template.

    Produces a spec-sheet PDF with no cover page, colored section banners,
    organization metadata grid, and component specification tables.
    Modelled on Smartsheet IT specification layouts.
    """

    # ------------------------------------------------------------------
    # Story assembly
    # ------------------------------------------------------------------

    def build_story(self, content: dict) -> list:
        """
        Assemble the datasheet story:
          Title + Org Grid → Project Sections → Technical Specs.
        """
        story: list = []
        title = content.get("title", self.target_path.name.replace("-", " ").title())
        overview = content.get("overview", "")
        subsystems = content.get("subsystems", [])
        org = self.brand.get("org", "")

        # ---- Title row ----
        story.extend(self._build_title_row(title, org))
        story.append(Spacer(1, 6 * mm))

        # ---- Organization metadata grid ----
        story.extend(self._build_org_grid(title, org, overview))
        story.append(Spacer(1, 8 * mm))

        # ---- Project section ----
        story.extend(self._build_project_section(subsystems, overview))
        story.append(Spacer(1, 8 * mm))

        # ---- Technical specifications ----
        story.extend(self._build_tech_specs(subsystems))

        return story

    # ------------------------------------------------------------------
    # Title row
    # ------------------------------------------------------------------

    def _build_title_row(self, title: str, org: str) -> list:
        """Large bold title at top-left, org name at top-right."""
        flowables: list = []

        title_style = _ps(
            "DSTitle", brand=self.brand,
            fontSize=16, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "body_text"),
            alignment=0, spaceAfter=2,
        )
        flowables.append(Paragraph(_safe_text(title), title_style))

        if org:
            org_style = _ps(
                "DSOrg", brand=self.brand,
                fontSize=9, textColor=_hex(self.brand, "caption"),
                alignment=0,
            )
            flowables.append(Paragraph(_safe_text(org), org_style))

        return flowables

    # ------------------------------------------------------------------
    # Organization metadata grid
    # ------------------------------------------------------------------

    def _build_org_grid(self, title: str, org: str, overview: str) -> list:
        """Bordered metadata grid with secondary-colored header row."""
        flowables: list = []
        secondary = _hex(self.brand, "secondary")
        rule_c = HexColor(self.brand.get("rule", "#CCCCCC"))

        cell_style = _ps(
            "DSCell", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "body_text"),
            leading=12,
        )
        label_style = _ps(
            "DSLabel", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "secondary"),
            leading=12,
        )
        header_cell_style = _ps(
            "DSHeaderCell", brand=self.brand,
            fontSize=10, fontName="Helvetica-Bold",
            textColor="#FFFFFF",
            leading=13,
        )

        # Extract a mailing address hint from overview (first line that looks like one)
        address = ""
        if overview:
            for line in overview.split("\n"):
                stripped = line.strip().lstrip("#- *>")
                if len(stripped) > 10 and not stripped.startswith("```"):
                    address = stripped[:80]
                    break

        col_w = self.content_width / 4

        # Header row: ORGANIZATION spanning full width
        header_row = [Paragraph("ORGANIZATION", header_cell_style), "", "", ""]

        data = [
            header_row,
            [
                Paragraph("PROJECT NAME", label_style),
                Paragraph(_safe_text(title), cell_style),
                "",
                "",
            ],
            [
                Paragraph("NAME", label_style),
                Paragraph(_safe_text(org), cell_style),
                Paragraph("MAILING ADDRESS", label_style),
                Paragraph(_safe_text(address), cell_style),
            ],
            [
                Paragraph("PHONE", label_style),
                Paragraph("", cell_style),
                "",
                "",
            ],
            [
                Paragraph("EMAIL", label_style),
                Paragraph("", cell_style),
                "",
                "",
            ],
            [
                Paragraph("DATE", label_style),
                Paragraph(self.date_str, cell_style),
                Paragraph("AUTHOR", label_style),
                Paragraph(_safe_text(org), cell_style),
            ],
        ]

        t = Table(data, colWidths=[col_w] * 4)
        t.setStyle(TableStyle([
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), secondary),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("SPAN", (0, 0), (-1, 0)),
            # PROJECT NAME spans cols 1-3
            ("SPAN", (1, 1), (3, 1)),
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.4, rule_c),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))

        flowables.append(t)
        return flowables

    # ------------------------------------------------------------------
    # Project section
    # ------------------------------------------------------------------

    def _build_project_section(
        self,
        subsystems: list[dict],
        overview: str,
    ) -> list:
        """
        Build the PROJECT section with banner and categorized rows.

        Categorizes the first ~5 subsystems by keyword into:
        OVERVIEW, OBJECTIVE, BUSINESS CASE, RISKS, OUT OF SCOPE.
        """
        flowables: list = []
        secondary = _hex(self.brand, "secondary")
        rule_c = HexColor(self.brand.get("rule", "#CCCCCC"))

        label_style = _ps(
            "DSProjLabel", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "secondary"),
            leading=12,
        )
        value_style = _ps(
            "DSProjValue", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "body_text"),
            leading=12,
        )
        banner_style = _ps(
            "DSBanner", brand=self.brand,
            fontSize=10, fontName="Helvetica-Bold",
            textColor="#FFFFFF",
            leading=13,
        )

        # Section banner
        banner_data = [[Paragraph("PROJECT", banner_style), ""]]
        label_w = self.content_width * 0.25
        value_w = self.content_width * 0.75
        banner_t = Table(banner_data, colWidths=[label_w, value_w])
        banner_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), secondary),
            ("SPAN", (0, 0), (-1, 0)),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        flowables.append(banner_t)

        # Build category -> content mapping
        categorized: dict[str, str] = {
            "OVERVIEW": "",
            "OBJECTIVE": "",
            "BUSINESS CASE": "",
            "RISKS": "",
            "OUT OF SCOPE": "",
        }

        # Use overview text as default OVERVIEW
        if overview:
            clean = re.sub(r"#+ ", "", overview).strip()
            paragraphs = [p.strip() for p in re.split(r"\n\n+", clean) if p.strip()]
            categorized["OVERVIEW"] = (paragraphs[0][:500] if paragraphs else "")

        # Categorize subsystems
        for sub in subsystems[:5]:
            name = sub.get("name", "")
            cat = _categorize_subsystem(name)
            if cat and not categorized.get(cat):
                raw = sub.get("content", "")
                clean = re.sub(r"#+ ", "", raw).strip()
                paragraphs = [
                    p.strip() for p in re.split(r"\n\n+", clean) if p.strip()
                ]
                categorized[cat] = (paragraphs[0][:500] if paragraphs else name)

        # Render category rows
        rows = []
        for cat_name in ["OVERVIEW", "OBJECTIVE", "BUSINESS CASE", "RISKS", "OUT OF SCOPE"]:
            text = categorized.get(cat_name, "")
            rows.append([
                Paragraph(cat_name, label_style),
                Paragraph(_safe_text(text) if text else "&mdash;", value_style),
            ])

        t = Table(rows, colWidths=[label_w, value_w])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, rule_c),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        flowables.append(t)

        return flowables

    # ------------------------------------------------------------------
    # Technical specifications
    # ------------------------------------------------------------------

    def _build_tech_specs(self, subsystems: list[dict]) -> list:
        """
        Build the TECHNICAL SPECIFICATIONS section.

        Subsystems beyond the first 5 are rendered as component tables
        with key/value rows extracted from table data or list items.
        """
        flowables: list = []
        secondary = _hex(self.brand, "secondary")
        rule_c = HexColor(self.brand.get("rule", "#CCCCCC"))

        banner_style = _ps(
            "DSTechBanner", brand=self.brand,
            fontSize=10, fontName="Helvetica-Bold",
            textColor="#FFFFFF",
            leading=13,
        )
        comp_header_style = _ps(
            "DSCompHeader", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor="#FFFFFF",
            leading=12, alignment=1,
        )
        label_style = _ps(
            "DSTechLabel", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "secondary"),
            leading=12,
        )
        value_style = _ps(
            "DSTechValue", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "body_text"),
            leading=12,
        )

        # Section banner
        banner_data = [[Paragraph("TECHNICAL SPECIFICATIONS", banner_style), ""]]
        banner_t = Table(
            banner_data,
            colWidths=[self.content_width / 2, self.content_width / 2],
        )
        banner_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), secondary),
            ("SPAN", (0, 0), (-1, 0)),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        flowables.append(banner_t)

        # Components from subsystems beyond the first 5
        tech_subs = subsystems[5:] if len(subsystems) > 5 else subsystems
        label_w = self.content_width * 0.35
        value_w = self.content_width * 0.65

        for sub in tech_subs:
            name = sub.get("name", "Component")

            # Component header row
            header_data = [[Paragraph(_safe_text(name), comp_header_style), ""]]
            header_t = Table(header_data, colWidths=[label_w, value_w])
            header_t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), secondary),
                ("SPAN", (0, 0), (-1, 0)),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]))
            flowables.append(header_t)

            # Extract key/value pairs
            kv_pairs = self._extract_kv_pairs(sub)

            if kv_pairs:
                rows = [
                    [
                        Paragraph(_safe_text(k), label_style),
                        Paragraph(_safe_text(v), value_style),
                    ]
                    for k, v in kv_pairs
                ]
                t = Table(rows, colWidths=[label_w, value_w])
                t.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.4, rule_c),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]))
                flowables.append(t)
            else:
                # Fallback: render content as single-cell prose
                raw = sub.get("content", "")
                if raw.strip():
                    clean = re.sub(r"#+ ", "", raw).strip()
                    first_para = re.split(r"\n\n+", clean)[0][:400]
                    row = [[
                        Paragraph("DESCRIPTION", label_style),
                        Paragraph(_safe_text(first_para), value_style),
                    ]]
                    t = Table(row, colWidths=[label_w, value_w])
                    t.setStyle(TableStyle([
                        ("GRID", (0, 0), (-1, -1), 0.4, rule_c),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ]))
                    flowables.append(t)

            flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Key-value extraction helper
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_kv_pairs(sub: dict) -> list[tuple[str, str]]:
        """
        Extract characteristic/value pairs from a subsystem.

        Sources (in priority order):
          1. Table data — first two columns become key/value
          2. List items — split on colon or dash
          3. Headings + following paragraph
        """
        pairs: list[tuple[str, str]] = []

        # 1. From tables
        for tbl in sub.get("tables", []):
            for row in tbl.get("rows", []):
                if len(row) >= 2:
                    k = str(row[0]).strip() if row[0] else ""
                    v = str(row[1]).strip() if row[1] else ""
                    if k:
                        pairs.append((k, v))
            if pairs:
                return pairs[:20]

        # 2. From list items (colon-separated)
        blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
        for block in blocks:
            if block.get("type") == "list":
                for item in block.get("items", []):
                    text = item if isinstance(item, str) else str(item)
                    if ":" in text:
                        parts = text.split(":", 1)
                        pairs.append((parts[0].strip(), parts[1].strip()))
                    elif " - " in text:
                        parts = text.split(" - ", 1)
                        pairs.append((parts[0].strip(), parts[1].strip()))
        if pairs:
            return pairs[:20]

        # 3. From heading + paragraph sequences
        prev_heading = ""
        for block in blocks:
            if block.get("type") == "heading":
                prev_heading = block.get("text", "")
            elif block.get("type") == "paragraph" and prev_heading:
                text = block.get("text", "").strip()
                if text and len(text) > 5:
                    pairs.append((prev_heading, text[:200]))
                    prev_heading = ""

        return pairs[:20]

    # ------------------------------------------------------------------
    # Override generate() for custom layout
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the datasheet PDF with Letter size and custom header/footer."""
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

        # Populate module-level state for header/footer
        _ds_state["title"] = title
        _ds_state["brand"] = self.brand

        # Also populate base _hf_state for consistency

        # Recalculate content width for Letter
        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        self.content_width = compute_content_width(letter, margins)

        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=title,
            author=self.brand.get("org", "briefkit"),
            subject="Technical Datasheet",
            creator="briefkit",
        )

        story = self.build_story(content)
        doc.build(
            story,
            onFirstPage=_ds_header_footer,
            onLaterPages=_ds_header_footer,
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

    def build_back_cover(self, *args, **kwargs) -> list:
        return []
