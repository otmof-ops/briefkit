"""
briefkit.templates.magazine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Magazine-style definitive guide template — pixel-perfect match of
Chromecast & Android TV Guide visual design (dark + print variants).

Exact specifications reverse-engineered from PDF content streams.

Cover page (canvas-drawn):
  - Full-page dark fill #0A0E16
  - Right sidebar: #003846, 155.9pt wide, 1.5pt cyan left edge
  - Sidebar vertical text: rotated 90deg, Helvetica 7pt #006B79
  - Corner bracket: #00E4FF 2pt stroke, top-left L-shape
  - Accent blocks: purple #492D79 56.69x8.5pt, cyan #00E4FF 34x5.67pt
  - Pre-title: Helvetica 9pt #495467 "THE DEFINITIVE GUIDE TO"
  - Title: Helvetica-Bold 54pt, #E8EDF2 for "Chrome-cast &", #00E4FF for accent words
  - Divider rule: #1C2A3A 0.8pt
  - Edition: Helvetica-Bold 12pt #B387FF "2026 EDITION"
  - Chapter list: number Helvetica-Bold 7.5pt #00E4FF, name Helvetica 8pt #8799AA
  - Date: Helvetica-Bold 7.5pt #495467
  - Bottom bar: 4 segments x 95.67pt x 4.25pt (cyan, blue, purple, pink)

Body pages (dark):
  - Full bg #0A0E16
  - Header: #006B79 1pt rule at y=807.87, title Helvetica 7pt #495467, page# #00E4FF
  - Footer: #1C2A3A 0.5pt rule at y=34.02, text Helvetica 6.5pt #495467 centered
  - Section label: Helvetica-Bold 10pt #00E4FF "S E C T I O N nn"
  - Section title: Helvetica-Bold 20pt #E8EDF2
  - Title rule: #00E4FF 2pt
  - H2: Helvetica-Bold 13pt #B387FF
  - Body: Helvetica 9.5pt #E8EDF2, 14pt leading
  - Table header: bg #0D2136, text #00E4FF Helvetica-Bold 8.5pt
  - Table rows: alternating #0F1823 / #131C28, text #E8EDF2 Helvetica 8.5pt
  - TOC: alternating rows 23pt tall, number Helvetica-Bold 8.5pt #00E4FF, title 8.5pt #E8EDF2
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
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
)
from briefkit.styles import (
    _get_brand,
    _ps,
    _safe_text,
    compute_content_width,
)
from briefkit.templates._helpers import should_skip

# ---------------------------------------------------------------------------
# Exact colors from PDF content streams — DARK variant
# ---------------------------------------------------------------------------

_D_BG = "#0A0E16"
_D_SIDEBAR = "#003846"
_D_SIDEBAR_EDGE = "#00E4FF"
_D_SIDEBAR_TEXT = "#006B79"
_D_PURPLE = "#492D79"
_D_CYAN = "#00E4FF"
_D_TEXT = "#E8EDF2"
_D_CAPTION = "#495467"
_D_LINK = "#B387FF"
_D_CHAPTER_TEXT = "#8799AA"
_D_RULE = "#1C2A3A"
_D_ROW_EVEN = "#0F1823"
_D_ROW_ODD = "#131C28"
_D_TABLE_HEADER = "#0D2136"
_D_PINK = "#FF3F80"
_D_BLUE = "#00AFFF"

# PRINT variant colors
_P_BG = "#FFFFFF"
_P_SIDEBAR = "#EBF4FB"
_P_SIDEBAR_EDGE = "#0077B5"
_P_SIDEBAR_TEXT = "#A0AEBF"
_P_PURPLE = "#5B21B5"
_P_CYAN = "#0077B5"
_P_TEXT = "#1A1F2B"
_P_CAPTION = "#495467"
_P_LINK = "#C3B5FD"
_P_ACCENT = "#0095C6"
_P_PINK = "#BD185D"
_P_RULE = "#D1D4DB"
_P_ROW_EVEN = "#EFF4F7"
_P_ROW_ODD = "#FFFFFF"
_P_TABLE_HEADER = "#0077B5"

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
    """Magazine header/footer — exact match of PDF body pages."""
    canvas.saveState()
    _get_brand(_mag_state.get("brand"))
    w, h = doc.pagesize
    is_dark = _mag_state.get("is_dark", True)

    # Select colors based on dark/light mode
    if is_dark:
        bg_c, rule_c, caption_c, accent_c = _D_BG, _D_SIDEBAR_TEXT, _D_CAPTION, _D_CYAN
    else:
        bg_c, rule_c, caption_c, accent_c = _P_BG, _P_RULE, _P_CAPTION, _P_CYAN

    # Dark mode: full page dark background
    if is_dark:
        canvas.setFillColor(HexColor(bg_c))
        canvas.rect(0, 0, w, h, stroke=0, fill=1)

    # Header rule at y=807.87
    canvas.setStrokeColor(HexColor(rule_c))
    canvas.setLineWidth(1)
    canvas.line(56.693, 807.874, 538.583, 807.874)

    # Header text at y=812.13
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(HexColor(caption_c))
    title = _mag_state.get("title", "")
    subtitle = _mag_state.get("subtitle", "")
    header_text = f"{title}  //  {subtitle}" if subtitle else title
    canvas.drawString(56.693, 812.126, header_text[:70])

    # Page number right — cyan
    page_num = canvas.getPageNumber()
    canvas.setFillColor(HexColor(accent_c))
    canvas.drawRightString(538.583, 812.126, f"{page_num:02d}")

    # Footer rule at y=34.02
    footer_rule_c = _D_RULE if is_dark else _P_RULE
    canvas.setStrokeColor(HexColor(footer_rule_c))
    canvas.setLineWidth(0.5)
    canvas.line(56.693, 34.016, 538.583, 34.016)

    # Footer text centered
    date_str = _mag_state.get("date", "")
    if date_str:
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(HexColor(caption_c))
        canvas.drawCentredString(w / 2, 22.677, date_str)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class MagazineTemplate(BaseBriefingTemplate):
    """
    Magazine-style definitive guide template — pixel-perfect Chromecast style.

    Large stacked typography, multi-color accent bars, sidebar spine text.
    Adapts between dark and light modes based on brand.background color.

    Suitable for: definitive guides, product guides, technology references,
    buyer's guides, ecosystem overviews.
    """

    def build_story(self, content: dict) -> list:
        """Assemble the magazine story."""
        story: list = []
        subsystems = content.get("subsystems", [])
        b = self.brand
        is_dark = _is_dark_bg(b.get("background", "#FFFFFF"))

        # Select palette
        if is_dark:
            cyan, text_c, _caption_c, _purple, _rule_c = _D_CYAN, _D_TEXT, _D_CAPTION, _D_LINK, _D_RULE
            row_even, row_odd, _table_hdr = _D_ROW_EVEN, _D_ROW_ODD, _D_TABLE_HEADER
        else:
            cyan, text_c, _caption_c, _purple, _rule_c = _P_CYAN, _P_TEXT, _P_CAPTION, _P_LINK, _P_RULE
            row_even, row_odd, _table_hdr = _P_ROW_EVEN, _P_ROW_ODD, _P_TABLE_HEADER

        cfg = self.config
        # Cover placeholder
        story.append(Spacer(1, 200 * mm))
        story.append(PageBreak())

        _toc_start = len(story)
        # TOC page — "S E C T I O N 00"
        sec_label_style = _ps(
            "MagSecLabel", brand=b,
            fontSize=10, fontName="Helvetica-Bold",
            textColor=HexColor(cyan), spaceBefore=4, spaceAfter=4,
        )
        story.append(Paragraph("S E C T I O N 00", sec_label_style))
        story.append(Spacer(1, 4 * mm))

        # "Table of Contents" — Helvetica-Bold 20pt
        toc_title_style = _ps(
            "MagTocTitle", brand=b,
            fontSize=20, fontName="Helvetica-Bold",
            textColor=HexColor(text_c), leading=24,
        )
        story.append(Paragraph("Table of Contents", toc_title_style))
        story.append(Spacer(1, 2 * mm))

        # Cyan rule: 2pt
        rule_data = [[""]]
        rule = Table(rule_data, colWidths=[self.content_width], rowHeights=[2])
        rule.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 2, HexColor(cyan)),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(rule)
        story.append(Spacer(1, 4 * mm))

        # TOC as alternating-row table — 23pt rows, number + title
        toc_data = []
        for i, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {i}")
            toc_data.append([
                Paragraph(
                    f'<b>{i:02d}</b>',
                    _ps(f"MagTocN_{i}", brand=b, fontSize=8.5,
                        fontName="Helvetica-Bold",
                        textColor=HexColor(cyan), leading=11),
                ),
                Paragraph(
                    _safe_text(name),
                    _ps(f"MagTocT_{i}", brand=b, fontSize=8.5,
                        textColor=HexColor(text_c), leading=11),
                ),
            ])

        if toc_data:
            toc_table = Table(
                toc_data,
                colWidths=[40, self.content_width - 40],
                rowHeights=[23] * len(toc_data),
            )
            style_cmds = [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, -1), 6),
                ("LEFTPADDING", (1, 0), (1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
            for i in range(len(toc_data)):
                bg = row_even if i % 2 == 0 else row_odd
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), HexColor(bg)))

            toc_table.setStyle(TableStyle(style_cmds))
            story.append(toc_table)

        story.append(PageBreak())

        if should_skip(cfg, "toc"):
            del story[_toc_start:]

        # Body sections
        for idx, sub in enumerate(subsystems, 1):
            name = sub.get("name", f"Section {idx}")

            # "S E C T I O N nn"
            story.append(Paragraph(
                f"S E C T I O N {idx:02d}",
                _ps(f"MagSL_{idx}", brand=b, fontSize=10,
                    fontName="Helvetica-Bold",
                    textColor=HexColor(cyan), spaceBefore=4, spaceAfter=4),
            ))
            story.append(Spacer(1, 2 * mm))

            # Section title: Helvetica-Bold 20pt
            story.append(Paragraph(
                name,
                _ps(f"MagST_{idx}", brand=b, fontSize=20,
                    fontName="Helvetica-Bold",
                    textColor=HexColor(text_c), leading=24),
            ))
            story.append(Spacer(1, 1 * mm))

            # Cyan rule
            rule2 = Table([[""]], colWidths=[self.content_width], rowHeights=[2])
            rule2.setStyle(TableStyle([
                ("LINEBELOW", (0, 0), (-1, -1), 2, HexColor(cyan)),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(rule2)
            story.append(Spacer(1, 3 * mm))

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
        subtitle_text = mag_cfg.get("subtitle", "THE DEFINITIVE GUIDE TO")
        bottom_colors = mag_cfg.get("bottom_colors", [])

        b = self.brand
        is_dark = _is_dark_bg(b.get("background", "#FFFFFF"))

        # Default bottom bar colors from PDF
        if not bottom_colors:
            if is_dark:
                bottom_colors = [_D_CYAN, _D_BLUE, _D_LINK, _D_PINK]
            else:
                bottom_colors = [_P_CYAN, _P_ACCENT, _P_LINK, _P_PINK]

        # Compiled date string
        compiled_date = f"COMPILED {self.date.strftime('%B %d, %Y').upper()}"
        footer_text = mag_cfg.get(
            "footer_text",
            f"{compiled_date}  \u2022  ECOSYSTEM STATUS AS OF EARLY {self.date.year}",
        )

        # Header/footer state
        _mag_state["title"] = mag_cfg.get("header_title", title).upper()
        _mag_state["subtitle"] = "THE DEFINITIVE GUIDE"
        _mag_state["date"] = footer_text
        _mag_state["is_dark"] = is_dark
        _mag_state["brand"] = b


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
            creator="(unspecified)",
            keywords="",
        )

        story = self.build_story(content)

        # Select cover palette
        if is_dark:
            bg, sidebar, sidebar_edge = _D_BG, _D_SIDEBAR, _D_SIDEBAR_EDGE
            sidebar_txt, purple, cyan = _D_SIDEBAR_TEXT, _D_PURPLE, _D_CYAN
            text_c, caption, link = _D_TEXT, _D_CAPTION, _D_LINK
            chapter_c, rule_c = _D_CHAPTER_TEXT, _D_RULE
        else:
            bg, sidebar, sidebar_edge = _P_BG, _P_SIDEBAR, _P_SIDEBAR_EDGE
            sidebar_txt, purple, cyan = _P_SIDEBAR_TEXT, _P_PURPLE, _P_CYAN
            text_c, caption, link = _P_TEXT, _P_CAPTION, _P_LINK
            chapter_c, rule_c = _P_CAPTION, _P_RULE

        def _cover_page(canvas, doc_inner):
            """Draw cover — exact match of Chromecast Guide page 1."""
            canvas.saveState()
            w, h = doc_inner.pagesize

            # Full background
            canvas.setFillColor(HexColor(bg))
            canvas.rect(0, 0, w, h, stroke=0, fill=1)

            # Right sidebar: 155.9pt wide
            canvas.setFillColor(HexColor(sidebar))
            canvas.rect(439.370, 0, 155.906, h, stroke=0, fill=1)

            # Sidebar cyan left edge: 1.5pt
            canvas.setFillColor(HexColor(sidebar_edge))
            canvas.rect(439.370, 0, 1.5, h, stroke=0, fill=1)

            # Sidebar vertical text (rotated 90deg)
            if sidebar_text:
                canvas.saveState()
                canvas.translate(518.740, 113.386)
                canvas.rotate(90)
                canvas.setFont("Helvetica", 7)
                canvas.setFillColor(HexColor(sidebar_txt))
                canvas.drawString(0, 0, sidebar_text.upper()[:60])
                canvas.restoreState()

            # Accent blocks on sidebar
            # Purple block: 56.69 x 8.50 at (481.89, 671.81)
            canvas.setFillColor(HexColor(purple))
            canvas.rect(481.890, 671.811, 56.693, 8.504, stroke=0, fill=1)
            # Cyan block: 34.02 x 5.67 at (481.89, 660.47)
            canvas.setFillColor(HexColor(cyan))
            canvas.rect(481.890, 660.472, 34.016, 5.669, stroke=0, fill=1)

            # Corner bracket: L-shape top-left, 2pt cyan stroke
            canvas.setStrokeColor(HexColor(cyan))
            canvas.setLineWidth(2)
            canvas.line(56.693, 785.197, 141.732, 785.197)  # horizontal
            canvas.line(56.693, 785.197, 56.693, 714.331)   # vertical

            # Content area origin at (62.69, 98.88)
            cx = 62.693

            # Pre-title: "THE DEFINITIVE GUIDE TO"
            if subtitle_text:
                canvas.setFont("Helvetica", 9)
                canvas.setFillColor(HexColor(caption))
                canvas.drawString(cx, 716.834, subtitle_text.upper()[:50])

            # Title: Helvetica-Bold 54pt, stacked words
            title_words = title.replace("\u2014", "\u2014 ").split()
            title_font_size = 54

            # Determine accent word index
            if accent_word_idx == -1:
                aw_idx = len(title_words) - 1
                for i in range(len(title_words) // 2, len(title_words)):
                    if len(title_words[i]) > 3:
                        aw_idx = i
                        break
            else:
                aw_idx = accent_word_idx

            # Group words into lines that fit in content area (to sidebar edge)
            content_w = 439.370 - cx - 10
            title_lines = []
            current = []
            for word in title_words:
                test = " ".join(current + [word])
                test_w = canvas.stringWidth(test, "Helvetica-Bold", title_font_size)
                if test_w > content_w and current:
                    title_lines.append(current[:])
                    current = [word]
                else:
                    current.append(word)
            if current:
                title_lines.append(current)

            # Draw title lines — count global word index for accent
            title_y = 631.795
            line_spacing = title_font_size + 10.8  # 64.8pt leading from PDF
            word_global_idx = 0
            for line_words in title_lines[:5]:
                line_text = " ".join(line_words)
                has_accent = any(word_global_idx + j == aw_idx for j in range(len(line_words)))

                if has_accent and len(line_words) > 1:
                    # Draw word by word for mixed coloring
                    x = cx
                    for j, word in enumerate(line_words):
                        if word_global_idx + j == aw_idx:
                            canvas.setFillColor(HexColor(cyan))
                        else:
                            canvas.setFillColor(HexColor(text_c))
                        canvas.setFont("Helvetica-Bold", title_font_size)
                        canvas.drawString(x, title_y, word)
                        x += canvas.stringWidth(word + " ", "Helvetica-Bold", title_font_size)
                elif has_accent:
                    canvas.setFillColor(HexColor(cyan))
                    canvas.setFont("Helvetica-Bold", title_font_size)
                    canvas.drawString(cx, title_y, line_text)
                else:
                    canvas.setFillColor(HexColor(text_c))
                    canvas.setFont("Helvetica-Bold", title_font_size)
                    canvas.drawString(cx, title_y, line_text)

                word_global_idx += len(line_words)
                title_y -= line_spacing

            # Divider rule: #1C2A3A 0.8pt
            rule_y = title_y + line_spacing - 56
            canvas.setFillColor(HexColor(rule_c))
            canvas.rect(cx, rule_y, 141.732, 0.8, stroke=0, fill=1)

            # Edition label: Helvetica-Bold 12pt purple
            edition_y = rule_y - 34
            canvas.setFont("Helvetica-Bold", 12)
            canvas.setFillColor(HexColor(link))
            canvas.drawString(cx, edition_y, edition.upper())

            # Chapter preview list
            list_y = edition_y - 45
            for i, sub in enumerate(subsystems[:6], 1):
                name = sub.get("name", f"Section {i}")
                # Number: Helvetica-Bold 7.5pt cyan
                canvas.setFont("Helvetica-Bold", 7.5)
                canvas.setFillColor(HexColor(cyan))
                canvas.drawString(cx, list_y, f"{i:02d}")
                # Name: Helvetica 8pt
                canvas.setFont("Helvetica", 8)
                canvas.setFillColor(HexColor(chapter_c))
                canvas.drawString(cx + 25.512, list_y, name[:45])
                list_y -= 15.591

            # Date label: Helvetica-Bold 7.5pt
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.setFillColor(HexColor(caption))
            month_year = self.date.strftime("%B %Y").upper()
            canvas.drawString(cx, 110.220, month_year)

            # Multi-color bottom bar: 4 segments x 95.67pt x 4.25pt at y=39.685
            if bottom_colors:
                segment_w = 95.669
                for i, color_hex in enumerate(bottom_colors[:4]):
                    canvas.setFillColor(HexColor(color_hex))
                    canvas.rect(
                        segment_w * i, 39.685,
                        segment_w, 4.252,
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
