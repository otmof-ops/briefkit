"""
briefkit.templates.resume
~~~~~~~~~~~~~~~~~~~~~~~~~
Resume / CV template -- clean professional layout, portrait orientation.

Build order:
  Header (name centered + contact) -> HR rule ->
  Education & Qualifications -> Work Experience -> Additional Information

Follows Oxford (A4) and Colorado State (Letter) production resume norms:
  - Centered name in 16pt bold black
  - Contact line centered, 9pt dark grey, pipe-separated
  - 1pt black horizontal rule after header
  - Education first, then work experience
  - Two-column date|company layout for experience entries
  - Three-column date|institution|degree layout for education entries
  - Fully monochrome -- black text, grey (#666666) secondary
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import A3, A4, legal, letter
from reportlab.lib.units import mm
from reportlab.platypus import (
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
    _ps,
    _safe_para,
    _safe_text,
)

_PAGE_SIZES = {"A4": A4, "A3": A3, "Letter": letter, "Legal": legal}

_DARK_GREY = HexColor("#666666")
_BLACK = black

# Keywords that identify education/qualification subsystems
_EDUCATION_KEYWORDS = re.compile(
    r"(?i)(education|qualification|degree|university|academic|school|college"
    r"|diploma|certificate|masters|bachelor|phd|mba|postgrad)",
)


class ResumeTemplate(BaseBriefingTemplate):
    """
    Professional resume / CV template.

    Produces a clean monochrome portrait PDF with centered name header,
    contact info, education section, work experience entries, and
    additional information.
    """

    def _section_heading(self, title: str) -> list:
        """Return flowables for a section heading with a black underline rule."""
        items: list = []
        items.append(Spacer(1, 5 * mm))
        h_style = _ps(
            "ResumeSection", brand=self.brand, fontSize=12, textColor=_BLACK,
            fontName="Helvetica-Bold", spaceAfter=1,
        )
        items.append(_safe_para(title.upper(), h_style))
        line = Table([[""]], colWidths=[self.content_width], rowHeights=[0.6])
        line.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.8, _BLACK),
        ]))
        items.append(line)
        items.append(Spacer(1, 3 * mm))
        return items

    def _extract_contact(self, overview: str) -> tuple[list[str], list[str]]:
        """
        Parse overview text to separate contact info lines from body text.

        Returns (contact_lines, body_lines).
        """
        contact: list[str] = []
        body: list[str] = []
        blocks = parse_markdown(overview)[:20]

        for block in blocks:
            text = block.get("text", "").strip()
            if not text:
                continue
            btype = block.get("type", "")
            if btype == "heading":
                continue
            if ("@" in text or re.search(r"\+?\d[\d\s\-().]{6,}", text)
                    or re.search(r"(?i)(email|phone|location|address|linkedin)", text)):
                contact.append(text)
            elif len(text) < 60 and "|" in text:
                contact.append(text)
            else:
                body.append(text)

        return contact, body

    def _classify_subsystems(
        self, subsystems: list[dict],
    ) -> tuple[list[dict], list[dict]]:
        """
        Split subsystems into (education_subs, experience_subs) by scanning
        subsystem names for education-related keywords.
        """
        education: list[dict] = []
        experience: list[dict] = []
        for sub in subsystems:
            name = sub.get("name", "")
            if _EDUCATION_KEYWORDS.search(name):
                education.append(sub)
            else:
                experience.append(sub)
        return education, experience

    def build_story(self, content: dict) -> list:
        """
        Assemble the resume story:
          Header -> Education & Qualifications -> Work Experience
          -> Additional Information.
        """
        story: list = []
        b = self.brand

        title = content.get("title", "")
        overview = content.get("overview", "")
        subsystems = content.get("subsystems", [])
        _raw_terms = content.get("terms", [])
        terms = list(_raw_terms.keys()) if isinstance(_raw_terms, dict) else (list(_raw_terms) if _raw_terms else [])
        _raw_keywords = content.get("keywords") or []
        keywords = list(_raw_keywords.keys()) if isinstance(_raw_keywords, dict) else list(_raw_keywords)

        # --- Header: Name (centered, 16pt bold black) ---
        name_style = _ps(
            "ResumeName", brand=b, fontSize=16, textColor=_BLACK,
            fontName="Helvetica-Bold", alignment=1, spaceAfter=2,
        )
        if title:
            story.append(_safe_para(_safe_text(title), name_style))

        # --- Contact info (centered, 9pt dark grey, pipe-separated) ---
        contact_lines, body_lines = self._extract_contact(overview)
        if contact_lines:
            # Join all contact fragments into a single pipe-separated line
            all_contact = " | ".join(
                c.strip() for line in contact_lines
                for c in (line.split("|") if "|" in line else [line])
                if c.strip()
            )
            contact_style = _ps(
                "ResumeContact", brand=b, fontSize=9, textColor=_DARK_GREY,
                alignment=1, spaceAfter=1,
            )
            story.append(_safe_para(all_contact, contact_style))

        # --- 1pt black horizontal rule spanning full content width ---
        story.append(Spacer(1, 2 * mm))
        divider = Table([[""]], colWidths=[self.content_width], rowHeights=[1])
        divider.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 1, _BLACK),
        ]))
        story.append(divider)
        story.append(Spacer(1, 4 * mm))

        # --- Classify subsystems ---
        education_subs, experience_subs = self._classify_subsystems(subsystems)

        # --- Education & Qualifications (FIRST per Oxford norm) ---
        guide = content.get("guide_content", "")
        if education_subs or guide:
            story.extend(self._section_heading("Education & Qualifications"))
            for sub in education_subs:
                self._render_education_entry(story, sub)
            if guide:
                guide_style = _ps(
                    "ResumeGuide", brand=b, fontSize=10, textColor=_BLACK,
                    leading=14,
                )
                blocks = parse_markdown(guide)[:10]
                for block in blocks:
                    text = block.get("text", "").strip()
                    if text:
                        story.append(_safe_para(text, guide_style))

        # --- Work Experience ---
        if experience_subs:
            story.extend(self._section_heading("Work Experience"))
            for sub in experience_subs:
                self._render_experience_entry(story, sub)

        # --- Professional Summary / Additional Information ---
        additional_parts: list = []
        if body_lines:
            additional_parts.extend(body_lines[:5])

        all_terms = list(dict.fromkeys(terms + keywords))
        if all_terms:
            skills_text = ", ".join(_safe_text(t) for t in all_terms[:30])
            additional_parts.append(f"<b>Skills:</b> {skills_text}")

        if additional_parts:
            story.extend(self._section_heading("Additional Information"))
            info_style = _ps(
                "ResumeAdditional", brand=b, fontSize=10, textColor=_BLACK,
                leading=14, spaceAfter=2,
            )
            for part in additional_parts:
                story.append(_safe_para(part, info_style))

        return story

    def _render_experience_entry(self, story: list, sub: dict) -> None:
        """
        Render a work experience entry with two-column header:
          Left: date range (bold)  |  Right: company + city (right-aligned)
        Below: job title in italic, then bullet points.
        """
        name = sub.get("name", "")
        blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))

        # Extract structured info from blocks
        date_range = ""
        company_location = ""
        job_title = ""
        bullet_items: list[str] = []
        other_blocks: list[dict] = []

        first_para = True
        for block in blocks:
            btype = block.get("type", "")
            text = block.get("text", "").strip()
            if not text and btype != "list":
                continue
            if btype == "heading" and block.get("level", 1) <= 1:
                continue
            if btype == "list":
                for item in block.get("items", [])[:8]:
                    item_text = item if isinstance(item, str) else item.get("text", "")
                    if item_text:
                        bullet_items.append(item_text)
            elif btype in ("paragraph", "text") and first_para and text:
                # First paragraph is typically date/company/title detail
                job_title = text
                first_para = False
            else:
                other_blocks.append(block)

        # Use subsystem name as the primary label
        # Try to extract date range from name or job_title
        date_match = re.search(
            r"(\w{3,9}[\-\s]\d{2,4}\s*[-\u2013\u2014]\s*\w{3,9}[\-\s]\d{2,4}"
            r"|\d{4}\s*[-\u2013\u2014]\s*(?:\d{4}|[Pp]resent|[Cc]urrent))",
            name,
        )
        if date_match:
            date_range = date_match.group(0)
            company_location = name.replace(date_range, "").strip(" ,-\u2013\u2014")
        else:
            company_location = name

        # Two-column header table: [date_range | company_location]
        date_style = _ps(
            "ResumeExpDate", brand=self.brand, fontSize=10, textColor=_BLACK,
            fontName="Helvetica-Bold", spaceAfter=0,
        )
        company_style = _ps(
            "ResumeExpCompany", brand=self.brand, fontSize=10, textColor=_BLACK,
            fontName="Helvetica-Bold", alignment=2, spaceAfter=0,
        )

        left_cell = _safe_para(_safe_text(date_range), date_style) if date_range else _safe_para("", date_style)
        right_cell = _safe_para(_safe_text(company_location), company_style) if company_location else _safe_para("", company_style)

        col_w = self.content_width
        header_table = Table(
            [[left_cell, right_cell]],
            colWidths=[col_w * 0.35, col_w * 0.65],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)

        # Job title in italic
        if job_title:
            title_style = _ps(
                "ResumeExpTitle", brand=self.brand, fontSize=10,
                textColor=_DARK_GREY, fontName="Helvetica-Oblique",
                spaceAfter=2,
            )
            story.append(_safe_para(_safe_text(job_title), title_style))

        # Bullet points
        if bullet_items:
            bullet_style = _ps(
                "ResumeBullet", brand=self.brand, fontSize=10,
                textColor=_BLACK, leftIndent=10, bulletIndent=0,
                leading=13,
            )
            for item_text in bullet_items[:8]:
                story.append(_safe_para(
                    f"\u2022  {_safe_text(item_text)}", bullet_style,
                ))

        # Any remaining blocks
        rendered = 0
        for block in other_blocks:
            if rendered >= 10:
                break
            for fl in self.render_blocks([block]):
                story.append(fl)
                rendered += 1

        story.append(Spacer(1, 3 * mm))

    def _render_education_entry(self, story: list, sub: dict) -> None:
        """
        Render an education entry with three-column layout:
          Col 1: date range (bold)
          Col 2: institution + location
          Col 3: degree + subject (right-aligned)
        """
        name = sub.get("name", "")
        blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))

        date_range = ""
        institution = name
        location = ""
        degree = ""
        extra_items: list[str] = []

        # Try to extract date from name
        date_match = re.search(
            r"(\w{3,9}[\-\s]\d{2,4}\s*[-\u2013\u2014]\s*\w{3,9}[\-\s]\d{2,4}"
            r"|\d{4}\s*[-\u2013\u2014]\s*(?:\d{4}|[Pp]resent|[Cc]urrent))",
            name,
        )
        if date_match:
            date_range = date_match.group(0)
            institution = name.replace(date_range, "").strip(" ,-\u2013\u2014")

        # Parse blocks for degree info and location
        for block in blocks:
            btype = block.get("type", "")
            text = block.get("text", "").strip()
            if not text and btype != "list":
                continue
            if btype == "heading":
                continue
            if btype == "list":
                for item in block.get("items", [])[:4]:
                    item_text = item if isinstance(item, str) else item.get("text", "")
                    if item_text:
                        extra_items.append(item_text)
            elif btype in ("paragraph", "text") and not degree:
                degree = text
            elif btype in ("paragraph", "text") and not location:
                location = text

        # Three-column education table
        date_style = _ps(
            "ResumeEduDate", brand=self.brand, fontSize=10, textColor=_BLACK,
            fontName="Helvetica-Bold", spaceAfter=0,
        )
        inst_style = _ps(
            "ResumeEduInst", brand=self.brand, fontSize=10, textColor=_BLACK,
            fontName="Helvetica-Bold", spaceAfter=0,
        )
        degree_style = _ps(
            "ResumeEduDegree", brand=self.brand, fontSize=10, textColor=_BLACK,
            alignment=2, spaceAfter=0,
        )

        date_cell = _safe_para(_safe_text(date_range), date_style)
        inst_parts = _safe_text(institution)
        if location:
            inst_parts += f"<br/><font size='9' color='#666666'>{_safe_text(location)}</font>"
        inst_cell = _safe_para(inst_parts, inst_style)
        degree_cell = _safe_para(_safe_text(degree), degree_style)

        col_w = self.content_width
        edu_table = Table(
            [[date_cell, inst_cell, degree_cell]],
            colWidths=[col_w * 0.22, col_w * 0.43, col_w * 0.35],
        )
        edu_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(edu_table)

        # Extra items as bullets below
        if extra_items:
            bullet_style = _ps(
                "ResumeEduBullet", brand=self.brand, fontSize=10,
                textColor=_BLACK, leftIndent=10, bulletIndent=0,
                leading=13,
            )
            for item_text in extra_items[:4]:
                story.append(_safe_para(
                    f"\u2022  {_safe_text(item_text)}", bullet_style,
                ))

        story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # Override generate() -- clean resume with minimal footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the resume PDF with minimal page-number footer."""
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

        # Header/footer state -- minimal for resume
        _hf_state["section"] = ""
        _hf_state["date"] = self.date_str
        _hf_state["doc_id"] = ""
        _hf_state["brand"] = self.brand

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 20) * mm
        bottom_m = margins.get("bottom", 18) * mm
        left_m = margins.get("left", 22) * mm
        right_m = margins.get("right", 22) * mm

        page_size = _PAGE_SIZES.get(layout.get("page_size", "A4"), A4)

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=content.get("title", "Resume"),
            author=self.brand.get("org", "briefkit"),
            subject="Resume",
            creator="briefkit",
        )

        story = self.build_story(content)

        def _resume_footer(canvas, doc_inner):
            """Subtle page number footer for multi-page resumes."""
            canvas.saveState()
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(_DARK_GREY)
            canvas.drawCentredString(
                doc_inner.pagesize[0] / 2, 10 * mm,
                f"Page {doc_inner.page}",
            )
            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=lambda c, d: None,
            onLaterPages=_resume_footer,
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
