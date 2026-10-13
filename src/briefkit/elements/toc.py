"""
briefkit.elements.toc — Table of contents builder.

Every entry is an internal link to the heading it names: the heading is
bookmarked under the slug of its text when it is drawn (see
``BriefkitDocTemplate.afterFlowable``), and the TOC entry links to that
slug. An entry may carry its own key as a third tuple element.
"""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph

from briefkit.styles import CONTENT_WIDTH, _get_brand, _hex, _ps, esc, slugify


def build_toc(sections, brand=None, content_width=None):
    """
    Build a table of contents from a list of section titles.

    Parameters
    ----------
    sections : list of (int, str) or (int, str, str)
        Each tuple is (level, title) or (level, title, anchor key).
        Level 1 entries are rendered bold and full-width; level 2 entries
        are indented. Without a key the entry links to ``slugify(title)``,
        which is the key the matching heading is bookmarked under.
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    list
        List of ReportLab Paragraph flowables, each an internal link.
    """
    b = _get_brand(brand)
    _ = content_width or CONTENT_WIDTH
    primary = _hex(b, "primary")
    secondary = _hex(b, "secondary")

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
    for entry in sections:
        level, title = entry[0], entry[1]
        key = entry[2] if len(entry) > 2 and entry[2] else slugify(title)
        style = toc_h1 if level == 1 else toc_h2
        elements.append(Paragraph(f'<a href="#{esc(key)}">{esc(str(title).strip())}</a>', style))

    return elements
