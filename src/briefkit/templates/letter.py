"""
briefkit.templates.letter
~~~~~~~~~~~~~~~~~~~~~~~~~
Formal correspondence template — letterhead, addressee, body, signature.

Build order:
  Letterhead → Date → Reference → Body → Closing → Signature

Key differences:
  - No cover page, no TOC, no dashboard
  - Letterhead with org name and tagline
  - Divider line under letterhead
  - Body paragraphs with optional section headings
  - Formal closing and signature block
  - Minimal footer (page number only, no header on first page)
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
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
    _hf_state,
)
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
)

_PAGE_SIZES = {"A4": A4, "A3": A3, "Letter": letter, "Legal": legal}


class LetterTemplate(BaseBriefingTemplate):
    """
    Formal letter/correspondence template.

    Produces a clean letterhead PDF with org branding, date, reference
    line, body paragraphs, and a formal closing with signature block.
    Suitable for official correspondence, cover letters, and notices.
    """

    def build_story(self, content: dict) -> list:
        """
        Assemble the letter story:
          Letterhead, date, reference, body, closing, signature.
        """
        story = []
        b = self.brand
        primary = _hex(b, "primary")
        caption_c = _hex(b, "caption")
        body_c = _hex(b, "body_text")
        org = b.get("org", "")
        project = self.config.get("project", {})

        # --- Letterhead ---
        if org:
            lh_style = _ps(
                "LetterHead", brand=b, fontSize=14, textColor=primary,
                fontName="Helvetica-Bold", spaceAfter=2,
            )
            story.append(Paragraph(org, lh_style))

        tagline = project.get("tagline", "")
        if tagline:
            tag_style = _ps(
                "LetterTagline", brand=b, fontSize=9, textColor=caption_c,
                fontName="Helvetica-Oblique",
            )
            story.append(Paragraph(tagline, tag_style))

        url = project.get("url", "")
        if url:
            url_style = _ps("LetterURL", brand=b, fontSize=8, textColor=caption_c)
            story.append(Paragraph(url, url_style))

        # Divider line
        story.append(Spacer(1, 3 * mm))
        divider = Table([[""]], colWidths=[self.content_width], rowHeights=[1])
        divider.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, -1), 1, HexColor(b.get("primary", "#1B2A4A"))),
        ]))
        story.append(divider)
        story.append(Spacer(1, 8 * mm))

        # --- Date ---
        date_style = _ps("LetterDate", brand=b, fontSize=10, textColor=body_c)
        story.append(Paragraph(self.date_str, date_style))
        story.append(Spacer(1, 6 * mm))

        # --- Reference line ---
        title = content.get("title", "")
        if title:
            ref_style = _ps(
                "LetterRef", brand=b, fontSize=10, textColor=body_c,
                fontName="Helvetica-Bold",
            )
            story.append(Paragraph(f"RE: {title}", ref_style))
            story.append(Spacer(1, 6 * mm))

        # --- Body ---
        self.styles.get(
            "STYLE_BODY",
            _ps("LetterBody", brand=b, fontSize=10),
        )

        # Overview as opening paragraphs
        overview = content.get("overview", "")
        if overview:
            for block in parse_markdown(overview)[:20]:
                story.extend(self.render_blocks([block]))
            story.append(Spacer(1, 4 * mm))

        # Subsystem content as body paragraphs
        for sub in content.get("subsystems", []):
            name = sub.get("name", "")
            if name:
                h_style = _ps(
                    "LetterH2", brand=b, fontSize=11, textColor=primary,
                    fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=3,
                )
                story.append(_safe_para(name, h_style))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                btype = block.get("type", "")
                if btype == "heading" and block.get("level", 1) <= 1:
                    continue
                for fl in self.render_blocks([block]):
                    story.append(fl)
                    rendered += 1
                if rendered >= 60:
                    break

            story.append(Spacer(1, 2 * mm))

        story.append(Spacer(1, 10 * mm))

        # --- Closing ---
        close_style = _ps("LetterClose", brand=b, fontSize=10, textColor=body_c)
        story.append(Paragraph("Yours faithfully,", close_style))
        story.append(Spacer(1, 15 * mm))  # Space for signature

        # Signature block
        sig_style = _ps(
            "LetterSig", brand=b, fontSize=10, textColor=body_c,
            fontName="Helvetica-Bold",
        )
        if org:
            story.append(Paragraph(org, sig_style))

        abn = project.get("abn", "")
        if abn:
            abn_style = _ps("LetterABN", brand=b, fontSize=8, textColor=caption_c)
            story.append(Paragraph(f"ABN {abn}", abn_style))

        return story

    # ------------------------------------------------------------------
    # Override generate() to use minimal header/footer for letters
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """
        Generate the letter PDF with page-number-only footer.
        """
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
        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 25) * mm   # Wider margins for letters
        right_m = margins.get("right", 25) * mm

        page_size = _PAGE_SIZES.get(layout.get("page_size", "A4"), A4)

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=content.get("title", "Correspondence"),
            author=self.brand.get("org", "briefkit"),
            subject="Letter",
            creator="briefkit",
        )

        story = self.build_story(content)

        caption_color = HexColor(self.brand.get("caption", "#666666"))

        def _letter_footer(canvas, doc_inner):
            """Page number footer for later pages only."""
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(caption_color)
            canvas.drawCentredString(
                doc_inner.pagesize[0] / 2, 12 * mm,
                f"Page {doc_inner.page}",
            )
            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=lambda c, d: None,
            onLaterPages=_letter_footer,
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
