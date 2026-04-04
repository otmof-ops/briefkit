"""
briefkit.templates.minutes
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Meeting minutes template.

Build order:
  Meeting Header → Attendees → Agenda Items (body) →
  Action Items Table → Resolutions → Next Meeting → Closing

Key differences:
  - Meeting header block (title, date, location, chair, secretary)
  - Attendees section auto-extracted from content
  - Each numbered markdown file = one agenda item
  - Action items auto-extracted and consolidated into summary table
  - Resolutions auto-extracted (RESOLVED: / RESOLUTION: patterns)
  - Next meeting info from config or content
  - Closing with adjournment time and chair signature line
  - No cover page, no bibliography, no back cover
  - Header: meeting title + date
  - Footer: page number
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor
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
    build_data_table,
)
from briefkit.styles import (
    _get_brand,
    _hex,
    _ps,
    build_styles,
)

# ---------------------------------------------------------------------------
# Regex patterns for extraction
# ---------------------------------------------------------------------------

_ACTION_PATTERN = re.compile(
    r'(?:^|\n)\s*(?:\*\*)?(?:Action(?:\s*Item)?|TODO|ACTION\s*ITEM)[:\s]+\s*'
    r'(.{10,300})',
    re.IGNORECASE | re.MULTILINE,
)

_RESOLUTION_PATTERN = re.compile(
    r'(?:^|\n)\s*(?:\*\*)?(?:RESOLVED|RESOLUTION)[:\s]+\s*(.{10,400})',
    re.IGNORECASE | re.MULTILINE,
)

_ATTENDEE_SECTION_PATTERN = re.compile(
    r'(?:^|\n)#+\s*(?:Attendees?|Present|Participants?|Apologies)\s*\n'
    r'((?:\s*[\*\-]\s+.+\n?)+)',
    re.IGNORECASE | re.MULTILINE,
)

_NEXT_MEETING_PATTERN = re.compile(
    r'(?:^|\n)(?:#+\s*)?(?:Next\s+Meeting)[:\s]+\s*(.{5,200})',
    re.IGNORECASE | re.MULTILINE,
)

_ADJOURN_PATTERN = re.compile(
    r'(?:adjourned|closed|ended)\s+(?:at\s+)?(\d{1,2}[:\.]?\d{0,2}\s*(?:am|pm|AM|PM)?)',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Custom header / footer
# ---------------------------------------------------------------------------

_minutes_state: dict = {
    "title": "",
    "date": "",
    "brand": {},
}


def _minutes_header_footer(canvas, doc):
    """
    Minutes template header/footer.

    Header: meeting title (left) + date (right).
    Footer: page number centered.
    """
    canvas.saveState()
    b = _get_brand(_minutes_state.get("brand"))
    page_width, page_height = doc.pagesize
    caption_c = HexColor(b.get("caption", "#666666"))
    rule_c = HexColor(b.get("rule", "#CCCCCC"))

    # Header
    top_y = page_height - doc.topMargin + 8 * mm
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(caption_c)

    title = _minutes_state.get("title", "")
    date_str = _minutes_state.get("date", "")

    if title:
        canvas.drawString(doc.leftMargin, top_y, title)
    if date_str:
        canvas.drawRightString(page_width - doc.rightMargin, top_y, date_str)

    # Rule below header
    canvas.setStrokeColor(rule_c)
    canvas.setLineWidth(0.4)
    canvas.line(doc.leftMargin, top_y - 3, page_width - doc.rightMargin, top_y - 3)

    # Footer — page number centered
    bottom_y = doc.bottomMargin - 6 * mm
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(caption_c)
    canvas.drawCentredString(
        page_width / 2, bottom_y + 1.5 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


class MinutesTemplate(BaseBriefingTemplate):
    """
    Meeting minutes template.

    Produces a PDF formatted as formal meeting minutes with attendees,
    numbered agenda items, auto-extracted action items, resolutions,
    and a closing block.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the minutes story:
          Meeting header, attendees, agenda items, action items,
          resolutions, next meeting, closing.
        """
        story: list = []
        title = content.get("title", self.target_path.name.replace("-", " ").title())
        all_text = self._gather_all_text(content)

        # ---- Meeting header block ----
        story.extend(self._build_meeting_header(title, content))
        story.append(Spacer(1, 6 * mm))

        # ---- Attendees ----
        attendees = self._extract_attendees(all_text, content)
        if attendees:
            story.extend(self._build_attendees_section(attendees))
            story.append(Spacer(1, 6 * mm))

        # ---- Agenda items (body) ----
        story.extend(self._build_agenda_items(content))

        # ---- Action items table ----
        actions = self._extract_actions(all_text, content)
        if actions:
            story.append(Spacer(1, 4 * mm))
            story.extend(self._build_action_items_table(actions))

        # ---- Resolutions ----
        resolutions = self._extract_resolutions(all_text)
        if resolutions:
            story.append(Spacer(1, 4 * mm))
            story.extend(self._build_resolutions(resolutions))

        # ---- Next meeting ----
        next_meeting = self._extract_next_meeting(all_text, content)
        if next_meeting:
            story.append(Spacer(1, 4 * mm))
            story.extend(self._build_next_meeting(next_meeting))

        # ---- Closing ----
        story.append(Spacer(1, 6 * mm))
        story.extend(self._build_closing(all_text, content))

        return story

    # ------------------------------------------------------------------
    # Gather all text for pattern matching
    # ------------------------------------------------------------------

    def _gather_all_text(self, content: dict) -> str:
        """Concatenate all textual content for regex extraction."""
        parts = [content.get("overview", "")]
        for sub in content.get("subsystems", []):
            parts.append(sub.get("content", ""))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Meeting header
    # ------------------------------------------------------------------

    def _build_meeting_header(self, title: str, content: dict) -> list:
        """
        Build the meeting header block with title, date, location,
        chair, and secretary.
        """
        flowables: list = []

        # Title
        title_style = _ps(
            "MinutesTitle", brand=self.brand,
            fontSize=22, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "primary"),
            alignment=1, spaceAfter=6,
        )
        flowables.append(Paragraph(title, title_style))

        # Subtitle: "Meeting Minutes"
        subtitle_style = _ps(
            "MinutesSubtitle", brand=self.brand,
            fontSize=13, textColor=_hex(self.brand, "caption"),
            alignment=1, spaceAfter=8,
        )
        flowables.append(Paragraph("Meeting Minutes", subtitle_style))
        flowables.append(Spacer(1, 4 * mm))

        # Meta fields in a small table
        project = self.config.get("project", {})
        meta_rows: list[list[str]] = []

        meta_rows.append(["Date", self.date_str])

        location = project.get("location", "")
        if location:
            meta_rows.append(["Location", location])

        chair = project.get("chair", "")
        if chair:
            meta_rows.append(["Chair", chair])

        secretary = project.get("secretary", "")
        if secretary:
            meta_rows.append(["Secretary", secretary])

        if meta_rows:
            build_styles(self.brand)
            label_style = _ps(
                "MinutesMetaLabel", brand=self.brand,
                fontSize=10, fontName="Helvetica-Bold",
                textColor=_hex(self.brand, "primary"),
            )
            value_style = _ps(
                "MinutesMetaValue", brand=self.brand,
                fontSize=10, textColor=_hex(self.brand, "body_text"),
            )

            table_data = [
                [
                    Paragraph(row[0], label_style),
                    Paragraph(row[1], value_style),
                ]
                for row in meta_rows
            ]

            t = Table(
                table_data,
                colWidths=[35 * mm, self.content_width - 35 * mm],
            )
            t.setStyle(TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING",   (0, 0), (-1, -1), 4),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
                ("LINEBELOW",     (0, -1), (-1, -1), 0.4,
                 HexColor(self.brand.get("rule", "#CCCCCC"))),
            ]))

            flowables.append(t)

        return flowables

    # ------------------------------------------------------------------
    # Attendees
    # ------------------------------------------------------------------

    def _extract_attendees(self, all_text: str, content: dict) -> dict[str, list[str]]:
        """
        Extract attendee lists. Returns dict with keys like
        'present', 'apologies' mapping to lists of names.
        """
        result: dict[str, list[str]] = {}

        # Try structured extraction from markdown headings
        for heading_match in re.finditer(
            r'(?:^|\n)#+\s*(Attendees?|Present|Participants?|Apologies)\s*\n'
            r'((?:\s*[\*\-]\s+.+\n?)+)',
            all_text, re.IGNORECASE | re.MULTILINE,
        ):
            category = heading_match.group(1).strip().lower()
            if category in ("attendee", "attendees", "present", "participants", "participant"):
                category = "present"
            names = re.findall(r'[\*\-]\s+(.+)', heading_match.group(2))
            names = [n.strip() for n in names if n.strip()]
            if names:
                result[category] = names

        return result

    def _build_attendees_section(self, attendees: dict[str, list[str]]) -> list:
        """Render attendees as labeled lists."""
        flowables: list = []

        flowables.append(Paragraph("Attendees", self.styles["STYLE_H2"]))
        flowables.append(Spacer(1, 2 * mm))

        label_style = _ps(
            "AttendeeLabel", brand=self.brand,
            fontSize=10, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "primary"),
            spaceBefore=4, spaceAfter=2,
        )
        name_style = _ps(
            "AttendeeName", brand=self.brand,
            fontSize=10, textColor=_hex(self.brand, "body_text"),
            leftIndent=12, spaceAfter=1,
        )

        for category, names in attendees.items():
            flowables.append(Paragraph(category.title(), label_style))
            for name in names:
                flowables.append(Paragraph(f"\u2022 {name}", name_style))

        return flowables

    # ------------------------------------------------------------------
    # Agenda items
    # ------------------------------------------------------------------

    def _build_agenda_items(self, content: dict) -> list:
        """
        Render each subsystem as a numbered agenda item.
        """
        flowables: list = []
        subsystems = content.get("subsystems", [])

        if not subsystems:
            overview = content.get("overview", "")
            if overview:
                flowables.append(Paragraph("Minutes", self.styles["STYLE_H2"]))
                flowables.append(Spacer(1, 3 * mm))
                for block in parse_markdown(overview)[:40]:
                    flowables.extend(self.render_blocks([block]))
            return flowables

        flowables.append(Paragraph("Agenda", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        for idx, sub in enumerate(subsystems, 1):
            item_title = f"Item {idx}: {sub['name']}"
            flowables.append(Paragraph(item_title, self.styles["STYLE_H2"]))
            flowables.append(Spacer(1, 2 * mm))

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

            flowables.append(Spacer(1, 4 * mm))

        return flowables

    # ------------------------------------------------------------------
    # Action items
    # ------------------------------------------------------------------

    def _extract_actions(self, all_text: str, content: dict) -> list[dict]:
        """
        Extract action items from content.

        Looks for:
          - "Action:", "TODO:", "ACTION ITEM:" text patterns
          - Tables with who/what/when headers
        """
        actions: list[dict] = []
        seen: set[str] = set()

        # Pattern-based extraction
        for m in _ACTION_PATTERN.finditer(all_text):
            text = m.group(1).strip().rstrip("*")
            key = text[:50].lower()
            if key not in seen:
                seen.add(key)
                actions.append({"description": text, "who": "", "when": ""})
            if len(actions) >= 30:
                break

        # Table-based extraction: look for tables with who/what/when headers
        for sub in content.get("subsystems", []):
            for tbl in sub.get("tables", []):
                headers_lower = [h.lower().strip() for h in tbl.get("headers", [])]
                # Check if this looks like an action table
                if any(kw in " ".join(headers_lower) for kw in ("who", "action", "responsible", "assigned")):
                    for row in tbl.get("rows", []):
                        if not row:
                            continue
                        desc = str(row[0]) if len(row) > 0 else ""
                        who = str(row[1]) if len(row) > 1 else ""
                        when = str(row[2]) if len(row) > 2 else ""
                        key = desc[:50].lower()
                        if key and key not in seen:
                            seen.add(key)
                            actions.append({
                                "description": desc,
                                "who": who,
                                "when": when,
                            })

        return actions

    def _build_action_items_table(self, actions: list[dict]) -> list:
        """Render action items as a consolidated table."""
        flowables: list = []

        flowables.append(Paragraph("Action Items", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        headers = ["#", "Action", "Responsible", "Due"]
        rows = []
        for idx, action in enumerate(actions, 1):
            rows.append([
                str(idx),
                action.get("description", ""),
                action.get("who", ""),
                action.get("when", ""),
            ])

        flowables.extend(build_data_table(
            headers, rows, brand=self.brand, content_width=self.content_width,
        ))

        return flowables

    # ------------------------------------------------------------------
    # Resolutions
    # ------------------------------------------------------------------

    def _extract_resolutions(self, all_text: str) -> list[str]:
        """Extract RESOLVED: or RESOLUTION: patterns."""
        resolutions: list[str] = []
        seen: set[str] = set()
        for m in _RESOLUTION_PATTERN.finditer(all_text):
            text = m.group(1).strip().rstrip("*")
            key = text[:50].lower()
            if key not in seen:
                seen.add(key)
                resolutions.append(text)
            if len(resolutions) >= 20:
                break
        return resolutions

    def _build_resolutions(self, resolutions: list[str]) -> list:
        """Render resolutions as numbered bold statements."""
        flowables: list = []

        flowables.append(Paragraph("Resolutions", self.styles["STYLE_H1"]))
        flowables.append(Spacer(1, 3 * mm))

        res_style = _ps(
            "MinutesResolution", brand=self.brand,
            fontSize=10, fontName="Helvetica-Bold",
            textColor=_hex(self.brand, "body_text"),
            leading=14, leftIndent=12, spaceBefore=3, spaceAfter=3,
        )

        for idx, text in enumerate(resolutions, 1):
            flowables.append(Paragraph(
                f"Resolution {idx}: {text}", res_style,
            ))

        return flowables

    # ------------------------------------------------------------------
    # Next meeting
    # ------------------------------------------------------------------

    def _extract_next_meeting(self, all_text: str, content: dict) -> str:
        """Extract next meeting info from content or config."""
        # Config first
        project = self.config.get("project", {})
        next_mtg = project.get("next_meeting", "")
        if next_mtg:
            return next_mtg

        # Pattern match
        m = _NEXT_MEETING_PATTERN.search(all_text)
        if m:
            return m.group(1).strip()

        return ""

    def _build_next_meeting(self, next_meeting: str) -> list:
        """Render next meeting info."""
        flowables: list = []

        flowables.append(Paragraph("Next Meeting", self.styles["STYLE_H2"]))
        flowables.append(Spacer(1, 2 * mm))
        flowables.append(Paragraph(next_meeting, self.styles["STYLE_BODY"]))

        return flowables

    # ------------------------------------------------------------------
    # Closing
    # ------------------------------------------------------------------

    def _build_closing(self, all_text: str, content: dict) -> list:
        """Render closing block with adjournment and signature line."""
        flowables: list = []

        # Try to extract adjournment time
        m = _ADJOURN_PATTERN.search(all_text)
        adjourn_time = m.group(1).strip() if m else ""

        closing_style = _ps(
            "MinutesClosing", brand=self.brand,
            fontSize=10, textColor=_hex(self.brand, "body_text"),
            leading=14, spaceBefore=4,
        )
        sig_style = _ps(
            "MinutesSig", brand=self.brand,
            fontSize=10, textColor=_hex(self.brand, "body_text"),
            leading=20, spaceBefore=16,
        )

        if adjourn_time:
            flowables.append(Paragraph(
                f"Meeting adjourned at {adjourn_time}.", closing_style,
            ))
        else:
            flowables.append(Paragraph(
                "Meeting adjourned.", closing_style,
            ))

        flowables.append(Spacer(1, 10 * mm))

        # Chair signature line
        project = self.config.get("project", {})
        chair = project.get("chair", "Chair")
        flowables.append(Paragraph(
            f"____________________________<br/>{chair}", sig_style,
        ))

        return flowables

    # ------------------------------------------------------------------
    # Override generate() for custom header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the minutes PDF with custom header/footer."""
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

        # Populate minutes header/footer state
        _minutes_state["title"] = title
        _minutes_state["date"] = self.date_str
        _minutes_state["brand"] = self.brand

        # Also populate base _hf_state
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
            subject="Meeting Minutes",
            creator="briefkit",
        )

        story = self.build_story(content)
        doc.build(
            story,
            onFirstPage=_minutes_header_footer,
            onLaterPages=_minutes_header_footer,
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
