"""
briefkit.templates.resume
~~~~~~~~~~~~~~~~~~~~~~~~~
Resume / CV template — clean professional layout, portrait orientation.

Build order:
  Header (name + contact) → Summary → Experience → Education → Skills

Key differences:
  - No cover page, no TOC, no dashboard, no bibliography, no back cover
  - Header with large name and contact info
  - Professional summary from overview body
  - Experience from subsystems (each = a position/role)
  - Skills from terms/keywords as tag-style list
  - Minimal branding, subtle color accents
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
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
    _hex,
    _ps,
    _safe_para,
    _safe_text,
)

_PAGE_SIZES = {"A4": A4, "A3": A3, "Letter": letter, "Legal": legal}


class ResumeTemplate(BaseBriefingTemplate):
    """
    Professional resume / CV template.

    Produces a clean portrait PDF with name header, contact info,
    professional summary, experience entries, education, and a skills
    section.  Each subsystem in the extracted content maps to a
    position or role entry.
    """

    def _section_divider(self, title: str) -> list:
        """Return flowables for a section heading with a subtle underline."""
        b = self.brand
        primary = _hex(b, "primary")
        items: list = []
        items.append(Spacer(1, 5 * mm))
        h_style = _ps(
            "ResumeSection", brand=b, fontSize=12, textColor=primary,
            fontName="Helvetica-Bold", spaceAfter=1,
        )
        items.append(_safe_para(title.upper(), h_style))
        line = Table([[""]], colWidths=[self.content_width], rowHeights=[0.6])
        line.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.8,
             HexColor(b.get("primary", "#1B2A4A"))),
        ]))
        items.append(line)
        items.append(Spacer(1, 3 * mm))
        return items

    def _extract_contact(self, overview: str) -> tuple[list[str], list[str]]:
        """
        Parse overview text to separate contact info lines from body text.

        Returns (contact_lines, body_lines).
        Contact lines are those containing @, phone-like patterns, or
        short single-field lines (location).
        """
        import re

        contact: list[str] = []
        body: list[str] = []
        blocks = parse_markdown(overview)[:20]

        for block in blocks:
            text = block.get("text", "").strip()
            if not text:
                continue
            btype = block.get("type", "")
            # Skip headings — those are the name
            if btype == "heading":
                continue
            # Detect contact-like lines
            if ("@" in text or re.search(r"\+?\d[\d\s\-().]{6,}", text)
                    or re.search(r"(?i)(email|phone|location|address|linkedin)", text)):
                contact.append(text)
            elif len(text) < 60 and "|" in text:
                # Pipe-separated contact line
                contact.append(text)
            else:
                body.append(text)

        return contact, body

    def build_story(self, content: dict) -> list:
        """
        Assemble the resume story:
          Header, summary, experience, education, skills.
        """
        story: list = []
        b = self.brand
        primary = _hex(b, "primary")
        body_c = _hex(b, "body_text")
        caption_c = _hex(b, "caption")

        title = content.get("title", "")
        overview = content.get("overview", "")
        subsystems = content.get("subsystems", [])
        terms = content.get("terms", [])
        keywords = content.get("keywords", [])

        # --- Header: Name ---
        name_style = _ps(
            "ResumeName", brand=b, fontSize=22, textColor=primary,
            fontName="Helvetica-Bold", alignment=0, spaceAfter=2,
        )
        if title:
            story.append(_safe_para(_safe_text(title), name_style))

        # --- Contact info ---
        contact_lines, body_lines = self._extract_contact(overview)
        if contact_lines:
            contact_style = _ps(
                "ResumeContact", brand=b, fontSize=9, textColor=caption_c,
                spaceAfter=1,
            )
            for line in contact_lines[:4]:
                story.append(_safe_para(line, contact_style))

        # --- Divider under header ---
        story.append(Spacer(1, 2 * mm))
        divider = Table([[""]], colWidths=[self.content_width], rowHeights=[1.2])
        divider.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 1.2, primary),
        ]))
        story.append(divider)
        story.append(Spacer(1, 4 * mm))

        # --- Professional Summary ---
        if body_lines:
            story.extend(self._section_divider("Professional Summary"))
            summary_style = _ps(
                "ResumeSummary", brand=b, fontSize=10, textColor=body_c,
                leading=14, spaceAfter=2,
            )
            for line in body_lines[:5]:
                story.append(_safe_para(line, summary_style))

        # --- Experience ---
        # All subsystems except the last one (reserved for education)
        experience_subs = subsystems[:-1] if len(subsystems) > 1 else subsystems
        education_subs = subsystems[-1:] if len(subsystems) > 1 else []

        if experience_subs:
            story.extend(self._section_divider("Experience"))
            for sub in experience_subs:
                self._render_position(story, sub, b, primary, body_c, caption_c)

        # --- Education ---
        guide = content.get("guide_content", "")
        if education_subs or guide:
            story.extend(self._section_divider("Education"))
            if education_subs:
                for sub in education_subs:
                    self._render_position(story, sub, b, primary, body_c, caption_c)
            if guide:
                guide_style = _ps(
                    "ResumeGuide", brand=b, fontSize=10, textColor=body_c,
                    leading=14,
                )
                blocks = parse_markdown(guide)[:10]
                for block in blocks:
                    text = block.get("text", "").strip()
                    if text:
                        story.append(_safe_para(text, guide_style))

        # --- Skills ---
        all_terms = list(dict.fromkeys(terms + keywords))
        if all_terms:
            story.extend(self._section_divider("Skills"))
            self._render_skills(story, all_terms, b, primary)

        return story

    def _render_position(
        self, story: list, sub: dict, brand: dict,
        primary, body_c, caption_c,
    ) -> None:
        """Render a single experience or education entry."""
        name = sub.get("name", "")
        if name:
            pos_style = _ps(
                "ResumePos", brand=brand, fontSize=11, textColor=primary,
                fontName="Helvetica-Bold", spaceAfter=1,
            )
            story.append(_safe_para(_safe_text(name), pos_style))

        blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
        first_para = True
        rendered = 0
        for block in blocks:
            btype = block.get("type", "")
            text = block.get("text", "").strip()

            # First paragraph treated as company/date detail
            if btype in ("paragraph", "text") and first_para and text:
                detail_style = _ps(
                    "ResumePosDetail", brand=brand, fontSize=9,
                    textColor=caption_c, fontName="Helvetica-Oblique",
                    spaceAfter=2,
                )
                story.append(_safe_para(text, detail_style))
                first_para = False
                rendered += 1
                continue

            if btype == "heading" and block.get("level", 1) <= 1:
                continue

            # Render list items as bullet points
            if btype == "list":
                items = block.get("items", [])
                bullet_style = _ps(
                    "ResumeBullet", brand=brand, fontSize=10,
                    textColor=body_c, leftIndent=10, bulletIndent=0,
                    leading=13,
                )
                for item in items[:8]:
                    item_text = item if isinstance(item, str) else item.get("text", "")
                    if item_text:
                        story.append(_safe_para(
                            f"\u2022  {_safe_text(item_text)}", bullet_style,
                        ))
                rendered += len(items)
            else:
                for fl in self.render_blocks([block]):
                    story.append(fl)
                    rendered += 1
                first_para = False

            if rendered >= 30:
                break

        story.append(Spacer(1, 3 * mm))

    def _render_skills(self, story: list, terms: list, brand: dict, primary) -> None:
        """Render skills as a tag-cloud style inline list."""
        if not terms:
            return

        accent_hex = brand.get("accent", brand.get("primary", "#1B2A4A"))
        bg_hex = brand.get("background", "#F5F5F5")

        # Build skill tags as a pipe-separated inline string
        tag_style = _ps(
            "ResumeSkillTag", brand=brand, fontSize=10,
            textColor=HexColor(accent_hex),
            leading=16,
        )
        # Join terms with a styled separator
        sep = f'<font color="{bg_hex}"> </font> \u2022 '
        tags_text = sep.join(_safe_text(t) for t in terms[:30])
        story.append(_safe_para(tags_text, tag_style))

    # ------------------------------------------------------------------
    # Override generate() — clean resume with minimal footer
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

        # Header/footer state — minimal for resume
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

        caption_color = HexColor(self.brand.get("caption", "#666666"))

        def _resume_footer(canvas, doc_inner):
            """Subtle page number footer for multi-page resumes."""
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
