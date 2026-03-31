"""
briefkit.elements.callout — Callout box builder.

Extracted and generalized from generate-briefing-v2.py build_callout_box()
(original lines 1426-1494).
"""

from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm

from briefkit.styles import _get_brand, _hex, _ps, _safe_para, CONTENT_WIDTH, build_styles

# Semantic tint colors for callout backgrounds.
# These are intentionally kept as near-neutral tints so they work across
# different brand primaries; callers may override via brand dict extensions.
_GOLD_BG  = HexColor("#fef9e7")
_GREEN_BG = HexColor("#eafaf1")
_RED_BG   = HexColor("#fdeaea")
_BG_GREY  = HexColor("#f5f6fa")

# Semantic status colors (not brand-specific — convey meaning universally)
SUCCESS = HexColor("#00b894")
WARNING = HexColor("#fdcb6e")
DANGER  = HexColor("#d63031")


def build_callout_box(text, box_type="insight", brand=None, content_width=None):
    """
    Build a callout box Table flowable.

    Parameters
    ----------
    text : str
        Body text.  Lines starting with '- ' or '• ' are rendered as bullets.
        Blank lines create small vertical gaps.
    box_type : str
        One of: 'insight', 'takeaway', 'warning', 'learn'.
        Controls the left-border color, background tint, and header label.
        - insight  : secondary color border, grey background, "KEY INSIGHT"
        - takeaway : accent color border, gold tint, "KEY TAKEAWAYS"
        - warning  : danger red border, red tint, "WARNING"
        - learn    : success green border, green tint, "WHAT YOU'LL LEARN"
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    Table
        A single Table flowable.  Wrap in KeepTogether at the call site
        if you want to prevent the box from splitting across pages.
    """
    b = _get_brand(brand)
    cw = content_width or CONTENT_WIDTH
    styles = build_styles(b)

    secondary = _hex(b, "secondary")
    accent    = _hex(b, "accent")
    rule      = _hex(b, "rule")

    config = {
        "insight":  {"border": secondary, "bg": _BG_GREY,  "label": "KEY INSIGHT"},
        "takeaway": {"border": accent,    "bg": _GOLD_BG,  "label": "KEY TAKEAWAYS"},
        "warning":  {"border": DANGER,    "bg": _RED_BG,   "label": "WARNING"},
        "learn":    {"border": SUCCESS,   "bg": _GREEN_BG, "label": "WHAT YOU'LL LEARN"},
    }
    cfg = config.get(box_type, config["insight"])

    label_style = _ps(
        f"BKCalloutLabel_{box_type}",
        brand=b,
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=cfg["border"],
        spaceAfter=2,
    )
    content_style = styles["STYLE_CALLOUT"]

    paragraphs = []
    for line in text.strip().split("\n"):
        stripped = line.strip()
        if stripped:
            if stripped.startswith("- ") or stripped.startswith("\u2022 "):
                stripped = "\u2022 " + stripped.lstrip("-\u2022 ")
            paragraphs.append(Paragraph(stripped, content_style))
        else:
            paragraphs.append(Spacer(1, 3))

    content_cell = [Paragraph(cfg["label"], label_style)] + paragraphs

    border_data = [[
        "",           # left color strip (4 pt wide)
        content_cell, # body content
    ]]

    box = Table(
        border_data,
        colWidths=[4, cw - 4],
        spaceBefore=6,
        spaceAfter=6,
    )
    box.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, -1), cfg["border"]),
        ("BACKGROUND",   (1, 0), (1, -1), cfg["bg"]),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (1, 0), (1, -1), 8),
        ("BOTTOMPADDING",(1, 0), (1, -1), 8),
        ("LEFTPADDING",  (1, 0), (1, -1), 10),
        ("RIGHTPADDING", (1, 0), (1, -1), 8),
        ("TOPPADDING",   (0, 0), (0, -1), 0),
        ("BOTTOMPADDING",(0, 0), (0, -1), 0),
        ("LEFTPADDING",  (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 0),
        ("BOX",          (0, 0), (-1, -1), 0.5, rule),
    ]))
    return box


def build_pull_quote(text, attribution="", brand=None, content_width=None):
    """
    Build a pull-quote block with thin rules above and below.

    Parameters
    ----------
    text : str
        The quote text.
    attribution : str, optional
        Attribution line shown below the quote.
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    list
        List of flowables.
    """
    b = _get_brand(brand)
    cw = content_width or CONTENT_WIDTH
    primary = _hex(b, "primary")
    caption = _hex(b, "caption")

    pull_style = _ps(
        "BKPullQuote",
        brand=b,
        fontName="Helvetica-Oblique",
        fontSize=14,
        textColor=primary,
        leading=20,
        alignment=1,
        spaceAfter=4,
        leftIndent=20,
        rightIndent=20,
    )

    flowables = []
    flowables.append(Spacer(1, 6 * mm))

    rule_data = [[""]]
    rule_table = Table(rule_data, colWidths=[cw * 0.7], rowHeights=[1])
    rule_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), primary),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    rule_wrapper = Table([[rule_table]], colWidths=[cw])
    rule_wrapper.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    flowables.append(rule_wrapper)
    flowables.append(Spacer(1, 4 * mm))

    flowables.append(Paragraph(f"\u201c{text}\u201d", pull_style))

    if attribution:
        attr_style = _ps(
            "PullQuoteAttr", brand=b,
            fontSize=9, textColor=caption,
            alignment=1, fontName="Helvetica-Oblique",
        )
        flowables.append(Paragraph(f"\u2014 {attribution}", attr_style))

    flowables.append(Spacer(1, 4 * mm))
    flowables.append(rule_wrapper)
    flowables.append(Spacer(1, 6 * mm))
    return flowables
