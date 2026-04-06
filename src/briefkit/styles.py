"""
briefkit.styles — Shared style builders and text utilities.

Extracted and generalized from generate-briefing-v2.py.
All styles accept a brand dict; a DEFAULT_BRAND fallback is provided.
"""

import functools
import re
import unicodedata
import xml.sax.saxutils

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph

# =============================================================================
# DEFAULT BRAND
# =============================================================================

DEFAULT_BRAND = {
    "primary":      "#1B2A4A",
    "secondary":    "#2E86AB",
    "accent":       "#E8C547",
    "body_text":    "#2C2C2C",
    "caption":      "#666666",
    "background":   "#FFFFFF",
    "rule":         "#CCCCCC",
    "success":      "#00b894",
    "warning":      "#fdcb6e",
    "danger":       "#d63031",
    "code_bg":      "#f5f6fa",
    "table_alt":    "#f8f9fa",
    "font_body":    "Helvetica",
    "font_heading": "Helvetica-Bold",
    "font_mono":    "Courier",
    "font_caption": "Helvetica-Oblique",
    "org":          "",
    "tagline":      "",
    "abn":          "",
    "logo":         "",
    "copyright":    "\u00a9 {year}",
    "url":          "",
}


_SAFE_FONTS = frozenset({
    'Courier', 'Courier-Bold', 'Courier-Oblique', 'Courier-BoldOblique',
    'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique', 'Helvetica-BoldOblique',
    'Times-Roman', 'Times-Bold', 'Times-Italic', 'Times-BoldItalic',
})


def _get_brand(brand=None):
    """Return a fully populated brand dict, merging with DEFAULT_BRAND."""
    if brand is None:
        return dict(DEFAULT_BRAND)
    key = tuple(sorted(brand.items()))
    return _get_brand_cached(key)


@functools.lru_cache(maxsize=32)
def _get_brand_cached(brand_key):
    merged = dict(DEFAULT_BRAND)
    merged.update(dict(brand_key))
    return merged


def _hex(brand, key):
    """Return a HexColor for the given brand key."""
    return HexColor(brand[key])


# =============================================================================
# PAGE LAYOUT CONSTANTS
# =============================================================================

PAGE_SIZE      = A4
MARGIN_TOP     = 25 * mm
MARGIN_BOTTOM  = 20 * mm
MARGIN_LEFT    = 20 * mm
MARGIN_RIGHT   = 20 * mm
CONTENT_WIDTH  = 170 * mm   # 210mm - 20mm left - 20mm right
GUTTER         = 8 * mm


def compute_content_width(page_size=None, margins=None):
    """Calculate content width from page size and margins."""
    if page_size is None:
        from reportlab.lib.pagesizes import A4
        page_size = A4
    if margins is None:
        margins = {}
    left = margins.get("left", 20) * mm
    right = margins.get("right", 20) * mm
    return page_size[0] - left - right


def truncate_to_width(text, font_name, font_size, max_width):
    """Truncate text with ellipsis if it exceeds max_width in given font."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    if not text:
        return text
    if stringWidth(str(text), font_name, font_size) <= max_width:
        return str(text)
    t = str(text)
    while t and stringWidth(t + "...", font_name, font_size) > max_width:
        t = t[:-1]
    return t + "..." if t else "..."


def get_layout(page_size=None):
    """
    Return a dict of page layout constants.

    page_size: a reportlab page size tuple (width, height).
               Defaults to A4.
    """
    ps = page_size or A4
    width, height = ps
    ml = MARGIN_LEFT
    mr = MARGIN_RIGHT
    mt = MARGIN_TOP
    mb = MARGIN_BOTTOM
    return {
        "page_size":     ps,
        "page_width":    width,
        "page_height":   height,
        "margin_top":    mt,
        "margin_bottom": mb,
        "margin_left":   ml,
        "margin_right":  mr,
        "content_width": width - ml - mr,
        "gutter":        GUTTER,
    }


# =============================================================================
# TEXT UTILITIES
# =============================================================================

def _safe_text(text):
    """Sanitize text for ReportLab's XML parser.

    ReportLab's Paragraph uses an XML parser that chokes on:
    - Bare < and > (must be &lt; &gt;)
    - Improperly nested tags (<b><i>text</b></i>)
    - Unknown tags
    - Very long words (URLs, hex strings) with no whitespace

    This function escapes raw text to be safe for Paragraph().
    """
    if not text:
        return ""
    # Normalise unicode — handle accented characters in filenames
    try:
        text = unicodedata.normalize("NFC", text)
    except (ValueError, TypeError):
        pass
    # Escape bare < > that aren't part of allowed ReportLab tags.
    # Strategy: escape ALL < > then unescape the allowed ones.
    text = xml.sax.saxutils.escape(text)
    # Restore allowed tags
    for tag in ['b', 'i', 'u', 'br/', 'br', 'super', 'sub', 'strike']:
        text = text.replace(f'&lt;{tag}&gt;', f'<{tag}>')
        text = text.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
    # Restore font tags with attributes
    text = re.sub(r'&lt;font ([^&]+)&gt;', r'<font \1>', text)
    text = text.replace('&lt;/font&gt;', '</font>')

    # After restoring font tags, sanitize attributes to allowlist
    def _sanitize_font_attrs(match):
        tag_content = match.group(1)
        parts = []
        # Only allow name= with safe font families
        name_match = re.search(r'name="([^"]*)"', tag_content)
        if name_match and name_match.group(1) in _SAFE_FONTS:
            parts.append(f'name="{name_match.group(1)}"')
        else:
            parts.append('name="Courier"')
        # Allow size= with numeric values only
        size_match = re.search(r'size="(\d+(?:\.\d+)?)"', tag_content)
        if size_match:
            parts.append(f'size="{size_match.group(1)}"')
        # Allow color= with hex values only
        color_match = re.search(r'color="(#[0-9A-Fa-f]{6})"', tag_content)
        if color_match:
            parts.append(f'color="{color_match.group(1)}"')
        return f'<font {" ".join(parts)}>'

    text = re.sub(r'<font ([^>]+)>', _sanitize_font_attrs, text)

    # Close any unclosed tags (from content truncation mid-tag)
    open_tags = re.findall(r'<(b|i|u|font|strike)[^>]*>', text)
    close_tags = re.findall(r'</(b|i|u|font|strike)>', text)
    for tag in reversed(open_tags[len(close_tags):]):
        text += f'</{tag}>'

    # Insert zero-width spaces in very long words to prevent Paragraph overflow
    def _break_long_word(m):
        word = m.group(0)
        if len(word) > 60:
            return '&#8203;'.join(word[i:i+60] for i in range(0, len(word), 60))
        return word
    text = re.sub(r'\S{61,}', _break_long_word, text)
    return text


def _safe_para(text, style):
    """Create a Paragraph with sanitized text. Never raises on bad markup."""
    try:
        return Paragraph(_safe_text(text), style)
    except Exception:
        clean = re.sub(r'<[^>]+>', '', text)
        clean = clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        try:
            return Paragraph(clean, style)
        except Exception:
            return Paragraph("", style)


def _ps(name, brand=None, **kw):
    """
    Build a ParagraphStyle with sane defaults, overridden by kw.

    brand: optional brand dict; used for default textColor if not overridden.
    """
    b = _get_brand(brand)
    defaults = {
        "fontName":  b.get("font_body", "Helvetica"),
        "textColor": _hex(b, "body_text"),
        "spaceAfter": 6,
        "spaceBefore": 0,
        "leading":   14,
    }
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


# =============================================================================
# NAMED STYLE BUILDERS
# =============================================================================

def build_styles(brand=None):
    """
    Return a dict of all named ParagraphStyle objects using brand colors.
    Results are cached per unique brand configuration.
    """
    b = _get_brand(brand)
    key = tuple(sorted(b.items()))
    return _build_styles_cached(key)


@functools.lru_cache(maxsize=32)
def _build_styles_cached(brand_key):
    """Cached implementation of build_styles."""
    b = dict(brand_key)

    primary   = _hex(b, "primary")
    secondary = _hex(b, "secondary")
    body_text = _hex(b, "body_text")
    caption   = _hex(b, "caption")
    # Derived semantic aliases matching source conventions
    otm_navy  = primary
    otm_steel = secondary
    bg_grey   = HexColor(b.get("code_bg", "#f5f6fa"))
    table_alt = HexColor(b.get("table_alt", "#f8f9fa"))

    styles = {}

    styles["STYLE_TITLE"] = _ps(
        "BKTitle",
        brand=b,
        fontName=b.get("font_heading", "Helvetica-Bold"),
        fontSize=28,
        textColor=otm_navy,
        leading=34,
        spaceAfter=12,
        spaceBefore=0,
        alignment=1,
    )

    styles["STYLE_H1"] = _ps(
        "BKH1",
        brand=b,
        fontName=b.get("font_heading", "Helvetica-Bold"),
        fontSize=18,
        textColor=otm_navy,
        leading=22,
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True,
    )

    styles["STYLE_H2"] = _ps(
        "BKH2",
        brand=b,
        fontName=b.get("font_heading", "Helvetica-Bold"),
        fontSize=14,
        textColor=otm_navy,
        leading=18,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    styles["STYLE_H3"] = _ps(
        "BKH3",
        brand=b,
        fontName=b.get("font_heading", "Helvetica-Bold"),
        fontSize=12,
        textColor=otm_steel,
        leading=16,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    styles["STYLE_BODY"] = _ps(
        "BKBody",
        brand=b,
        fontSize=10,
        leading=15,
        spaceAfter=6,
        spaceBefore=0,
    )

    styles["STYLE_TABLE_HEADER"] = _ps(
        "BKTableHeader",
        brand=b,
        fontName=b.get("font_heading", "Helvetica-Bold"),
        fontSize=9,
        textColor=white,
        leading=12,
        spaceAfter=0,
        spaceBefore=0,
    )

    styles["STYLE_TABLE_BODY"] = _ps(
        "BKTableBody",
        brand=b,
        fontSize=9,
        textColor=body_text,
        leading=12,
        spaceAfter=0,
        spaceBefore=0,
    )

    styles["STYLE_CAPTION"] = _ps(
        "BKCaption",
        brand=b,
        fontName=b.get("font_caption", "Helvetica-Oblique"),
        fontSize=8,
        textColor=caption,
        leading=11,
        spaceAfter=4,
    )

    styles["STYLE_FOOTER"] = _ps(
        "BKFooter",
        brand=b,
        fontSize=7,
        textColor=caption,
        leading=9,
        spaceAfter=0,
    )

    styles["STYLE_CODE"] = _ps(
        "BKCode",
        brand=b,
        fontName=b.get("font_mono", "Courier"),
        fontSize=9,
        textColor=otm_steel,
        leading=13,
        spaceAfter=6,
        backColor=bg_grey,
        leftIndent=6,
        rightIndent=6,
    )

    styles["STYLE_CALLOUT"] = _ps(
        "BKCallout",
        brand=b,
        fontSize=10,
        textColor=otm_steel,
        leading=15,
        spaceAfter=4,
        leftIndent=8,
    )

    styles["STYLE_METRIC_NUMBER"] = _ps(
        "BKMetricNumber",
        brand=b,
        fontName=b.get("font_heading", "Helvetica-Bold"),
        fontSize=36,
        textColor=white,
        leading=42,
        alignment=1,
        spaceAfter=0,
    )

    styles["STYLE_METRIC_LABEL"] = _ps(
        "BKMetricLabel",
        brand=b,
        fontSize=10,
        textColor=white,
        leading=13,
        alignment=1,
        spaceAfter=0,
    )

    styles["STYLE_PULL_QUOTE"] = _ps(
        "BKPullQuote",
        brand=b,
        fontName=b.get("font_caption", "Helvetica-Oblique"),
        fontSize=14,
        textColor=otm_navy,
        leading=20,
        alignment=1,
        spaceAfter=4,
        leftIndent=20,
        rightIndent=20,
    )

    styles["STYLE_INDEX_TERM"] = _ps(
        "BKIndexTerm",
        brand=b,
        fontSize=8,
        textColor=body_text,
        leading=11,
        spaceAfter=2,
    )

    styles["STYLE_LIST_ITEM"] = _ps(
        "BKListItem",
        brand=b,
        fontSize=10,
        textColor=body_text,
        leading=14,
        leftIndent=12,
        spaceAfter=2,
    )

    # Store derived colors on the dict for use by element builders
    styles["_primary"]   = otm_navy
    styles["_secondary"] = otm_steel
    styles["_caption"]   = caption
    styles["_body_text"] = body_text
    styles["_bg_grey"]   = bg_grey
    styles["_table_alt"] = table_alt

    return styles


# Public aliases for template authors (prefer these over underscore-prefixed versions)
get_brand = _get_brand
hex_color = _hex
make_style = _ps
safe_para = _safe_para
safe_text = _safe_text
