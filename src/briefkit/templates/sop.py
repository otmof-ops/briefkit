"""
briefkit.templates.sop
~~~~~~~~~~~~~~~~~~~~~~
Standard Operating Procedure template — grounded in WSU SOP format.

Build order:
  Header block → Summary → Approval table → Change history →
  Numbered sections (auto-ordered by SOP convention)

Key differences:
  - No cover page, no TOC, no dashboard, no bibliography, no back cover
  - Bordered header block with procedure metadata
  - Approval/concurrence table with signature lines
  - Change history table on page 2
  - Auto-numbered sections (1.0, 2.0, ...) ordered by SOP convention
  - "STANDARD OPERATING PROCEDURE" centered on every page header
  - Grey (#f2f2f2) backgrounds on header cells, 0.5pt black borders throughout
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import letter
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
from briefkit.generator import (
    BaseBriefingTemplate,
)
from briefkit.styles import (
    _ps,
    _safe_text,
)

_GREY_BG = HexColor("#f2f2f2")
_BORDER_W = 0.5
_BODY_SIZE = 10
_HEAD_SIZE = 11

# Section ordering patterns
_SECTION_PATTERNS = {
    1: re.compile(r"purpose|applicability|scope", re.IGNORECASE),
    2: re.compile(r"responsibilit", re.IGNORECASE),
    3: re.compile(r"definition", re.IGNORECASE),
    4: re.compile(r"acronym|abbreviation", re.IGNORECASE),
}


def _classify_section(name: str) -> int:
    """Return the SOP section bucket (1-4) or 0 for general procedure."""
    for bucket, pattern in _SECTION_PATTERNS.items():
        if pattern.search(name):
            return bucket
    return 0


class SOPTemplate(BaseBriefingTemplate):
    """
    Standard Operating Procedure template.

    Produces a formal SOP document with header block, approval table,
    change history, and auto-numbered sections following standard SOP
    ordering conventions (Purpose, Responsibilities, Definitions,
    Acronyms, then Procedure steps).
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the SOP story:
          Header block, summary, approval table, change history,
          numbered sections.
        """
        story: list = []
        b = self.brand
        org = b.get("org", "")
        project = self.config.get("project", {})
        title = content.get("title", "Untitled Procedure")
        overview = content.get("overview", "")

        # Derive work location from overview or org
        work_location = org or project.get("name", "")
        if overview:
            first_line = overview.strip().split("\n")[0].strip()
            if len(first_line) < 80:
                work_location = first_line

        # ---- Styles ----
        heading_style = _ps(
            "SOPHeading", brand=b, fontSize=_HEAD_SIZE,
            textColor=black, fontName="Helvetica-Bold",
            spaceBefore=8, spaceAfter=4,
        )
        cell_style = _ps(
            "SOPCell", brand=b, fontSize=_BODY_SIZE,
            textColor=black, leading=13,
        )
        cell_bold = _ps(
            "SOPCellBold", brand=b, fontSize=_BODY_SIZE,
            textColor=black, fontName="Helvetica-Bold", leading=13,
        )
        cell_grey = _ps(
            "SOPCellGrey", brand=b, fontSize=_HEAD_SIZE,
            textColor=black, fontName="Helvetica-Bold",
            leading=14, alignment=1,
        )

        # ================================================================
        # PAGE 1 — Header block
        # ================================================================

        # Row 1: full-width grey banner
        row1 = [[Paragraph("STANDARD OPERATING PROCEDURE (SOP)", cell_grey)]]
        t1 = Table(row1, colWidths=[self.content_width])
        t1.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _GREY_BG),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), _BORDER_W, black),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t1)

        # Row 2-4: metadata grid
        col_w = self.content_width / 4
        meta_data = [
            [
                Paragraph("<b>Procedure No.:</b>", cell_bold),
                Paragraph(_safe_text(self.doc_id or "—"), cell_style),
                Paragraph("<b>Revision:</b>", cell_bold),
                Paragraph("<b>Effective Date:</b>", cell_bold),
            ],
            [
                Paragraph("<b>Title:</b>", cell_bold),
                Paragraph(_safe_text(title), cell_style),
                Paragraph("<b>Page Count:</b>", cell_bold),
                Paragraph("", cell_style),
            ],
            [
                Paragraph("<b>Work Location:</b>", cell_bold),
                Paragraph(_safe_text(work_location), cell_style),
                Paragraph("", cell_style),
                Paragraph("", cell_style),
            ],
        ]
        # Row 2: proc no | value | revision | effective date value
        meta_data[0][3] = Paragraph(
            _safe_text(self.date_str), cell_style,
        )

        t_meta = Table(meta_data, colWidths=[col_w] * 4)
        t_meta.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), _BORDER_W, black),
            ("INNERGRID", (0, 0), (-1, -1), _BORDER_W, black),
            ("BACKGROUND", (0, 0), (0, -1), _GREY_BG),
            ("BACKGROUND", (2, 0), (2, -1), _GREY_BG),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 6 * mm))

        # ---- Summary paragraph ----
        if overview:
            story.append(Paragraph("Summary", heading_style))
            for block in parse_markdown(overview)[:15]:
                story.extend(self.render_blocks([block]))
            story.append(Spacer(1, 6 * mm))

        # ================================================================
        # APPROVAL / CONCURRENCE TABLE
        # ================================================================
        story.append(Paragraph("Approval / Concurrence", heading_style))

        sig_line = "_" * 30
        approval_header = [
            Paragraph("<b>Role</b>", cell_bold),
            Paragraph("<b>Name</b>", cell_bold),
            Paragraph("<b>Signature</b>", cell_bold),
            Paragraph("<b>Date</b>", cell_bold),
        ]
        approval_rows = [
            [Paragraph("Author", cell_style),
             Paragraph("", cell_style),
             Paragraph(sig_line, cell_style),
             Paragraph("", cell_style)],
            [Paragraph("Peer Reviewer", cell_style),
             Paragraph("", cell_style),
             Paragraph(sig_line, cell_style),
             Paragraph("", cell_style)],
            [Paragraph("Principal Investigator", cell_style),
             Paragraph("", cell_style),
             Paragraph(sig_line, cell_style),
             Paragraph("", cell_style)],
        ]
        t_approval = Table(
            [approval_header, *approval_rows],
            colWidths=[
                self.content_width * 0.25,
                self.content_width * 0.25,
                self.content_width * 0.30,
                self.content_width * 0.20,
            ],
        )
        t_approval.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), _BORDER_W, black),
            ("INNERGRID", (0, 0), (-1, -1), _BORDER_W, black),
            ("BACKGROUND", (0, 0), (-1, 0), _GREY_BG),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_approval)

        # ================================================================
        # PAGE 2 — Change history
        # ================================================================
        story.append(PageBreak())
        story.append(Paragraph("Change History", heading_style))

        ch_header = [
            Paragraph("<b>Revision</b>", cell_bold),
            Paragraph("<b>Effective Date</b>", cell_bold),
            Paragraph("<b>Description of Change</b>", cell_bold),
        ]
        ch_empty = [
            [Paragraph("", cell_style)] * 3
            for _ in range(5)
        ]
        t_ch = Table(
            [ch_header, *ch_empty],
            colWidths=[
                self.content_width * 0.15,
                self.content_width * 0.25,
                self.content_width * 0.60,
            ],
        )
        t_ch.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), _BORDER_W, black),
            ("INNERGRID", (0, 0), (-1, -1), _BORDER_W, black),
            ("BACKGROUND", (0, 0), (-1, 0), _GREY_BG),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t_ch)
        story.append(Spacer(1, 8 * mm))

        # ================================================================
        # NUMBERED SECTIONS from subsystems
        # ================================================================
        subsystems = content.get("subsystems", [])

        # Bucket subsystems: 1-4 = known, 0 = procedure
        buckets: dict[int, list] = {0: [], 1: [], 2: [], 3: [], 4: []}
        for sub in subsystems:
            name = sub.get("name", "")
            bucket = _classify_section(name)
            buckets[bucket].append(sub)

        # Build ordered list: 1, 2, 3, 4, then 0 (procedure)
        ordered: list[tuple[str, list]] = []
        for bk in (1, 2, 3, 4):
            for sub in buckets[bk]:
                ordered.append((sub.get("name", ""), sub))
        for sub in buckets[0]:
            ordered.append((sub.get("name", ""), sub))

        section_num = 1
        for name, sub in ordered:
            label = f"{section_num}.0"
            section_num += 1
            display_name = f"{label}  {_safe_text(name)}" if name else label
            story.append(Paragraph(display_name, heading_style))

            blocks = sub.get("blocks") or parse_markdown(
                sub.get("content", ""),
            )
            rendered = 0
            for block in blocks:
                btype = block.get("type", "")
                # Skip top-level headings (already rendered as section title)
                if btype == "heading" and block.get("level", 1) <= 1:
                    continue
                for fl in self.render_blocks([block]):
                    story.append(fl)
                    rendered += 1
                if rendered >= 80:
                    break

            story.append(Spacer(1, 4 * mm))

        return story

    # ------------------------------------------------------------------
    # Override generate() for SOP-specific header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the SOP PDF with custom header and footer."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.extract_content()

        # Doc ID
        doc_ids_cfg = self.config.get("doc_ids", {})
        if doc_ids_cfg.get("enabled", True):
            from briefkit.doc_ids import get_or_assign_doc_id

            self.doc_id = get_or_assign_doc_id(
                self.target_path,
                self.level,
                content.get("title", ""),
                config=self.config,
            )

        # Header/footer state

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 25) * mm
        right_m = margins.get("right", 25) * mm

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=content.get("title", "Standard Operating Procedure"),
            author=self.brand.get("org", "briefkit"),
            subject="SOP",
            creator="briefkit",
        )

        story = self.build_story(content)

        revision_text = f"Revision: {self.doc_id}" if self.doc_id else ""

        def _sop_header_footer(canvas, doc_inner):
            """SOP header and footer on every page."""
            canvas.saveState()
            pw = doc_inner.pagesize[0]

            # Header: centered title
            canvas.setFont("Helvetica-Bold", 10)
            canvas.setFillColor(black)
            canvas.drawCentredString(
                pw / 2, doc_inner.pagesize[1] - 15 * mm,
                "STANDARD OPERATING PROCEDURE",
            )

            # Header right: revision
            if revision_text:
                canvas.setFont("Helvetica", 8)
                canvas.drawRightString(
                    pw - left_m, doc_inner.pagesize[1] - 15 * mm,
                    revision_text,
                )

            # Footer: page number
            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(
                pw / 2, 12 * mm,
                f"Page {doc_inner.page}",
            )

            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_sop_header_footer,
            onLaterPages=_sop_header_footer,
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
