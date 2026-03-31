"""
briefkit.elements.cover — Cover page builder.

Extracted and generalized from generate-briefing-v2.py build_cover_page()
(original lines 1187-1345). All OTM-specific branding replaced with
brand dict lookups.
"""

import datetime
from pathlib import Path

from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm

from reportlab.pdfbase.pdfmetrics import stringWidth

from briefkit.styles import (
    _get_brand, _hex, _ps, _safe_para, CONTENT_WIDTH, build_styles
)


def build_cover_page(title, subtitle, path, level, date, doc_id="", brand=None, content_width=None):
    """
    Build the cover page flowables.

    Parameters
    ----------
    title : str
        Main document title.
    subtitle : str
        Subtitle shown below the title; may be empty.
    path : str or Path
        Filesystem path used to render the breadcrumb.
    level : int
        Hierarchy level (1–4).  Controls the level label badge.
    date : str or datetime.date
        Generation date shown on the cover.
    doc_id : str, optional
        Document reference ID shown below the date row.
    brand : dict, optional
        Brand config dict.  Falls back to DEFAULT_BRAND when omitted.

    Returns
    -------
    list
        List of ReportLab flowables ending with a PageBreak.
    """
    b = _get_brand(brand)
    cw = content_width or CONTENT_WIDTH
    styles = build_styles(b)

    primary   = _hex(b, "primary")
    secondary = _hex(b, "secondary")
    accent    = _hex(b, "accent")
    caption   = _hex(b, "caption")

    org      = b.get("org", "")
    abn      = b.get("abn", "")
    tagline  = b.get("tagline", "")

    level_labels = {
        1: "DIVISION BRIEFING",
        2: "SUBJECT BRIEFING",
        3: "DOCUMENTATION SET BRIEFING",
        4: "SPECIAL BRIEFING",
    }
    level_label = level_labels.get(level, "EXECUTIVE BRIEFING")

    # Breadcrumb from filesystem path
    path_parts = Path(path).parts
    breadcrumb_parts = [p for p in path_parts if p not in ("/", "\\")][-4:]
    breadcrumb = " \u203a ".join(breadcrumb_parts) if breadcrumb_parts else str(path)

    flowables = []

    # --- Top bar (primary color) ---
    left_text = f'<font color="white"><b>{org}</b></font>' if org else '<font color="white"><b>\u00a0</b></font>'
    navy_bar_data = [[
        Paragraph(
            left_text,
            _ps("CoverTopBarLeft", brand=b, fontSize=10, textColor=white, fontName="Helvetica-Bold"),
        ),
        Paragraph(
            f'<font color="white">{level_label}</font>',
            _ps("CoverTopBarRight", brand=b, fontSize=9, textColor=white, alignment=2),
        ),
    ]]
    navy_bar = Table(
        navy_bar_data,
        colWidths=[cw * 0.6, cw * 0.4],
        rowHeights=[14 * mm],
    )
    navy_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), primary),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (0, -1), 6),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 6),
    ]))
    flowables.append(navy_bar)
    flowables.append(Spacer(1, 30 * mm))

    # --- Title (auto-size font for long titles) ---
    title_font_size = 28
    while stringWidth(str(title), "Helvetica-Bold", title_font_size) > cw * 0.85 and title_font_size > 16:
        title_font_size -= 2

    flowables.append(Paragraph(title, styles["STYLE_TITLE"]))
    flowables.append(Spacer(1, 6 * mm))

    # --- Subtitle ---
    if subtitle:
        sub_style = _ps(
            "CoverSubtitle",
            brand=b,
            fontSize=14,
            textColor=secondary,
            fontName="Helvetica-Oblique",
            alignment=1,
            spaceAfter=8,
        )
        flowables.append(Paragraph(subtitle, sub_style))
        flowables.append(Spacer(1, 4 * mm))

    # --- Accent divider ---
    divider_data = [[""]]
    divider = Table(divider_data, colWidths=[cw], rowHeights=[3])
    divider.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), accent),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    flowables.append(divider)
    flowables.append(Spacer(1, 8 * mm))

    # --- Breadcrumb path ---
    path_style = _ps(
        "CoverPath",
        brand=b,
        fontSize=9,
        textColor=caption,
        alignment=1,
        fontName="Courier",
        spaceAfter=4,
    )
    flowables.append(Paragraph(breadcrumb, path_style))
    flowables.append(Spacer(1, 4 * mm))

    # --- Level badge (secondary color pill) ---
    badge_data = [[
        Paragraph(
            f'<font color="white"><b>{level_label}</b></font>',
            _ps("CoverBadge", brand=b, fontSize=9, textColor=white,
                fontName="Helvetica-Bold", alignment=1),
        )
    ]]
    badge = Table(badge_data, colWidths=[80 * mm], rowHeights=[8 * mm])
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), secondary),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    badge_wrapper = Table([[badge]], colWidths=[cw])
    badge_wrapper.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    flowables.append(badge_wrapper)
    flowables.append(Spacer(1, 30 * mm))

    # --- Date / version row ---
    date_str = date if isinstance(date, str) else date.strftime("%d %B %Y")
    meta_data = [[
        Paragraph(f"<b>Generated:</b> {date_str}", styles["STYLE_CAPTION"]),
    ]]
    meta = Table(meta_data, colWidths=[cw])
    meta.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    flowables.append(meta)

    # --- Document ID ---
    if doc_id:
        flowables.append(Paragraph(
            f"Document ID: {doc_id}",
            _ps("CoverDocID", brand=b, fontSize=10, textColor=caption, alignment=1),
        ))

    flowables.append(Spacer(1, 20 * mm))

    # --- Footer bar ---
    abn_part = f" — ABN {abn}" if abn else ""
    tagline_part = f'"{tagline}"' if tagline else ""
    org_display = org if org else ""

    footer_left_content = f'<font color="white">{org_display}{abn_part}</font>'
    footer_right_content = f'<font color="white">{tagline_part}</font>' if tagline_part else '<font color="white">\u00a0</font>'

    footer_data = [[
        Paragraph(
            footer_left_content,
            _ps("CoverFooterLeft", brand=b, fontSize=7, textColor=white),
        ),
        Paragraph(
            footer_right_content,
            _ps("CoverFooterRight", brand=b, fontSize=7, textColor=white,
                fontName="Helvetica-Oblique", alignment=2),
        ),
    ]]
    footer_bar = Table(
        footer_data,
        colWidths=[cw * 0.6, cw * 0.4],
        rowHeights=[10 * mm],
    )
    footer_bar.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), primary),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (0, -1),  6),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 6),
    ]))
    flowables.append(footer_bar)
    flowables.append(PageBreak())

    return flowables
