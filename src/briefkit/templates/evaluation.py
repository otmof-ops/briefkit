"""
briefkit.templates.evaluation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Evaluation report template — categorical rating matrix for performance reviews.

Build order:
  Employee Information Grid → Categorical Rating Matrix →
  Goals Section → Comments and Approval Section

Design norms (CenturyGothic/Letter and UNODC/TimesNewRoman patterns):
  - No cover page, no TOC, no back cover (standalone form)
  - Employee information metadata grid at top
  - Categorical rating matrix (Unsatisfactory/Satisfactory/Good/Excellent)
  - Goals achievement and forward-looking goals section
  - Comments area with dual signature block

Suitable for: performance evaluations, employee reviews, appraisal forms.
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import A3, A4, legal, letter
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

_PAGE_SIZES = {"A4": A4, "A3": A3, "Letter": letter, "Legal": legal}

# ---------------------------------------------------------------------------
# Metadata extraction helpers
# ---------------------------------------------------------------------------

_FIELD_RE = re.compile(
    r"(?:department|dept)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE,
)
_POSITION_RE = re.compile(
    r"(?:position|title|role)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE,
)
_REVIEWER_RE = re.compile(
    r"(?:reviewer|supervisor|manager)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE,
)
_REVIEWER_TITLE_RE = re.compile(
    r"(?:reviewer title|supervisor title)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE,
)

# Alternating row colors
_ROW_WHITE = white
_ROW_ALT = HexColor("#f0f4f8")
_HEADER_BG = HexColor("#f2f2f2")
_BORDER_COLOR = HexColor("#000000")
_BORDER_WIDTH = 0.5


def _extract_field(pattern: re.Pattern, text: str) -> str:
    """Extract a field value from overview text, or return empty string."""
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class EvaluationTemplate(BaseBriefingTemplate):
    """
    Production evaluation form template.

    Renders a standalone performance evaluation form with metadata grid,
    categorical rating matrix, goals section, and signature block.
    No cover page, TOC, or back cover.
    """

    # ------------------------------------------------------------------
    # generate() — standalone form, no cover/TOC/back cover
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the evaluation PDF as a standalone form."""
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
        bottom_m = margins.get("bottom", 18) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        page_size = _PAGE_SIZES.get(layout.get("page_size", "Letter"), letter)

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=content.get("title", "Employee Evaluation"),
            author=self.brand.get("org", "briefkit"),
            subject="Performance Evaluation",
            creator="briefkit",
        )

        story = self.build_story(content)

        caption_color = HexColor(self.brand.get("caption", "#666666"))

        def _eval_footer(canvas, doc_inner):
            """Minimal page number footer."""
            canvas.saveState()
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(caption_color)
            canvas.drawCentredString(
                doc_inner.pagesize[0] / 2, 10 * mm,
                f"Page {doc_inner.page}",
            )
            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=lambda c, d: None,
            onLaterPages=_eval_footer,
        )

        return self.output_path

    # ------------------------------------------------------------------
    # build_story — evaluation form structure
    # ------------------------------------------------------------------

    def build_story(self, content: dict) -> list:
        """
        Assemble the evaluation form (no cover/TOC/back cover):
          Title → Employee Info Grid → Rating Matrix → Goals → Comments/Signatures
        """
        story: list = []
        subsystems = content.get("subsystems", [])

        # Form title
        title_style = _ps(
            "EvalFormTitle", brand=self.brand,
            fontSize=14, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "primary"),
            alignment=1, spaceAfter=6, spaceBefore=2,
        )
        story.append(Paragraph("EMPLOYEE PERFORMANCE EVALUATION", title_style))
        story.append(Spacer(1, 4 * mm))

        # 1. Employee information metadata grid
        story.extend(self._build_metadata_grid(content))
        story.append(Spacer(1, 5 * mm))

        # 2. Categorical rating matrix
        story.extend(self._build_rating_matrix(subsystems))
        story.append(Spacer(1, 5 * mm))

        # 3. Goals section
        story.extend(self._build_goals_section(subsystems))
        story.append(Spacer(1, 5 * mm))

        # 4. Comments and approval section
        story.extend(self._build_comments_and_approval())

        return story

    # ------------------------------------------------------------------
    # build_body — delegate to build_story sections
    # ------------------------------------------------------------------

    def build_body(self, content: dict) -> list:
        """Not used — build_story handles everything."""
        return []

    # ------------------------------------------------------------------
    # 1. Employee information metadata grid
    # ------------------------------------------------------------------

    def _build_metadata_grid(self, content: dict) -> list:
        """Render the EMPLOYEE INFORMATION bordered table."""
        flowables: list = []

        title = content.get("title", "")
        doc_id = self.doc_id or ""
        review_date = self.date_str
        overview = content.get("overview", "")

        position = _extract_field(_POSITION_RE, overview)
        department = _extract_field(_FIELD_RE, overview)
        reviewer = _extract_field(_REVIEWER_RE, overview)
        reviewer_title = _extract_field(_REVIEWER_TITLE_RE, overview)

        # Section heading
        heading_style = _ps(
            "EvalSectionHead", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor=black,
            spaceAfter=2, spaceBefore=2,
        )
        flowables.append(Paragraph("EMPLOYEE INFORMATION", heading_style))
        flowables.append(Spacer(1, 1 * mm))

        label_style = _ps(
            "EvalMetaLabel", brand=self.brand,
            fontSize=8, fontName="Helvetica-Bold",
            textColor=black, leading=11,
        )
        def _cell(label: str, value: str) -> Paragraph:
            safe_val = _safe_text(value) if value else " "
            return _safe_para(
                f"<b>{_safe_text(label)}:</b><br/>{safe_val}",
                label_style,
            )

        col_width = self.content_width / 3

        table_data = [
            [
                _cell("EMPLOYEE NAME", title),
                _cell("EMPLOYEE ID", doc_id),
                _cell("DATE OF CURRENT REVIEW", review_date),
            ],
            [
                _cell("POSITION HELD", position),
                _cell("DEPARTMENT", department),
                _cell("DATE OF LAST REVIEW", ""),
            ],
            [
                _cell("REVIEWER NAME", reviewer),
                _cell("REVIEWER TITLE", reviewer_title),
                _cell("DATE SUBMITTED", ""),
            ],
        ]

        t = Table(table_data, colWidths=[col_width] * 3)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _HEADER_BG),
            ("GRID", (0, 0), (-1, -1), _BORDER_WIDTH, _BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        flowables.append(t)

        return flowables

    # ------------------------------------------------------------------
    # 2. Categorical rating matrix
    # ------------------------------------------------------------------

    def _build_rating_matrix(self, subsystems: list[dict]) -> list:
        """Build the categorical rating matrix table."""
        flowables: list = []

        heading_style = _ps(
            "EvalRubricHead", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor=black,
            spaceAfter=2, spaceBefore=2,
        )
        flowables.append(Paragraph("PERFORMANCE RATING", heading_style))
        flowables.append(Spacer(1, 1 * mm))

        # Column headers
        headers = ["QUALITY", "UNSATISFACTORY", "SATISFACTORY", "GOOD", "EXCELLENT"]
        quality_col_w = self.content_width * 0.36
        rating_col_w = (self.content_width - quality_col_w) / 4

        col_widths = [quality_col_w] + [rating_col_w] * 4

        header_style = _ps(
            "EvalMatrixHeader", brand=self.brand,
            fontSize=8, fontName="Helvetica-Bold",
            textColor=white, alignment=1, leading=10,
        )
        primary = _hex(self.brand, "primary")

        header_row = [_safe_para(h, header_style) for h in headers]
        table_data = [header_row]

        category_style = _ps(
            "EvalCatHead", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor=black, leading=12,
        )
        criterion_style = _ps(
            "EvalCriterion", brand=self.brand,
            fontSize=9, fontName="Helvetica",
            textColor=black, leading=12,
        )

        # Track row types for alternating shading
        row_types: list[str] = []  # "category" or "criterion"

        for cat_idx, sub in enumerate(subsystems, 1):
            # Category group header row
            cat_name = f"{cat_idx}. {_safe_text(sub.get('name', 'Category'))}"
            table_data.append([
                _safe_para(cat_name, category_style),
                "", "", "", "",
            ])
            row_types.append("category")

            # Extract criteria from bullet/list items in content
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            criteria_items = self._extract_criteria_items(blocks)

            if not criteria_items:
                # If no list items found, use category as single criterion
                criteria_items = [sub.get("name", "General")]

            for item in criteria_items:
                table_data.append([
                    _safe_para(f"    {_safe_text(item[:80])}", criterion_style),
                    "", "", "", "",
                ])
                row_types.append("criterion")

        t = Table(table_data, colWidths=col_widths, repeatRows=1)

        style_cmds = [
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGNMENT", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), _BORDER_WIDTH, _BORDER_COLOR),
        ]

        # Apply category and alternating row styles
        criterion_count = 0
        for row_idx, rtype in enumerate(row_types):
            data_row = row_idx + 1  # +1 for header
            if rtype == "category":
                # Category header: light grey background, span all columns
                style_cmds.append(
                    ("BACKGROUND", (0, data_row), (-1, data_row), _HEADER_BG),
                )
                style_cmds.append(
                    ("SPAN", (0, data_row), (-1, data_row)),
                )
                criterion_count = 0
            else:
                # Alternating criterion rows
                bg = _ROW_WHITE if criterion_count % 2 == 0 else _ROW_ALT
                style_cmds.append(
                    ("BACKGROUND", (0, data_row), (-1, data_row), bg),
                )
                criterion_count += 1

        t.setStyle(TableStyle(style_cmds))
        flowables.append(t)

        return flowables

    def _extract_criteria_items(self, blocks: list[dict]) -> list[str]:
        """Extract list items from parsed blocks to use as criteria rows."""
        items: list[str] = []
        for block in blocks:
            btype = block.get("type", "")
            if btype == "list":
                for li in block.get("items", []):
                    text = li if isinstance(li, str) else li.get("text", "")
                    if text.strip():
                        items.append(text.strip())
            elif btype == "list_item":
                text = block.get("text", "")
                if text.strip():
                    items.append(text.strip())
        return items

    # ------------------------------------------------------------------
    # 3. Goals section
    # ------------------------------------------------------------------

    def _build_goals_section(self, subsystems: list[dict]) -> list:
        """Build the goals achievement and future goals section."""
        flowables: list = []

        heading_style = _ps(
            "EvalGoalsHead", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor=black,
            spaceAfter=2, spaceBefore=2,
        )
        body_style = _ps(
            "EvalGoalsBody", brand=self.brand,
            fontSize=9, fontName="Helvetica",
            textColor=black, leading=12,
        )

        # Collect blockquote content as goals text
        goals_text: list[str] = []
        for sub in subsystems:
            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            for block in blocks:
                if block.get("type") == "blockquote":
                    goals_text.append(block.get("text", ""))

        flowables.append(Paragraph("GOALS", heading_style))
        flowables.append(Spacer(1, 2 * mm))

        # Goal area 1: Were previously set goals achieved?
        label1 = _safe_para(
            "<b>Were previously set goals achieved?</b>", body_style,
        )
        flowables.append(label1)
        flowables.append(Spacer(1, 1 * mm))

        goals_achieved_text = " ".join(goals_text[:3]) if goals_text else " "
        box1_data = [[_safe_para(goals_achieved_text, body_style)]]
        box1 = Table(box1_data, colWidths=[self.content_width])
        box1.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), _BORDER_WIDTH, HexColor("#999999")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        flowables.append(box1)
        flowables.append(Spacer(1, 4 * mm))

        # Goal area 2: Goals for next review period
        label2 = _safe_para(
            "<b>Goals for next review period:</b>", body_style,
        )
        flowables.append(label2)
        flowables.append(Spacer(1, 1 * mm))

        remaining_goals = " ".join(goals_text[3:]) if len(goals_text) > 3 else " "
        box2_data = [[_safe_para(remaining_goals, body_style)]]
        box2 = Table(box2_data, colWidths=[self.content_width])
        box2.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), _BORDER_WIDTH, HexColor("#999999")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        flowables.append(box2)

        return flowables

    # ------------------------------------------------------------------
    # 4. Comments and approval section
    # ------------------------------------------------------------------

    def _build_comments_and_approval(self) -> list:
        """Build comments area and dual signature row."""
        flowables: list = []

        heading_style = _ps(
            "EvalCommentsHead", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor=black,
            spaceAfter=2, spaceBefore=2,
        )
        body_style = _ps(
            "EvalCommentsBody", brand=self.brand,
            fontSize=9, fontName="Helvetica",
            textColor=black, leading=12,
        )

        flowables.append(Paragraph("COMMENTS AND APPROVAL", heading_style))
        flowables.append(Spacer(1, 2 * mm))

        # Large comments box
        comments_data = [[_safe_para(" ", body_style)]]
        comments_box = Table(comments_data, colWidths=[self.content_width])
        comments_box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), _BORDER_WIDTH, HexColor("#999999")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 40),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        flowables.append(comments_box)
        flowables.append(Spacer(1, 6 * mm))

        # Dual signature row
        sig_label_style = _ps(
            "EvalSigLabel", brand=self.brand,
            fontSize=8, fontName="Helvetica-Bold",
            textColor=black, leading=10,
        )
        sig_line_style = _ps(
            "EvalSigLine", brand=self.brand,
            fontSize=8, fontName="Helvetica",
            textColor=black, leading=10,
        )

        col_w = self.content_width / 4
        sig_data = [
            [
                _safe_para("<b>EMPLOYEE SIGNATURE</b>", sig_label_style),
                _safe_para("<b>DATE</b>", sig_label_style),
                _safe_para("<b>REVIEWER SIGNATURE</b>", sig_label_style),
                _safe_para("<b>DATE</b>", sig_label_style),
            ],
            [
                _safe_para("_" * 30, sig_line_style),
                _safe_para("_" * 15, sig_line_style),
                _safe_para("_" * 30, sig_line_style),
                _safe_para("_" * 15, sig_line_style),
            ],
        ]

        sig_table = Table(sig_data, colWidths=[col_w] * 4)
        sig_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        flowables.append(sig_table)

        return flowables

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
