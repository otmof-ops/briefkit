"""
briefkit.elements.dashboard — Metric dashboard builder.

Extracted and generalized from generate-briefing-v2.py build_metric_dashboard()
(original lines 1497-1556).
"""

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.platypus import Spacer

from briefkit.styles import CONTENT_WIDTH, _get_brand, _hex


def build_metric_dashboard(metrics, brand=None, content_width=None):
    """
    Build a metric dashboard Drawing — primary-color background with large
    white numbers.

    Parameters
    ----------
    metrics : list of (str, str)
        Each tuple is (value_str, label_str).  Maximum of 5 metrics are shown;
        any beyond the fifth are silently discarded.
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    Drawing or Spacer
        A ReportLab Drawing flowable, or a 1pt Spacer if metrics is empty.
    """
    b       = _get_brand(brand)
    cw      = content_width or CONTENT_WIDTH
    primary = _hex(b, "primary")

    metrics = metrics[:5]
    n = len(metrics)
    if n == 0:
        return Spacer(1, 1)

    panel_width  = float(cw)
    panel_height = 60 * mm
    cell_w       = panel_width / n

    d = Drawing(panel_width, panel_height)

    # Primary background
    bg = Rect(0, 0, panel_width, panel_height, fillColor=primary, strokeColor=None)
    d.add(bg)

    for idx, (value, label) in enumerate(metrics):
        cx = cell_w * idx + cell_w / 2

        # Vertical divider between cells
        if idx > 0:
            div = Line(
                cell_w * idx, panel_height * 0.15,
                cell_w * idx, panel_height * 0.85,
                strokeColor=HexColor("#3d4556"),
                strokeWidth=0.5,
            )
            d.add(div)

        # Large value text
        val_str = String(
            cx,
            panel_height * 0.45,
            str(value),
            fontName=b.get("font_heading", "Helvetica-Bold"),
            fontSize=28,
            fillColor=white,
            textAnchor="middle",
        )
        d.add(val_str)

        # Smaller label text below value
        lbl_str = String(
            cx,
            panel_height * 0.22,
            str(label),
            fontName=b.get("font_body", "Helvetica"),
            fontSize=9,
            fillColor=HexColor("#a0aec0"),
            textAnchor="middle",
        )
        d.add(lbl_str)

    return d
