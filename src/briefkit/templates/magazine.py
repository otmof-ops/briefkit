"""
briefkit.templates.magazine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Magazine-style definitive guide template — large typography, multi-color accents.

Grounded in Chromecast & Android TV Guide visual design (dark + print variants).

Build order:
  Cover (canvas) → TOC page → Body sections → Back page

Design norms:
  - Adaptive dark/light based on brand.background color
  - Large stacked title words with accent-colored emphasis word
  - Sidebar vertical spine text (rotated 90deg)
  - Geometric corner bracket decorations
  - Multi-color bottom bar on cover
  - "SECTION nn" labels on body pages
  - Alternating-row TOC table
  - Edition label and chapter preview on cover
  - Header: title // subtitle left, page number right
  - Footer: centered compilation date
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
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
    _hf_state,
)
from briefkit.styles import (
    _get_brand,
    _hex,
    _ps,
    _safe_para,
    _safe_text,
    compute_content_width,
)

# ---------------------------------------------------------------------------
# Module-level state for custom header / footer
# ---------------------------------------------------------------------------

_mag_state: dict = {
    "title": "",
    "subtitle": "",
    "date": "",
    "is_dark": True,
    "brand": {},
}


def _is_dark_bg(bg_hex: str) -> bool:
    """Determine if a hex color is dark (luminance < 0.5)."""
    bg_hex = bg_hex.lstrip("#")
    if len(bg_hex) != 6:
        return False
    r, g, b = int(bg_hex[:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance < 0.5


def _mag_header_footer(canvas, doc):
    """Magazine header/footer — title rule header, centered date footer."""
    canvas.saveState()
    b = _get_brand(_mag_state.get("brand"))
    w, h = doc.pagesize
    is_dark = _mag_state.get("is_dark", False)

    caption_c = HexColor(b.get("caption", "#8899AA"))
    secondary_c = HexColor(b.get("secondary", "#00E5FF"))
    rule_c = HexColor(b.get("rule", "#00E5FF"))
    body_font = b.get("font_body", "Helvetica")

    if is_dark:
        text_c = HexColor("#AABBCC")
    else:
        text_c = caption_c

    # Header — title // subtitle left, page number right
    header_y = h - doc.topMargin + 8 * mm

    title = _mag_state.get("title", "")
    subtitle = _mag_state.get("subtitle", "")
    header_text = title.upper()
    if subtitle:
        header_text += f"  //  {subtitle.upper()}"

    canvas.setFont(body_font, 7)
    canvas.setFillColor(text_c)
    canvas.drawString(doc.leftMargin, header_y, header_text[:70])

    # Page number right
    page_num = canvas.getPageNumber()
    canvas.setFont(body_font, 7)
    canvas.setFillColor(secondary_c)
    canvas.drawRightString(w - doc.rightMargin, header_y, f"{page_num:02d}")

    # Header rule
    canvas.setStrokeColor(rule_c)
    canvas.setLineWidth(0.5)
    canvas.line(
        doc.leftMargin, header_y - 4,
        w - doc.rightMargin, header_y - 4,
    )

    # Footer — centered compilation date
    footer_y = doc.bottomMargin - 6 * mm
    date_str = _mag_state.get("date", "")
    if date_str:
        canvas.setFont(body_font, 7)
        canvas.setFillColor(text_c)
        canvas.drawCentredString(w / 2, footer_y, date_str.upper())

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class MagazineTemplate(BaseBriefingTemplate):
    """
    Magazine-style definitive guide template.

    Produces a visually rich guide with large stacked typography on the
    cover, multi-color accent bars, sidebar spine text, and section-labeled
    body pages. Adapts between dark and light modes based on the
    brand.background color.

    Suitable for: definitive guides, product guides, technology references,
    buyer's guides, ecosystem overviews.
    """

    def build_story(self, content: dict) -> list:
        """Assemble the magazine story."""
        story: list = []
        subsystems = content.get("subsystems", [])
        b = self.brand
        is_dark = _is_dark_bg(b.get("background", "#FFFFFF"))

        # Cover placeholder
        story.append(Spacer(1, 200 * mm))
        story.append(PageBreak())

        # TOC page
        secondary_c = _hex(b, "secondary")

        # Section label
        section_label_style = _ps(
            "MagSectionLabel", brand=b,
            fontSize=9, fontName=b.get("font_heading", "Helvetica-Bold"),
            textColor=secondary_c, spaceBefore=4, spaceAfter=4,
            letterSpacing=3,
        )
        story.append(Paragraph("S E C T I O N  0 0", section_label_style))
        story.append(Spacer(1, 4 * mm))

        story.append(Paragraph("Table of Contents", self.styles["STYLE_H1"]))
        story.append(Spacer(1, 2 * mm))

        # Accent rule
        rule_data = [[""]]
        rule = Table(rule_data, colWidths=[self.content_width], rowHeights=[2])
        rule.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), secondary_c),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(rule)
        story.append(Spacer(1, 4 * mm))

        # TOC as alternating-row table
        if is_dark:
            row_bg_even = HexColor(b.get("table_alt", "#1F2535"))
            row_bg_odd = HexColor(b.get("background", "#1A1F2E"))
        else:
            row_bg_even = HexColor(b.get("table_alt", "#F5FAFB"))
            row_bg_odd = HexColor(b.get("background", "#FFFFFF"))

        toc_data = []
        for i, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {i}")
            toc_data.append([
                Paragraph(
                    f'<b>{i:02d}</b>',
                    _ps(f"MagTocN_{i}", brand=b, fontSize=10,
                        fontName=b.get("font_heading", "Helvetica-Bold"),
                        textColor=secondary_c, leading=14),
                ),
                Paragraph(
                    _safe_text(name),
                    _ps(f"MagTocT_{i}", brand=b, fontSize=10,
                        textColor=_hex(b, "body_text"), leading=14),
                ),
            ])

        if toc_data:
            toc_table = Table(
                toc_data,
                colWidths=[40, self.content_width - 40],
                rowHeights=[28] * len(toc_data),
            )
            style_cmds = [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, -1), 8),
                ("LEFTPADDING", (1, 0), (1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
            for i in range(len(toc_data)):
                bg = row_bg_even if i % 2 == 0 else row_bg_odd
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

            toc_table.setStyle(TableStyle(style_cmds))
            story.append(toc_table)

        story.append(PageBreak())

        # Body sections
        for idx, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {idx}")

            # Section label
            story.append(Paragraph(
                f"S E C T I O N  {idx:02d}",
                _ps(f"MagSecLbl_{idx}", brand=b, fontSize=9,
                    fontName=b.get("font_heading", "Helvetica-Bold"),
                    textColor=secondary_c, spaceBefore=4, spaceAfter=4),
            ))
            story.append(Spacer(1, 2 * mm))

            story.append(Paragraph(name, self.styles["STYLE_H1"]))
            story.append(Spacer(1, 2 * mm))

            blocks = sub.get("blocks") or parse_markdown(sub.get("content", ""))
            rendered = 0
            for block in blocks:
                if block["type"] == "heading" and block["level"] <= 1:
                    continue
                for fl in self.render_blocks([block]):
                    story.append(fl)
                    rendered += 1
                    if rendered >= 100:
                        break
                if rendered >= 100:
                    break

            story.append(Spacer(1, 6 * mm))

        # Back page
        story.append(Spacer(1, 60 * mm))
        attr_style = _ps(
            "MagBackAttr", brand=b,
            fontSize=9, textColor=_hex(b, "caption"),
            alignment=1,
        )
        story.append(_safe_para("Generated by briefkit", attr_style))

        return story

    # ------------------------------------------------------------------
    # generate() — custom cover and header/footer
    # ------------------------------------------------------------------

    def generate(self) -> Path:
        """Generate the magazine PDF with large-typography cover."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.extract_content()
        title = content.get(
            "title",
            self.target_path.name.replace("-", " ").title(),
        )
        subsystems = content.get("subsystems", [])

        # Doc ID
        doc_ids_cfg = self.config.get("doc_ids", {})
        if doc_ids_cfg.get("enabled", True):
            from briefkit.doc_ids import get_or_assign_doc_id

            self.doc_id = get_or_assign_doc_id(
                self.target_path, self.level,
                title, config=self.config,
            )

        # Template-specific config
        mag_cfg = self.config.get("magazine", {})
        edition = mag_cfg.get("edition", f"{self.date.year} EDITION")
        accent_word_idx = mag_cfg.get("accent_word", -1)
        sidebar_text = mag_cfg.get(
            "sidebar_text",
            f"{title}  //  {self.date.year}",
        )
        bottom_colors = mag_cfg.get("bottom_colors", [])
        subtitle = mag_cfg.get("subtitle", "THE DEFINITIVE GUIDE TO")

        b = self.brand
        is_dark = _is_dark_bg(b.get("background", "#FFFFFF"))

        # Default bottom bar colors
        if not bottom_colors:
            bottom_colors = [
                b.get("danger", "#FF4081"),
                b.get("secondary", "#00E5FF"),
                b.get("accent", "#B388FF"),
                b.get("danger", "#FF4081"),
            ]

        # Header/footer state
        _mag_state["title"] = title
        _mag_state["subtitle"] = subtitle
        _mag_state["date"] = f"COMPILED {self.date.strftime('%B %d, %Y').upper()}"
        _mag_state["is_dark"] = is_dark
        _mag_state["brand"] = b

        _hf_state["section"] = title
        _hf_state["date"] = self.date_str
        _hf_state["doc_id"] = self.doc_id
        _hf_state["brand"] = b

        layout = self.config.get("layout", {})
        margins = layout.get("margins", {})
        top_m = margins.get("top", 25) * mm
        bottom_m = margins.get("bottom", 22) * mm
        left_m = margins.get("left", 20) * mm
        right_m = margins.get("right", 20) * mm

        page_size = A4
        self.content_width = compute_content_width(page_size, margins)

        cfg_author = mag_cfg.get("author", "Research Compilation")
        cfg_subject = mag_cfg.get("subject", title)

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=page_size,
            topMargin=top_m,
            bottomMargin=bottom_m,
            leftMargin=left_m,
            rightMargin=right_m,
            title=title,
            author=cfg_author,
            subject=cfg_subject,
            creator="briefkit",
            keywords=self.doc_id or "briefkit",
        )

        story = self.build_story(content)

        primary_color = HexColor(b.get("primary", "#1A1F2E"))
        secondary_color = HexColor(b.get("secondary", "#00E5FF"))
        accent_color = HexColor(b.get("accent", "#B388FF"))
        bg_color = HexColor(b.get("background", "#1A1F2E"))

        def _cover_page(canvas, doc_inner):
            """Draw the magazine-style cover with large stacked typography."""
            canvas.saveState()
            w, h = doc_inner.pagesize

            # Full background
            canvas.setFillColor(bg_color)
            canvas.rect(0, 0, w, h, stroke=0, fill=1)

            # Right sidebar band
            sidebar_w = 60
            sidebar_color = HexColor("#1F2535") if is_dark else HexColor("#0097A7")
            canvas.setFillColor(sidebar_color)
            canvas.rect(w - sidebar_w, 0, sidebar_w, h, stroke=0, fill=1)

            # Sidebar vertical text
            if sidebar_text:
                canvas.saveState()
                canvas.translate(w - 18, h * 0.35)
                canvas.rotate(90)
                canvas.setFont("Helvetica", 7)
                sb_text_c = HexColor("#556677") if is_dark else HexColor("#FFFFFF")
                canvas.setFillColor(sb_text_c)
                canvas.drawString(0, 0, sidebar_text.upper()[:60])
                canvas.restoreState()

            # Geometric corner bracket (top-left)
            bracket_c = accent_color if is_dark else HexColor("#B0D8E0")
            canvas.setStrokeColor(bracket_c)
            canvas.setLineWidth(2)
            bx, by = left_m + 10, h - 80
            canvas.line(bx, by, bx, by + 50)
            canvas.line(bx, by + 50, bx + 40, by + 50)

            # Sidebar accent blocks (top-right area)
            block_x = w - sidebar_w - 20
            # Cyan block
            canvas.setFillColor(secondary_color)
            canvas.rect(block_x, h - 160, 50, 12, stroke=0, fill=1)
            # Purple block
            canvas.setFillColor(accent_color)
            canvas.rect(block_x, h - 176, 30, 8, stroke=0, fill=1)

            # Subtitle / pre-title text
            if subtitle:
                canvas.setFont("Helvetica", 9)
                sub_c = HexColor("#AAAAAA") if is_dark else HexColor("#666666")
                canvas.setFillColor(sub_c)
                canvas.drawString(left_m + 10, h - 130, subtitle.upper()[:50])

            # Large stacked title
            title_words = title.split()
            title_font_size = 44
            title_y = h - 180
            content_area_w = w - sidebar_w - left_m - 20

            # Determine which word gets accent color
            if accent_word_idx == -1:
                # Auto: last word or word > 4 chars in second half
                aw_idx = len(title_words) - 1
                for i in range(len(title_words) // 2, len(title_words)):
                    if len(title_words[i]) > 4:
                        aw_idx = i
                        break
            else:
                aw_idx = accent_word_idx

            # Group words into lines
            title_lines = []
            current = []
            for word in title_words:
                test = " ".join(current + [word])
                test_w = canvas.stringWidth(test, "Helvetica-Bold", title_font_size)
                if test_w > content_area_w and current:
                    title_lines.append(current[:])
                    current = [word]
                else:
                    current.append(word)
            if current:
                title_lines.append(current)

            word_global_idx = 0
            for line_words in title_lines[:5]:
                for word in line_words:
                    if word_global_idx == aw_idx:
                        canvas.setFillColor(secondary_color)
                    else:
                        if is_dark:
                            canvas.setFillColor(white)
                        else:
                            canvas.setFillColor(primary_color)

                    canvas.setFont("Helvetica-Bold", title_font_size)
                    break
                line_text = " ".join(line_words)

                # Check if accent word is in this line
                has_accent = any(
                    word_global_idx + j == aw_idx
                    for j in range(len(line_words))
                )
                if has_accent and len(line_words) > 1:
                    # Draw word by word
                    x = left_m + 10
                    for j, word in enumerate(line_words):
                        if word_global_idx + j == aw_idx:
                            canvas.setFillColor(secondary_color)
                        else:
                            if is_dark:
                                canvas.setFillColor(white)
                            else:
                                canvas.setFillColor(primary_color)
                        canvas.setFont("Helvetica-Bold", title_font_size)
                        canvas.drawString(x, title_y, word)
                        x += canvas.stringWidth(word + " ", "Helvetica-Bold", title_font_size)
                elif has_accent:
                    canvas.setFillColor(secondary_color)
                    canvas.setFont("Helvetica-Bold", title_font_size)
                    canvas.drawString(left_m + 10, title_y, line_text)
                else:
                    if is_dark:
                        canvas.setFillColor(white)
                    else:
                        canvas.setFillColor(primary_color)
                    canvas.setFont("Helvetica-Bold", title_font_size)
                    canvas.drawString(left_m + 10, title_y, line_text)

                word_global_idx += len(line_words)
                title_y -= title_font_size + 12

            # Accent rule under title
            rule_y = title_y + 4
            canvas.setStrokeColor(HexColor("#555555") if is_dark else HexColor("#CCCCCC"))
            canvas.setLineWidth(0.5)
            canvas.line(left_m + 10, rule_y, left_m + 160, rule_y)

            # Edition label
            edition_y = rule_y - 24
            canvas.setFont("Helvetica-Bold", 9)
            canvas.setFillColor(secondary_color)
            canvas.drawString(left_m + 10, edition_y, edition.upper())

            # Chapter preview list
            list_y = edition_y - 28
            canvas.setFont("Helvetica", 8)
            for i, sub in enumerate(subsystems[:6], 1):
                name = sub.get("name", f"Section {i}")
                # Number
                canvas.setFillColor(secondary_color)
                canvas.setFont("Helvetica-Bold", 8)
                canvas.drawString(left_m + 10, list_y, f"{i:02d}")
                # Name
                sub_c = HexColor("#CCCCCC") if is_dark else HexColor("#444444")
                canvas.setFillColor(sub_c)
                canvas.setFont("Helvetica", 8)
                canvas.drawString(left_m + 40, list_y, name[:45])
                list_y -= 16

            # Date label
            month_year = self.date.strftime("%B %Y").upper()
            canvas.setFont("Helvetica-Bold", 8)
            canvas.setFillColor(secondary_color)
            canvas.drawString(left_m + 10, 50, month_year)

            # Multi-color bottom bar
            if bottom_colors:
                bar_y = 16
                bar_h = 6
                total_w = w - sidebar_w
                segment_w = total_w / len(bottom_colors)
                for i, color_hex in enumerate(bottom_colors):
                    canvas.setFillColor(HexColor(color_hex))
                    canvas.rect(
                        segment_w * i, bar_y,
                        segment_w, bar_h,
                        stroke=0, fill=1,
                    )

            canvas.restoreState()

        doc.build(
            story,
            onFirstPage=_cover_page,
            onLaterPages=_mag_header_footer,
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

    def build_back_cover(self) -> list:
        return []
