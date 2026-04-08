"""
briefkit.templates.certificate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Certificate template — single-page landscape with decorative border.

Build order:
  Border → Title → Certifies line → Recipient → Description → Date/Org → Signature

Key differences:
  - Single page, landscape orientation
  - Decorative double-line border via Table
  - Large centered title: "CERTIFICATE OF [type]"
  - Recipient name in large ornamental font
  - No multi-page flow, no TOC, no body sections
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
)
from briefkit.styles import (
    _hex,
    _ps,
    _safe_para,
    _safe_text,
)

_PAGE_SIZES = {"A4": A4, "A3": A3, "Letter": letter, "Legal": legal}


def _landscape(size: tuple) -> tuple:
    """Return the page size rotated to landscape orientation."""
    w, h = size
    if w < h:
        return (h, w)
    return (w, h)


class CertificateTemplate(BaseBriefingTemplate):
    """
    Single-page certificate template.

    Produces a landscape PDF with a decorative border, large centered
    title, recipient name, achievement description, date, and signature
    line.  Suitable for completion, achievement, and recognition
    certificates.
    """

    def _detect_cert_type(self, title: str) -> str:
        """Derive certificate type from the content title."""
        lower = title.lower()
        for keyword in ("achievement", "recognition", "excellence",
                        "participation", "appreciation", "completion"):
            if keyword in lower:
                return keyword.upper()
        return "COMPLETION"

    def build_story(self, content: dict) -> list:
        """
        Assemble the certificate story — all flowables for a single page.
        """
        story: list = []
        b = self.brand
        primary = _hex(b, "primary")
        accent = _hex(b, "accent") if "accent" in b else primary
        body_c = _hex(b, "body_text")
        caption_c = _hex(b, "caption")
        org = b.get("org", "")

        title = content.get("title", "Certificate")
        cert_type = self._detect_cert_type(title)
        overview = content.get("overview", "")

        # --- Extract recipient and description from overview ---
        recipient = ""
        description_lines: list[str] = []
        if overview:
            blocks = parse_markdown(overview)[:10]
            for block in blocks:
                btype = block.get("type", "")
                text = block.get("text", "").strip()
                if not text:
                    continue
                if btype == "heading" and not recipient:
                    recipient = text
                elif btype in ("paragraph", "text") and text:
                    description_lines.append(text)

        if not recipient:
            recipient = title

        description = " ".join(description_lines[:3]) if description_lines else ""

        # --- Top spacing ---
        story.append(Spacer(1, 18 * mm))

        # --- Certificate title ---
        title_style = _ps(
            "CertTitle", brand=b, fontSize=28, textColor=primary,
            fontName="Helvetica-Bold", alignment=1, spaceAfter=6,
        )
        story.append(_safe_para(f"CERTIFICATE OF {cert_type}", title_style))

        # --- Decorative accent line ---
        story.append(Spacer(1, 4 * mm))
        line_tbl = Table([[""]], colWidths=[80 * mm], rowHeights=[0.8])
        line_tbl.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, -1), 1.5, accent),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        # Wrap in centering table
        wrapper = Table([[line_tbl]], colWidths=[self.content_width])
        wrapper.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(wrapper)
        story.append(Spacer(1, 10 * mm))

        # --- "This certifies that" ---
        certifies_style = _ps(
            "CertCertifies", brand=b, fontSize=13, textColor=body_c,
            fontName="Helvetica-Oblique", alignment=1, spaceAfter=4,
        )
        story.append(_safe_para("This certifies that", certifies_style))
        story.append(Spacer(1, 6 * mm))

        # --- Recipient name ---
        name_style = _ps(
            "CertRecipient", brand=b, fontSize=24, textColor=primary,
            fontName="Helvetica-Bold", alignment=1, spaceAfter=4,
        )
        story.append(_safe_para(_safe_text(recipient), name_style))
        story.append(Spacer(1, 6 * mm))

        # --- Achievement description ---
        if description:
            desc_style = _ps(
                "CertDesc", brand=b, fontSize=11, textColor=body_c,
                fontName="Helvetica", alignment=1, spaceAfter=4,
                leading=15,
            )
            story.append(_safe_para(description, desc_style))
            story.append(Spacer(1, 10 * mm))
        else:
            story.append(Spacer(1, 14 * mm))

        # --- Date and org ---
        date_style = _ps(
            "CertDate", brand=b, fontSize=10, textColor=caption_c,
            alignment=1, spaceAfter=2,
        )
        story.append(_safe_para(self.date_str, date_style))

        if org:
            org_style = _ps(
                "CertOrg", brand=b, fontSize=11, textColor=body_c,
                fontName="Helvetica-Bold", alignment=1, spaceAfter=2,
            )
            story.append(_safe_para(org, org_style))

        story.append(Spacer(1, 14 * mm))

        # --- Signature line ---
        sig_line = Table(
            [[""]],
            colWidths=[60 * mm],
            rowHeights=[0.5],
        )
        sig_line.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.8,
             HexColor(b.get("body_text", "#333333"))),
        ]))
        sig_wrapper = Table([[sig_line]], colWidths=[self.content_width])
        sig_wrapper.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(sig_wrapper)

        sig_label_style = _ps(
            "CertSigLabel", brand=b, fontSize=9, textColor=caption_c,
            alignment=1, spaceAfter=0,
        )
        story.append(_safe_para("Authorized Signature", sig_label_style))

        return story

    # ------------------------------------------------------------------
    # Override generate() — single-page landscape document
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate a single-page landscape certificate PDF."""
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

        # Header/footer state — minimal for certificate

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 20) * mm
        bottom_m = margins.get("bottom", 20) * mm
        left_m = margins.get("left", 25) * mm
        right_m = margins.get("right", 25) * mm

        page_size = _PAGE_SIZES.get(layout.get("page_size", "A4"), A4)
        page_size = _landscape(page_size)

        # Recompute content width for landscape
        self.content_width = page_size[0] - left_m - right_m

        doc = self._build_doc(
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            subject="Certificate",
        )

        story = self.build_story(content)
        story = self._finalize_story(story)

        primary_color = HexColor(self.brand.get("primary", "#1B2A4A"))
        accent_color = HexColor(
            self.brand.get("accent", self.brand.get("primary", "#1B2A4A")),
        )

        def _cert_border(canvas, doc_inner):
            """Draw a decorative double-line border on the certificate page."""
            canvas.saveState()
            w, h = doc_inner.pagesize

            # Outer border
            canvas.setStrokeColor(primary_color)
            canvas.setLineWidth(2.5)
            canvas.rect(12 * mm, 12 * mm, w - 24 * mm, h - 24 * mm)

            # Inner border
            canvas.setStrokeColor(accent_color)
            canvas.setLineWidth(0.8)
            canvas.rect(16 * mm, 16 * mm, w - 32 * mm, h - 32 * mm)

            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_cert_border,
            onLaterPages=_cert_border,
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
