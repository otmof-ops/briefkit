"""
briefkit.elements — Visual element builder modules.

All builders accept a ``brand`` dict parameter for customizing colors and
organization text.  Falls back to DEFAULT_BRAND when ``brand`` is omitted.

Available builders
------------------
cover
  build_cover_page(title, subtitle, path, level, date, doc_id="", brand=None)

header_footer
  header_footer(canvas, doc)
  make_header_footer(state, brand=None)
  build_classification_banner(level, path, brand=None)

toc
  build_toc(sections, brand=None)

callouts  (canonical callout/pull-quote module)
  build_callout_box(text, box_type="insight", brand=None)
  build_pull_quote(text, attribution="", brand=None)

callout  (thin alias — delegates to callouts)
  build_callout_box

dashboard
  build_metric_dashboard(metrics, brand=None)

tables
  build_data_table(headers, rows, title=None, brand=None)
  build_comparison_table(headers, rows, brand=None)

charts
  build_bar_chart(data, title="", brand=None)
  build_pull_quote  (re-exported from callouts)

back_cover
  build_back_cover(date=None, generator_note="", brand=None)
"""

from briefkit.elements.back_cover import build_back_cover
from briefkit.elements.callout import build_callout_box, build_pull_quote
from briefkit.elements.charts import build_bar_chart, build_timeline
from briefkit.elements.cover import build_cover_page
from briefkit.elements.dashboard import build_metric_dashboard
from briefkit.elements.header_footer import (
    _hf_state,
    build_classification_banner,
    header_footer,
    make_header_footer,
)
from briefkit.elements.tables import build_comparison_table, build_data_table
from briefkit.elements.toc import build_toc

__all__ = [
    "build_cover_page",
    "header_footer",
    "make_header_footer",
    "build_classification_banner",
    "_hf_state",
    "build_toc",
    "build_callout_box",
    "build_pull_quote",
    "build_metric_dashboard",
    "build_data_table",
    "build_comparison_table",
    "build_bar_chart",
    "build_timeline",
    "build_back_cover",
]
