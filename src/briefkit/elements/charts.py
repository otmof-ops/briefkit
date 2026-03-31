"""
briefkit.elements.charts — Bar chart and pull-quote builders.

Extracted and generalized from generate-briefing-v2.py:
  - build_pull_quote() original lines 1692-1741
  - build_bar_chart()  original lines 1744-1818

Note: build_pull_quote is also available via briefkit.elements.callouts
(the canonical location for all callout-style elements).  This module
re-exports it for convenience so callers can import either way.
"""

from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.graphics.shapes import Drawing, Rect, Line, String
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm

from briefkit.styles import (
    _get_brand, _hex, _ps, CONTENT_WIDTH, build_styles
)
from briefkit.elements.callout import build_pull_quote  # canonical location

def build_bar_chart(data, title="", brand=None, content_width=None):
    """
    Build a horizontal bar chart Drawing.

    Parameters
    ----------
    data : list of (str, float | int)
        Each tuple is (label_str, numeric_value).  Bars are scaled relative
        to the maximum value in the dataset.
    title : str, optional
        Caption shown above the chart (uses STYLE_CAPTION).
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    list
        List of flowables: optional Paragraph caption + Drawing.
    """
    b         = _get_brand(brand)
    cw        = content_width or CONTENT_WIDTH
    styles    = build_styles(b)
    secondary = _hex(b, "secondary")
    body_text = _hex(b, "body_text")
    bg_grey   = HexColor(b.get("code_bg", "#f5f6fa"))

    flowables = []
    if title:
        flowables.append(Paragraph(title, styles["STYLE_CAPTION"]))

    if not data:
        return flowables

    chart_width  = float(cw)
    bar_height   = 10 * mm
    gap          = 4 * mm
    label_width  = 50 * mm
    value_width  = chart_width - label_width - 10 * mm
    chart_height = len(data) * (bar_height + gap) + 10 * mm

    d = Drawing(chart_width, chart_height)

    # Light background
    bg = Rect(0, 0, chart_width, chart_height, fillColor=bg_grey, strokeColor=None)
    d.add(bg)

    max_val = max((v for _, v in data if isinstance(v, (int, float))), default=1)
    if max_val == 0:
        max_val = 1

    for i, (label, value) in enumerate(reversed(data)):
        y = gap + i * (bar_height + gap)

        # Bar fill
        try:
            numeric_val = float(value)
        except (ValueError, TypeError):
            numeric_val = 0.0
        bar_w = (numeric_val / max_val) * value_width

        bar = Rect(
            label_width, y, bar_w, bar_height,
            fillColor=secondary,
            strokeColor=None,
        )
        d.add(bar)

        # Label (left of bar, right-aligned)
        lbl = String(
            label_width - 4, y + bar_height * 0.35,
            str(label)[:28],
            fontName=b.get("font_body", "Helvetica"),
            fontSize=8,
            fillColor=body_text,
            textAnchor="end",
        )
        d.add(lbl)

        # Value (right of bar)
        val_lbl = String(
            label_width + bar_w + 4, y + bar_height * 0.35,
            str(value),
            fontName=b.get("font_heading", "Helvetica-Bold"),
            fontSize=8,
            fillColor=body_text,
            textAnchor="start",
        )
        d.add(val_lbl)

    flowables.append(d)
    return flowables


def build_timeline(events, title="", brand=None, content_width=None):
    """
    Build a horizontal timeline Drawing.

    Parameters
    ----------
    events : list of (str, str)
        Each tuple is (year_or_label, description).
    title : str, optional
        Caption shown above the timeline.
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    list
        List of flowables.
    """
    b = _get_brand(brand)
    cw        = content_width or CONTENT_WIDTH
    primary   = _hex(b, "primary")
    accent    = _hex(b, "accent")
    caption_c = _hex(b, "caption")
    bg_grey   = HexColor(b.get("code_bg", "#f5f6fa"))

    flowables = []
    if not events:
        return flowables

    chart_width  = float(cw)
    chart_height = 40 * mm
    axis_y       = chart_height * 0.55
    tick_height  = 5 * mm
    n            = len(events)

    d = Drawing(chart_width, chart_height)
    bg = Rect(0, 0, chart_width, chart_height, fillColor=bg_grey, strokeColor=None)
    d.add(bg)

    axis = Line(
        10 * mm, axis_y, chart_width - 10 * mm, axis_y,
        strokeColor=primary, strokeWidth=2,
    )
    d.add(axis)

    usable_width = chart_width - 20 * mm
    spacing = usable_width / max(n - 1, 1) if n > 1 else usable_width / 2

    for i, (label, desc) in enumerate(events):
        x = 10 * mm + (i * spacing if n > 1 else usable_width / 2)

        tick = Line(
            x, axis_y - tick_height / 2, x, axis_y + tick_height / 2,
            strokeColor=primary, strokeWidth=1.5,
        )
        d.add(tick)

        dot = Rect(x - 3, axis_y - 3, 6, 6, fillColor=accent, strokeColor=None)
        d.add(dot)

        text_y = axis_y + tick_height + 2 * mm if i % 2 == 0 else axis_y - tick_height - 8 * mm
        year_str = String(
            x, text_y, str(label)[:10],
            fontName=b.get("font_heading", "Helvetica-Bold"), fontSize=8,
            fillColor=primary, textAnchor="middle",
        )
        d.add(year_str)

        desc_y = text_y - 5 * mm if i % 2 == 0 else text_y + 5 * mm
        desc_str = String(
            x, desc_y, str(desc)[:20],
            fontName=b.get("font_body", "Helvetica"), fontSize=6,
            fillColor=caption_c, textAnchor="middle",
        )
        d.add(desc_str)

    flowables.append(d)
    return flowables


__all__ = ["build_bar_chart", "build_pull_quote", "build_timeline"]
