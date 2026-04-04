"""
briefkit.elements.header_footer — Page template canvas callbacks.

Extracted and generalized from generate-briefing-v2.py header_footer()
(original lines 1911-1985) and build_classification_banner() (lines 1348-1405).

The header_footer canvas callback uses a module-level _hf_state dict that
callers must populate before building the PDF. The make_header_footer()
factory returns a configured callback bound to a specific brand and state.
"""

import datetime
from pathlib import Path

from reportlab.lib.colors import white
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Table, TableStyle

from briefkit.styles import (
    CONTENT_WIDTH,
    _get_brand,
    _hex,
    _ps,
    truncate_to_width,
)

# =============================================================================
# MODULE-LEVEL STATE (mirrors the original _hf_state pattern)
# =============================================================================

_hf_state = {
    "section":     "",
    "date":        "",
    "total_pages": None,
    "doc_id":      "",
}


def header_footer(canvas, doc):
    """
    Canvas callback: draws the header and footer on every page.

    Uses the module-level _hf_state dict and DEFAULT_BRAND colors.
    For custom branding, use make_header_footer() to obtain a bound callback.

    Header: primary-color rule, org name left, section name right.
    Footer: date left, "Page N of M" centre, doc_id / copyright right.
    """
    _draw_header_footer(canvas, doc, _hf_state, brand=None)


def make_header_footer(state, brand=None):
    """
    Return a canvas callback with the given state dict and brand config.

    Parameters
    ----------
    state : dict
        Keys: section, date, total_pages, doc_id.
        Pass the same dict object you will mutate before PDF generation.
    brand : dict, optional
        Brand config.  Falls back to DEFAULT_BRAND.

    Returns
    -------
    callable
        A (canvas, doc) callback suitable for PageTemplate onPage/onLaterPages.
    """
    def _callback(canvas, doc):
        _draw_header_footer(canvas, doc, state, brand=brand)
    return _callback


def _draw_header_footer(canvas, doc, state, brand=None):
    """Internal implementation shared by both callback variants."""
    b = _get_brand(brand)

    primary   = _hex(b, "primary")
    caption   = _hex(b, "caption")
    body_text = _hex(b, "body_text")
    rule      = _hex(b, "rule")
    org       = b.get("org", "")

    canvas.saveState()

    page_width, page_height = doc.pagesize
    left   = doc.leftMargin
    right  = page_width - doc.rightMargin
    top    = page_height - doc.topMargin + 6 * mm
    bottom = doc.bottomMargin - 6 * mm
    max_text_width = right - left

    # --- HEADER ---
    # Primary horizontal rule
    canvas.setFillColor(primary)
    canvas.setStrokeColor(primary)
    canvas.rect(left, top - 1, right - left, 0.8 * mm, fill=1, stroke=0)

    # Left label (org name)
    brand_dict = b
    heading_font = brand_dict.get("font_heading", "Helvetica-Bold")
    body_font = brand_dict.get("font_body", "Helvetica")

    canvas.setFillColor(primary)
    canvas.setFont(heading_font, 7)
    org_text = truncate_to_width(org, heading_font, 7, max_text_width * 0.5)
    canvas.drawString(left, top + 1 * mm, org_text)

    # Right label (section name)
    section_name = state.get("section", "")
    if section_name:
        canvas.setFont(body_font, 7)
        canvas.setFillColor(caption)
        section_text = truncate_to_width(section_name, body_font, 7, max_text_width * 0.5)
        canvas.drawRightString(right, top + 1 * mm, section_text)

    # --- FOOTER ---
    # Light rule
    canvas.setStrokeColor(rule)
    canvas.setLineWidth(0.5)
    canvas.line(left, bottom + 4 * mm, right, bottom + 4 * mm)

    # Page number (centre, upper line)
    page_num = doc.page
    total    = state.get("total_pages")
    page_text = f"Page {page_num} of {total}" if total else f"Page {page_num}"
    canvas.setFont(body_font, 7)
    canvas.setFillColor(body_text)
    canvas.drawCentredString((left + right) / 2, bottom + 1.5 * mm, page_text)

    # Copyright (centre, lower line — below page number)
    hf_doc_id   = state.get("doc_id", "")
    year        = datetime.date.today().year
    raw_cr      = b.get("copyright", "\u00a9 {year}")
    copyright   = raw_cr.replace("{year}", str(year))

    canvas.setFont(body_font, 6)
    canvas.setFillColor(caption)
    copyright_text = truncate_to_width(copyright, body_font, 6, max_text_width)
    canvas.drawCentredString(
        (left + right) / 2,
        bottom - 1.5 * mm,
        copyright_text,
    )

    if hf_doc_id:
        doc_id_text = truncate_to_width(hf_doc_id, body_font, 6, max_text_width * 0.4)
        canvas.drawRightString(right, bottom - 1.5 * mm, doc_id_text)

    canvas.restoreState()


# =============================================================================
# CLASSIFICATION BANNER
# =============================================================================

def build_classification_banner(level, path, brand=None, content_width=None):
    """
    Build the classification/navigation banner that appears after the cover.

    Parameters
    ----------
    level : int
        Hierarchy level (1–4).
    path : str or Path
        Filesystem path for the navigation breadcrumb.
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    Table
        A single Table flowable with primary-color background.
    """
    b = _get_brand(brand)
    cw = content_width or CONTENT_WIDTH
    primary = _hex(b, "primary")
    org     = b.get("org", "")

    level_labels = {
        1: "DIVISION",
        2: "SUBJECT",
        3: "DOCUMENTATION SET",
        4: "SPECIAL",
    }
    level_text = level_labels.get(level, "BRIEFING")

    parts    = [p for p in Path(path).parts if p not in ("/", "\\")]
    nav_path = " > ".join(parts[-5:]) if parts else str(path)

    title_left = f'<font color="white"><b>{org} \u2014 Executive Briefing</b></font>' if org \
        else '<font color="white"><b>Executive Briefing</b></font>'

    banner_data = [
        [
            Paragraph(
                title_left,
                _ps("BannerTitle", brand=b, fontSize=11, textColor=white, fontName=b.get("font_heading", "Helvetica-Bold")),
            ),
            Paragraph(
                f'<font color="white"><b>LEVEL: {level_text}</b></font>',
                _ps("BannerLevel", brand=b, fontSize=10, textColor=white,
                    fontName=b.get("font_heading", "Helvetica-Bold"), alignment=2),
            ),
        ],
        [
            Paragraph(
                f'<font color="white">{nav_path}</font>',
                _ps("BannerPath", brand=b, fontSize=8, textColor=white, fontName=b.get("font_mono", "Courier")),
            ),
            Paragraph(
                '<font color="white">Generated by briefkit</font>',
                _ps("BannerLib", brand=b, fontSize=8, textColor=white,
                    fontName=b.get("font_caption", "Helvetica-Oblique"), alignment=2),
            ),
        ],
    ]

    banner = Table(
        banner_data,
        colWidths=[cw * 0.65, cw * 0.35],
        rowHeights=[10 * mm, 8 * mm],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), primary),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (0, -1),  8),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ("SPAN",         (0, 0), (0, 0)),
    ]))
    return banner
