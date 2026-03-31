"""
briefkit.elements.back_cover — Back cover page builder.

Extracted and generalized from generate-briefing-v2.py _build_back_cover()
(original lines 2754-2840).
"""

import datetime
from pathlib import Path

from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm

from briefkit.styles import (
    _get_brand, _hex, _ps, CONTENT_WIDTH, build_styles
)


def build_back_cover(date=None, generator_note="", brand=None, content_width=None):
    """
    Build the back cover page flowables.

    Parameters
    ----------
    date : datetime.date or str, optional
        The date shown in the meta line.  Defaults to today.
    generator_note : str, optional
        Short technical note shown in the bottom bar (e.g. tool name/version).
        If empty the bottom bar is omitted.
    brand : dict, optional
        Brand config dict.  The following keys are used:
          - org       : organisation name shown in the top bar
          - tagline   : large centred tagline (e.g. brand slogan)
          - url       : monospaced URL shown below the tagline
          - copyright : copyright line (supports {year} placeholder)
          - abn       : ABN shown in the meta block if present
          - primary   : top/bottom bar background color
          - secondary : URL text color
          - caption   : muted text color for sub-lines

    Returns
    -------
    list
        List of ReportLab flowables starting with PageBreak.
    """
    b = _get_brand(brand)
    cw = content_width or CONTENT_WIDTH
    styles = build_styles(b)

    primary   = _hex(b, "primary")
    secondary = _hex(b, "secondary")
    caption   = _hex(b, "caption")

    org     = b.get("org", "")
    tagline = b.get("tagline", "")
    url     = b.get("url", "")
    abn     = b.get("abn", "")

    if date is None:
        date = datetime.date.today()
    if isinstance(date, str):
        date_str = date
        year     = datetime.date.today().year
    else:
        date_str = date.strftime("%d %B %Y")
        year     = date.year

    raw_cr    = b.get("copyright", "\u00a9 {year}")
    copyright = raw_cr.replace("{year}", str(year))

    flowables = []
    flowables.append(PageBreak())

    # --- Top primary bar ---
    org_display = org if org else "\u00a0"
    top_data = [[
        Paragraph(
            f'<font color="white"><b>{org_display}</b></font>',
            _ps("BKBackCoverTop", brand=b, fontSize=12, textColor=white,
                fontName=b.get("font_heading", "Helvetica-Bold")),
        ),
    ]]
    top_bar = Table(top_data, colWidths=[cw], rowHeights=[16 * mm])
    top_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), primary),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
    ]))
    flowables.append(top_bar)
    flowables.append(Spacer(1, 40 * mm))

    # --- Tagline ---
    if tagline:
        tagline_style = _ps(
            "BKBackCoverTagline",
            brand=b,
            fontSize=20,
            textColor=primary,
            fontName=b.get("font_heading", "Helvetica-Bold"),
            alignment=1,
        )
        flowables.append(Paragraph(f'"{tagline}"', tagline_style))
        flowables.append(Spacer(1, 8 * mm))

    # --- Sub-label ---
    sub_style = _ps(
        "BKBackCoverSub",
        brand=b,
        fontSize=11,
        textColor=caption,
        fontName=b.get("font_caption", "Helvetica-Oblique"),
        alignment=1,
    )
    flowables.append(Paragraph(org if org else "\u00a0", sub_style))
    flowables.append(Spacer(1, 6 * mm))

    # --- URL ---
    if url:
        url_style = _ps(
            "BKBackCoverURL",
            brand=b,
            fontSize=9,
            textColor=secondary,
            fontName=b.get("font_mono", "Courier"),
            alignment=1,
        )
        flowables.append(Paragraph(url, url_style))

    flowables.append(Spacer(1, 20 * mm))

    # --- Meta block ---
    meta_style = _ps(
        "BKBackCoverMeta",
        brand=b,
        fontSize=8,
        textColor=caption,
        alignment=1,
    )
    if date_str:
        flowables.append(Paragraph(
            f"This document was generated on {date_str}.",
            meta_style,
        ))

    abn_part = f" | ABN {abn}" if abn else ""
    flowables.append(Paragraph(
        f"{copyright}{abn_part}. All rights reserved.",
        meta_style,
    ))

    flowables.append(Spacer(1, 40 * mm))

    # --- Bottom primary bar (optional generator note) ---
    if generator_note:
        bottom_data = [[
            Paragraph(
                f'<font color="white">{generator_note}</font>',
                _ps("BKBackCoverBottomText", brand=b, fontSize=7, textColor=white),
            ),
        ]]
        bottom_bar = Table(bottom_data, colWidths=[cw], rowHeights=[10 * mm])
        bottom_bar.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), primary),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        flowables.append(bottom_bar)

    return flowables
