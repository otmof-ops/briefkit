"""
briefkit.templates.playbook
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Playbook template — phase-based incident response / operational playbook.

Grounded in Microsoft Ransomware IR Playbook (9pg, Letter, SegoeUI).

Build order:
  Dark cover page → Phase pages (auto-detected) → Back page

Design norms:
  - Full-page dark cover with white text (canvas-level drawing)
  - Phase-based structure: Preparation → Detection → Containment → Recovery
  - Role-based callout boxes for security, legal, finance, comms sections
  - Blockquotes rendered as callout boxes
  - Tables with secondary-colored headers
  - Running footer only (no header), suppressed on cover
  - NO TOC, NO bibliography
  - Back page with brand bar and briefkit attribution
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, white
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

from briefkit.elements.callout import build_callout_box
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
)

# ---------------------------------------------------------------------------
# Phase detection
# ---------------------------------------------------------------------------

_PHASE_PATTERNS: list[tuple[str, str]] = [
    (r"prepar|plan|before", "Preparation"),
    (r"detect|identif|analys|monitor", "Detection & Analysis"),
    (r"contain|eradicat|isolat|mitigat|respond", "Containment & Eradication"),
    (r"recover|restor|post|after|lesson", "Recovery & Post-Incident"),
]

_ROLE_KEYWORDS = (
    "security", "legal", "finance", "communications",
    "procurement", "engineering",
)


def _classify_phase(name: str) -> str | None:
    """Return a phase title if *name* matches a known phase pattern."""
    lower = name.lower()
    for pattern, phase_title in _PHASE_PATTERNS:
        if re.search(pattern, lower):
            return phase_title
    return None


def _is_role_section(name: str) -> str | None:
    """Return the role keyword if *name* contains a role keyword."""
    lower = name.lower()
    for role in _ROLE_KEYWORDS:
        if role in lower:
            return role.title()
    return None


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class PlaybookTemplate(BaseBriefingTemplate):
    """
    Playbook template.

    Produces a phase-based operational playbook PDF with a dark cover page,
    auto-detected phases, role-based callout sections, and running footer.
    Suitable for incident response playbooks, operational procedures,
    and runbooks.
    """

    # ------------------------------------------------------------------
    # Phase grouping
    # ------------------------------------------------------------------

    def _group_into_phases(
        self, subsystems: list[dict],
    ) -> list[dict]:
        """
        Group subsystems into phases.

        Returns a list of phase dicts:
          {"number": int, "title": str, "subsystems": [sub, ...]}
        """
        phase_map: dict[str, list[dict]] = {}
        ungrouped: list[dict] = []

        for sub in subsystems:
            name = sub.get("name", "")
            phase_title = _classify_phase(name)
            if phase_title:
                phase_map.setdefault(phase_title, []).append(sub)
            else:
                ungrouped.append(sub)

        # Build ordered phases — known phases first in canonical order
        phases: list[dict] = []
        phase_num = 1
        for _pattern, title in _PHASE_PATTERNS:
            if title in phase_map:
                phases.append({
                    "number": phase_num,
                    "title": title,
                    "subsystems": phase_map[title],
                })
                phase_num += 1

        # Remaining subsystems as numbered phases
        for sub in ungrouped:
            phases.append({
                "number": phase_num,
                "title": sub.get("name", f"Phase {phase_num}"),
                "subsystems": [sub],
            })
            phase_num += 1

        return phases

    # ------------------------------------------------------------------
    # Phase header builder
    # ------------------------------------------------------------------

    def _build_phase_header(self, phase: dict) -> list:
        """Build a phase header: circle number + title + accent rule."""
        flowables: list = []
        primary = _hex(self.brand, "primary")
        secondary = _hex(self.brand, "secondary")

        # Phase number in a circle (table cell with round-ish background)
        num_style = _ps(
            "PBPhaseNum", brand=self.brand,
            fontSize=16, fontName="Helvetica-Bold",
            textColor=white, alignment=1,
        )
        num_para = Paragraph(str(phase["number"]), num_style)

        title_style = _ps(
            "PBPhaseTitle", brand=self.brand,
            fontSize=18, fontName="Helvetica-Bold",
            textColor=primary, alignment=0,
            spaceBefore=0, spaceAfter=0,
        )
        title_para = Paragraph(_safe_text(phase["title"]), title_style)

        header_data = [[num_para, title_para]]
        header_tbl = Table(
            header_data,
            colWidths=[12 * mm, self.content_width - 14 * mm],
            rowHeights=[12 * mm],
        )
        header_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), primary),
            ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (1, 0), (1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        flowables.append(header_tbl)
        flowables.append(Spacer(1, 2 * mm))

        # Accent rule
        rule_data = [[""]]
        rule_tbl = Table(
            rule_data, colWidths=[self.content_width], rowHeights=[2],
        )
        rule_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), secondary),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        flowables.append(rule_tbl)
        flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Subsystem block renderer
    # ------------------------------------------------------------------

    def _render_subsystem(self, sub: dict) -> list:
        """Render a single subsystem's content blocks."""
        flowables: list = []
        name = sub.get("name", "")
        role = _is_role_section(name)

        # Role-based header callout
        if role:
            flowables.append(build_callout_box(
                f"<b>Role: {_safe_text(role)}</b> — {_safe_text(name)}",
                "insight",
                brand=self.brand,
                content_width=self.content_width,
            ))
            flowables.append(Spacer(1, 2 * mm))
        else:
            # Regular subsystem heading
            sub_heading_style = _ps(
                "PBSubHead", brand=self.brand,
                fontSize=13, fontName="Helvetica-Bold",
                textColor=_hex(self.brand, "primary"),
                spaceAfter=3, spaceBefore=4,
            )
            flowables.append(
                _safe_para(_safe_text(name), sub_heading_style),
            )

        blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
        for block in blocks:
            btype = block.get("type", "")

            # Skip top-level headings (already rendered)
            if btype == "heading" and block.get("level", 1) <= 2:
                continue

            # Blockquotes as callout boxes
            if btype == "blockquote":
                text = block.get("text", "")
                if text.strip():
                    flowables.append(build_callout_box(
                        text[:500],
                        "insight",
                        brand=self.brand,
                        content_width=self.content_width,
                    ))
                continue

            # Tables with secondary-colored headers
            if btype == "table":
                flowables.extend(self._render_table_block(block))
                continue

            # Everything else — delegate to base renderer
            for fl in self.render_blocks([block]):
                flowables.append(fl)

        return flowables

    # ------------------------------------------------------------------
    # Table with colored header
    # ------------------------------------------------------------------

    def _render_table_block(self, block: dict) -> list:
        """Render a table block with secondary-colored header row."""
        flowables: list = []
        rows = block.get("rows", [])
        headers = block.get("headers", [])
        if not rows and not headers:
            return flowables

        secondary = _hex(self.brand, "secondary")
        body_c = _hex(self.brand, "body_text")

        header_style = _ps(
            "PBTblHead", brand=self.brand,
            fontSize=9, fontName="Helvetica-Bold",
            textColor=white, alignment=0,
        )
        cell_style = _ps(
            "PBTblCell", brand=self.brand,
            fontSize=9, textColor=body_c, alignment=0,
        )

        data: list[list] = []
        if headers:
            data.append([
                Paragraph(_safe_text(str(h)), header_style)
                for h in headers
            ])

        for row in rows:
            cells = row if isinstance(row, list) else row.get("cells", [])
            data.append([
                Paragraph(_safe_text(str(c)), cell_style)
                for c in cells
            ])

        if not data:
            return flowables

        n_cols = max(len(r) for r in data)
        col_w = self.content_width / max(n_cols, 1)
        tbl = Table(data, colWidths=[col_w] * n_cols)

        style_cmds: list = [
            ("GRID", (0, 0), (-1, -1), 0.5, _hex(self.brand, "rule")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        if headers:
            style_cmds.append(
                ("BACKGROUND", (0, 0), (-1, 0), secondary),
            )
        tbl.setStyle(TableStyle(style_cmds))
        flowables.append(tbl)
        flowables.append(Spacer(1, 3 * mm))
        return flowables

    # ------------------------------------------------------------------
    # build_story
    # ------------------------------------------------------------------

    def build_story(self, content: dict) -> list:
        """Assemble the playbook story (cover is handled by canvas)."""
        story: list = []
        subsystems = content.get("subsystems", [])

        # Cover page placeholder — actual drawing is in onFirstPage callback.
        # We just need enough flowables to fill page 1.
        story.append(Spacer(1, 200 * mm))
        story.append(PageBreak())

        # Group into phases
        phases = self._group_into_phases(subsystems)

        for phase in phases:
            # Phase header
            story.extend(self._build_phase_header(phase))

            # Render each subsystem in the phase
            for sub in phase["subsystems"]:
                story.extend(self._render_subsystem(sub))
                story.append(Spacer(1, 4 * mm))

            story.append(PageBreak())

        # Back page
        story.extend(self._build_back_page())

        return story

    # ------------------------------------------------------------------
    # Back page
    # ------------------------------------------------------------------

    def _build_back_page(self) -> list:
        """Build a simple back page with brand bar and attribution."""
        flowables: list = []
        primary = _hex(self.brand, "primary")
        org = self.brand.get("org", "")

        flowables.append(Spacer(1, 60 * mm))

        # Brand bar
        bar_data = [[""]]
        bar = Table(bar_data, colWidths=[self.content_width], rowHeights=[4])
        bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), primary),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        flowables.append(bar)
        flowables.append(Spacer(1, 8 * mm))

        # Org name
        if org:
            org_style = _ps(
                "PBBackOrg", brand=self.brand,
                fontSize=14, fontName="Helvetica-Bold",
                textColor=primary, alignment=1,
            )
            flowables.append(_safe_para(_safe_text(org), org_style))
            flowables.append(Spacer(1, 4 * mm))

        # Attribution
        attr_style = _ps(
            "PBBackAttr", brand=self.brand,
            fontSize=9, textColor=_hex(self.brand, "caption"),
            alignment=1,
        )
        flowables.append(_safe_para("Generated by briefkit", attr_style))

        return flowables

    # ------------------------------------------------------------------
    # generate() — custom cover via canvas, letter size
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the playbook PDF with dark cover page."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.extract_content()
        title = content.get("title", self.target_path.name.replace("-", " ").title())
        overview = content.get("overview", "")

        # Derive subtitle from first sentence of overview
        subtitle = ""
        if overview:
            first_line = overview.strip().split("\n")[0]
            # Take first sentence
            for sep in (".", "!", "?"):
                idx = first_line.find(sep)
                if idx > 0:
                    first_line = first_line[: idx + 1]
                    break
            subtitle = first_line[:200]

        # Doc ID (optional)
        doc_ids_cfg = self.config.get("doc_ids", {})
        if doc_ids_cfg.get("enabled", True):
            from briefkit.doc_ids import get_or_assign_doc_id

            self.doc_id = get_or_assign_doc_id(
                self.target_path, self.level,
                title, config=self.config,
            )

        # Header/footer state
        _hf_state["section"] = title
        _hf_state["date"] = self.date_str
        _hf_state["doc_id"] = self.doc_id
        _hf_state["brand"] = self.brand

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 20) * mm
        bottom_m = margins.get("bottom", 20) * mm
        left_m = margins.get("left", 25) * mm
        right_m = margins.get("right", 25) * mm

        self.content_width = letter[0] - left_m - right_m

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=title,
            author=self.brand.get("org", "briefkit"),
            subject="Playbook",
            creator="briefkit",
        )

        story = self.build_story(content)

        primary_color = HexColor(self.brand.get("primary", "#1B2A4A"))
        org = self.brand.get("org", "")
        caption_c = self.brand.get("caption", "#999999")

        def _cover_page(canvas, doc_inner):
            """Draw the dark cover page — full primary background, white text."""
            canvas.saveState()
            w, h = doc_inner.pagesize

            # Full-page primary background
            canvas.setFillColor(primary_color)
            canvas.rect(0, 0, w, h, stroke=0, fill=1)

            # Org name — top-left
            if org:
                canvas.setFillColor(white)
                canvas.setFont("Helvetica", 12)
                canvas.drawString(left_m, h - 25 * mm, org)

            # Title — centered at ~35% from top
            canvas.setFillColor(white)
            canvas.setFont("Helvetica-Bold", 32)
            title_y = h * 0.65
            canvas.drawCentredString(w / 2, title_y, title[:80])

            # Subtitle
            if subtitle:
                canvas.setFont("Helvetica", 14)
                canvas.drawCentredString(w / 2, title_y - 30, subtitle[:120])

            # Date at bottom
            canvas.setFont("Helvetica", 10)
            canvas.drawCentredString(w / 2, 25 * mm, self.date_str)

            canvas.restoreState()

        def _body_footer(canvas, doc_inner):
            """Running footer: org name left, page number center."""
            canvas.saveState()
            w = doc_inner.pagesize[0]
            y = 12 * mm

            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(HexColor(caption_c))

            # Org name left
            if org:
                canvas.drawString(left_m, y, org)

            # Page number center
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(w / 2, y, str(page_num))

            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_cover_page,
            onLaterPages=_body_footer,
        )

        return self.output_path

    # ------------------------------------------------------------------
    # Suppress unused base section builders
    # ------------------------------------------------------------------

    def build_body(self, content: dict) -> list:
        return []

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
