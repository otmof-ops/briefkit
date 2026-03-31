"""
briefkit.elements.toc — Table of contents builder.

Extracted and generalized from generate-briefing-v2.py build_toc()
(original lines 1408-1423).
"""

from briefkit.styles import _get_brand, _hex, _ps, _safe_para, CONTENT_WIDTH


def build_toc(sections, brand=None, content_width=None):
    """
    Build a manual table of contents from a list of section titles.

    Parameters
    ----------
    sections : list of (int, str)
        Each tuple is (level, title) where level is 1 or 2.
        Level 1 entries are rendered bold and full-width.
        Level 2 entries are indented.
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    list
        List of ReportLab Paragraph flowables.
    """
    b = _get_brand(brand)
    cw = content_width or CONTENT_WIDTH  # noqa: F841
    primary   = _hex(b, "primary")
    secondary = _hex(b, "secondary")

    from reportlab.lib.units import mm

    toc_h1 = _ps(
        "BKTOC1",
        brand=b,
        fontName=b.get("font_heading", "Helvetica-Bold"),
        fontSize=11,
        textColor=primary,
        spaceBefore=4,
        spaceAfter=2,
        leftIndent=0,
    )
    toc_h2 = _ps(
        "BKTOC2",
        brand=b,
        fontName=b.get("font_body", "Helvetica"),
        fontSize=10,
        textColor=secondary,
        spaceBefore=1,
        spaceAfter=1,
        leftIndent=10 * mm,
    )

    elements = []
    for level, title in sections:
        style = toc_h1 if level == 1 else toc_h2
        elements.append(_safe_para(title, style))

    return elements
