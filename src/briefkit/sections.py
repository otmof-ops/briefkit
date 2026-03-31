"""
briefkit.sections
~~~~~~~~~~~~~~~~~
Public re-export surface for template authors.

Templates should import from this module rather than reaching into
generator.py internals. This decouples template implementations from
the generator's internal organization.
"""
from briefkit.generator import (
    BaseBriefingTemplate,
    HierarchyTreeFlowable,
    detect_level,
)
from briefkit.styles import (
    _get_brand, _hex, _ps, _safe_para, _safe_text,
    CONTENT_WIDTH, GUTTER, MARGIN_TOP, MARGIN_BOTTOM, MARGIN_LEFT, MARGIN_RIGHT,
    build_styles,
)
from briefkit.elements.cover import build_cover_page
from briefkit.elements.header_footer import build_classification_banner, make_header_footer
from briefkit.elements.toc import build_toc
from briefkit.elements.callout import build_callout_box, build_pull_quote
from briefkit.elements.dashboard import build_metric_dashboard
from briefkit.elements.tables import build_data_table
from briefkit.elements.charts import build_bar_chart, build_timeline

__all__ = [
    "BaseBriefingTemplate",
    "HierarchyTreeFlowable",
    "detect_level",
    "_get_brand", "_hex", "_ps", "_safe_para", "_safe_text",
    "CONTENT_WIDTH", "GUTTER", "MARGIN_TOP", "MARGIN_BOTTOM", "MARGIN_LEFT", "MARGIN_RIGHT",
    "build_styles",
    "build_cover_page",
    "build_classification_banner", "make_header_footer",
    "build_toc",
    "build_callout_box", "build_pull_quote",
    "build_metric_dashboard",
    "build_data_table",
    "build_bar_chart", "build_timeline",
]
