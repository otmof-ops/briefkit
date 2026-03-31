"""
briefkit.elements.tables — Data and comparison table builders.

Extracted and generalized from generate-briefing-v2.py:
  - build_data_table()       original lines 1559-1620
  - build_comparison_table() original lines 1623-1689
"""

import re

from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm

from briefkit.styles import (
    _get_brand, _hex, _ps, _safe_para, _safe_text, CONTENT_WIDTH, build_styles
)

# Semantic tint colors for comparison table cell coding
_GREEN_BG = HexColor("#eafaf1")
_RED_BG   = HexColor("#fdeaea")
_GOLD_BG  = HexColor("#fef9e7")


def build_data_table(headers, rows, title=None, brand=None, content_width=None):
    """
    Build a standard data table with primary-color header and alternating rows.

    Parameters
    ----------
    headers : list of str
        Column header labels.
    rows : list of list of str
        Table data rows.  Rows are padded or truncated to match header count.
        None cells are converted to empty strings.
    title : str, optional
        Caption shown above the table.
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    list
        List of flowables: optional Paragraph caption + Table.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth as sw

    b       = _get_brand(brand)
    cw      = content_width or CONTENT_WIDTH
    styles  = build_styles(b)
    primary = _hex(b, "primary")
    rule    = _hex(b, "rule")

    table_alt = HexColor(b.get("table_alt", "#f8f9fa"))

    flowables = []
    if title:
        flowables.append(Paragraph(title, styles["STYLE_CAPTION"]))
        flowables.append(Spacer(1, 2))

    if not headers:
        return flowables

    col_count = len(headers)

    header_row = [
        _safe_para(f"<b>{_safe_text(str(h))}</b>", styles["STYLE_TABLE_HEADER"])
        for h in headers
    ]

    if not rows:
        rows = [["No data available"] + [""] * (col_count - 1)]

    table_data = [header_row]
    for row in rows:
        sanitised = [("" if cell is None else cell) for cell in row]
        padded    = list(sanitised) + [""] * max(0, col_count - len(sanitised))
        padded    = padded[:col_count]
        table_data.append([
            _safe_para(str(cell), styles["STYLE_TABLE_BODY"]) for cell in padded
        ])

    # Content-aware column widths based on header text
    heading_font = b.get("font_heading", "Helvetica-Bold")
    raw = [sw(str(h), heading_font, 9) + 16 for h in headers]
    total_raw = sum(raw) or 1
    if total_raw > cw:
        col_widths = [w * cw / total_raw for w in raw]
    else:
        extra = cw - total_raw
        col_widths = [w + extra * (w / total_raw) for w in raw]
    col_widths = [max(w, 15 * mm) for w in col_widths]

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  primary),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  white),
        ("FONTNAME",      (0, 0), (-1, 0),  b.get("font_heading", "Helvetica-Bold")),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("GRID",          (0, 0), (-1, -1), 0.4, rule),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, table_alt]),
    ]))
    flowables.append(t)
    return flowables


def build_comparison_table(headers, rows, brand=None, content_width=None):
    """
    Build a comparison table with color-coded cells.

    Positive values ('+', 'Yes', checkmark, 'True', 'Supported',
    'Available') receive a green background.
    Negative values ('-', 'No', 'x', 'False', 'Unsupported',
    'Unavailable') receive a red background.
    Partial values ('~', 'Partial', 'Limited', 'Optional') receive a
    gold background.
    The first column is treated as a row-label column (bold, no color
    coding applied).

    Parameters
    ----------
    headers : list of str
        Column header labels.
    rows : list of list of str
        Table data rows.
    brand : dict, optional
        Brand config dict.

    Returns
    -------
    list
        List of flowables: Table (possibly preceded by a caption if provided
        via the title parameter — use build_data_table for captioned tables).
    """
    b       = _get_brand(brand)
    cw      = content_width or CONTENT_WIDTH
    styles  = build_styles(b)
    primary = _hex(b, "primary")
    rule    = _hex(b, "rule")

    table_alt = HexColor(b.get("table_alt", "#f8f9fa"))

    flowables = []

    if not headers:
        return flowables

    col_count = len(headers)
    col_width = cw / col_count

    header_row = [
        _safe_para(f"<b>{_safe_text(str(h))}</b>", styles["STYLE_TABLE_HEADER"])
        for h in headers
    ]
    table_data = [header_row]

    if not rows:
        rows = [["No data available"] + [""] * (col_count - 1)]

    for row in rows:
        sanitised = [("" if cell is None else cell) for cell in row]
        padded    = list(sanitised) + [""] * max(0, col_count - len(sanitised))
        padded    = padded[:col_count]
        table_data.append([
            _safe_para(str(c), styles["STYLE_TABLE_BODY"]) for c in padded
        ])

    t = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)

    style_commands = [
        ("BACKGROUND",   (0, 0), (-1, 0),  primary),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  white),
        ("FONTNAME",     (0, 0), (-1, 0),  b.get("font_heading", "Helvetica-Bold")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("GRID",         (0, 0), (-1, -1), 0.4, rule),
        ("FONTNAME",     (0, 1), (0, -1),  b.get("font_heading", "Helvetica-Bold")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [white, table_alt]),
    ]

    positive_pat = re.compile(r'^(\+|yes|✓|check|true|supported|available)', re.I)
    negative_pat = re.compile(r'^(\-|no|✗|x|false|unsupported|unavailable)', re.I)
    partial_pat  = re.compile(r'^(~|partial|limited|optional)', re.I)

    for r_idx, row in enumerate(rows, start=1):
        padded = list(row) + [""] * max(0, col_count - len(row))
        for c_idx in range(1, col_count):
            cell_val = str(padded[c_idx]).strip()
            if positive_pat.match(cell_val):
                style_commands.append(("BACKGROUND", (c_idx, r_idx), (c_idx, r_idx), _GREEN_BG))
            elif negative_pat.match(cell_val):
                style_commands.append(("BACKGROUND", (c_idx, r_idx), (c_idx, r_idx), _RED_BG))
            elif partial_pat.match(cell_val):
                style_commands.append(("BACKGROUND", (c_idx, r_idx), (c_idx, r_idx), _GOLD_BG))

    t.setStyle(TableStyle(style_commands))
    flowables.append(t)
    return flowables
